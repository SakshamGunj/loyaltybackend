from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Optional
from sqlalchemy.exc import IntegrityError
from datetime import datetime

def create_user(db: Session, user: schemas.UserBase):
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, uid: str):
    return db.query(models.User).filter(models.User.uid == uid).first()

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
def get_all_menu_categories(db: Session):
    return db.query(models.MenuCategory).all()

def create_menu_category(db: Session, category: schemas.MenuCategoryCreate):
    db_cat = models.MenuCategory(**category.dict())
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat

def get_menu_category(db: Session, category_id: int):
    return db.query(models.MenuCategory).filter(models.MenuCategory.id == category_id).first()

def update_menu_category(db: Session, category_id: int, category: schemas.MenuCategoryCreate):
    db_cat = get_menu_category(db, category_id)
    if not db_cat:
        return None
    for field, value in category.dict(exclude_unset=True).items():
        setattr(db_cat, field, value)
    db.commit()
    db.refresh(db_cat)
    return db_cat

def delete_menu_category(db: Session, category_id: int):
    db_cat = get_menu_category(db, category_id)
    if db_cat:
        db.delete(db_cat)
        db.commit()
        return True
    return False

# --- Menu Item ---
def get_all_menu_items(db: Session):
    return db.query(models.MenuItem).all()

def create_menu_item(db: Session, item: schemas.MenuItemCreate):
    db_item = models.MenuItem(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_menu_item(db: Session, item_id: int):
    return db.query(models.MenuItem).filter(models.MenuItem.id == item_id).first()

def update_menu_item(db: Session, item_id: int, item: schemas.MenuItemCreate):
    db_item = get_menu_item(db, item_id)
    if not db_item:
        return None
    for field, value in item.dict(exclude_unset=True).items():
        setattr(db_item, field, value)
    db.commit()
    db.refresh(db_item)
    return db_item

def delete_menu_item(db: Session, item_id: int):
    db_item = get_menu_item(db, item_id)
    if db_item:
        db.delete(db_item)
        db.commit()
        return True
    return False

# --- Orders ---
def create_order(db: Session, order: schemas.OrderCreate, user_id: str):
    # Calculate total cost and create order + order items atomically
    total_cost = 0
    db_items = []
    for item in order.items:
        db_menu_item = db.query(models.MenuItem).filter(models.MenuItem.id == item.item_id, models.MenuItem.available == True).first()
        if not db_menu_item:
            raise Exception(f"Menu item not found or unavailable: {item.item_id}")
        db_items.append((db_menu_item, item.quantity))
        total_cost += db_menu_item.price * item.quantity
    applied_promo = None
    if order.promo_code:
        applied_promo = db.query(models.PromoCode).filter(models.PromoCode.code == order.promo_code, models.PromoCode.active == True).first()
        if applied_promo:
            # Check validity and usage
            now = datetime.utcnow()
            if applied_promo.valid_from and now < applied_promo.valid_from:
                raise Exception("Promo code not yet valid")
            if applied_promo.valid_to and now > applied_promo.valid_to:
                raise Exception("Promo code expired")
            if applied_promo.usage_limit and applied_promo.used_count >= applied_promo.usage_limit:
                raise Exception("Promo code usage limit reached")
            if applied_promo.discount_percent:
                total_cost *= (1 - applied_promo.discount_percent/100)
            elif applied_promo.discount_amount:
                total_cost -= applied_promo.discount_amount
            total_cost = max(0, total_cost)
            applied_promo.used_count += 1
            db.commit()
    db_order = models.Order(
        user_id=user_id,
        created_at=datetime.utcnow(),
        status="Pending",
        total_cost=total_cost,
        payment_status="Pending",
        promo_code_id=applied_promo.id if applied_promo else None
    )
    db.add(db_order)
    db.commit()
    for db_menu_item, qty in db_items:
        db_order_item = models.OrderItem(
            order_id=db_order.id,
            item_id=db_menu_item.id,
            quantity=qty,
            price=db_menu_item.price
        )
        db.add(db_order_item)
    db.commit()
    db.refresh(db_order)
    return db_order

def get_orders_by_user(db: Session, user_id: str):
    return db.query(models.Order).filter(models.Order.user_id == user_id).order_by(models.Order.created_at.desc()).all()

def get_all_orders(db: Session):
    return db.query(models.Order).order_by(models.Order.created_at.desc()).all()

def get_all_orders(db: Session):
    return db.query(models.Order).order_by(models.Order.created_at.desc()).all()

def filter_orders(db: Session, status=None, start_date=None, end_date=None, payment_method=None, user_id=None, order_id=None, user_email=None, user_phone=None):
    q = db.query(models.Order)
    if status:
        q = q.filter(models.Order.status == status)
    if start_date:
        q = q.filter(models.Order.created_at >= start_date)
    if end_date:
        q = q.filter(models.Order.created_at <= end_date)
    if payment_method:
        q = q.join(models.Payment).filter(models.Payment.method == payment_method)
    if user_id:
        q = q.filter(models.Order.user_id == user_id)
    if order_id:
        q = q.filter(models.Order.id == order_id)
    if user_email or user_phone:
        q = q.join(models.User)
        if user_email:
            q = q.filter(models.User.email.ilike(f"%{user_email}%"))
        if user_phone:
            q = q.filter(models.User.name.ilike(f"%{user_phone}%"))  # Change to phone if available
    return q.order_by(models.Order.created_at.desc()).all()

def update_order_status(db: Session, order_id: int, status: str):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise Exception("Order not found")
    db_order.status = status
    db.commit()
    db.refresh(db_order)
    return db_order

def confirm_order(db: Session, order_id: int):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise Exception("Order not found")
    db_order.status = "Confirmed"
    db.commit()
    db.refresh(db_order)
    return db_order

def mark_order_paid(db: Session, order_id: int):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise Exception("Order not found")
    db_order.payment_status = "Paid"
    # Also update Payment record if present
    if db_order.payment:
        db_order.payment.status = "Paid"
        from datetime import datetime
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
        from datetime import datetime
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
            paid_at=payment.paid_at
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
    writer.writerow(["Order ID", "User ID", "Created At", "Status", "Total Cost", "Payment Status"])
    for order in orders:
        writer.writerow([
            order.id, order.user_id, order.created_at, order.status, order.total_cost, order.payment_status
        ])
    return output.getvalue()

