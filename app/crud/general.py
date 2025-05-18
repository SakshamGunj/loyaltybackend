from sqlalchemy.orm import Session, joinedload, selectinload
from .. import models, schemas # Adjusted for new location
from typing import List, Optional, Tuple, Dict
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, desc, or_
from datetime import datetime, timedelta
from ..utils.timezone import ist_now, utc_to_ist # Adjusted for new location
from ..auth.custom_auth import get_password_hash # Adjusted for new location
import logging
import uuid
import re
from .crud_inventory import deduct_inventory_for_sale # Correct after move
from .crud_tables import create_restaurant_table # ADDED import for creating tables

logger = logging.getLogger(__name__)

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    uid = str(uuid.uuid4())
    
    # Prepare data for User model, ensuring all fields from UserCreate are included
    user_data = user.dict(exclude_unset=True) # Exclude unset to handle optional fields gracefully
    
    # Handle password separately for hashing
    hashed_password = get_password_hash(user_data.pop('password'))

    db_user = models.User(
        uid=uid,
        hashed_password=hashed_password,
        created_at=datetime.utcnow(),
        **user_data  # Unpack remaining fields: email, name, number, role, restaurant_id, designation, permissions
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, uid: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.uid == uid).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_number(db: Session, number: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.number == number).first()

def update_user(db: Session, uid: str, user: schemas.UserUpdate) -> Optional[models.User]:
    db_user = get_user(db, uid)
    if not db_user:
        return None
    
    update_data = user.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, uid: str) -> bool:
    db_user = get_user(db, uid)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True

# import re # Already imported above

def slugify(text: str) -> str:
    # A simple slugify function, can be enhanced
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text).strip('-')
    return text

def create_restaurant(db: Session, restaurant: schemas.RestaurantCreate, owner_uid: str):
    # Generate a unique restaurant_id (slug) from name
    base_slug = slugify(restaurant.restaurant_name)
    slug = base_slug
    suffix = 1
    # Check if slug already exists
    while db.query(models.Restaurant).filter(models.Restaurant.restaurant_id == slug).first():
        slug = f"{base_slug}-{suffix}"
        suffix += 1
    
    data = restaurant.dict(exclude_unset=True)
    number_of_tables_to_create = data.pop('number_of_tables', None) # Get and remove from data dict
    
    data["restaurant_id"] = slug
    data["owner_uid"] = owner_uid 
    
    if "admin_uid" not in data or data["admin_uid"] is None:
        data["admin_uid"] = owner_uid

    db_restaurant = models.Restaurant(**data)
    db.add(db_restaurant)
    # db.commit() # Commit later after tables are also added or if table creation fails
    db.flush() # Flush to get the db_restaurant.restaurant_id for table creation

    # Auto-create tables if number_of_tables is provided
    created_tables = []
    if number_of_tables_to_create and number_of_tables_to_create > 0:
        try:
            for i in range(1, number_of_tables_to_create + 1):
                table_data = schemas.RestaurantTableCreate(
                    table_number=f"Table {i}", # Default naming, can be customized later
                    capacity=None, # Default capacity, can be set later
                    status=schemas.TableStatus.EMPTY # Default status
                )
                # Use the create_restaurant_table from crud_tables which handles individual commit for table
                # However, for atomicity, it's better if create_restaurant_table doesn't commit itself
                # For now, assuming create_restaurant_table might commit, or adjust it.
                # Let's modify create_restaurant_table to not commit itself, and commit here.
                
                # Simplified: Create table object and add to session
                db_table = models.RestaurantTable(
                    restaurant_id=db_restaurant.restaurant_id,
                    table_number=table_data.table_number,
                    status=table_data.status,
                    capacity=table_data.capacity
                )
                db.add(db_table)
                created_tables.append(db_table)
        except Exception as e:
            db.rollback() # Rollback restaurant creation if table creation fails
            logger.error(f"Error creating tables for restaurant {slug}: {e}")
            raise ValueError(f"Failed to create initial tables for restaurant: {str(e)}")

    db.commit() # Commit restaurant and all tables together
    db.refresh(db_restaurant)
    # Refresh tables if needed, though they are not directly part of db_restaurant for this return
    # for table in created_tables:
    #     db.refresh(table)
        
    return db_restaurant

def get_restaurant(db: Session, restaurant_id: str):
    return db.query(models.Restaurant).filter(models.Restaurant.restaurant_id == restaurant_id).first()

def get_restaurants(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Restaurant).offset(skip).limit(limit).all()

# Loyalty CRUD

def create_loyalty(db: Session, loyalty: schemas.LoyaltyCreate):
    db_loyalty = models.Loyalty(**loyalty.dict())
    db.add(db_loyalty)
    db.commit()
    db.refresh(db_loyalty)
    return db_loyalty

def get_loyalty(db: Session, uid: str, restaurant_id: str):
    return db.query(models.Loyalty).filter(models.Loyalty.uid == uid, models.Loyalty.restaurant_id == restaurant_id).first()

def list_loyalties(db: Session, uid: Optional[str] = None):
    q = db.query(models.Loyalty)
    if uid:
        q = q.filter(models.Loyalty.uid == uid)
    return q.all()

# Submission CRUD

def create_submission(db: Session, submission: schemas.SubmissionCreate):
    db_submission = models.Submission(**submission.dict())
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission

