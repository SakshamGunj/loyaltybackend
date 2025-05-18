from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Union
from datetime import datetime

from ... import crud, schemas, models # Assuming loyalty_backend/app is the root for these
from ...database import get_db
from ...auth.custom_auth import get_current_user, TokenData # For authentication/authorization
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    # prefix="/coupons", # Prefix is already in main.py
    tags=["coupons"]
)

# --- Helper for Admin Check ---
def verify_system_admin(current_user: TokenData):
    if not current_user or current_user.role != "system_admin":
        # More specific roles can be added later, e.g., "coupon_manager"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have sufficient privileges for this operation."
        )

# --- Helper for Restaurant Admin/Owner or System Admin Check ---
# Similar to the one in employees.py, but generalized for coupons if they become restaurant-specific.
async def verify_coupon_management_permission(
    db: Session, 
    restaurant_id: Optional[str], 
    current_user: TokenData,
    required_permission: Optional[str] = "manage_coupons" # Define a specific permission
):
    if current_user.role == "system_admin":
        return # System admin has global access

    if not restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restaurant ID is required for this operation for non-system admins."
        )

    restaurant = db.query(models.Restaurant).filter(models.Restaurant.restaurant_id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Restaurant with ID {restaurant_id} not found")

    is_owner = restaurant.admin_uid == current_user.uid
    
    has_permission = False
    if not is_owner: # Non-owners need explicit permission
        user_details = db.query(models.User).filter(
            models.User.uid == current_user.uid, 
            models.User.restaurant_id == restaurant_id
        ).first()
        if user_details and user_details.permissions and required_permission in user_details.permissions:
            has_permission = True
            
    if not is_owner and not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"User does not own restaurant {restaurant_id} or lacks \'{required_permission}\' permission."
        )
    return restaurant


# --- API Endpoints ---

