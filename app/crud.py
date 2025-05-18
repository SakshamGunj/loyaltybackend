from sqlalchemy.orm import Session, joinedload, selectinload
from . import models, schemas
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, desc, or_
from datetime import datetime, timedelta
from .utils.timezone import ist_now, utc_to_ist
from .auth.custom_auth import get_password_hash
import logging
import uuid
import re
from .crud_inventory import deduct_inventory_for_sale

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

import re

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
        slug = f"{base_slug}-{suffix}" # Use hyphen for better readability
        suffix += 1
    
    # Get all data from the Pydantic schema, including new fields with their defaults
    # owner_uid is now passed explicitly to the function, not taken from schema directly for creation.
    data = restaurant.dict(exclude_unset=True) # exclude_unset=True is good for updates, for create we want all fields including defaults from schema
    
    # Ensure restaurant_id (slug) and owner_uid are set correctly
    data["restaurant_id"] = slug
    data["owner_uid"] = owner_uid # Set owner_uid from the authenticated user creating it
    
    # created_at is handled by the model's default
    # admin_uid can also be set here if the owner is also the initial admin
    if "admin_uid" not in data or data["admin_uid"] is None:
        data["admin_uid"] = owner_uid

    # All other fields from RestaurantCreate (address, contact_phone, email, tax_id, currency, timezone,
    # opening_time, closing_time, is_open, weekly_off_days, accepted_payment_modes,
    # allow_manual_discount, bill_number_prefix, bill_series_start, 
    # show_tax_breakdown_on_invoice, enable_tips_collection,
    # offers, points_per_rupee, points_per_spin, reward_thresholds, spend_thresholds, referral_rewards)
    # should be present in `data` if they were provided in the request or have defaults in `schemas.RestaurantCreate`.
    # The model `models.Restaurant` has defaults for some of these too.

    db_restaurant = models.Restaurant(**data)
    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)
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

def create_claimed_reward(db: Session, reward_data: dict, current_uid: str):
    # Generate unique coupon code
    coupon_code = generate_coupon_code(db)
    # Only use allowed fields
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
def get_all_menu_items(db: Session, restaurant_id: str):
    return db.query(models.MenuItem).filter(models.MenuItem.restaurant_id == restaurant_id).all()