def get_submission(db: Session, submission_id: int):
    return db.query(models.Submission).filter(models.Submission.submission_id == submission_id).first()

def list_submissions(db: Session, uid: Optional[str] = None):
    q = db.query(models.Submission)
    if uid:
        q = q.filter(models.Submission.uid == uid)
    return q.all()

# ClaimedReward CRUD
# Assuming generate_coupon_code was defined in the original app/crud.py or accessible.
# If not, it might need to be defined or imported here. For now, using a placeholder.
def generate_coupon_code(db: Session, length: int = 8, prefix: Optional[str] = None) -> str:
    """Generates a unique coupon code."""
    while True:
        random_part = str(uuid.uuid4()).replace("-", "")[:length].upper()
        code = f"{prefix}{random_part}" if prefix else random_part
        # Check if this code already exists in the Coupon table
        existing_coupon = db.query(models.Coupon).filter(models.Coupon.code == code).first()
        if not existing_coupon:
            return code

# Placeholder for the old function name if it's called from elsewhere, 
# can be removed if generate_coupon_code is now the standard.
# def generate_unique_coupon_code(db: Session, length: int = 8, prefix: Optional[str] = None) -> str:
# return generate_coupon_code(db, length, prefix)


def disassociate_employee_from_restaurant(db: Session, user_id: str, restaurant_id: str) -> Optional[models.User]:
    """
    Disassociates an employee from a specific restaurant.
    Sets restaurant_id, designation, and permissions to None.
    Changes role to 'customer' if it was 'employee' or specific to the restaurant context.
    """
    db_user = get_user(db, user_id)
    if not db_user:
        return None

    if db_user.restaurant_id != restaurant_id:
        # This check might be better handled at the API layer before calling this,
        # but an extra check here ensures data integrity.
        # Or raise an error: raise ValueError("User is not an employee of the specified restaurant")
        return None # Or indicate failure/inapplicability

    db_user.restaurant_id = None
    db_user.designation = None
    db_user.permissions = None
    
    # Optionally, reset role if it's a restaurant-specific role
    # For now, let's assume specific employee roles might exist, e.g. "restaurant_manager"
    # If the role is generic "employee", changing to "customer" makes sense.
    # This logic can be refined based on how roles are defined and used.
    if db_user.role in ["employee", "restaurant_staff", "restaurant_manager"]: # Add other employee-specific roles as needed
        db_user.role = "customer"

    db.commit()
    db.refresh(db_user)
    return db_user

def create_claimed_reward(db: Session, reward_data: dict, current_uid: str):
    coupon_code = generate_coupon_code(db) # Uses default length/prefix for claimed rewards
    allowed_fields = [
        'restaurant_id', 'reward_name', 'threshold_id', 'whatsapp_number', 'user_name'
    ]
    filtered_data = {field: reward_data.get(field) for field in allowed_fields if field in reward_data}
    db_reward = models.ClaimedReward(**filtered_data, uid=current_uid, coupon_code=coupon_code)
    db.add(db_reward)
    db.commit()
    db.refresh(db_reward)
    return db_reward

def get_claimed_reward(db: Session, reward_id: int):
    return db.query(models.ClaimedReward).filter(models.ClaimedReward.id == reward_id).first()

def list_claimed_rewards(db: Session, uid: Optional[str] = None):
    q = db.query(models.ClaimedReward)
    if uid:
        q = q.filter(models.ClaimedReward.uid == uid)
    return q.all()

# AuditLog CRUD

def create_audit_log(db: Session, audit: schemas.AuditLogCreate):
    db_audit = models.AuditLog(**audit.dict())
    db.add(db_audit)
    db.commit()
    db.refresh(db_audit)
    return db_audit

def list_audit_logs(db: Session, uid: Optional[str] = None):
    q = db.query(models.AuditLog)
    if uid:
        q = q.filter(models.AuditLog.user_id == uid)
    return q.order_by(models.AuditLog.timestamp.desc()).all()

# --- Online Ordering CRUD ---

# --- Menu Category ---
def get_all_menu_categories(db: Session, restaurant_id: str):
    return db.query(models.MenuCategory).filter(models.MenuCategory.restaurant_id == restaurant_id).all()

