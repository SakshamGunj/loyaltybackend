from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    uid = Column(String, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Restaurant(Base):
    __tablename__ = "restaurants"
    restaurant_id = Column(Integer, primary_key=True, index=True)
    restaurant_name = Column(String, index=True)
    offers = Column(JSON)
    points_per_rupee = Column(Float)
    points_per_spin = Column(Float, default=1.0)
    reward_thresholds = Column(JSON, default=list)  # Now a list of dicts
    spend_thresholds = Column(JSON, default=list)   # Now a list of dicts
    referral_rewards = Column(JSON)
    owner_uid = Column(String, ForeignKey("users.uid"))
    admin_uid = Column(String, default=None)  # New field
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    owner = relationship("User")


class Loyalty(Base):
    __tablename__ = "loyalty"
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, ForeignKey("users.uid"), index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.restaurant_id"), index=True)
    total_points = Column(Integer, default=0)
    restaurant_points = Column(Integer, default=0)
    tier = Column(String, default="Bronze")
    punches = Column(Integer, default=0)
    redemption_history = Column(JSON, default=list)
    visited_restaurants = Column(JSON, default=list)
    last_spin_time = Column(DateTime, nullable=True)
    spin_history = Column(JSON, default=list)
    referral_codes = Column(JSON, default=dict)
    referrals_made = Column(JSON, default=list)
    referred_by = Column(JSON, default=dict)

class Submission(Base):
    __tablename__ = "submissions"
    submission_id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, ForeignKey("users.uid"), index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.restaurant_id"), index=True)
    amount_spent = Column(Float)
    points_earned = Column(Integer)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)

class ClaimedReward(Base):
    __tablename__ = "claimed_rewards"
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, ForeignKey("users.uid"), index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.restaurant_id"), index=True)
    reward_name = Column(String)
    threshold_id = Column(Integer, nullable=True)
    whatsapp_number = Column(String, nullable=True)
    user_name = Column(String, nullable=True)
    claimed_at = Column(DateTime, default=datetime.datetime.utcnow)
    redeemed = Column(Boolean, default=False)
    redeemed_at = Column(DateTime, nullable=True)
    coupon_code = Column(String, unique=True, nullable=True)  # New field

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"))
    action = Column(String)
    details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
