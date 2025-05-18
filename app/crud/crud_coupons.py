# app/crud/crud_coupons.py
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, and_, or_
from .. import models, schemas # Assuming this file is in app/crud/
from typing import List, Optional, Dict, Any
from datetime import datetime
import random
import string
import logging

logger = logging.getLogger(__name__)

# --- Coupon Code Generation Utility ---
def generate_unique_coupon_code(db: Session, length: int = 8, prefix: str = "") -> str:
    """Generates a unique alphanumeric coupon code."""
    max_attempts = 100 # Avoid infinite loops
    for _ in range(max_attempts):
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        code = f"{prefix.upper()}{random_part}" if prefix else random_part
        exists = db.query(models.Coupon).filter(models.Coupon.code == code).first()
        if not exists:
            return code
    raise Exception(f"Failed to generate a unique coupon code after {max_attempts} attempts.")

# --- Coupon CRUD Operations ---

def create_coupon_instance(db: Session, coupon_data: schemas.CouponCreateInternal) -> models.Coupon:
    """Creates a single coupon instance in the database.
    The coupon_data should already include a uniquely generated code.
    """
    # CouponCreateInternal inherits from CouponBase, which has all the fields.
    # created_at is handled by the model's default.
    
    db_coupon = models.Coupon(**coupon_data.dict())
    db.add(db_coupon)
    db.commit()
    db.refresh(db_coupon)
    return db_coupon

def get_coupon_by_id(db: Session, coupon_id: int) -> Optional[models.Coupon]:
    """Fetches a coupon by its primary key ID."""
    return db.query(models.Coupon).filter(models.Coupon.id == coupon_id).first()

def get_coupon_by_code(db: Session, code: str) -> Optional[models.Coupon]:
    """Fetches a coupon by its unique code."""
    return db.query(models.Coupon).filter(models.Coupon.code == code).first()

def list_coupons(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    coupon_type: Optional[schemas.CouponType] = None,
    is_active: Optional[bool] = None,
    restaurant_id: Optional[str] = None,
    valid_on_date: Optional[datetime] = None, # Check if coupon is valid on this specific date
    search_code: Optional[str] = None,
    search_name: Optional[str] = None
) -> List[models.Coupon]:
    """Lists coupons with various filtering options."""
    query = db.query(models.Coupon)

    if coupon_type:
        query = query.filter(models.Coupon.coupon_type == coupon_type)
    if is_active is not None:
        query = query.filter(models.Coupon.is_active == is_active)
    if restaurant_id:
        query = query.filter(models.Coupon.restaurant_id == restaurant_id)
    
    if valid_on_date:
        query = query.filter(
            and_(
                models.Coupon.start_date <= valid_on_date,
                models.Coupon.end_date >= valid_on_date,
                models.Coupon.is_active == True
            )
        )
    
    if search_code:
        query = query.filter(models.Coupon.code.ilike(f'%{search_code}%'))
    if search_name:
        query = query.filter(models.Coupon.name.ilike(f'%{search_name}%'))
        
    return query.order_by(models.Coupon.id.desc()).offset(skip).limit(limit).all()

def update_coupon(
    db: Session, 
    coupon_id: int, 
    coupon_update_data: schemas.CouponBase # Use CouponBase as it contains all updatable fields
) -> Optional[models.Coupon]:
    """Updates an existing coupon."""
    db_coupon = get_coupon_by_id(db, coupon_id)
    if not db_coupon:
        return None

    update_data = coupon_update_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        # Prevent updating 'code' if it's part of CouponBase for some reason (it shouldn't be for updates)
        if field == 'code': 
            continue 
        setattr(db_coupon, field, value)
    
    db.commit()
    db.refresh(db_coupon)
    return db_coupon

def deactivate_coupon(db: Session, coupon_id: int) -> Optional[models.Coupon]:
    """Sets a coupon's is_active status to False."""
    db_coupon = get_coupon_by_id(db, coupon_id)
    if not db_coupon:
        return None
    
    db_coupon.is_active = False
    db.commit()
    db.refresh(db_coupon)
    return db_coupon

# --- Coupon Usage CRUD --- 
def record_coupon_usage(
    db: Session, 
    coupon_id: int, 
    user_uid: str, 
    order_id: Optional[str] = None
) -> models.CouponUsage:
    """Records an instance of a coupon being used."""
    db_usage = models.CouponUsage(
        coupon_id=coupon_id,
        user_uid=user_uid,
        order_id=order_id,
        used_at=datetime.utcnow()
    )
    db.add(db_usage)
    db.commit()
    db.refresh(db_usage)
    return db_usage

def get_coupon_total_usage_count(db: Session, coupon_id: int) -> int:
    """Counts how many times a specific coupon code has been used in total."""
    return db.query(func.count(models.CouponUsage.id)).filter(models.CouponUsage.coupon_id == coupon_id).scalar() or 0

def get_user_coupon_usage_count(db: Session, coupon_id: int, user_uid: str) -> int:
    """Counts how many times a specific user has used a specific coupon code."""
    return db.query(func.count(models.CouponUsage.id)).filter(
        models.CouponUsage.coupon_id == coupon_id,
        models.CouponUsage.user_uid == user_uid
    ).scalar() or 0

def get_coupon_usages_by_user(db: Session, user_uid: str, coupon_id: Optional[int] = None) -> List[models.CouponUsage]:
    """Lists all coupon usages for a specific user, optionally filtered by a specific coupon."""
    query = db.query(models.CouponUsage).filter(models.CouponUsage.user_uid == user_uid)
    if coupon_id:
        query = query.filter(models.CouponUsage.coupon_id == coupon_id)
    return query.order_by(models.CouponUsage.used_at.desc()).all()

# Placeholder for more complex validation logic that might be needed in CRUD or services
# For example, checking all conditions before allowing a coupon to be applied to an order. 