def create_menu_category(db: Session, restaurant_id: str, category: schemas.MenuCategoryCreate):
    data = category.dict(exclude={"restaurant_id"})
    db_category = models.MenuCategory(**data, restaurant_id=restaurant_id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def get_menu_category(db: Session, category_id: int, restaurant_id: str):
    return db.query(models.MenuCategory).filter(models.MenuCategory.id == category_id, models.MenuCategory.restaurant_id == restaurant_id).first()

def update_menu_category(db: Session, category_id: int, restaurant_id: str, category: schemas.MenuCategoryCreate):
    db_cat = get_menu_category(db, category_id, restaurant_id)
    if not db_cat:
        return None
    for field, value in category.dict(exclude_unset=True).items():
        setattr(db_cat, field, value)
    db.commit()
    db.refresh(db_cat)
    return db_cat

def delete_menu_category(db: Session, category_id: int, restaurant_id: str):
    db_cat = get_menu_category(db, category_id, restaurant_id)
    if db_cat:
        db.delete(db_cat)
        db.commit()
        return True
    return False

# --- Menu Item ---
def get_all_menu_items(db: Session, restaurant_id: str) -> List[models.MenuItem]:
    return db.query(models.MenuItem).options(
        selectinload(models.MenuItem.components).selectinload(models.ComboItemComponent.component_item).selectinload(models.MenuItem.category), # Eager load component's category too
        selectinload(models.MenuItem.category) # Eager load category for the main item
    ).filter(models.MenuItem.restaurant_id == restaurant_id).order_by(models.MenuItem.name).all()

def create_menu_item(db: Session, restaurant_id: str, item: schemas.MenuItemCreate) -> models.MenuItem:
    variations_data = [v.dict() for v in item.variations] if item.variations else None
    
    # Exclude 'components' from the main item data dictionary for initial MenuItem creation
    item_data_dict = item.dict(exclude={'restaurant_id', 'variations', 'components'})
    
    # Ensure item_type from schema is correctly passed to the model
    db_item = models.MenuItem(
        **item_data_dict, # This now includes item_type
        restaurant_id=restaurant_id,
        variations=variations_data
    )
    
    db.add(db_item) # Add the main item to session first

    if item.item_type == schemas.ItemType.COMBO:
        if not item.components: # Schema validator should have caught this
            db.rollback()
            raise ValueError("Components must be provided for a combo item type.")
        
        try:
            db.flush() # Flush to get db_item.id for foreign key references in components

            component_objects_to_add = []
            for comp_data in item.components:
                # Verify component item exists, is for the same restaurant, and is a REGULAR item
                component_menu_item_db = db.query(models.MenuItem).filter(
                    models.MenuItem.id == comp_data.menu_item_id,
                    models.MenuItem.restaurant_id == restaurant_id,
                    models.MenuItem.item_type == schemas.ItemType.REGULAR.value # components must be regular items
                ).first()
                
                if not component_menu_item_db:
                    db.rollback() # Rollback if any component is invalid
                    raise ValueError(f"Component item with ID {comp_data.menu_item_id} not found for restaurant {restaurant_id}, is not available, or is not a 'regular' item.")

                # Prevent a combo from containing itself (direct check)
                if db_item.id == component_menu_item_db.id:
                    db.rollback()
                    raise ValueError(f"A combo item cannot contain itself as a component. Item ID: {db_item.id}")

                new_component_link = models.ComboItemComponent(
                    combo_menu_item_id=db_item.id,
                    component_menu_item_id=comp_data.menu_item_id,
                    quantity=comp_data.quantity
                )
                component_objects_to_add.append(new_component_link)
            
            if component_objects_to_add:
                db.add_all(component_objects_to_add)
            
            db.commit() # Commit main item and all components together
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating combo menu item '{item.name}' components: {e}", exc_info=True)
            # More specific error or re-raise generic one
            raise ValueError(f"Failed to create combo item and its components: {str(e)}")
            
    else: # Regular item or item_type not COMBO
        if item.components and len(item.components) > 0: # Schema validator should prevent this
            db.rollback()
            raise ValueError("Components should not be provided for a regular item type.")
        db.commit() # Commit the regular item

    db.refresh(db_item)
    # For combos, after refresh, db_item.components should be populated if lazy='selectin' works as expected
    # or if explicitly loaded in a subsequent get query.
    # To ensure components are available immediately after creation for the return:
    if db_item.item_type == schemas.ItemType.COMBO.value:
        # Re-fetch with explicit loading for the return value, as refresh might not populate nested relationships deeply enough.
        # This is a common pattern: create, then get with full loading options for the response.
        # However, db.refresh should respect the lazy loading strategy on the relationships.
        # Let's rely on the refresh and the model's lazy loading config for now.
        # If components are not present in the returned db_item, we'd need to re-query like get_menu_item(db, db_item.id, restaurant_id)
        pass

    return db_item

def get_menu_item(db: Session, item_id: int, restaurant_id: str) -> Optional[models.MenuItem]:
    # Eager load components and their actual item details, including the category of component items
    # Also eager load the category of the main menu item itself.
    query = db.query(models.MenuItem).options(
        selectinload(models.MenuItem.category), # Category of the main/combo item
        selectinload(models.MenuItem.variations), # Variations of the main/combo item
        selectinload(models.MenuItem.components).selectinload(models.ComboItemComponent.component_item).options(
            selectinload(models.MenuItem.category), # Category of the component item
            selectinload(models.MenuItem.variations) # Variations of the component item (if any)
        )
    ).filter(
        models.MenuItem.id == item_id, 
        models.MenuItem.restaurant_id == restaurant_id
    )
    return query.first()

def update_menu_item(db: Session, item_id: int, restaurant_id: str, item_update: schemas.MenuItemCreate):
    db_item = get_menu_item(db, item_id, restaurant_id) # Use the enhanced get_menu_item
    if not db_item:
        return None

    # Handle item_type change carefully.
    # If changing from COMBO to REGULAR, existing components should be deleted.
    # If changing from REGULAR to COMBO, new components must be provided.
    # If item_type is not changing but components are, update them.

    update_data = item_update.dict(exclude_unset=True, exclude={'components'}) # Exclude components for direct setattr

    # Update standard fields first
    for field, value in update_data.items():
        if field == 'item_type' and value != db_item.item_type:
            # Handle type change implications for components
            if value == schemas.ItemType.REGULAR.value and db_item.item_type == schemas.ItemType.COMBO.value:
                # Deleting components: The relationship cascade on MenuItem.components should handle this
                # when db_item.components is cleared or items removed.
                # For explicit control:
                for comp_link in list(db_item.components): # Iterate over a copy
                    db.delete(comp_link)
                # db_item.components.clear() # Alternative way if cascade works from parent side
                logger.info(f"Menu item {db_item.id} changed from COMBO to REGULAR. Components cleared.")

            elif value == schemas.ItemType.COMBO.value and db_item.item_type == schemas.ItemType.REGULAR.value:
                if not item_update.components:
                    db.rollback()
                    raise ValueError("Components must be provided when changing item type to COMBO.")
                logger.info(f"Menu item {db_item.id} changing from REGULAR to COMBO. New components will be added.")
        
        setattr(db_item, field, value)

    # Handle component updates for COMBO items (or if type changed to COMBO)
    if db_item.item_type == schemas.ItemType.COMBO.value:
        # Delete existing components before adding new ones to simplify logic (idempotent update)
        # This relies on the cascade delete for ComboItemComponent when objects are removed from db_item.components list
        # or deleted directly.
        existing_component_links = list(db_item.components) # Make a copy before modifying
        for comp_link in existing_component_links:
            db.delete(comp_link)
        db.flush() # Ensure deletions are processed before adding potentially same component items

        if item_update.components:
            new_component_links = []
            for comp_data in item_update.components:
                component_menu_item_db = db.query(models.MenuItem).filter(
                    models.MenuItem.id == comp_data.menu_item_id,
                    models.MenuItem.restaurant_id == restaurant_id,
                    models.MenuItem.item_type == schemas.ItemType.REGULAR.value
                ).first()
                if not component_menu_item_db:
                    db.rollback()
                    raise ValueError(f"Invalid component item ID {comp_data.menu_item_id} for combo update.")
                if db_item.id == component_menu_item_db.id: # Prevent self-reference
                    db.rollback()
                    raise ValueError("A combo item cannot contain itself.")

                new_link = models.ComboItemComponent(
                    combo_menu_item_id=db_item.id, # db_item.id is already known
                    component_menu_item_id=comp_data.menu_item_id,
                    quantity=comp_data.quantity
                )
                new_component_links.append(new_link)
            db.add_all(new_component_links)
        elif db_item.item_type == schemas.ItemType.COMBO.value: # Combo type but no components provided
            db.rollback()
            raise ValueError("Combo items must have components. To make it regular, change item_type.")


    try:
        db.commit()
        db.refresh(db_item)
        # Similar to create, ensure the returned object has components loaded for the response
        # This refresh should work due to lazy='selectin' and explicit loads in get_menu_item.
        # If not, a re-fetch might be needed: return get_menu_item(db, item_id, restaurant_id)
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating menu item {item_id}: {e}", exc_info=True)
        raise ValueError(f"Failed to update menu item: {str(e)}")
        
    return db_item

def delete_menu_item(db: Session, item_id: int, restaurant_id: str):
    db_item = get_menu_item(db, item_id, restaurant_id)
    if db_item:
        db.delete(db_item)
        db.commit()
        return True
    return False

# --- Orders ---
def create_order(db: Session, order: schemas.OrderCreate, user_uid: str, user_role: str, admin_uid: Optional[str] = None):
    if not order.items or not isinstance(order.items, list):
        raise Exception("Order must contain at least one item.")
    seen_items = set()
    
    restaurant_id = order.restaurant_id
    restaurant_name = None
    
    restaurant = db.query(models.Restaurant).filter(models.Restaurant.restaurant_id == restaurant_id).first()
    if restaurant:
        restaurant_name = restaurant.restaurant_name
    
    db_items = []
    
    for item in order.items:
        if not hasattr(item, 'item_id') or not hasattr(item, 'quantity'):
            raise Exception("Each order item must have item_id and quantity.")
        if item.item_id in seen_items:
            raise Exception(f"Duplicate item in order: {item.item_id}")
        seen_items.add(item.item_id)
        if not isinstance(item.quantity, int) or item.quantity <= 0:
            raise Exception(f"Invalid quantity for item {item.item_id}")
        
        db_menu_item = db.query(models.MenuItem).filter(
            models.MenuItem.id == item.item_id,
            models.MenuItem.available == True
        ).first()
        if not db_menu_item:
            raise Exception(f"Menu item not found or unavailable: {item.item_id}")
            
        db_items.append((db_menu_item, item.quantity))

    total_cost = sum(db_menu_item.price * quantity for db_menu_item, quantity in db_items)

    promo_code_id = None
    if order.promo_code:
        promo = db.query(models.PromoCode).filter(
            models.PromoCode.code == order.promo_code,
            models.PromoCode.active == True
        ).first()
        if promo:
            promo_code_id = promo.id

    latest_order = db.query(models.Order).filter(
        models.Order.restaurant_id == restaurant_id
    ).order_by(models.Order.order_number.desc()).first()
    
    order_number = 1
    if latest_order and latest_order.order_number:
        order_number = latest_order.order_number + 1
    
    order_id = f"{restaurant_id}_{order_number}"

    db_order = models.Order(
        id=order_id,
        order_number=order_number,
        user_uid=user_uid,
        user_role=user_role,
        table_number=order.table_number,
        created_at=datetime.utcnow(),
        status="Pending",
        total_cost=total_cost,
        payment_status="Pending",
        restaurant_id=restaurant_id,
        restaurant_name=restaurant_name
    )
    if admin_uid:
        db_order.admin_uid = admin_uid
    
    try:
        db.add(db_order)
        
        order_items_models = []
        for db_menu_item, qty in db_items:
            order_item = models.OrderItem(
                order_id=db_order.id, 
                item_id=db_menu_item.id,
                quantity=qty,
                price=db_menu_item.price
            )
            order_items_models.append(order_item)
        
        db.add_all(order_items_models)
        
        for db_menu_item, qty_sold in db_items:
            deduct_inventory_for_sale(
                db=db,
                restaurant_id=db_order.restaurant_id,
                menu_item_id=db_menu_item.id,
                quantity_sold=float(qty_sold), 
                order_id=db_order.id,
                changed_by_user_id=user_uid 
            )

        db.commit()
        db.refresh(db_order) 
        
        return db_order
    except IntegrityError as e:
        db.rollback()
        raise Exception("Duplicate order item detected. Please try again.")
    except Exception as e:
        db.rollback()
        raise Exception(f"Error creating order: {str(e)}")

def get_orders_by_user(db: Session, user_uid: str, restaurant_id: Optional[str] = None):
    try:
        orders_query = db.query(models.Order).filter(models.Order.user_uid == user_uid)
        if restaurant_id:
            orders_query = orders_query.filter(models.Order.restaurant_id == restaurant_id) # Filter directly on order
        
        orders = orders_query.options( # Eager load relationships
            selectinload(models.Order.items).selectinload(models.OrderItem.item),
            selectinload(models.Order.payment),
            selectinload(models.Order.status_history)
        ).order_by(models.Order.created_at.desc()).all()
        
        result_orders = []
        for order_orm in orders:
            # Attempt to use Pydantic schema for conversion first for cleaner structure
            try:
                order_dict = schemas.OrderOut.from_orm(order_orm).dict()
            except Exception: # Fallback to manual dictionary creation if OrderOut fails or is not suitable
                logger.warning(f"Falling back to manual dict creation for order {order_orm.id} in get_orders_by_user")
                order_dict = {
                    "id": order_orm.id, "user_uid": order_orm.user_uid, "user_role": order_orm.user_role,
                    "table_number": order_orm.table_number, "created_at": order_orm.created_at,
                    "status": order_orm.status, "total_cost": order_orm.total_cost,
                    "payment_status": order_orm.payment_status, "promo_code_id": order_orm.promo_code_id,
                    "restaurant_id": order_orm.restaurant_id, "restaurant_name": order_orm.restaurant_name,
                    "items": [schemas.OrderItemOut.from_orm(item).dict() for item in order_orm.items] if order_orm.items else [],
                    "payment": schemas.PaymentOut.from_orm(order_orm.payment).dict() if order_orm.payment else None,
                    "status_history": [schemas.OrderStatusHistoryOut.from_orm(hist).dict() for hist in order_orm.status_history] if order_orm.status_history else []
                }
            result_orders.append(order_dict)
        return result_orders
    except Exception as e:
        logger.error(f"Error in get_orders_by_user: {e}", exc_info=True)
        return []

def get_all_orders(db: Session, restaurant_id: Optional[str] = None):
    try:
        orders_query = db.query(models.Order).options(
            selectinload(models.Order.items).selectinload(models.OrderItem.item),
            selectinload(models.Order.payment),
            selectinload(models.Order.status_history)
        ).order_by(models.Order.created_at.desc())
        
        if restaurant_id:
            orders_query = orders_query.filter(models.Order.restaurant_id == restaurant_id)
        
        orders_orm = orders_query.all()
        
        result_orders = []
        for order_orm in orders_orm:
            try:
                order_dict = schemas.OrderOut.from_orm(order_orm).dict()
            except Exception:
                logger.warning(f"Falling back to manual dict creation for order {order_orm.id} in get_all_orders")
                order_dict = {
                    "id": order_orm.id, "user_uid": order_orm.user_uid, "user_role": order_orm.user_role,
                    "table_number": order_orm.table_number, "created_at": order_orm.created_at,
                    "status": order_orm.status, "total_cost": order_orm.total_cost,
                    "payment_status": order_orm.payment_status, "promo_code_id": order_orm.promo_code_id,
                    "restaurant_id": order_orm.restaurant_id, "restaurant_name": order_orm.restaurant_name,
                    "items": [schemas.OrderItemOut.from_orm(item).dict() for item in order_orm.items] if order_orm.items else [],
                    "payment": schemas.PaymentOut.from_orm(order_orm.payment).dict() if order_orm.payment else None,
                    "status_history": [schemas.OrderStatusHistoryOut.from_orm(hist).dict() for hist in order_orm.status_history] if order_orm.status_history else []
                }
            result_orders.append(order_dict)
        return result_orders
    except Exception as e:
        logger.error(f"Error in get_all_orders: {e}", exc_info=True)
        return []

def filter_orders(db: Session, status=None, start_date=None, end_date=None, payment_method=None, user_uid: Optional[str]=None, order_id: Optional[str]=None, user_email: Optional[str]=None, user_phone: Optional[str]=None, restaurant_id: Optional[str]=None):
    try:
        query = db.query(models.Order).options(
            selectinload(models.Order.items).selectinload(models.OrderItem.item),
            selectinload(models.Order.user), 
            selectinload(models.Order.payment),
            selectinload(models.Order.status_history)
        )
        
        if status: query = query.filter(models.Order.status == status)
        if start_date: query = query.filter(models.Order.created_at >= start_date)
        if end_date: query = query.filter(models.Order.created_at <= end_date)
        if order_id: query = query.filter(models.Order.id == order_id)
        if user_uid: query = query.filter(models.Order.user_uid == user_uid)
        if restaurant_id: query = query.filter(models.Order.restaurant_id == restaurant_id)
        
        if payment_method:
            query = query.join(models.Order.payment).filter(models.Payment.method == payment_method)
            
        if user_email:
            query = query.join(models.Order.user).filter(models.User.email.ilike(f"%{user_email}%"))
        
        if user_phone: 
            query = query.join(models.Order.user).filter(or_(
                models.User.number.ilike(f"%{user_phone}%"), 
                # models.User.name.ilike(f"%{user_phone}%") # Original had name check, might be too broad
            ))

        orders_orm = query.order_by(models.Order.created_at.desc()).all()
        
        result_orders = []
        for order_orm in orders_orm:
            try:
                order_dict = schemas.OrderOut.from_orm(order_orm).dict()
            except Exception:
                logger.warning(f"Falling back to manual dict creation for order {order_orm.id} in filter_orders")
                order_dict = { # Manual fallback
                    "id": order_orm.id, "user_uid": order_orm.user_uid, "user_role": order_orm.user_role,
                    "table_number": order_orm.table_number, "created_at": order_orm.created_at,
                    "status": order_orm.status, "total_cost": order_orm.total_cost,
                    "payment_status": order_orm.payment_status, "promo_code_id": order_orm.promo_code_id,
                    "restaurant_id": order_orm.restaurant_id, "restaurant_name": order_orm.restaurant_name,
                    "items": [schemas.OrderItemOut.from_orm(item).dict() for item in order_orm.items] if order_orm.items else [],
                    "payment": schemas.PaymentOut.from_orm(order_orm.payment).dict() if order_orm.payment else None,
                    "status_history": [schemas.OrderStatusHistoryOut.from_orm(hist).dict() for hist in order_orm.status_history] if order_orm.status_history else []
                }
            result_orders.append(order_dict)
        return result_orders
    except Exception as e:
        logger.error(f"Error in filter_orders: {e}", exc_info=True)
        return []

def update_order_status(db: Session, order_id: str, status: str, changed_by: str):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise Exception(f"Order not found: {order_id}")
    
    db_order.status = status
    
    status_history = models.OrderStatusHistory(
        order_id=order_id,
        status=status,
        changed_by=changed_by
    )
    db.add(status_history)
    
    if status == "Payment Done":
        db_order.payment_status = "Paid"
    
    db.commit()
    db.refresh(db_order)
    return db_order

def confirm_order(db: Session, order_id: str, changed_by: str):
    return update_order_status(db, order_id, "Order Confirmed", changed_by)

def mark_order_paid(
    db: Session, 
    order_id: str, 
    changed_by: str, # UID of the staff/system user marking as paid
    payment_method: str, 
    transaction_id: Optional[str] = None,
    customer_uid: Optional[str] = None # NEW: UID of the customer associated with this order
):
    db_order = db.query(models.Order).options(
        selectinload(models.Order.items).selectinload(models.OrderItem.item).selectinload(models.MenuItem.category),
        selectinload(models.Order.user), # This is the staff/system user (Order.user_uid)
        selectinload(models.Order.payment),
        selectinload(models.Order.customer_detail) # Eager load potential customer details
    ).filter(models.Order.id == order_id).first()

    if not db_order:
        raise ValueError(f"Order {order_id} not found")

    if db_order.payment_status == "Paid":
        logging.info(f"Order {order_id} is already marked as Paid.")
        # Consider if customer_uid should still be updated if provided for an already paid order
        # For now, we'll allow it if the order exists and is already paid.

    # Validate and set customer_uid if provided
    if customer_uid:
        db_customer = get_user(db, customer_uid) # Reusing existing get_user CRUD
        if not db_customer:
            raise ValueError(f"Customer with UID {customer_uid} not found.")
        # You might want to check if db_customer.role is 'customer' or similar if needed
        db_order.customer_uid = customer_uid
        logging.info(f"Order {order_id} associated with customer UID {customer_uid}.")
    elif db_order.customer_uid: # If customer_uid is not provided in this call, but already exists on order, keep it.
        pass # No change to customer_uid
    # else: customer_uid is None and db_order.customer_uid is also None - no action needed

    # Create or Update Payment record
    if db_order.payment:
        db_payment = db_order.payment
        db_payment.amount = db_order.total_cost 
        db_payment.method = payment_method
        db_payment.status = "Paid"
        db_payment.paid_at = datetime.utcnow()
        db_payment.transaction_id = transaction_id
        db_payment.processed_at = datetime.utcnow() 
    else:
        db_payment = models.Payment(
            order_id=db_order.id,
            amount=db_order.total_cost,
            method=payment_method,
            status="Paid",
            paid_at=datetime.utcnow(),
            transaction_id=transaction_id,
            processed_at=datetime.utcnow()
        )
        db.add(db_payment)
        # db_order.payment = db_payment # SQLAlchemy handles this relationship if back_populates is set

    db_order.payment_status = "Paid"
    db_order.status = "Payment Done" 
    db_order.updated_at = datetime.utcnow()
    
    audit_details = {
        "order_id": order_id, 
        "marked_by": changed_by, 
        "payment_method": payment_method,
        "transaction_id": transaction_id, 
        "new_payment_status": "Paid"
    }
    if db_order.customer_uid: # Include customer_uid in audit log if set
        audit_details["customer_uid"] = db_order.customer_uid

    create_audit_log(db, schemas.AuditLogCreate(
        user_id=changed_by, 
        action="Order Marked Paid", 
        details=audit_details,
        order_id=order_id 
    ))
    
    try:
        db.commit()
        db.refresh(db_order)
        if hasattr(db_order, 'payment') and db_order.payment: # Refresh payment if it exists
             db.refresh(db_order.payment)
    except Exception as e:
        db.rollback()
        logging.error(f"Error committing payment for order {order_id}: {e}", exc_info=True)
        raise 
        
    return db_order

def cancel_order(db: Session, order_id: str, cancelled_by: str):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise Exception("Order not found")
    if db_order.status not in ["Pending", "Confirmed"]:
        raise Exception("Order cannot be cancelled at this stage.")
    db_order.status = "Cancelled"
    
    # Create audit log before main commit for atomicity with status change
    db.add(models.AuditLog(order_id=order_id, user_id=cancelled_by, action="cancel", timestamp=datetime.utcnow(), details="Order cancelled"))

    db.commit()
    db.refresh(db_order)
    return db_order

def refund_order(db: Session, order_id: str, refunded_by: str):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise Exception("Order not found")
    if db_order.payment_status != "Paid":
        raise Exception("Order is not paid, cannot refund.")
    
    db_order.payment_status = "Refunded"
    if db_order.payment:
        db_order.payment.status = "Refunded"
        # db_order.payment.paid_at = datetime.utcnow() # paid_at might not be appropriate to update
    
    db.add(models.AuditLog(order_id=order_id, user_id=refunded_by, action="refund", timestamp=datetime.utcnow(), details="Order refunded"))

    db.commit()
    db.refresh(db_order)
    if db_order.payment:
        db.refresh(db_order.payment)
    return db_order

# --- Payments ---
def update_payment(db: Session, order_id: str, payment: schemas.PaymentCreate):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise Exception("Order not found")
    
    db_payment = db.query(models.Payment).filter(models.Payment.order_id == order_id).first()
    if not db_payment:
        db_payment = models.Payment(
            order_id=order_id,
            amount=payment.amount,
            status=payment.status or "Pending",
            method=payment.method,
            paid_at=payment.paid_at if payment.paid_at else datetime.utcnow() # Use provided paid_at or now
        )
        db.add(db_payment)
    else:
        update_data = payment.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_payment, field, value)
            
    db_order.payment_status = db_payment.status # Sync order payment status
    
    db.commit()
    db.refresh(db_payment)
    db.refresh(db_order)
    return db_payment