def create_menu_item(db: Session, restaurant_id: str, item: schemas.MenuItemCreate):
    # Convert Pydantic MenuItemVariationSchema to dicts if they are provided
    variations_data = None
    if item.variations:
        variations_data = [v.dict() for v in item.variations]

    item_data = item.dict(exclude={'restaurant_id', 'variations'}) # Exclude variations for now, will add it separately
    
    db_item = models.MenuItem(
        **item_data, 
        restaurant_id=restaurant_id,
        variations=variations_data # Add the processed variations data
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_menu_item(db: Session, item_id: int, restaurant_id: str):
    return db.query(models.MenuItem).filter(models.MenuItem.id == item_id, models.MenuItem.restaurant_id == restaurant_id).first()

def update_menu_item(db: Session, item_id: int, restaurant_id: str, item: schemas.MenuItemCreate):
    db_item = get_menu_item(db, item_id, restaurant_id)
    if not db_item:
        return None
    for field, value in item.dict(exclude_unset=True).items():
        setattr(db_item, field, value)
    db.commit()
    db.refresh(db_item)
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
    # Validate input
    if not order.items or not isinstance(order.items, list):
        raise Exception("Order must contain at least one item.")
    seen_items = set()
    
    # Always use the restaurant_id from the order
    restaurant_id = order.restaurant_id
    restaurant_name = None
    
    # Try to get restaurant name
    restaurant = db.query(models.Restaurant).filter(models.Restaurant.restaurant_id == restaurant_id).first()
    if restaurant:
        restaurant_name = restaurant.restaurant_name
    
    db_items = []
    
    # Validate items
    for item in order.items:
        if not hasattr(item, 'item_id') or not hasattr(item, 'quantity'):
            raise Exception("Each order item must have item_id and quantity.")
        if item.item_id in seen_items:
            raise Exception(f"Duplicate item in order: {item.item_id}")
        seen_items.add(item.item_id)
        if not isinstance(item.quantity, int) or item.quantity <= 0:
            raise Exception(f"Invalid quantity for item {item.item_id}")
        
        # Get menu item and validate
        db_menu_item = db.query(models.MenuItem).filter(
            models.MenuItem.id == item.item_id,
            models.MenuItem.available == True
        ).first()
        if not db_menu_item:
            raise Exception(f"Menu item not found or unavailable: {item.item_id}")
            
        # No longer enforcing item restaurant_id to match order restaurant_id
        # Use the items as long as they exist, regardless of their restaurant
            
        # Store validated items
        db_items.append((db_menu_item, item.quantity))

    # Calculate total cost
    total_cost = 0
    for db_menu_item, quantity in db_items:
        total_cost += db_menu_item.price * quantity

    # Get promo code ID if applicable
    promo_code_id = None
    if order.promo_code:
        promo = db.query(models.PromoCode).filter(
            models.PromoCode.code == order.promo_code,
            models.PromoCode.active == True
        ).first()
        if promo:
            promo_code_id = promo.id

    # Generate restaurant-specific order number
    # Find the highest order_number for this restaurant
    latest_order = db.query(models.Order).filter(
        models.Order.restaurant_id == restaurant_id
    ).order_by(models.Order.order_number.desc()).first()
    
    order_number = 1  # Default start
    if latest_order and latest_order.order_number:
        order_number = latest_order.order_number + 1
    
    # Generate order ID in format "restaurant_id{order_number}"
    order_id = f"{restaurant_id}_{order_number}"

    # Create order
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
        promo_code_id=promo_code_id,
        restaurant_id=restaurant_id,
        restaurant_name=restaurant_name
    )
    if admin_uid:
        db_order.admin_uid = admin_uid
    
    # Add both order and order items in a single transaction
    try:
        # Add the order to the session. ID is manually generated so it's available.
        db.add(db_order)
        
        # Now create and add order items with the order ID
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
        
        # Deduct inventory for each item in the order
        # This should happen before the final commit of the order transaction
        for db_menu_item, qty_sold in db_items:
            # crud_inventory.deduct_inventory_for_sale expects restaurant_id, menu_item_id, quantity_sold, order_id, changed_by_user_id
            deduct_inventory_for_sale(
                db=db,
                restaurant_id=db_order.restaurant_id,
                menu_item_id=db_menu_item.id,
                quantity_sold=float(qty_sold), # Ensure quantity is float for consistency with model
                order_id=db_order.id,
                changed_by_user_id=user_uid # user_uid is the user placing the order
            )
            # deduct_inventory_for_sale handles its own logging for inventory changes.
            # It will create an InventoryUpdateLog entry.

        # Commit all changes together: order, order_items, and inventory adjustments (via logs)
        db.commit()
        db.refresh(db_order) # Refresh to get any DB-generated changes for the order
        
        # If OrderOut schema expects items to be populated, ensure they are.
        # SQLAlchemy relationships usually handle this (lazy loading or eager loading if configured).
        # db.refresh(db_order.items) # Not usually needed explicitly if using relationship correctly
        
        return db_order
    except IntegrityError as e:
        db.rollback()
        raise Exception("Duplicate order item detected. Please try again.")
    except Exception as e:
        db.rollback()
        raise Exception(f"Error creating order: {str(e)}")

def get_orders_by_user(db: Session, user_uid: str, restaurant_id: Optional[str] = None):
    """Get orders for a specific user with a fault-tolerant approach."""
    try:
        # Get base orders for this user
        orders = db.query(models.Order).filter(
            models.Order.user_uid == user_uid
        ).order_by(models.Order.created_at.desc()).all()
        
        result_orders = []
        for order in orders:
            # Add minimal order info to result
            order_dict = {
                "id": order.id,
                "user_uid": order.user_uid,
                "user_role": order.user_role,
                "table_number": order.table_number,
                "created_at": order.created_at,
                "status": order.status,
                "total_cost": order.total_cost,
                "payment_status": order.payment_status,
                "promo_code_id": order.promo_code_id
            }
            
            # Safely try to add items
            try:
                order_items = db.query(models.OrderItem).filter(
                    models.OrderItem.order_id == order.id
                ).all()
                
                items = []
                restaurant_ids = set()
                
                for order_item in order_items:
                    item_dict = {
                        "id": order_item.id,
                        "quantity": order_item.quantity,
                        "price": order_item.price
                    }
                    
                    # Try to get menu item details
                    try:
                        menu_item = db.query(models.MenuItem).filter(
                            models.MenuItem.id == order_item.item_id
                        ).first()
                        
                        if menu_item:
                            item_dict["item"] = {
                                "id": menu_item.id,
                                "name": menu_item.name,
                                "price": menu_item.price,
                                "restaurant_id": menu_item.restaurant_id
                            }
                            restaurant_ids.add(menu_item.restaurant_id)
                    except Exception as e:
                        logger.warning(f"Error getting menu item for order {order.id}: {e}")
                        
                    items.append(item_dict)
                
                # Set items on the order
                order_dict["items"] = items
                
                # Filter by restaurant_id if provided
                if restaurant_id and restaurant_id not in restaurant_ids:
                    continue  # Skip this order if it doesn't match the requested restaurant
                
                # Add restaurant info if found
                if restaurant_ids:
                    restaurant_id_value = next(iter(restaurant_ids))
                    order_dict["restaurant_id"] = restaurant_id_value
                    
                    # Try to get restaurant name
                    try:
                        restaurant = db.query(models.Restaurant).filter(
                            models.Restaurant.restaurant_id == restaurant_id_value
                        ).first()
                        if restaurant:
                            order_dict["restaurant_name"] = restaurant.restaurant_name
                    except Exception as e:
                        logger.warning(f"Error getting restaurant for order {order.id}: {e}")
            
            except Exception as e:
                logger.warning(f"Error getting items for order {order.id}: {e}")
                order_dict["items"] = []
            
            # Safely try to add payment info
            try:
                payment = db.query(models.Payment).filter(
                    models.Payment.order_id == order.id
                ).first()
                
                if payment:
                    order_dict["payment"] = {
                        "id": payment.id,
                        "amount": payment.amount,
                        "method": payment.method,
                        "status": payment.status,
                        "paid_at": payment.paid_at
                    }
            except Exception as e:
                logger.warning(f"Error getting payment for order {order.id}: {e}")
            
            # Safely try to add status history
            try:
                status_history = db.query(models.OrderStatusHistory).filter(
                    models.OrderStatusHistory.order_id == order.id
                ).order_by(models.OrderStatusHistory.changed_at.desc()).all()
                
                if status_history:
                    order_dict["status_history"] = [{
                        "id": history.id,
                        "status": history.status,
                        "changed_at": history.changed_at,
                        "changed_by": history.changed_by
                    } for history in status_history]
            except Exception as e:
                logger.warning(f"Error getting status history for order {order.id}: {e}")
            
            # Add this order to results
            result_orders.append(order_dict)
        
        return result_orders
        
    except Exception as e:
        logger.error(f"Error in get_orders_by_user: {e}")
        # Return empty list in case of error
        return []

