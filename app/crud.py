from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Optional

def create_user(db: Session, user: schemas.UserBase):
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, uid: str):
    return db.query(models.User).filter(models.User.uid == uid).first()

def create_restaurant(db: Session, restaurant: schemas.RestaurantCreate):
    db_restaurant = models.Restaurant(**restaurant.dict())
    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant

def update_restaurant(db: Session, restaurant_id: int, restaurant: schemas.RestaurantCreate):
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
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        exists = db.query(models.ClaimedReward).filter(models.ClaimedReward.coupon_code == code).first()
        if not exists:
            return code

def get_restaurant(db: Session, restaurant_id: int):
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

def get_loyalty(db: Session, uid: str, restaurant_id: int):
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
