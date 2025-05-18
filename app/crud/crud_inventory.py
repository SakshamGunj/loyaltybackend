from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sql_func # To avoid conflict with datetime.func if used
from typing import List, Optional
from datetime import datetime

from .. import models, schemas # Use .. to go up to app directory then import models, schemas
# Ensure correct relative path if crud_inventory.py is in app/crud/

# Helper function to create log entries consistently
def _create_inventory_log_entry(
    db: Session,
    inventory_item_id: int,
    change_type: schemas.InventoryChangeType,
    quantity_changed: float,
    previous_quantity: float,
    new_quantity: float,
    changed_by_user_id: Optional[str] = None,
    reason: Optional[str] = None,
    notes: Optional[str] = None
) -> models.InventoryUpdateLog:
    log_entry_data = schemas.InventoryUpdateLogCreate(
        inventory_item_id=inventory_item_id,
        changed_by_user_id=changed_by_user_id,
        change_type=change_type,
        quantity_changed=quantity_changed,
        previous_quantity=previous_quantity,
        new_quantity=new_quantity,
        reason=reason,
        notes=notes,
        # timestamp will be set by DB default if not provided by schema with default
    )
    db_log_entry = models.InventoryUpdateLog(**log_entry_data.dict())
    db.add(db_log_entry)
    # Commit will be handled by the calling function to ensure atomicity
    return db_log_entry

def get_inventory_item(db: Session, inventory_item_id: int, restaurant_id: str) -> Optional[models.InventoryItem]:
    """Fetches an inventory item by its ID, ensuring it belongs to the specified restaurant."""
    return db.query(models.InventoryItem).filter(
        models.InventoryItem.id == inventory_item_id,
        models.InventoryItem.restaurant_id == restaurant_id
    ).first()

def get_inventory_item_by_menu_id(
    db: Session, menu_item_id: int, restaurant_id: str
) -> Optional[models.InventoryItem]:
    """Fetches an inventory item by menu_item_id and restaurant_id."""
    return db.query(models.InventoryItem).filter(
        models.InventoryItem.menu_item_id == menu_item_id,
        models.InventoryItem.restaurant_id == restaurant_id
    ).first()

def create_inventory_item(
    db: Session,
    inventory_data: schemas.InventoryItemCreate, # Contains menu_item_id, quantity, unit, low_stock_threshold, restaurant_id
    changed_by_user_id: str
) -> models.InventoryItem:
    """Creates an initial inventory item entry for a menu item for a specific restaurant."""
    existing_inventory_item = get_inventory_item_by_menu_id(
        db, menu_item_id=inventory_data.menu_item_id, restaurant_id=inventory_data.restaurant_id
    )
    if existing_inventory_item:
        raise ValueError(f"Inventory item for menu item ID {inventory_data.menu_item_id} in restaurant {inventory_data.restaurant_id} already exists.")

    # Validate that the menu item exists and belongs to the restaurant
    menu_item = db.query(models.MenuItem).filter(
        models.MenuItem.id == inventory_data.menu_item_id,
        models.MenuItem.restaurant_id == inventory_data.restaurant_id
    ).first()
    if not menu_item:
        raise ValueError(f"Menu item ID {inventory_data.menu_item_id} not found for restaurant {inventory_data.restaurant_id}.")

    db_inventory_item = models.InventoryItem(
        restaurant_id=inventory_data.restaurant_id,
        menu_item_id=inventory_data.menu_item_id,
        quantity=inventory_data.quantity,
        unit=inventory_data.unit,
        low_stock_threshold=inventory_data.low_stock_threshold,
        created_at=datetime.utcnow(),
        last_updated_at=datetime.utcnow()
    )
    db.add(db_inventory_item)
    db.flush() # To get db_inventory_item.id for the log entry

    _create_inventory_log_entry(
        db=db,
        inventory_item_id=db_inventory_item.id,
        change_type=schemas.InventoryChangeType.INITIAL_STOCK,
        quantity_changed=inventory_data.quantity, # Initial stock is the quantity changed
        previous_quantity=0.0, # Assuming starts from 0
        new_quantity=inventory_data.quantity,
        changed_by_user_id=changed_by_user_id,
        reason="Initial stock registration"
    )
    
    db.commit()
    db.refresh(db_inventory_item)
    return db_inventory_item

