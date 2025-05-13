from sqlalchemy.orm import Session, joinedload
from . import models, schemas
from typing import List, Optional
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from .utils.timezone import ist_now, utc_to_ist
from .auth.custom_auth import get_password_hash
import logging
import uuid

logger = logging.getLogger(__name__)

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    uid = str(uuid.uuid4())
    db_user = models.User(
        uid=uid,
        email=user.email,
        name=user.name,
        number=user.number,
        hashed_password=get_password_hash(user.password),
        role=user.role,
        created_at=datetime.utcnow()
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

def slugify(name: str) -> str:
    # Lowercase, replace spaces and non-alphanum with underscores
    slug = re.sub(r'[^a-zA-Z0-9]+', '_', name.strip().lower())
    slug = re.sub(r'_+', '_', slug)  # collapse multiple underscores
    return slug.strip('_')

def create_restaurant(db: Session, restaurant: schemas.RestaurantCreate):
    # Generate a unique restaurant_id (slug) from name
    base_slug = slugify(restaurant.restaurant_name)
    slug = base_slug
    suffix = 1
    while db.query(models.Restaurant).filter(models.Restaurant.restaurant_id == slug).first():
        slug = f"{base_slug}_{suffix}"
        suffix += 1
    data = restaurant.dict(exclude={"restaurant_id"}, exclude_unset=True)
    data["restaurant_id"] = slug
    data["created_at"] = datetime.utcnow()
    db_restaurant = models.Restaurant(**data)
    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant

def update_restaurant(db: Session, restaurant_id: str, restaurant: schemas.RestaurantCreate):
    db_restaurant = db.query(models.Restaurant).filter(models.Restaurant.restaurant_id == restaurant_id).first()
    if not db_restaurant:
        return None
    for field, value in restaurant.dict(exclude_unset=True).items():
        setattr(db_restaurant, field, value)
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant

def generate_coupon_code(db: Session):
    import random, string
    max_attempts = 1000
    for _ in range(max_attempts):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        exists = db.query(models.ClaimedReward).filter(models.ClaimedReward.coupon_code == code).first()
        if not exists:
            return code
    raise Exception("Unable to generate unique coupon code after 1000 attempts")

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
    # Create a dictionary from the item but exclude restaurant_id since it's already provided
    item_data = item.dict(exclude={'restaurant_id'})
    db_item = models.MenuItem(**item_data, restaurant_id=restaurant_id)
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
def create_order(db: Session, order: schemas.OrderCreate, user_id: str, admin_uid: Optional[str] = None):
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
        user_id=user_id,
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
        # First commit the order to get an ID
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        
        # Now create and add order items with the order ID
        order_items = []
        for db_menu_item, qty in db_items:
            order_item = models.OrderItem(
                order_id=db_order.id,
                item_id=db_menu_item.id,
                quantity=qty,
                price=db_menu_item.price
            )
            order_items.append(order_item)
        
        db.add_all(order_items)
        db.commit()
        db.refresh(db_order)
        return db_order
    except IntegrityError as e:
        db.rollback()
        raise Exception("Duplicate order item detected. Please try again.")
    except Exception as e:
        db.rollback()
        raise Exception(f"Error creating order: {str(e)}")

def get_orders_by_user(db: Session, user_id: str, restaurant_id: Optional[str] = None):
    """Get orders for a specific user with a fault-tolerant approach."""
    try:
        # Get base orders for this user
        orders = db.query(models.Order).filter(
            models.Order.user_id == user_id
        ).order_by(models.Order.created_at.desc()).all()
        
        result_orders = []
        for order in orders:
            # Add minimal order info to result
            order_dict = {
                "id": order.id,
                "user_id": order.user_id,
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
        orders = db.query(models.Order).order_by(models.Order.created_at.desc()).all()
        
        result_orders = []
        for order in orders:
            # Add minimal order info to result
            order_dict = {
                "id": order.id,
                "user_id": order.user_id,
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

def filter_orders(db: Session, status=None, start_date=None, end_date=None, payment_method=None, user_id=None, order_id=None, user_email=None, user_phone=None, restaurant_id=None):
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
        if user_id:
            query = query.filter(models.Order.user_id == user_id)
        
        # Get the filtered orders
        orders = query.order_by(models.Order.created_at.desc()).all()
        
        # Post-process orders using safe queries for relationships
        result_orders = []
        for order in orders:
            # Initialize with base order fields
            order_dict = {
                "id": order.id,
                "user_id": order.user_id,
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
                    user = db.query(models.User).filter(models.User.uid == order.user_id).first()
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

def mark_order_paid(db: Session, order_id: int, changed_by: str):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise Exception("Order not found")
    db_order.payment_status = "Paid"
    
    # Add status history record
    status_history = models.OrderStatusHistory(
        order_id=order_id,
        status="Payment Done",
        changed_by=changed_by
    )
    db.add(status_history)
    
    # Also update Payment record if present
    if db_order.payment:
        db_order.payment.status = "Paid"
        db_order.payment.paid_at = datetime.utcnow()
    db.commit()
    db.refresh(db_order)
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

def export_orders_csv(db: Session, orders):
    import csv
    from io import StringIO
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Order ID", "User ID", "Restaurant ID", "Restaurant Name", "Created At", "Status", "Total Cost", "Payment Status"])
    for order in orders:
        restaurant_id = getattr(order, 'restaurant_id', None) 
        restaurant_name = getattr(order, 'restaurant_name', None)
        writer.writerow([
            order.id, 
            order.user_id, 
            restaurant_id,
            restaurant_name,
            order.created_at, 
            order.status, 
            order.total_cost, 
            order.payment_status
        ])
    return output.getvalue()