# --- Promo Codes ---
def apply_promo_code(db: Session, code: str, user_id: str): # user_id is not used in current logic
    promo = db.query(models.PromoCode).filter(models.PromoCode.code == code, models.PromoCode.active == True).first()
    if not promo:
        raise Exception("Promo code not found or inactive")
    now = datetime.utcnow()
    if promo.valid_from and now < promo.valid_from:
        raise Exception("Promo code not yet valid")
    if promo.valid_to and now > promo.valid_to:
        raise Exception("Promo code expired")
    if promo.usage_limit is not None and promo.used_count >= promo.usage_limit:
        raise Exception("Promo code usage limit reached")
    
    promo.used_count = (promo.used_count or 0) + 1
    db.commit()
    db.refresh(promo)
    return promo

def create_promo_code(db: Session, promo: schemas.PromoCodeCreate):
    db_promo = models.PromoCode(**promo.dict())
    db.add(db_promo)
    db.commit()
    db.refresh(db_promo)
    return db_promo

def get_all_promo_codes(db: Session):
    return db.query(models.PromoCode).all()

def update_promo_code(db: Session, promo_id: int, promo: schemas.PromoCodeCreate):
    db_promo = db.query(models.PromoCode).filter(models.PromoCode.id == promo_id).first()
    if not db_promo:
        return None
    update_data = promo.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_promo, field, value)
    db.commit()
    db.refresh(db_promo)
    return db_promo