@router.post("/create", response_model=schemas.StandardResponse, status_code=status.HTTP_201_CREATED)
async def create_coupons_endpoint(
    request_data: schemas.CouponCreateRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Create one or more coupon codes based on the provided definition.
    - System admins can create coupons for any restaurant or global coupons.
    - Restaurant admins/owners can create coupons for their own restaurant if restaurant_id is provided.
    """
    logger.info(f"User {current_user.uid} attempting to create coupons with data: {request_data.dict()}")

    if request_data.restaurant_id:
        await verify_coupon_management_permission(db, request_data.restaurant_id, current_user, "manage_coupons")
    else: # Global coupon or coupon where restaurant context isn't primary for creation (system admin)
        verify_system_admin(current_user) # Only system admins can create non-restaurant-assigned coupons this way

    if request_data.total_coupons_to_generate <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="total_coupons_to_generate must be positive.")

    # Validate coupon type specific fields
    if request_data.coupon_type == schemas.CouponType.FIXED_AMOUNT and request_data.discount_value is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="discount_value is required for fixed_amount coupons.")
    if request_data.coupon_type == schemas.CouponType.PERCENTAGE and request_data.discount_percentage is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="discount_percentage is required for percentage coupons.")
    if request_data.coupon_type == schemas.CouponType.FREE_ITEM and request_data.menu_item_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="menu_item_id is required for free_item coupons.")
    if request_data.coupon_type == schemas.CouponType.CATEGORY_OFFER and request_data.menu_category_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="menu_category_id is required for category_offer coupons.")
    if request_data.coupon_type == schemas.CouponType.CATEGORY_OFFER and request_data.category_offer_type is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="category_offer_type is required for category_offer coupons.")


    created_coupon_codes = []
    # Potentially create a "master" coupon if total_coupons_to_generate > 1 and a linking mechanism is desired.
    # For now, each generated coupon is independent but shares properties from CouponCreateRequest.
    
    # The CouponCreateRequest does not have a `code` field.
    # It has `name`, `coupon_type`, etc.
    # crud.create_coupon_instance expects schemas.CouponCreateInternal which includes `code`.

    parent_coupon_db: Optional[models.Coupon] = None

    # If we are generating multiple unique codes for the same campaign, 
    # we might want to create a "parent" conceptual coupon and link individuals to it.
    # For now, we'll create individual coupons based on the request.
    # If `request_data.total_coupons_to_generate > 1` and they should be linked, a parent_coupon_id mechanism is in the model.

    for i in range(request_data.total_coupons_to_generate):
        try:
            # Generate a unique code for each coupon instance
            # The uniqueness check is now handled within generate_coupon_code
            unique_code = crud.generate_coupon_code(db, length=8, prefix="C")

            coupon_instance_data = schemas.CouponCreateInternal(
                code=unique_code,
                name=request_data.name,
                description=request_data.description,
                coupon_type=request_data.coupon_type,
                discount_value=request_data.discount_value,
                discount_percentage=request_data.discount_percentage,
                menu_item_id=request_data.menu_item_id,
                menu_category_id=request_data.menu_category_id,
                category_offer_type=request_data.category_offer_type,
                start_date=request_data.start_date,
                end_date=request_data.end_date,
                usage_limit=request_data.usage_limit, # This is total uses for this specific code
                per_user_limit=request_data.per_user_limit, # How many times a user can use THIS code
                assigned_user_ids=request_data.assigned_user_ids,
                is_active=True, # New coupons are active by default
                restaurant_id=request_data.restaurant_id,
                # parent_coupon_id can be set here if a master/parent concept is fully implemented
            )
            db_coupon = crud.create_coupon_instance(db, coupon_instance_data)
            created_coupon_codes.append(schemas.CouponCodeResponseItem(id=db_coupon.id, code=db_coupon.code))
        except Exception as e:
            logger.error(f"Error generating coupon code instance: {e}", exc_info=True)
            # If one fails, should we roll back others or collect failures?
            # For now, we continue and report, but a transaction for all might be better.
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate one or more coupon codes: {str(e)}")
            
    return schemas.StandardResponse(
        message=f"Successfully created {len(created_coupon_codes)} coupon(s).",
        data=created_coupon_codes
    )


@router.get("/admin-list/", response_model=List[schemas.CouponOut])
async def list_all_coupons_admin(
    skip: int = 0,
    limit: int = 100,
    coupon_type: Optional[schemas.CouponType] = Query(None),
    is_active: Optional[bool] = Query(None),
    restaurant_id: Optional[str] = Query(None), # Filter by restaurant
    valid_on_date: Optional[datetime] = Query(None),
    search_code: Optional[str] = Query(None),
    search_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    List all coupons. Admin access required.
    System admins can see all. Restaurant admins see their own if restaurant_id not forced by system admin.
    """
    # If the user is a system admin, they can list any restaurant's coupons or all.
    # If they are a restaurant admin, they should only be able to list their own restaurant's coupons.
    effective_restaurant_id = restaurant_id
    if current_user.role != "system_admin":
        if not current_user.restaurant_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not associated with a restaurant.")
        if restaurant_id and restaurant_id != current_user.restaurant_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot list coupons for another restaurant.")
        effective_restaurant_id = current_user.restaurant_id # Force their own restaurant
    # If system admin and restaurant_id is provided, it filters by that. If not, lists all.

    coupons = crud.list_coupons(
        db, skip=skip, limit=limit, 
        coupon_type=coupon_type, is_active=is_active, 
        restaurant_id=effective_restaurant_id, 
        valid_on_date=valid_on_date,
        search_code=search_code, search_name=search_name
    )
    return coupons


@router.get("/{coupon_identifier}", response_model=schemas.CouponOut)
async def get_single_coupon(
    coupon_identifier: Union[int, str], # Can be ID (int) or Code (str)
    db: Session = Depends(get_db)
    # current_user: TokenData = Depends(get_current_user) # Optional: if access needs to be restricted
):
    """
    Get a specific coupon by its ID or unique code.
    This endpoint can be public or restricted based on requirements.
    Currently, it's public.
    """
    coupon = None
    if isinstance(coupon_identifier, int) or coupon_identifier.isdigit():
        coupon = crud.get_coupon_by_id(db, int(coupon_identifier))
    else:
        coupon = crud.get_coupon_by_code(db, str(coupon_identifier))
    
    if not coupon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found.")
    if not coupon.is_active: # Or based on dates
        # Decide if inactive/expired coupons should be hidden or shown with a status
        logger.info(f"Attempt to access inactive/expired coupon ID/Code: {coupon_identifier}")
        # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon is not active or has expired.")
        # For now, let's return it but client should check dates/active status from response.

    return coupon


@router.put("/{coupon_id}", response_model=schemas.CouponOut)
async def update_existing_coupon(
    coupon_id: int,
    coupon_update_data: schemas.CouponBase, # CouponBase contains all updatable fields except 'code'
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Update an existing coupon. Admin access required.
    System admins can update any. Restaurant admins can update their own.
    """
    db_coupon = crud.get_coupon_by_id(db, coupon_id)
    if not db_coupon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found to update.")

    if db_coupon.restaurant_id:
        await verify_coupon_management_permission(db, db_coupon.restaurant_id, current_user, "manage_coupons")
    else: # Global coupon
        verify_system_admin(current_user)

    # Prevent changing restaurant_id or parent_coupon_id via this general update if not intended
    if coupon_update_data.restaurant_id and coupon_update_data.restaurant_id != db_coupon.restaurant_id:
         verify_system_admin(current_user) # Only system admin can re-assign restaurant
    
    updated_coupon = crud.update_coupon(db, coupon_id, coupon_update_data)
    if not updated_coupon:
        # This case should ideally be covered by the get_coupon_by_id check above
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found during update process.")
    return updated_coupon


@router.delete("/{coupon_id}", response_model=schemas.StandardResponse)
async def deactivate_existing_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Deactivate a coupon (sets is_active=False). Admin access required.
    System admins can deactivate any. Restaurant admins can deactivate their own.
    """
    db_coupon = crud.get_coupon_by_id(db, coupon_id)
    if not db_coupon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found to deactivate.")

    if db_coupon.restaurant_id:
        await verify_coupon_management_permission(db, db_coupon.restaurant_id, current_user, "manage_coupons")
    else: # Global coupon
        verify_system_admin(current_user)
        
    deactivated_coupon = crud.deactivate_coupon(db, coupon_id)
    if not deactivated_coupon:
         # This case should ideally be covered by the get_coupon_by_id check above
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found during deactivation.")

    return schemas.StandardResponse(message=f"Coupon ID {coupon_id} deactivated successfully.")

@router.post("/validate-apply", response_model=schemas.CouponValidationDetail, status_code=status.HTTP_200_OK)
async def validate_and_apply_coupon(
    apply_request: schemas.CouponApplyRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user) # Ensure user is authenticated
):
    """
    Validates a coupon code for a given user and context (restaurant).
    If valid, records its usage and returns coupon details.
    If apply_request.user_uid is not provided, it defaults to the current authenticated user.
    """
    logger.info(f"User {current_user.uid} attempting to validate/apply coupon: {apply_request.coupon_code} for restaurant {apply_request.restaurant_id}, request user_uid: {apply_request.user_uid}")

    effective_user_uid = current_user.uid
    if apply_request.user_uid:
        if apply_request.user_uid != current_user.uid:
            logger.warning(f"Attempt to apply coupon for user {apply_request.user_uid} by authenticated user {current_user.uid}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot apply coupon for a different user if user_uid is specified in request."
            )
        effective_user_uid = apply_request.user_uid # Use the validated request user_uid
    
    # If effective_user_uid is still None here, it means current_user.uid was None, which shouldn't happen with get_current_user dependency
    # but as a safeguard if auth is optional later.
    if not effective_user_uid:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User context is required to validate coupon per-user limits or assignments."
        )

    coupon = crud.get_coupon_by_code(db, code=apply_request.coupon_code)

    if not coupon:
        return schemas.CouponValidationDetail(is_valid=False, message="Coupon code not found.")

    # Prepare response data from coupon model
    response_data = {
        "coupon_id": coupon.id,
        "code": coupon.code,
        "name": coupon.name,
        "coupon_type": coupon.coupon_type,
        "discount_value": coupon.discount_value,
        "discount_percentage": coupon.discount_percentage,
        "menu_item_id": coupon.menu_item_id,
        "menu_category_id": coupon.menu_category_id,
        "category_offer_type": coupon.category_offer_type
    }

    if not coupon.is_active:
        return schemas.CouponValidationDetail(**response_data, is_valid=False, message="Coupon is not active.")

    now = datetime.utcnow()
    if coupon.start_date > now:
        return schemas.CouponValidationDetail(**response_data, is_valid=False, message=f"Coupon is not yet valid. Starts at {coupon.start_date}.")
    if coupon.end_date < now:
        return schemas.CouponValidationDetail(**response_data, is_valid=False, message=f"Coupon has expired on {coupon.end_date}.")

    # Check restaurant compatibility
    if coupon.restaurant_id and coupon.restaurant_id != apply_request.restaurant_id:
        return schemas.CouponValidationDetail(**response_data, is_valid=False, message=f"Coupon is not valid for this restaurant. Expected {coupon.restaurant_id}, got {apply_request.restaurant_id}")

    # Check total usage limit
    if coupon.usage_limit > 0:
        total_uses = crud.get_coupon_total_usage_count(db, coupon_id=coupon.id)
        if total_uses >= coupon.usage_limit:
            return schemas.CouponValidationDetail(**response_data, is_valid=False, message="Coupon has reached its total usage limit.")

    # Check per-user usage limit using effective_user_uid
    if coupon.per_user_limit > 0:
        user_uses = crud.get_user_coupon_usage_count(db, coupon_id=coupon.id, user_uid=effective_user_uid)
        if user_uses >= coupon.per_user_limit:
            return schemas.CouponValidationDetail(**response_data, is_valid=False, message="You have already used this coupon the maximum number of times.")

    # Check if coupon is assigned to specific users, using effective_user_uid
    if coupon.assigned_user_ids:
        if effective_user_uid not in coupon.assigned_user_ids:
            return schemas.CouponValidationDetail(**response_data, is_valid=False, message="This coupon is not assigned to you.")

    # If all checks pass, coupon is valid. Record its usage.
    try:
        crud.record_coupon_usage(db, coupon_id=coupon.id, user_uid=effective_user_uid, order_id=apply_request.order_id)
    except Exception as e:
        logger.error(f"Failed to record coupon usage for coupon ID {coupon.id}, user {effective_user_uid}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not record coupon usage. Please try again.")

    return schemas.CouponValidationDetail(**response_data, is_valid=True, message="Coupon applied successfully.")

