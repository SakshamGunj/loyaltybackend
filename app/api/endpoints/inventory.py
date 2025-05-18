from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from sqlalchemy.orm import Session
from typing import List, Optional

from ... import crud, schemas, models # Assuming loyalty_backend/app is the root
from ...database import get_db
from ...auth.custom_auth import get_current_user, TokenData
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/restaurants/{restaurant_id}", # All routes here are relative to a restaurant
    tags=["inventory"]
)

# --- Authorization Helper (similar to employees and coupons) ---
async def verify_restaurant_inventory_permission(
    db: Session, 
    restaurant_id: str, 
    current_user: TokenData,
    required_permission: str = "manage_inventory" 
):
    # System admin check (optional, if system admins should bypass restaurant-specific perms)
    # if current_user.role == "system_admin":
    #     restaurant = db.query(models.Restaurant).filter(models.Restaurant.restaurant_id == restaurant_id).first()
    #     if not restaurant:
    #         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Restaurant {restaurant_id} not found.")
    #     return restaurant
        
    restaurant = db.query(models.Restaurant).filter(models.Restaurant.restaurant_id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Restaurant {restaurant_id} not found")

    is_owner_or_admin = restaurant.owner_uid == current_user.uid or restaurant.admin_uid == current_user.uid
    
    has_permission = False
    if not is_owner_or_admin: # Non-owners/admins need explicit permission
        user_details = db.query(models.User).filter(
            models.User.uid == current_user.uid, 
            models.User.restaurant_id == restaurant_id # Ensure user is part of this restaurant
        ).first()
        if user_details and user_details.permissions and required_permission in user_details.permissions:
            has_permission = True
            
    if not is_owner_or_admin and not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"User lacks permission ('{required_permission}') for inventory operations in restaurant {restaurant_id}."
        )
    return restaurant

# --- API Endpoints ---

@router.post("/menu-items/{menu_item_id}/inventory", response_model=schemas.InventoryItemOut, status_code=status.HTTP_201_CREATED)
async def register_inventory_for_menu_item(
    restaurant_id: str = Path(...),
    menu_item_id: int = Path(...),
    inventory_data: schemas.InventoryItemCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):

    await verify_restaurant_inventory_permission(db, restaurant_id, current_user)

    if inventory_data.restaurant_id != restaurant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Restaurant ID in path and body must match.")
    if inventory_data.menu_item_id != menu_item_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Menu Item ID in path and body must match.")

    try:
        db_inventory_item = crud.create_inventory_item(
            db=db, 
            inventory_data=inventory_data, 
            changed_by_user_id=current_user.uid
        )
        return db_inventory_item
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Error registering inventory for menu item {menu_item_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not register inventory item.")

@router.get("/menu-items/{menu_item_id}/inventory", response_model=schemas.InventoryItemOut)
async def get_inventory_for_menu_item(
    restaurant_id: str = Path(...),
    menu_item_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user) # Assuming read access also needs permission
):
  
    await verify_restaurant_inventory_permission(db, restaurant_id, current_user, required_permission="view_inventory") # Or manage_inventory
    
    inventory_item = crud.get_inventory_item_by_menu_id(db, menu_item_id=menu_item_id, restaurant_id=restaurant_id)
    if not inventory_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory not found for menu item ID {menu_item_id}.")
    return inventory_item

@router.put("/inventory/{inventory_item_id}", response_model=schemas.InventoryItemOut)
async def adjust_inventory_stock(
    restaurant_id: str = Path(...),
    inventory_item_id: int = Path(...),
    update_payload: schemas.InventoryItemUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    
    await verify_restaurant_inventory_permission(db, restaurant_id, current_user)

    try:
        updated_inventory_item = crud.update_inventory_item_stock(
            db=db,
            inventory_item_id=inventory_item_id,
            restaurant_id=restaurant_id, # Pass for verification within CRUD
            update_data=update_payload,
            changed_by_user_id=current_user.uid
        )
        return updated_inventory_item
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Error updating inventory item {inventory_item_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update inventory stock.")

@router.get("/inventory/{inventory_item_id}/logs", response_model=List[schemas.InventoryUpdateLogOut])
async def get_inventory_item_logs(
    restaurant_id: str = Path(...),
    inventory_item_id: int = Path(...),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):

    await verify_restaurant_inventory_permission(db, restaurant_id, current_user, required_permission="view_inventory_logs") # Or manage_inventory

    try:
        logs = crud.list_inventory_update_logs(
            db=db, 
            inventory_item_id=inventory_item_id, 
            restaurant_id=restaurant_id, # Pass for verification within CRUD
            skip=skip, 
            limit=limit
        )
        return logs
    except ValueError as e: # Handles case where inventory item not found for restaurant in CRUD
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Error fetching logs for inventory item {inventory_item_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not fetch inventory logs.")


# - Consider a GET /restaurants/{restaurant_id}/inventory endpoint to list all inventory items for a restaurant.
# - Refine permissions (e.g., separate "view_inventory" from "manage_inventory").
# - Add automatic stock deduction on order placement/completion (Phase 4). 