from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ... import schemas, crud
from ...database import get_db
from ...auth.custom_auth import get_current_user, TokenData
from typing import List

router = APIRouter(prefix="/api/restaurants", tags=["restaurants"])

from fastapi import Body

@router.post("/register-restaurant", response_model=schemas.RestaurantOut)
def register_restaurant(
    restaurant: schemas.RestaurantCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    # Only main admin can create restaurants
    main_admin_uid = "03f09801-ae0f-4f1b-ad07-c3030bdd28c0"
    if current_user.uid != main_admin_uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only main admin can create restaurants.")
    if not restaurant.admin_uid:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="admin_uid is required.")
    return crud.create_restaurant(db, restaurant)

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
    main_admin_uid = "qkmgiVcJhYgTpJSITv7PD6kxgn12"
    if current_user.uid != main_admin_uid and current_user.uid != db_restaurant.admin_uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can update restaurant.")
    updated_restaurant = crud.update_restaurant(db, restaurant_id, restaurant)
    return updated_restaurant

@router.get("/{restaurant_id}", response_model=schemas.RestaurantOut)
def get_restaurant(restaurant_id: str, db: Session = Depends(get_db)):
    db_restaurant = crud.get_restaurant(db, restaurant_id)
    if not db_restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return db_restaurant

@router.get("/", response_model=List[schemas.RestaurantOut])
def list_restaurants(db: Session = Depends(get_db)):
    return crud.get_restaurants(db)