def get_all_orders(db: Session, restaurant_id: Optional[str] = None):
    """Get all orders with a fault-tolerant approach that works with schema changes."""
    try:
        # Get orders with minimal relationships first to avoid schema issues
        orders_query = db.query(models.Order).order_by(models.Order.created_at.desc())
        if restaurant_id:
            orders_query = orders_query.filter(models.Order.restaurant_id == restaurant_id)
        orders = orders_query.all()
        
        result_orders = []
        for order in orders:
            # Add minimal order info to result
            order_dict = {
                "id": order.id,
                "user_uid": order.user_uid,
                "user_role": order.user_role,
                "table_number": order.table_number,
                "created_at": order.created_at,
                "status": order.status,
                "total_cost": order.total_cost,
                "payment_status": order.payment_status,
                "promo_code_id": order.promo_code_id
            }
            
            # Safely try to add items
            try:
                order_items = db.query(models.OrderItem).filter(
                    models.OrderItem.order_id == order.id
                ).all()
                
                items = []
                restaurant_ids = set()
                
                for order_item in order_items:
                    item_dict = {
                        "id": order_item.id,
                        "quantity": order_item.quantity,
                        "price": order_item.price
                    }
                    
                    # Try to get menu item details
                    try:
                        menu_item = db.query(models.MenuItem).filter(
                            models.MenuItem.id == order_item.item_id
                        ).first()
                        
                        if menu_item:
                            item_dict["item"] = {
                                "id": menu_item.id,
                                "name": menu_item.name,
                                "price": menu_item.price,
                                "restaurant_id": menu_item.restaurant_id
                            }
                            restaurant_ids.add(menu_item.restaurant_id)
                    except Exception as e:
                        # Log the error but continue
                        logger.warning(f"Error getting menu item for order {order.id}: {e}")
                        
                    items.append(item_dict)
                
                # Set items on the order
                order_dict["items"] = items
                
                # Filter by restaurant_id if provided
                if restaurant_id and restaurant_id not in restaurant_ids:
                    continue  # Skip this order if it doesn't match the requested restaurant
                
                # Add restaurant info if found
                if restaurant_ids:
                    restaurant_id_value = next(iter(restaurant_ids))
                    order_dict["restaurant_id"] = restaurant_id_value
                    
                    # Try to get restaurant name
                    try:
                        restaurant = db.query(models.Restaurant).filter(
                            models.Restaurant.restaurant_id == restaurant_id_value
                        ).first()
                        if restaurant:
                            order_dict["restaurant_name"] = restaurant.restaurant_name
                    except Exception as e:
                        logger.warning(f"Error getting restaurant for order {order.id}: {e}")
            
            except Exception as e:
                logger.warning(f"Error getting items for order {order.id}: {e}")
                order_dict["items"] = []
            
            # Safely try to add payment info
            try:
                payment = db.query(models.Payment).filter(
                    models.Payment.order_id == order.id
                ).first()
                
                if payment:
                    order_dict["payment"] = {
                        "id": payment.id,
                        "amount": payment.amount,
                        "method": payment.method,
                        "status": payment.status,
                        "paid_at": payment.paid_at
                    }
            except Exception as e:
                logger.warning(f"Error getting payment for order {order.id}: {e}")
            
            # Safely try to add status history
            try:
                status_history = db.query(models.OrderStatusHistory).filter(
                    models.OrderStatusHistory.order_id == order.id
                ).order_by(models.OrderStatusHistory.changed_at.desc()).all()
                
                if status_history:
                    order_dict["status_history"] = [{
                        "id": history.id,
                        "status": history.status,
                        "changed_at": history.changed_at,
                        "changed_by": history.changed_by
                    } for history in status_history]
            except Exception as e:
                logger.warning(f"Error getting status history for order {order.id}: {e}")
            
            # Add this order to results
            result_orders.append(order_dict)
        
        return result_orders
        
    except Exception as e:
        logger.error(f"Error in get_all_orders: {e}")
        # Return empty list in case of error
        return []

