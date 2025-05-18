from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from ... import schemas, crud
from ...database import get_db
from ...auth.custom_auth import get_current_user, TokenData
from typing import List

from . import tables as tables_router

router = APIRouter()

@router.post("/register-restaurant", response_model=schemas.RestaurantOut)
def register_restaurant(
    restaurant: schemas.RestaurantCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    # Logic to ensure only a specific system admin can create, or other auth logic
    # For example, if you have a role check:
    # if current_user.role != "system_admin":
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to register restaurants")
    return crud.create_restaurant(db=db, restaurant=restaurant, owner_uid=current_user.uid)

@router.put("/{restaurant_id}", response_model=schemas.RestaurantOut)
def update_restaurant(
    restaurant_id: str,
    restaurant: schemas.RestaurantCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    db_restaurant = crud.get_restaurant(db, restaurant_id)
    if not db_restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    # Authorization: Allow owner, admin_uid, or system_admin (if you have one)
    is_owner = db_restaurant.owner_uid == current_user.uid
    is_admin = db_restaurant.admin_uid == current_user.uid
    # has_permission = current_user.role == "system_admin" # Example for system admin

    # if not (is_owner or is_admin or has_permission):
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this restaurant.")
    
    # Placeholder for actual update logic using a RestaurantUpdate schema if different from Create
    # For now, assuming crud.update_restaurant exists and takes schemas.RestaurantCreate
    # updated_restaurant = crud.update_restaurant(db, restaurant_id, restaurant)
    # return updated_restaurant
    # Temporary passthrough if crud.update_restaurant doesn't exist or schema mismatch
    # This part needs to be aligned with your actual update CRUD function and schema
    temp_update_data = restaurant.dict(exclude_unset=True)
    for key, value in temp_update_data.items():
        if hasattr(db_restaurant, key):
            setattr(db_restaurant, key, value)
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant # This is a simplified update, ensure your crud.update_restaurant is robust

@router.get("/{restaurant_id}", response_model=schemas.RestaurantOut)
def get_restaurant_details(
    restaurant_id: str, 
    db: Session = Depends(get_db)
):
    db_restaurant = crud.get_restaurant(db, restaurant_id)
    if not db_restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return db_restaurant

@router.get("/", response_model=List[schemas.RestaurantOut])
def list_all_restaurants(db: Session = Depends(get_db)):
    return crud.get_restaurants(db)

router.include_router(tables_router.router, prefix="/{restaurant_id}/tables")
