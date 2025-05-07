from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base
import datetime

# Table to store OTP-verified phone numbers in normalized 10-digit format
class VerifiedPhoneNumber(Base):
    __tablename__ = "verified_phone_numbers"
    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(10), unique=True, index=True, nullable=False)  # Always store as 10-digit string
    verified_at = Column(DateTime, default=datetime.datetime.utcnow)
    __table_args__ = (UniqueConstraint('number', name='uq_verified_number'),)

class User(Base):
    __tablename__ = "users"
    uid = Column(String, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    role = Column(String, default="user")  # 'user' or 'admin'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Restaurant(Base):
    __tablename__ = "restaurants"
    restaurant_id = Column(String, primary_key=True, index=True)
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
    restaurant_id = Column(String, ForeignKey("restaurants.restaurant_id"), index=True)
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
    restaurant_id = Column(String, ForeignKey("restaurants.restaurant_id"), index=True)
    amount_spent = Column(Float)
    points_earned = Column(Integer)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)

class ClaimedReward(Base):
    __tablename__ = "claimed_rewards"
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, ForeignKey("users.uid"), index=True)
    restaurant_id = Column(String, ForeignKey("restaurants.restaurant_id"), index=True)
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

# --- Online Ordering System Models ---

class MenuCategory(Base):
    __tablename__ = "menu_categories"
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(String, ForeignKey("restaurants.restaurant_id"), nullable=False, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    items = relationship("MenuItem", back_populates="category")

class MenuItem(Base):
    __tablename__ = "menu_items"
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(String, ForeignKey("restaurants.restaurant_id"), index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    available = Column(Boolean, default=True)
    category_id = Column(Integer, ForeignKey("menu_categories.id"))
    category = relationship("MenuCategory", back_populates="items")
    orders = relationship("OrderItem", back_populates="item")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="Order Placed")  # Order Placed -> Order Confirmed -> Payment Done
    total_cost = Column(Float, nullable=False)
    payment_status = Column(String, default="Pending")
    promo_code_id = Column(Integer, ForeignKey("promo_codes.id"), nullable=True)
    items = relationship("OrderItem", back_populates="order")
    user = relationship("User")
    payment = relationship("Payment", uselist=False, back_populates="order")
    status_history = relationship("OrderStatusHistory", back_populates="order", order_by="desc(OrderStatusHistory.changed_at)")

class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    status = Column(String, nullable=False)
    changed_at = Column(DateTime, default=datetime.datetime.utcnow)
    changed_by = Column(String, nullable=False)  # UID of the user who changed the status
    
    order = relationship("Order", back_populates="status_history")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    item_id = Column(Integer, ForeignKey("menu_items.id"))
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)  # Price at the time of order
    order = relationship("Order", back_populates="items")
    item = relationship("MenuItem", back_populates="orders")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True)
    amount = Column(Float, nullable=False)
    status = Column(String, default="Pending")  # Pending, Paid, Failed
    method = Column(String, nullable=True)  # e.g., 'cash', 'card', 'upi'
    paid_at = Column(DateTime, nullable=True)
    order = relationship("Order", back_populates="payment")

class PromoCode(Base):
    __tablename__ = "promo_codes"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    discount_percent = Column(Float, nullable=True)
    discount_amount = Column(Float, nullable=True)
    active = Column(Boolean, default=True)
    valid_from = Column(DateTime, nullable=True)
    valid_to = Column(DateTime, nullable=True)
    usage_limit = Column(Integer, nullable=True)
    used_count = Column(Integer, default=0)
    orders = relationship("Order", backref="promo_code")
