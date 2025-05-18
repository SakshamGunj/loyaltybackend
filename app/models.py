from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
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
    email = Column(String, unique=True, index=True)
    name = Column(String)
    number = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="customer")  # e.g., customer, employee, restaurant_admin_user, system_admin
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Employee-specific fields (nullable for non-employees)
    restaurant_id = Column(String, ForeignKey("restaurants.restaurant_id"), nullable=True, index=True)
    designation = Column(String, nullable=True)  # E.g., "Manager", "Staff", "Chef"
    permissions = Column(JSON, nullable=True) # E.g., ["view_orders", "edit_menu"]

    # Relationships
    loyalties = relationship("Loyalty", back_populates="user")
    submissions = relationship("Submission", back_populates="user")
    claimed_rewards = relationship("ClaimedReward", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    coupon_usages = relationship("CouponUsage", back_populates="user")
    # Relationship for restaurants owned by this user
    owned_restaurants = relationship("Restaurant", foreign_keys="[Restaurant.owner_uid]", back_populates="owner")
    # Relationship for the restaurant this user might be an employee of
    # This assumes a user can only be an employee of one restaurant directly via user.restaurant_id
    employee_of_restaurant = relationship("Restaurant", foreign_keys=[restaurant_id], back_populates="staff_members")
    # Relationship for orders placed by this user (as a customer)
    customer_orders = relationship("Order", foreign_keys="[Order.customer_uid]", back_populates="customer_detail")

class Restaurant(Base):
    __tablename__ = "restaurants"
    restaurant_id = Column(String, primary_key=True, index=True)
    restaurant_name = Column(String, index=True)

    # NEW: Basic Information
    address = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True) # Consider validation/normalization if needed
    email = Column(String, nullable=True) # Contact email, not necessarily unique like User.email
    tax_id = Column(String, nullable=True) # Optional GSTIN or other tax ID
    currency = Column(String, default="INR", nullable=False)
    timezone = Column(String, default="Asia/Kolkata", nullable=False)

    # EXISTING Loyalty/Offer fields
    offers = Column(JSON)
    points_per_rupee = Column(Float)
    points_per_spin = Column(Float, default=1.0)
    reward_thresholds = Column(JSON, default=list)
    spend_thresholds = Column(JSON, default=list)
    referral_rewards = Column(JSON)
    
    # NEW: Operational Settings
    opening_time = Column(String, nullable=True) # Store as "HH:MM" string
    closing_time = Column(String, nullable=True) # Store as "HH:MM" string
    is_open = Column(Boolean, default=True, nullable=False) # Manually toggle open/closed
    weekly_off_days = Column(JSON, default=list, nullable=True) # e.g., ["Monday", "Tuesday"]

    # NEW: Payments & Billing Settings
    accepted_payment_modes = Column(JSON, default=list, nullable=True) # e.g., ["Cash", "Card", "UPI"]
    allow_manual_discount = Column(Boolean, default=False, nullable=False)
    bill_number_prefix = Column(String, nullable=True)
    bill_series_start = Column(Integer, default=1, nullable=False)
    show_tax_breakdown_on_invoice = Column(Boolean, default=False, nullable=False)
    enable_tips_collection = Column(Boolean, default=False, nullable=False)

    # EXISTING Owner/Admin and Timestamps
    owner_uid = Column(String, ForeignKey("users.uid"))
    admin_uid = Column(String, default=None)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    owner = relationship("User", foreign_keys=[owner_uid], back_populates="owned_restaurants")
    # Relationship for staff members of this restaurant
    staff_members = relationship("User", foreign_keys="[User.restaurant_id]", back_populates="employee_of_restaurant")
    
    # Relationship to RestaurantTable
    tables = relationship("RestaurantTable", back_populates="restaurant", cascade="all, delete-orphan")

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
    user = relationship("User", back_populates="loyalties")

class Submission(Base):
    __tablename__ = "submissions"
    submission_id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, ForeignKey("users.uid"), index=True)
    restaurant_id = Column(String, ForeignKey("restaurants.restaurant_id"), index=True)
    amount_spent = Column(Float)
    points_earned = Column(Integer)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("User", back_populates="submissions")

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
    user = relationship("User", back_populates="claimed_rewards")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"))
    action = Column(String)
    details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    order_id = Column(String, ForeignKey("orders.id"), nullable=True)
    user = relationship("User", back_populates="audit_logs")

# --- Online Ordering System Models ---

