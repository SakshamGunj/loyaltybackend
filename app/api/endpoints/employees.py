from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy.exc import IntegrityError
import logging

from ... import crud, schemas, models # Corrected import path
from ...database import get_db
from ...auth.custom_auth import get_current_user, TokenData
# It's good practice to also import the Restaurant model if we are verifying against it
# from ...models import Restaurant 

# Helper function (can be moved to a shared utils or be specific here)
# This is similar to verify_restaurant_admin in ordering.py, consider refactoring to a shared location if used often
async def verify_restaurant_ownership_or_permission(db: Session, restaurant_id: str, current_user: TokenData, required_permission: Optional[str] = None):
    restaurant = db.query(models.Restaurant).filter(models.Restaurant.restaurant_id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Restaurant with ID {restaurant_id} not found")

    # Check if the current user is the restaurant owner (admin_uid)
    is_owner = restaurant.admin_uid == current_user.uid
    
    has_permission = False
    if required_permission and current_user.uid != restaurant.admin_uid: # Non-owners need explicit permission
        user_details = db.query(models.User).filter(models.User.uid == current_user.uid, models.User.restaurant_id == restaurant_id).first()
        if user_details and user_details.permissions and required_permission in user_details.permissions:
            has_permission = True
            
    if not is_owner and not has_permission:
        if required_permission:
            detail_msg = f"User does not own restaurant {restaurant_id} or lacks '{required_permission}' permission."
        else: # If no specific permission required, ownership is assumed to be the check
            detail_msg = f"User does not own restaurant {restaurant_id}."
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail_msg)
    
    return restaurant


router = APIRouter(
    prefix="/restaurants/{restaurant_id}/employees", # All routes here are relative to a restaurant
    tags=["employees"]
)

@router.post("/", response_model=schemas.EmployeeOut, status_code=status.HTTP_201_CREATED)
async def create_employee_for_restaurant(
    restaurant_id: str, # From path
    employee_data: schemas.EmployeeCreate, # From request body
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Create a new employee for a specific restaurant.
    Only the restaurant owner (admin_uid) or an employee with 'manage_employees' permission can perform this.
    """
    await verify_restaurant_ownership_or_permission(db, restaurant_id, current_user, required_permission="manage_employees")

    # Check if user (email or number) already exists
    if crud.get_user_by_email(db, email=employee_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists."
        )
    if employee_data.number and crud.get_user_by_number(db, number=employee_data.number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this phone number already exists."
        )

    # Prepare data for crud.create_user, which expects schemas.UserCreate
    # Ensure restaurant_id from path is used, and set a default role if not provided
    employee_payload = employee_data.dict(exclude_unset=True)

    # Explicitly set/override restaurant_id from path and set a default role
    # This ensures that the restaurant_id from the URL path is used,
    # and a default role is applied if not specified in the request.
    user_data_for_create = {
        **employee_payload,
        "restaurant_id": restaurant_id, 
        "role": employee_payload.get("role") or "employee"
    }
    
    user_create_data = schemas.UserCreate(**user_data_for_create)
    
    try:
        created_user_model = crud.create_user(db=db, user=user_create_data)
        # Convert to EmployeeOut for the response.
        # Note: EmployeeOut inherits from UserOut, which inherits from UserBase.
        # All fields (uid, created_at, is_active, email, name, number, role, 
        # restaurant_id, designation, permissions) should be present if set.
        return schemas.EmployeeOut.from_orm(created_user_model)
    except IntegrityError as e: # Catch potential DB constraint violations not caught by prior checks
        db.rollback()
        # Log the error e for more details
        logging.error(f"Integrity error creating employee: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Failed to create employee due to a data conflict (e.g., unique constraint)."
        )
    except Exception as e:
        db.rollback()
        logging.error(f"Unexpected error creating employee: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the employee."
        )

# TODO: Add other employee CRUD endpoints (List, Get, Update, Delete)
# List Employees for a Restaurant: GET /restaurants/{restaurant_id}/employees
# Get Specific Employee: GET /restaurants/{restaurant_id}/employees/{employee_uid}

@router.put("/{employee_uid}", response_model=schemas.EmployeeOut)
async def update_employee_for_restaurant(
    restaurant_id: str,
    employee_uid: str,
    employee_update_data: schemas.UserUpdate, # Using UserUpdate schema for flexibility
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Update an employee's details for a specific restaurant.
    Only restaurant owner or user with 'manage_employees' permission can perform this.
    """
    await verify_restaurant_ownership_or_permission(db, restaurant_id, current_user, required_permission="manage_employees")

    db_employee = crud.get_user(db, uid=employee_uid)
    if not db_employee or db_employee.restaurant_id != restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with UID {employee_uid} not found in restaurant {restaurant_id}."
        )

    # Prevent changing restaurant_id via this endpoint directly if it's in UserUpdate
    # Employee reassignment should be a more specific process if needed.
    if employee_update_data.restaurant_id is not None and employee_update_data.restaurant_id != restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change employee's restaurant via this endpoint. Use specific transfer process if available."
        )
    
    # Ensure password, if provided, is not empty string or handle hashing
    if employee_update_data.password is not None:
        if not employee_update_data.password.strip(): # Check for empty or whitespace-only password
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password cannot be empty."
            )
        # Hash the new password before updating
        hashed_password = get_password_hash(employee_update_data.password)
        employee_update_data.password = hashed_password

    updated_employee = crud.update_user(db=db, uid=employee_uid, user=employee_update_data)
    if not updated_employee:
        # This case should ideally not be reached if db_employee was found earlier
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found after update attempt.")
    
    return schemas.EmployeeOut.from_orm(updated_employee)

@router.delete("/{employee_uid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee_from_restaurant(
    restaurant_id: str,
    employee_uid: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Disassociate an employee from a specific restaurant.
    This does not delete the user account but removes their employee status for this restaurant.
    Only restaurant owner or user with 'manage_employees' permission can perform this.
    """
    await verify_restaurant_ownership_or_permission(db, restaurant_id, current_user, required_permission="manage_employees")

    db_employee = crud.get_user(db, uid=employee_uid)

    if not db_employee or db_employee.restaurant_id != restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with UID {employee_uid} not found in restaurant {restaurant_id}."
        )

    disassociated_user = crud.disassociate_employee_from_restaurant(db=db, user_id=employee_uid, restaurant_id=restaurant_id)

    if not disassociated_user:
        # This might occur if the user wasn't found or wasn't an employee of this restaurant (already checked)
        # Or if disassociate_employee_from_restaurant returns None for other reasons
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Or 404 if the condition in CRUD fails for a specific reason
            detail=f"Failed to disassociate employee {employee_uid} from restaurant {restaurant_id}."
        )
    
    return None # Returns 204 No Content by default

# Update Employee: PUT /restaurants/{restaurant_id}/employees/{employee_uid}
# Delete Employee: DELETE /restaurants/{restaurant_id}/employees/{employee_uid} 