def filter_orders(db: Session, status=None, start_date=None, end_date=None, payment_method=None, user_uid: Optional[str]=None, order_id: Optional[str]=None, user_email: Optional[str]=None, user_phone: Optional[str]=None, restaurant_id: Optional[str]=None):
    """Filter orders with a fault-tolerant approach."""
    try:
        # Start with a base query
        query = db.query(models.Order)
        
        # Apply standard filters
        if status:
            query = query.filter(models.Order.status == status)
        if start_date:
            query = query.filter(models.Order.created_at >= start_date)
        if end_date:
            query = query.filter(models.Order.created_at <= end_date)
        if order_id:
            query = query.filter(models.Order.id == order_id)
        if user_uid:
            query = query.filter(models.Order.user_uid == user_uid)
        if restaurant_id:
            query = query.filter(models.Order.restaurant_id == restaurant_id)

        # Get the filtered orders
        orders = query.order_by(models.Order.created_at.desc()).all()
        
        # Post-process orders using safe queries for relationships
        result_orders = []
        for order in orders:
            # Initialize with base order fields
            order_dict = {
                "id": order.id,
                "user_uid": order.user_uid,
                "user_role": order.user_role,
                "table_number": order.table_number,
                "created_at": order.created_at,
                "status": order.status,
                "total_cost": order.total_cost,
                "payment_status": order.payment_status,
                "promo_code_id": order.promo_code_id
            }
            
            # Apply payment method filter safely
            if payment_method:
                try:
                    payment = db.query(models.Payment).filter(
                        models.Payment.order_id == order.id,
                        models.Payment.method == payment_method
                    ).first()
                    if not payment:
                        continue  # Skip this order if payment method doesn't match
                except Exception as e:
                    logger.warning(f"Error checking payment method for order {order.id}: {e}")
                    continue  # Skip on error
            
            # Apply user email and phone filters safely
            if user_email or user_phone:
                try:
                    user = db.query(models.User).filter(models.User.uid == order.user_uid).first()
                    if not user:
                        continue
                    
                    if user_email and (not user.email or user_email.lower() not in user.email.lower()):
                        continue
                    
                    # For phone number check - note this assumes phone is stored in the name field
                    # You may need to adjust this based on your actual schema
                    if user_phone and (not user.name or user_phone not in user.name):
                        continue
                except Exception as e:
                    logger.warning(f"Error checking user filters for order {order.id}: {e}")
                    continue
            
            # Safely get items and check restaurant_id
            restaurant_match = restaurant_id is None  # If no filter, all orders match
            try:
                order_items = db.query(models.OrderItem).filter(
                    models.OrderItem.order_id == order.id
                ).all()
                
                items = []
                restaurant_ids = set()
                
                for order_item in order_items:
                    item_dict = {
                        "id": order_item.id,
                        "quantity": order_item.quantity,
                        "price": order_item.price
                    }
                    
                    # Try to get menu item details
                    try:
                        menu_item = db.query(models.MenuItem).filter(
                            models.MenuItem.id == order_item.item_id
                        ).first()
                        
                        if menu_item:
                            item_dict["item"] = {
                                "id": menu_item.id,
                                "name": menu_item.name,
                                "price": menu_item.price,
                                "restaurant_id": menu_item.restaurant_id
                            }
                            restaurant_ids.add(menu_item.restaurant_id)
                            
                            # Check for restaurant_id filter match
                            if restaurant_id and menu_item.restaurant_id == restaurant_id:
                                restaurant_match = True
                    except Exception as e:
                        logger.warning(f"Error getting menu item for order {order.id}: {e}")
                        
                    items.append(item_dict)
                
                # Set items on the order
                order_dict["items"] = items
                
                # Skip this order if restaurant_id filter doesn't match
                if not restaurant_match:
                    continue
                
                # Add restaurant info if found
                if restaurant_ids:
                    restaurant_id_value = next(iter(restaurant_ids))
                    order_dict["restaurant_id"] = restaurant_id_value
                    
                    # Try to get restaurant name
                    try:
                        restaurant = db.query(models.Restaurant).filter(
                            models.Restaurant.restaurant_id == restaurant_id_value
                        ).first()
                        if restaurant:
                            order_dict["restaurant_name"] = restaurant.restaurant_name
                    except Exception as e:
                        logger.warning(f"Error getting restaurant for order {order.id}: {e}")
            
            except Exception as e:
                logger.warning(f"Error getting items for order {order.id}: {e}")
                order_dict["items"] = []
                # Skip if restaurant filter is applied but we can't check it
                if restaurant_id:
                    continue
            
            # Safely try to add payment info
            try:
                payment = db.query(models.Payment).filter(
                    models.Payment.order_id == order.id
                ).first()
                
                if payment:
                    order_dict["payment"] = {
                        "id": payment.id,
                        "amount": payment.amount,
                        "method": payment.method,
                        "status": payment.status,
                        "paid_at": payment.paid_at
                    }
            except Exception as e:
                logger.warning(f"Error getting payment for order {order.id}: {e}")
            
            # Safely try to add status history
            try:
                status_history = db.query(models.OrderStatusHistory).filter(
                    models.OrderStatusHistory.order_id == order.id
                ).order_by(models.OrderStatusHistory.changed_at.desc()).all()
                
                if status_history:
                    order_dict["status_history"] = [{
                        "id": history.id,
                        "status": history.status,
                        "changed_at": history.changed_at,
                        "changed_by": history.changed_by
                    } for history in status_history]
            except Exception as e:
                logger.warning(f"Error getting status history for order {order.id}: {e}")
            
            # Add this order to results
            result_orders.append(order_dict)
        
        return result_orders
        
    except Exception as e:
        logger.error(f"Error in filter_orders: {e}")
        # Return empty list in case of error
        return []