class MenuCategory(Base):
    __tablename__ = "menu_categories"
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(String, ForeignKey("restaurants.restaurant_id"), nullable=False, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    items = relationship("MenuItem", back_populates="category")

class MenuItem(Base):
    __tablename__ = "menu_items"
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(String, ForeignKey("restaurants.restaurant_id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False) # Base/default price
    cost_price = Column(Float, nullable=True) # ADDED: Restaurant's cost for this item
    available = Column(Boolean, default=True)
    category_id = Column(Integer, ForeignKey("menu_categories.id"), nullable=True)
    image_url = Column(String, nullable=True)
    variations = Column(JSON, nullable=True) # ADDED: e.g., [{"name": "Small", "price": 5.00, "cost_price": 2.00, "available": true}]
    item_type = Column(String(50), default="REGULAR", nullable=False, server_default="REGULAR", index=True) # NEW: REGULAR, COMBO
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    category = relationship("MenuCategory", back_populates="items")
    orders = relationship("OrderItem", back_populates="item")

    # Relationship for combo items: if this MenuItem is a combo, these are its components.
    components = relationship("ComboItemComponent", 
                              foreign_keys="[ComboItemComponent.combo_menu_item_id]", 
                              back_populates="combo_item", 
                              cascade="all, delete-orphan",
                              lazy="selectin") # Eager load components when a combo item is fetched

class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True, index=True)  # Changed to String for format "restaurant_id{number}"
    user_uid = Column(String, ForeignKey("users.uid"), nullable=False) # Staff/system user creating/handling order
    customer_uid = Column(String, ForeignKey("users.uid"), nullable=True, index=True) # NEW: The actual customer
    user_role = Column(String, nullable=True)
    table_number = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    status = Column(String, default="Order Placed")  # Order Placed -> Order Confirmed -> Payment Done
    total_cost = Column(Float, nullable=False)
    payment_status = Column(String, default="Pending")
    restaurant_id = Column(String, nullable=True)
    restaurant_name = Column(String, nullable=True)
    order_number = Column(Integer, nullable=True)  # Store the numeric part separately
    
    items = relationship("OrderItem", back_populates="order")
    user = relationship("User", foreign_keys=[user_uid]) # Staff/system user creating/handling order
    customer_detail = relationship("User", foreign_keys=[customer_uid], back_populates="customer_orders") # NEW: The actual customer details
    payment = relationship("Payment", uselist=False, back_populates="order")
    status_history = relationship("OrderStatusHistory", back_populates="order", order_by="desc(OrderStatusHistory.changed_at)")

class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    status = Column(String, nullable=False)
    changed_at = Column(DateTime, default=datetime.datetime.utcnow)
    changed_by = Column(String, nullable=False)  # UID of the user who changed the status
    
    order = relationship("Order", back_populates="status_history")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, ForeignKey("orders.id"))
    item_id = Column(Integer, ForeignKey("menu_items.id"))
    quantity = Column(Integer, default=1)
    price = Column(Float, nullable=False)  # Store price at time of order
    options = Column(JSON, nullable=True)  # For customizations/options
    
    order = relationship("Order", back_populates="items")
    item = relationship("MenuItem")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    amount = Column(Float, nullable=False)
    method = Column(String, nullable=False)  # "Cash", "Card", "UPI", etc.
    status = Column(String, default="Pending")
    processed_at = Column(DateTime, default=datetime.datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    transaction_id = Column(String, nullable=True)
    
    order = relationship("Order", back_populates="payment")

class PromoCode(Base):
    __tablename__ = "promo_codes"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    discount_percent = Column(Float, nullable=True)
    discount_amount = Column(Float, nullable=True)
    valid_from = Column(DateTime, nullable=True)
    valid_to = Column(DateTime, nullable=True)
    usage_limit = Column(Integer, nullable=True)
    used_count = Column(Integer, default=0)
    restaurant_id = Column(String, ForeignKey("restaurants.restaurant_id"), nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# --- New Coupon System Models ---

class Coupon(Base):
    __tablename__ = "coupons"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False) # Increased length for potentially complex codes
    name = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    coupon_type = Column(String(50), nullable=False) # E.g., fixed_amount, percentage, bogo, free_item, category_offer
    
    discount_value = Column(Float, nullable=True)
    discount_percentage = Column(Float, nullable=True)
    
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=True)
    menu_category_id = Column(Integer, ForeignKey("menu_categories.id"), nullable=True)
    category_offer_type = Column(String(50), nullable=True) # If coupon_type is category_offer, this specifies its nature
    
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    usage_limit = Column(Integer, nullable=False, default=1) # Total uses for this specific coupon code instance
    per_user_limit = Column(Integer, nullable=False, default=1) # How many times a single user can use this specific code
    
    assigned_user_ids = Column(JSON, nullable=True) # Array of user UIDs
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    restaurant_id = Column(String, ForeignKey("restaurants.restaurant_id"), nullable=True, index=True)
    # For linking generated unique codes to a master coupon definition/template
    parent_coupon_id = Column(Integer, ForeignKey("coupons.id"), nullable=True, index=True)

    restaurant = relationship("Restaurant")
    parent_coupon = relationship("Coupon", remote_side=[id], back_populates="child_coupons")
    child_coupons = relationship("Coupon", back_populates="parent_coupon")
    
    menu_item = relationship("MenuItem")
    menu_category = relationship("MenuCategory")
    usages = relationship("CouponUsage", back_populates="coupon")

class CouponUsage(Base):
    __tablename__ = "coupon_usages"
    id = Column(Integer, primary_key=True, index=True)
    coupon_id = Column(Integer, ForeignKey("coupons.id"), nullable=False, index=True)
    user_uid = Column(String, ForeignKey("users.uid"), nullable=False, index=True)
    order_id = Column(String, ForeignKey("orders.id"), nullable=True, index=True) # If coupon applied to a specific order
    used_at = Column(DateTime, default=datetime.datetime.utcnow)

    coupon = relationship("Coupon", back_populates="usages")
    user = relationship("User") # Add back_populates="coupon_usages" to User model later if needed
    order = relationship("Order") # Add back_populates="coupon_usage" to Order model later if needed (likely one usage per order)

# Need to adjust Order model to remove promo_code_id and potentially link to CouponUsage or Coupon if a coupon is applied directly
# For now, we focus on creating Coupon and CouponUsage. The linkage to Order can be a subsequent step.

class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(String, ForeignKey("restaurants.restaurant_id"), nullable=False, index=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False, index=True)
    
    quantity = Column(Float, nullable=False, default=0.0)
    unit = Column(String(50), nullable=False)  # E.g., "pieces", "kg", "liters", "units"
    low_stock_threshold = Column(Float, nullable=True)
    
    last_updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    menu_item = relationship("MenuItem")
    restaurant = relationship("Restaurant")
    update_logs = relationship("InventoryUpdateLog", back_populates="inventory_item", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint('restaurant_id', 'menu_item_id', name='_restaurant_menu_item_uc'),)


class InventoryUpdateLog(Base):
    __tablename__ = "inventory_update_logs"

    id = Column(Integer, primary_key=True, index=True)
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False, index=True)
    
    changed_by_user_id = Column(String, ForeignKey("users.uid"), nullable=True) # Nullable if system change (e.g., sale)
    
    change_type = Column(String(50), nullable=False) 
    # Examples: "initial_stock", "manual_update", "sale_deduction", "spoilage", "restock", "audit_correction"
    
    quantity_changed = Column(Float, nullable=False) # Positive for addition, negative for deduction
    previous_quantity = Column(Float, nullable=False)
    new_quantity = Column(Float, nullable=False)
    
    reason = Column(String, nullable=True) # Optional reason for manual changes
    notes = Column(String, nullable=True) # Additional notes
    
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    inventory_item = relationship("InventoryItem", back_populates="update_logs")
    user = relationship("User") # User who made the change, if applicable