def update_inventory_item_stock(
    db: Session,
    inventory_item_id: int,
    restaurant_id: str, # For authorization and ensuring correct item
    update_data: schemas.InventoryItemUpdate, # Now contains new_quantity, change_type, reason, notes, unit, low_stock_threshold
    changed_by_user_id: Optional[str] # Can be None for system changes like sales
) -> models.InventoryItem:
    """Updates the stock of an existing inventory item to a new absolute value and logs the change."""
    db_inventory_item = get_inventory_item(db, inventory_item_id, restaurant_id)
    
    if not db_inventory_item:
        raise ValueError(f"Inventory item with ID {inventory_item_id} not found for restaurant {restaurant_id}.")

    previous_quantity = db_inventory_item.quantity
    # The new_quantity is the absolute desired stock level provided by the user/system.
    # quantity_changed is the delta calculated from previous and new quantities.
    quantity_changed = update_data.new_quantity - previous_quantity

    if update_data.new_quantity < 0:
        # Optionally, prevent stock from going negative depending on business rules
        # For now, we allow it but it should be flagged or handled.
        # Consider raising ValueError("Stock cannot be negative.") if that's a requirement.
        pass 

    db_inventory_item.quantity = update_data.new_quantity # Set to the new absolute quantity
    db_inventory_item.last_updated_at = datetime.utcnow()

    # Update unit and low_stock_threshold if provided
    if update_data.unit is not None:
        db_inventory_item.unit = update_data.unit
    if update_data.low_stock_threshold is not None:
        db_inventory_item.low_stock_threshold = update_data.low_stock_threshold
        
    _create_inventory_log_entry(
        db=db,
        inventory_item_id=db_inventory_item.id,
        change_type=update_data.change_type,
        quantity_changed=quantity_changed, # Use the calculated delta for logging
        previous_quantity=previous_quantity,
        new_quantity=db_inventory_item.quantity, # This is update_data.new_quantity
        changed_by_user_id=changed_by_user_id,
        reason=update_data.reason,
        notes=update_data.notes
    )
    
    db.commit()
    db.refresh(db_inventory_item)
    return db_inventory_item

def list_inventory_update_logs(
    db: Session, inventory_item_id: int, restaurant_id: str, skip: int = 0, limit: int = 100
) -> List[models.InventoryUpdateLog]:
    """Lists update logs for a specific inventory item, ensuring it belongs to the restaurant."""
    # First, verify the inventory_item_id belongs to the restaurant_id to prevent data leakage
    inventory_item = get_inventory_item(db, inventory_item_id, restaurant_id)
    if not inventory_item:
        raise ValueError(f"Inventory item ID {inventory_item_id} not found for restaurant {restaurant_id}.")

    return db.query(models.InventoryUpdateLog).options(
        joinedload(models.InventoryUpdateLog.user) # Eager load user details
    ).filter(
        models.InventoryUpdateLog.inventory_item_id == inventory_item_id
    ).order_by(
        models.InventoryUpdateLog.timestamp.desc()
    ).offset(skip).limit(limit).all()

def deduct_inventory_for_sale(
    db: Session,
    restaurant_id: str,
    menu_item_id: int,
    quantity_sold: float,
    order_id: str, # For logging purposes
    changed_by_user_id: Optional[str] = None # User who placed the order, or system if automated
) -> Optional[models.InventoryItem]:
    """
    Deducts stock for a menu item due to a sale.
    Logs the change. Returns the updated inventory item or None if not tracked.
    """
    inventory_item = get_inventory_item_by_menu_id(db, menu_item_id=menu_item_id, restaurant_id=restaurant_id)
    
    if not inventory_item:
        # Menu item is not tracked in inventory, or does not belong to this restaurant.
        # This is not necessarily an error; some items might not be inventoried.
        # logging.info(f"Inventory not tracked for menu item ID {menu_item_id} in restaurant {restaurant_id}. Skipping deduction.")
        return None

    previous_quantity = inventory_item.quantity
    # Quantity sold should be positive, so quantity_change for deduction is negative
    quantity_change = -abs(quantity_sold) 
    new_quantity = previous_quantity + quantity_change

    inventory_item.quantity = new_quantity
    inventory_item.last_updated_at = datetime.utcnow()

    _create_inventory_log_entry(
        db=db,
        inventory_item_id=inventory_item.id,
        change_type=schemas.InventoryChangeType.SALE_DEDUCTION,
        quantity_changed=quantity_change,
        previous_quantity=previous_quantity,
        new_quantity=new_quantity,
        changed_by_user_id=changed_by_user_id, # Could be the customer UID or system UID
        reason=f"Sale - Order ID: {order_id}"
    )
    # Commit is expected to be handled by the calling transaction (e.g., after order is finalized)
    # However, if this function is called stand-alone, it might need its own commit.
    # For now, assuming it's part of a larger transaction.
    # If standalone commit is needed: db.commit(); db.refresh(inventory_item)
    
    return inventory_item 