def update_order_status(db: Session, order_id: int, status: str, changed_by: str):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise Exception(f"Order not found: {order_id}")
    
    # Update order status
    db_order.status = status
    
    # Add status history record
    status_history = models.OrderStatusHistory(
        order_id=order_id,
        status=status,
        changed_by=changed_by
    )
    db.add(status_history)
    
    # Update payment status if needed
    if status == "Payment Done":
        db_order.payment_status = "Paid"
    
    db.commit()
    db.refresh(db_order)
    return db_order

def confirm_order(db: Session, order_id: int, changed_by: str):
    return update_order_status(db, order_id, "Order Confirmed", changed_by)

def mark_order_paid(db: Session, order_id: str, changed_by: str, payment_method: str, transaction_id: Optional[str] = None):
    db_order = db.query(models.Order).options(
        joinedload(models.Order.items).joinedload(models.OrderItem.item).joinedload(models.MenuItem.category),
        joinedload(models.Order.user),
        joinedload(models.Order.promo_code),
        joinedload(models.Order.payment) # Eager load existing payment record
    ).filter(models.Order.id == order_id).first()

    if not db_order:
        raise ValueError(f"Order {order_id} not found")

    # If already paid, and no further action is needed, can return early.
    # However, the function might be used to update transaction_id or other details even if already paid.
    # For inventory deduction, we specifically want to avoid re-deducting.
    # if db_order.payment_status == "Paid":
    #     logging.info(f"Order {order_id} is already marked as Paid. No further payment status change.")
    #     # return db_order # Or raise appropriate HTTP exception

    # Log the billing details (existing logging is good here)
    customer_name = db_order.user.name if db_order.user else "N/A"
    customer_email = db_order.user.email if db_order.user else "N/A"
    promo_code_details = "None"
    if db_order.promo_code:
        promo_code_details = f"Code: {db_order.promo_code.code}, Discount: {db_order.promo_code.discount_percent or db_order.promo_code.discount_amount}"
    
    logging.info(f"--- BILLING EVENT: Order {order_id} Marked Paid by {changed_by} via {payment_method} ---")
    logging.info(f"Transaction ID: {transaction_id if transaction_id else 'N/A'}")
    logging.info(f"Customer: {customer_name} (UID: {db_order.user_uid}, Email: {customer_email})")
    logging.info(f"Restaurant: {db_order.restaurant_id} ({db_order.restaurant_name})")
    logging.info(f"Table Number: {db_order.table_number if db_order.table_number else 'N/A'}")
    logging.info(f"Total Cost: {db_order.total_cost}")
    logging.info(f"Promo Code Applied: {promo_code_details}")
    logging.info("Items Billed:")
    for item in db_order.items:
        logging.info(f"  - {item.quantity} x {item.item.name if item.item else 'Unknown Item'} @ {item.price} each")
    logging.info(f"--- END BILLING EVENT --- ")

    # Deduct inventory for each item in the order when marking as paid.
    # IMPORTANT: Inventory is also deducted in `create_order` and `add_items_to_order`.
    # Review to ensure this is the desired behavior and to avoid double-deduction
    # if `deduct_inventory_for_sale` is not idempotent for this specific combination
    # of calls across the order lifecycle.
    # This block assumes that if `deduct_inventory_for_sale` fails, it will raise an
    # exception, which will be caught by the outer try-except block of this function,
    # leading to a rollback of the entire transaction.

    if db_order.payment_status != "Paid":
        logger.info(f"Order {order_id} current payment_status is '{db_order.payment_status}'. Proceeding with inventory deduction.")
        for order_item_model in db_order.items:
            if order_item_model.item and order_item_model.quantity > 0: # Ensure item exists and quantity is positive
                logger.info(f"Deducting inventory for order {db_order.id}, item {order_item_model.item_id} (menu item name: {order_item_model.item.name if order_item_model.item else 'N/A'}), quantity {order_item_model.quantity}.")
                deduct_inventory_for_sale(
                    db=db,
                    restaurant_id=db_order.restaurant_id,
                    menu_item_id=order_item_model.item_id, # ID of the MenuItem
                    quantity_sold=float(order_item_model.quantity),
                    order_id=db_order.id,
                    changed_by_user_id=changed_by # User who is marking the order paid
                )
                logger.info(f"Inventory deduction call for order {db_order.id}, item {order_item_model.item_id} completed.")
    else:
        logger.info(f"Order {order_id} is already 'Paid'. Skipping inventory deduction step in `mark_order_paid`.")

    # Create or Update Payment record
    if db_order.payment:
        db_payment = db_order.payment
        db_payment.amount = db_order.total_cost # Ensure amount is correct
        db_payment.method = payment_method
        db_payment.status = "Paid"
        db_payment.paid_at = datetime.utcnow()
        db_payment.transaction_id = transaction_id
        db_payment.processed_at = datetime.utcnow() # Update processed_at as well
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
        db_order.payment = db_payment # Associate with the order for the session

    db_order.payment_status = "Paid"
    db_order.status = "Payment Done"  # Or another appropriate status like "Completed"
    db_order.updated_at = datetime.utcnow()
    
    # Create an audit log for payment
    create_audit_log(db, schemas.AuditLogCreate(
        user_id=changed_by, 
        action="Order Marked Paid", 
        details={
            "order_id": order_id, 
            "marked_by": changed_by, 
            "payment_method": payment_method,
            "transaction_id": transaction_id,
            "new_payment_status": "Paid"
        },
        order_id=order_id # Link audit log to the order
    ))
    
    try:
        db.commit()
        db.refresh(db_order)
        if db_order.payment: # Refresh payment if it was created/updated
            db.refresh(db_order.payment)
    except Exception as e:
        db.rollback()
        logging.error(f"Error committing payment for order {order_id}: {e}", exc_info=True)
        raise # Re-raise the exception to be handled by the endpoint
        
    return db_order

