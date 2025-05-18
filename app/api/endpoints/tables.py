from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ... import crud, schemas, models # CHANGED to three dots
from ...database import get_db # CHANGED to three dots
from ...auth.custom_auth import get_current_user, TokenData # CHANGED to three dots
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Restaurant Tables"],
    # Prefix will be /restaurants/{restaurant_id}/tables, set in main app or parent router
)

# --- Helper for Table Management Permissions ---
async def verify_table_management_permission(
    db: Session,
    restaurant_id: str,
    current_user: TokenData,
    required_permission: str = "manage_tables" # Define a specific permission
):
    restaurant = crud.get_restaurant(db, restaurant_id=restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Restaurant {restaurant_id} not found")

    is_owner = restaurant.owner_uid == current_user.uid
    is_admin = restaurant.admin_uid == current_user.uid # Assuming admin_uid can also manage
    
    has_explicit_permission = False
    if not is_owner and not is_admin:
        user_details = db.query(models.User).filter(
            models.User.uid == current_user.uid,
            models.User.restaurant_id == restaurant_id
        ).first()
        if user_details and user_details.permissions and required_permission in user_details.permissions:
            has_explicit_permission = True
            
    if not is_owner and not is_admin and not has_explicit_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User lacks '{required_permission}' permission for restaurant {restaurant_id}."
        )
    return restaurant

@router.post("/", response_model=schemas.RestaurantTableOut, status_code=status.HTTP_201_CREATED)
async def add_new_table_to_restaurant(
    restaurant_id: str, 
    table_data: schemas.RestaurantTableCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    await verify_table_management_permission(db, restaurant_id, current_user)
    try:
        return crud.create_restaurant_table(db=db, restaurant_id=restaurant_id, table_data=table_data)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error creating table for restaurant {restaurant_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create table.")

@router.get("/", response_model=List[schemas.RestaurantTableOut])
async def list_restaurant_tables(
    restaurant_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user) # For auth, even if just view permission
):
    # For listing, might have a more lenient permission like "view_tables" or just being part of the restaurant staff
    # For now, using manage_tables, but this could be relaxed.
    await verify_table_management_permission(db, restaurant_id, current_user, "view_tables") # Or a new permission
    tables = crud.list_tables_by_restaurant(db, restaurant_id=restaurant_id, skip=skip, limit=limit)
    return tables

@router.get("/{table_id}", response_model=schemas.RestaurantTableOut)
async def get_specific_table_details(
    restaurant_id: str,
    table_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    await verify_table_management_permission(db, restaurant_id, current_user, "view_tables")
    table = crud.get_table_by_composed_id(db, composed_id=table_id, restaurant_id_from_path=restaurant_id)
    if not table:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Table '{table_id}' not found in restaurant {restaurant_id}")
    return table

@router.put("/{table_id}", response_model=schemas.RestaurantTableOut)
async def update_specific_table(
    restaurant_id: str,
    table_id: str,
    table_update_data: schemas.RestaurantTableUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    await verify_table_management_permission(db, restaurant_id, current_user)
    try:
        updated_table = crud.update_table_details(db, composed_id=table_id, restaurant_id=restaurant_id, update_data=table_update_data)
        if not updated_table:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Table '{table_id}' not found for update.")
        return updated_table
    except ValueError as ve: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error updating table '{table_id}' for restaurant {restaurant_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update table.")

@router.delete("/{table_id}", response_model=schemas.StandardResponse)
async def remove_table_from_restaurant(
    restaurant_id: str,
    table_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    await verify_table_management_permission(db, restaurant_id, current_user)
    if not crud.delete_restaurant_table(db, composed_id=table_id, restaurant_id=restaurant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Table '{table_id}' not found for deletion.")
    return schemas.StandardResponse(message=f"Table '{table_id}' deleted successfully from restaurant {restaurant_id}.") 