# TODO:
# - Add endpoint for a user to check coupon validity against their cart/order context.
# - Add endpoints for users to view their available/assigned coupons.
# - Refine authorization:
#   - `verify_coupon_management_permission` can be made more robust.
#   - Consider specific permissions like `create_global_coupon`, `create_restaurant_coupon`, etc.

# Example of using CouponUsage (not a direct endpoint here, but for context)
# async def apply_coupon_to_order(order_id: str, coupon_code: str, user_uid: str, db: Session):
#     coupon = crud.get_coupon_by_code(db, coupon_code)
#     if not coupon: raise HTTPException(404, "Coupon invalid")
#     if not coupon.is_active or coupon.start_date > datetime.utcnow() or coupon.end_date < datetime.utcnow():
#         raise HTTPException(400, "Coupon not active or expired")
        
#     total_usage = crud.get_coupon_total_usage_count(db, coupon.id)
#     if total_usage >= coupon.usage_limit:
#         raise HTTPException(400, "Coupon usage limit reached")
        
#     user_usage = crud.get_user_coupon_usage_count(db, coupon.id, user_uid)
#     if user_usage >= coupon.per_user_limit:
#         raise HTTPException(400, "You have already used this coupon the maximum number of times.")
        
#     # ... further validation based on coupon_type, items in order, etc. ...
    
#     # If valid, record usage
#     crud.record_coupon_usage(db, coupon.id, user_uid, order_id)
#     # ... apply discount to order ...
#     return {"message": "Coupon applied"} 