def cancel_order(db: Session, order_id: int, cancelled_by: str):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise Exception("Order not found")
    if db_order.status not in ["Pending", "Confirmed"]:
        raise Exception("Order cannot be cancelled at this stage.")
    db_order.status = "Cancelled"
    db.commit()
    db.refresh(db_order)
    # Log to audit
    try:
        from .schemas import AuditLogCreate
        db.add(models.AuditLog(order_id=order_id, user_id=cancelled_by, action="cancel", timestamp=datetime.utcnow(), details="Order cancelled"))
        db.commit()
    except Exception:
        pass
    return db_order

def refund_order(db: Session, order_id: int, refunded_by: str):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise Exception("Order not found")
    if db_order.payment_status != "Paid":
        raise Exception("Order is not paid, cannot refund.")
    db_order.payment_status = "Refunded"
    if db_order.payment:
        db_order.payment.status = "Refunded"
        db_order.payment.paid_at = datetime.utcnow()
    db.commit()
    db.refresh(db_order)
    # Log to audit
    try:
        from .schemas import AuditLogCreate
        db.add(models.AuditLog(order_id=order_id, user_id=refunded_by, action="refund", timestamp=datetime.utcnow(), details="Order refunded"))
        db.commit()
    except Exception:
        pass
    return db_order