def delete_promo_code(db: Session, promo_id: int):
    db_promo = db.query(models.PromoCode).filter(models.PromoCode.id == promo_id).first()
    if db_promo:
        db.delete(db_promo)
        db.commit()
        return True
    return False

# --- Analytics ---
def get_order_analytics(db: Session, period: str = "daily"):
    today = datetime.utcnow().date()
    if period == "daily":
        start_date_filter = today
        end_date_filter = today + timedelta(days=1)
    elif period == "weekly":
        start_date_filter = today - timedelta(days=today.weekday())
        end_date_filter = start_date_filter + timedelta(days=7)
    elif period == "monthly":
        start_date_filter = today.replace(day=1)
        if start_date_filter.month == 12:
            end_date_filter = start_date_filter.replace(year=start_date_filter.year + 1, month=1)
        else:
            end_date_filter = start_date_filter.replace(month=start_date_filter.month + 1)
    else:
        raise ValueError("Invalid period for analytics. Choose from 'daily', 'weekly', 'monthly'.")

    order_count = db.query(models.Order).filter(
        models.Order.created_at >= start_date_filter, models.Order.created_at < end_date_filter
    ).count()
    
    total_sales_query = db.query(func.sum(models.Order.total_cost)).filter(
        models.Order.created_at >= start_date_filter, models.Order.created_at < end_date_filter
    )
    total_sales = total_sales_query.scalar() or 0.0
    
    popular_items_query = db.query(
        models.MenuItem.name, func.sum(models.OrderItem.quantity).label('total_quantity')
    ).join(models.OrderItem, models.MenuItem.id == models.OrderItem.item_id)\
     .join(models.Order, models.Order.id == models.OrderItem.order_id)\
     .filter(models.Order.created_at >= start_date_filter, models.Order.created_at < end_date_filter)\
     .group_by(models.MenuItem.name)\
     .order_by(func.sum(models.OrderItem.quantity).desc())\
     .limit(5).all()

    return {
        "period": period,
        "start_date": start_date_filter.isoformat(),
        "end_date": end_date_filter.isoformat(),
        "order_count": order_count,
        "total_sales": total_sales,
        "popular_items": [{"name": name, "quantity": qty} for name, qty in popular_items_query]
    }