# NEW RestaurantTable model
class RestaurantTable(Base):
    __tablename__ = "restaurant_tables"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    restaurant_id = Column(String, ForeignKey("restaurants.restaurant_id"), nullable=False, index=True)
    table_number = Column(String, nullable=False) # E.g., "1", "A2", "Patio 5"
    status = Column(String(50), default="EMPTY", nullable=False) # E.g., EMPTY, OCCUPIED, RESERVED, OUT_OF_SERVICE
    capacity = Column(Integer, nullable=True) # Optional: seating capacity
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    restaurant = relationship("Restaurant", back_populates="tables")

    __table_args__ = (UniqueConstraint('restaurant_id', 'table_number', name='_restaurant_table_number_uc'),)

# --- New Combo Item Component Model ---
class ComboItemComponent(Base):
    __tablename__ = "combo_item_components"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # This is the ID of the MenuItem that IS the combo
    combo_menu_item_id = Column(Integer, ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False, index=True)
    # This is the ID of a MenuItem that is PART OF the combo
    component_menu_item_id = Column(Integer, ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationship back to the MenuItem that is the combo
    combo_item = relationship("MenuItem", foreign_keys=[combo_menu_item_id], back_populates="components")
    # Relationship to the MenuItem that is a component
    # No back_populates here to MenuItem to avoid making MenuItem aware of all combos it's part of directly
    component_item = relationship("MenuItem", foreign_keys=[component_menu_item_id], lazy="joined") 

    __table_args__ = (UniqueConstraint('combo_menu_item_id', 'component_menu_item_id', name='_combo_component_uc'),)

# Make sure all models are defined before any potential Base.metadata.create_all calls
# (though we rely on Alembic, so this is mostly for linters/type checkers)