# --- Payments ---
def update_payment(db: Session, order_id: int, payment: schemas.PaymentCreate):
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
            paid_at=datetime.utcnow()
        )
        db.add(db_payment)
    else:
        for field, value in payment.dict(exclude_unset=True).items():
            setattr(db_payment, field, value)
    db_order.payment_status = payment.status or "Pending"
    db.commit()
    db.refresh(db_payment)
    db.refresh(db_order)
    return db_payment

# --- Promo Codes ---
def apply_promo_code(db: Session, code: str, user_id: str):
    promo = db.query(models.PromoCode).filter(models.PromoCode.code == code, models.PromoCode.active == True).first()
    if not promo:
        raise Exception("Promo code not found or inactive")
    now = datetime.utcnow()
    if promo.valid_from and now < promo.valid_from:
        raise Exception("Promo code not yet valid")
    if promo.valid_to and now > promo.valid_to:
        raise Exception("Promo code expired")
    if promo.usage_limit and promo.used_count >= promo.usage_limit:
        raise Exception("Promo code usage limit reached")
    promo.used_count += 1
    db.commit()
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
    for field, value in promo.dict(exclude_unset=True).items():
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
    # Returns dict with order count, total sales, and popular items for given period
    from sqlalchemy import func
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    if period == "daily":
        start = today
        end = today + timedelta(days=1)
    elif period == "weekly":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=7)
    elif period == "monthly":
        start = today.replace(day=1)
        # Next month
        if start.month == 12:
            end = start.replace(year=start.year+1, month=1)
        else:
            end = start.replace(month=start.month+1)
    else:
        raise ValueError("Invalid period")
    order_count = db.query(models.Order).filter(models.Order.created_at >= start, models.Order.created_at < end).count()
    total_sales = db.query(func.sum(models.Order.total_cost)).filter(models.Order.created_at >= start, models.Order.created_at < end).scalar() or 0
    # Popular items: top 5 by quantity ordered in period
    popular = db.query(models.MenuItem.name, func.sum(models.OrderItem.quantity).label('qty')).join(models.OrderItem, models.MenuItem.id == models.OrderItem.item_id)
    popular = popular.join(models.Order, models.Order.id == models.OrderItem.order_id)
    popular = popular.filter(models.Order.created_at >= start, models.Order.created_at < end)
    popular = popular.group_by(models.MenuItem.name).order_by(func.sum(models.OrderItem.quantity).desc()).limit(5).all()
    return {
        "order_count": order_count,
        "total_sales": total_sales,
        "popular_items": [{"name": n, "quantity": q} for n, q in popular]
    }

def export_orders_csv(db: Session, orders: List[models.Order]):
    import csv
    from io import StringIO
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Order ID", "User UID", "User Role", "Table Number", "Restaurant ID", "Restaurant Name", "Created At", "Status", "Total Cost", "Payment Status"])
    for order in orders:
        restaurant_id = getattr(order, 'restaurant_id', None) 
        restaurant_name = getattr(order, 'restaurant_name', None)
        writer.writerow([
            order.id, 
            order.user_uid,
            order.user_role,
            order.table_number,
            restaurant_id,
            restaurant_name,
            order.created_at, 
            order.status, 
            order.total_cost, 
            order.payment_status
        ])
    return output.getvalue()

# --- Order ---

def get_unpaid_order_by_table(db: Session, restaurant_id: str, table_number: str) -> Optional[models.Order]:
    """Fetches an unpaid order for a specific table and restaurant."""
    if not table_number: # Cannot search for null table number this way
        return None
    return db.query(models.Order).options(
        joinedload(models.Order.items).options(joinedload(models.OrderItem.item)) # Eager load items and their menu item details
    ).filter(
        models.Order.restaurant_id == restaurant_id,
        models.Order.table_number == table_number,
        models.Order.payment_status == "Pending"
    ).first()