def export_orders_csv(db: Session, orders: List[models.Order]):
    import csv
    from io import StringIO
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Order ID", "User UID", "User Role", "Table Number", 
        "Restaurant ID", "Restaurant Name", "Created At (UTC)", "Status", 
        "Total Cost", "Payment Status"
    ])
    for order in orders: 
        writer.writerow([
            order.id, order.user_uid, order.user_role, order.table_number,
            order.restaurant_id, order.restaurant_name, 
            order.created_at.isoformat() if order.created_at else None, 
            order.status, order.total_cost, order.payment_status
        ])
    return output.getvalue()

# --- Order --- (get_unpaid_order_by_table, add_items_to_order)

def get_unpaid_order_by_table(db: Session, restaurant_id: str, table_number: str) -> Optional[models.Order]:
    if not table_number: 
        return None
    return db.query(models.Order).options(
        selectinload(models.Order.items).options(selectinload(models.OrderItem.item)) 
    ).filter(
        models.Order.restaurant_id == restaurant_id,
        models.Order.table_number == table_number,
        models.Order.payment_status == "Pending"
    ).first()

def add_items_to_order(db: Session, existing_order: models.Order, new_items_create: List[schemas.OrderItemCreate], user_uid: str) -> Tuple[models.Order, List[models.OrderItem]]:
    if not new_items_create:
        raise ValueError("Must provide items to add.")

    affected_item_models: List[models.OrderItem] = []

    for item_to_add in new_items_create: 
        menu_item_db = db.query(models.MenuItem).filter(
            models.MenuItem.id == item_to_add.item_id,
            models.MenuItem.available == True,
            models.MenuItem.restaurant_id == existing_order.restaurant_id
        ).first()

        if not menu_item_db:
            raise ValueError(f"Menu item with ID {item_to_add.item_id} for restaurant {existing_order.restaurant_id} not found or unavailable.")
        
        if item_to_add.quantity <= 0:
            raise ValueError(f"Quantity for item ID {item_to_add.item_id} must be positive.")

        deduct_inventory_for_sale(
            db=db,
            restaurant_id=existing_order.restaurant_id,
            menu_item_id=menu_item_db.id, 
            quantity_sold=float(item_to_add.quantity), 
            order_id=existing_order.id,
            changed_by_user_id=user_uid 
        )

        item_model_in_order = None
        for current_item_in_order in existing_order.items: 
            if current_item_in_order.item_id == item_to_add.item_id:
                item_model_in_order = current_item_in_order
                break
        
        if item_model_in_order:
            item_model_in_order.quantity += item_to_add.quantity
            affected_item_models.append(item_model_in_order)
        else:
            new_order_item_model = models.OrderItem(
                order_id=existing_order.id, 
                item_id=menu_item_db.id,
                quantity=item_to_add.quantity,
                price=menu_item_db.price 
            )
            db.add(new_order_item_model) 
            # existing_order.items.append(new_order_item_model) # SQLAlchemy handles relationship append upon commit if configured
            affected_item_models.append(new_order_item_model)
            
    recalculated_total_cost = sum(item.price * item.quantity for item in existing_order.items)
        
    existing_order.total_cost = recalculated_total_cost
    existing_order.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(existing_order)

        refreshed_affected_items_for_return: List[models.OrderItem] = []
        for affected_model_item in affected_item_models:
            db.refresh(affected_model_item)
            # Eagerly load .item and item.category as per original code's intention for the return
            if not hasattr(affected_model_item, 'item') or not affected_model_item.item :
                 db.refresh(affected_model_item, attribute_names=['item'])
            if hasattr(affected_model_item, 'item') and affected_model_item.item and \
               (not hasattr(affected_model_item.item, 'category') or not affected_model_item.item.category):
                 db.refresh(affected_model_item.item, attribute_names=['category'])
            refreshed_affected_items_for_return.append(affected_model_item)

    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError adding items to order {existing_order.id}: {e}")
        raise ValueError(f"Could not add items due to a database conflict: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding items to order {existing_order.id}: {e}", exc_info=True)
        raise Exception(f"An unexpected error occurred while adding items: {str(e)}")
        
    return existing_order, refreshed_affected_items_for_return 