def add_items_to_order(db: Session, existing_order: models.Order, new_items_create: List[schemas.OrderItemCreate], user_uid: str) -> Tuple[models.Order, List[models.OrderItem]]:
    """Adds new items to an existing order and recalculates total cost.
    Returns the updated order and a list of OrderItem model instances that were newly created or had their quantity updated.
    """
    if not new_items_create:
        raise ValueError("Must provide items to add.")

    # Ensure existing_order.items is loaded.
    # The get_unpaid_order_by_table should have eager loaded this.
    # If not, a quick refresh or re-query might be needed, but let's assume it's loaded.

    affected_item_models: List[models.OrderItem] = []

    for item_to_add in new_items_create: # item_to_add is schemas.OrderItemCreate
        menu_item_db = db.query(models.MenuItem).filter(
            models.MenuItem.id == item_to_add.item_id,
            models.MenuItem.available == True,
            models.MenuItem.restaurant_id == existing_order.restaurant_id
        ).first()

        if not menu_item_db:
            raise ValueError(f"Menu item with ID {item_to_add.item_id} for restaurant {existing_order.restaurant_id} not found or unavailable.")
        
        if item_to_add.quantity <= 0:
            raise ValueError(f"Quantity for item ID {item_to_add.item_id} must be positive.")

        # Deduct inventory for the item being added/updated
        # This should happen before the item quantity is updated in the order or a new item is added
        deduct_inventory_for_sale(
            db=db,
            restaurant_id=existing_order.restaurant_id,
            menu_item_id=menu_item_db.id, # Use menu_item_db.id as it's confirmed valid
            quantity_sold=float(item_to_add.quantity), # Quantity being added in this operation
            order_id=existing_order.id,
            changed_by_user_id=user_uid # user_uid is the user performing this action
        )

        # Check if item already exists in the order to update quantity
        item_model_in_order = None
        for current_item_in_order in existing_order.items: # these are models.OrderItem
            if current_item_in_order.item_id == item_to_add.item_id:
                item_model_in_order = current_item_in_order
                break
        
        if item_model_in_order:
            item_model_in_order.quantity += item_to_add.quantity
            affected_item_models.append(item_model_in_order)
        else:
            new_order_item_model = models.OrderItem(
                order_id=existing_order.id, # Associate with existing order
                item_id=menu_item_db.id,
                quantity=item_to_add.quantity,
                price=menu_item_db.price 
            )
            db.add(new_order_item_model) # Add to session
            existing_order.items.append(new_order_item_model) # Add to the Order's item collection
            affected_item_models.append(new_order_item_model)
            
    # Recalculate total cost from the now updated existing_order.items list
    recalculated_total_cost = 0
    for item_in_final_list in existing_order.items:
        recalculated_total_cost += (item_in_final_list.price * item_in_final_list.quantity)
        
    existing_order.total_cost = recalculated_total_cost
    existing_order.updated_at = datetime.utcnow()
    
    try:
        # The inventory deductions are already part of the session (flushed by deduct_inventory_for_sale if it does that, or just added to session).
        # The main db.commit() here will save order changes, new/updated order items, and inventory log entries.
        db.commit()
        db.refresh(existing_order) # Refresh the main order object

        # After commit, the affected_item_models (especially new ones) will have IDs.
        # Refresh each affected item to ensure all fields are up-to-date from DB 
        # and relationships like '.item' are loaded if needed for the return to endpoint.
        refreshed_affected_items_for_return: List[models.OrderItem] = []
        for affected_model_item in affected_item_models:
            db.refresh(affected_model_item)
            # Eagerly load the .item (MenuItem) relationship for each affected OrderItem
            if not affected_model_item.item: # If .item is not loaded
                 db.refresh(affected_model_item, attribute_names=['item'])
            # Further eager load item.category if your schemas.OrderItemOut needs it
            if affected_model_item.item and not affected_model_item.item.category:
                 db.refresh(affected_model_item.item, attribute_names=['category'])
            refreshed_affected_items_for_return.append(affected_model_item)

    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError adding items to order {existing_order.id}: {e}")
        raise ValueError(f"Could not add items due to a database conflict: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding items to order {existing_order.id}: {e}")
        # Consider logging exc_info=True for full traceback
        raise Exception(f"An unexpected error occurred while adding items: {str(e)}")
        
    return existing_order, refreshed_affected_items_for_return # MODIFIED

# --- User Dashboard --- 

def get_user_dashboard_data(db: Session, user_uid: str, restaurant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """ 
    Gathers data for a user's dashboard, including profile, orders, loyalty, and rewards.
    Returns None if the user is not found.
    """
    # Fetch user profile
    user_profile = get_user(db, uid=user_uid)
    if not user_profile:
        logger.info(f"User dashboard data requested for non-existent user UID: {user_uid}")
        return None # User not found

    # Fetch user orders
    # get_orders_by_user is fault-tolerant and returns List[Dict]
    user_orders = get_orders_by_user(db, user_uid=user_uid, restaurant_id=restaurant_id)

    # Fetch user loyalty information
    # list_loyalties returns List[models.Loyalty]
    user_loyalty_info = list_loyalties(db, uid=user_uid)

    # Fetch user claimed rewards
    # list_claimed_rewards returns List[models.ClaimedReward]
    user_claimed_rewards = list_claimed_rewards(db, uid=user_uid)

    dashboard_data = {
        "profile": user_profile,  # models.User object
        "orders": user_orders,    # List[Dict]
        "loyalty_info": user_loyalty_info,  # List[models.Loyalty]
        "claimed_rewards": user_claimed_rewards  # List[models.ClaimedReward]
    }
    
    logger.info(f"Successfully compiled dashboard data for user UID: {user_uid}")
    return dashboard_data

