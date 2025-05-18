from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Dict, Any, ForwardRef
from datetime import datetime
import enum

class UserBase(BaseModel):
    email: EmailStr
    name: str
    number: str
    role: Optional[str] = "customer"
    restaurant_id: Optional[str] = None
    designation: Optional[str] = None
    permissions: Optional[List[str]] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    number: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    restaurant_id: Optional[str] = None
    designation: Optional[str] = None
    permissions: Optional[List[str]] = None

class UserInDB(UserBase):
    uid: str
    hashed_password: str
    created_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True

class UserOut(UserBase):
    uid: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    number: str  # Phone number to be normalized and checked for duplicates

class RestaurantBase(BaseModel):
    restaurant_id: Optional[str] = None # Made optional for creation, will be set by backend
    restaurant_name: str

    # Basic Information - NEW
    address: Optional[str] = None
    contact_phone: Optional[str] = None
    email: Optional[EmailStr] = None # Using EmailStr for validation
    tax_id: Optional[str] = None
    currency: str = "INR"
    timezone: str = "Asia/Kolkata"

    # Operational Settings - NEW
    opening_time: Optional[str] = None # e.g., "10:00"
    closing_time: Optional[str] = None # e.g., "23:00"
    is_open: bool = True
    weekly_off_days: Optional[List[str]] = [] # e.g., ["Monday"]

    # Payments & Billing Settings - NEW
    accepted_payment_modes: Optional[List[str]] = ["Cash", "Card", "UPI"] # Default sensible values
    allow_manual_discount: bool = False
    bill_number_prefix: Optional[str] = None
    bill_series_start: int = 1
    show_tax_breakdown_on_invoice: bool = False
    enable_tips_collection: bool = False

    # Existing loyalty/offer fields (ensure they are retained and correctly typed)
    offers: Optional[List[str]] = [] # Default to empty list if optional
    points_per_rupee: Optional[float] = None
    points_per_spin: Optional[float] = 1.0
    reward_thresholds: Optional[List[Dict[str, Any]]] = []
    spend_thresholds: Optional[List[Dict[str, Any]]] = []
    referral_rewards: Optional[Dict[str, Any]] = {}
    
    owner_uid: str # Should be set by the system based on authenticated user creating it
    admin_uid: Optional[str] = None
    number_of_tables: Optional[int] = None # NEWLY ADDED for initial setup
    # created_at will be in RestaurantOut, not typically in Base for creation

class RestaurantCreate(RestaurantBase):
    # restaurant_id is handled by the backend usually, so it might not be in create directly
    # owner_uid will also be set by the backend from the current authenticated user
    # All fields from RestaurantBase are inherited. 
    # Specific overrides or additional fields for creation can go here if needed.
    # For now, we assume RestaurantBase covers creation needs for the new fields.
    pass

class RestaurantOut(RestaurantBase):
    restaurant_id: str # In Out schema, ID is definitely present
    created_at: datetime
    # owner: Optional[UserOut] # If you want to return owner details
    # tables: Optional[List['RestaurantTableOut']] = [] # Add if direct inclusion is desired, requires forward ref handling

    class Config:
        from_attributes = True

class LoyaltyBase(BaseModel):
    id: Optional[int]
    uid: str
    restaurant_id: str
    total_points: int = 0
    restaurant_points: int = 0
    tier: str = "Bronze"
    punches: int = 0
    redemption_history: List[Any] = []
    visited_restaurants: List[Any] = []
    last_spin_time: Optional[datetime]
    spin_history: List[Any] = []
    referral_codes: Dict[str, Any] = {}
    referrals_made: List[Any] = []
    referred_by: Dict[str, Any] = {}

class LoyaltyCreate(LoyaltyBase):
    pass

class LoyaltyOut(LoyaltyBase):
    pass

class SubmissionBase(BaseModel):
    submission_id: Optional[int]
    uid: str
    restaurant_id: str
    amount_spent: float
    points_earned: int
    submitted_at: Optional[datetime]

class SubmissionCreate(SubmissionBase):
    pass

class SubmissionOut(SubmissionBase):
    pass

class ClaimedRewardBase(BaseModel):
    id: Optional[int]
    uid: str
    restaurant_id: str
    reward_name: str
    threshold_id: Optional[int]
    whatsapp_number: Optional[str]
    user_name: Optional[str]
    claimed_at: Optional[datetime]
    redeemed: bool = False
    redeemed_at: Optional[datetime]
    coupon_code: Optional[str] = None  # New field

class ClaimedRewardCreate(ClaimedRewardBase):
    pass

class ClaimedRewardOut(ClaimedRewardBase):
    pass

class AuditLogBase(BaseModel):
    id: Optional[int] = None
    user_id: str
    action: str
    details: Dict[str, Any]
    timestamp: Optional[datetime] = None
    order_id: Optional[str] = None # Added order_id

class AuditLogCreate(AuditLogBase):
    pass

class AuditLogOut(AuditLogBase):
    pass

# --- Online Ordering System Schemas ---

class ItemType(str, enum.Enum):
    REGULAR = "regular"
    COMBO = "combo"

# Forward declaration for MenuItemOut for ComboComponentItemOutSchema
_MenuItemOut = ForwardRef('MenuItemOut') 

class MenuItemVariationSchema(BaseModel):
    name: str
    price: float  # Absolute price for this variation
    cost_price: Optional[float] = None
    available: bool = True

    class Config:
        from_attributes = True # If you ever create model instances for variations directly

class MenuCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class MenuCategoryCreate(MenuCategoryBase):
    pass

class MenuCategoryOut(MenuCategoryBase):
    id: int
    class Config:
        from_attributes = True

class ComboComponentItemCreateSchema(BaseModel):
    menu_item_id: int # ID of the item that is a component
    quantity: int = 1

    @validator('quantity')
    def quantity_must_be_positive(cls, value):
        if value <= 0:
            raise ValueError('Quantity must be positive')
        return value

class ComboComponentItemOutSchema(BaseModel):
    id: int # ID of the ComboItemComponent link itself
    quantity: int
    component_item: Optional[_MenuItemOut] = None # Details of the menu item that is a component

    class Config:
        from_attributes = True

class MenuItemBase(BaseModel):
    restaurant_id: str
    name: str
    description: Optional[str] = None
    price: float # Base/default price for regular items, or price of the combo itself
    cost_price: Optional[float] = None 
    available: bool = True
    category_id: int
    image_url: Optional[str] = None 
    variations: Optional[List[MenuItemVariationSchema]] = None 
    item_type: ItemType = ItemType.REGULAR
    inventory_available: bool = True  # New field
    inventory_quantity: Optional[float] = None  # New field

    @validator('item_type', pre=True, always=True)
    def ensure_item_type_lowercase(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

    @validator('inventory_quantity', always=True)
    def quantity_if_tracking_disabled(cls, v, values):
        inventory_available = values.get('inventory_available')
        if inventory_available is False and v is not None:
            # If inventory tracking is off, quantity should ideally be None or 0.
            # Forcing to None if a value is provided when not tracking.
            return None 
        if inventory_available is True and v is not None and v < 0:
            raise ValueError('Inventory quantity cannot be negative when tracking is enabled.')
        return v

class MenuItemCreate(MenuItemBase):
    # If item_type is COMBO, components must be provided by the client.
    # If item_type is REGULAR, components should be None or empty.
    components: Optional[List[ComboComponentItemCreateSchema]] = None

    @validator('components', always=True)
    def check_components_for_combo(cls, v, values):
        item_type = values.get('item_type')
        if item_type == ItemType.COMBO:
            if not v:
                raise ValueError('Components must be provided for a combo item type')
            if not isinstance(v, list) or len(v) == 0:
                 raise ValueError('Components must be a non-empty list for a combo item type')
        elif v is not None and len(v) > 0: # Components provided for a non-combo item
            raise ValueError('Components should not be provided for a regular item type')
        return v

class MenuItemOut(MenuItemBase):
    id: int
    category: Optional[MenuCategoryOut] # This was already here
    # If item_type is COMBO, components should be populated from the DB relation
    components: Optional[List[ComboComponentItemOutSchema]] = None 
    
    class Config:
        from_attributes = True

class OrderItemBase(BaseModel):
    item_id: int
    quantity: int
    # price removed for frontend, backend will resolve price

class OrderItemCreate(BaseModel):
    item_id: int
    quantity: int

class OrderItemOut(OrderItemBase):
    id: int
    item: Optional[MenuItemOut]
    price: float

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    user_uid: str
    customer_uid: Optional[str] = None
    user_role: Optional[str] = None
    table_number: Optional[str] = None
    restaurant_id: str
    restaurant_name: Optional[str] = None
    status: Optional[str] = "Pending"
    total_cost: float
    payment_status: Optional[str] = "Pending"
    promo_code_id: Optional[int] = None
    order_number: Optional[int] = None

class OrderCreate(BaseModel):
    restaurant_id: str
    items: list[OrderItemCreate]
    table_number: Optional[str] = None
    promo_code: Optional[str] = None

class OrderStatusHistoryOut(BaseModel):
    status: str
    changed_at: datetime
    changed_by: str

    class Config:
        from_attributes = True

class OrderOut(BaseModel):
    id: str
    order_number: int
    user_uid: str
    customer_uid: Optional[str] = None
    user_role: Optional[str] = None
    table_number: Optional[str] = None
    restaurant_id: str
    restaurant_name: Optional[str] = None
    created_at: datetime
    status: str
    total_cost: float
    payment_status: str
    items: list[OrderItemOut]
    payment: Optional['PaymentOut']
    status_history: list[OrderStatusHistoryOut] = []
    customer_detail: Optional[UserOut] = None

    class Config:
        from_attributes = True

# Ensure PaymentOut is defined before OrderOut uses it or use ForwardRef if defined later
_PaymentOut = ForwardRef('PaymentOut')

class OrderMarkPaidRequest(BaseModel):
    payment_method: str  # e.g., "Cash", "Card", "UPI"
    transaction_id: Optional[str] = None # For Card/UPI payments
    customer_uid: Optional[str] = None

class PaymentBase(BaseModel):
    amount: float
    status: Optional[str] = "Pending"
    method: Optional[str] = None
    paid_at: Optional[datetime] = None

class PaymentCreate(PaymentBase):
    order_id: str  # Changed to string for "restaurant_id_number" format

class PaymentOut(PaymentBase):
    id: int
    order_id: str
    transaction_id: Optional[str] = None # ADDED

    class Config:
        from_attributes = True

class PromoCodeBase(BaseModel):
    code: str
    description: Optional[str] = None
    discount_percent: Optional[float] = None
    discount_amount: Optional[float] = None
    active: bool = True
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    usage_limit: Optional[int] = None
    used_count: Optional[int] = 0

class PromoCodeCreate(PromoCodeBase):
    pass

class PromoCodeOut(PromoCodeBase):
    id: int
    class Config:
        from_attributes = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    uid: Optional[str] = None
    role: Optional[str] = None

# New Schemas for Employee specific operations
class EmployeeCreate(UserCreate):
    pass # Inherits all from UserCreate

class EmployeeOut(UserOut):
    pass # Inherits all from UserOut

# --- Coupon System Schemas ---

class CouponType(str, enum.Enum):
    FIXED_AMOUNT = "fixed_amount"
    PERCENTAGE = "percentage"
    BOGO = "bogo"  # Buy One Get One Free
    FREE_ITEM = "free_item"
    CATEGORY_OFFER = "category_offer"

class CategoryOfferType(str, enum.Enum):
    FIXED_AMOUNT = "fixed_amount"
    PERCENTAGE = "percentage"
    BOGO = "bogo"

class CouponBase(BaseModel):
    name: str
    description: Optional[str] = None
    coupon_type: CouponType
    discount_value: Optional[float] = None
    discount_percentage: Optional[float] = None
    menu_item_id: Optional[int] = None # Assuming MenuItem.id is int
    menu_category_id: Optional[int] = None # Assuming MenuCategory.id is int
    category_offer_type: Optional[CategoryOfferType] = None
    start_date: datetime
    end_date: datetime
    usage_limit: int = 1
    per_user_limit: int = 1
    assigned_user_ids: Optional[List[str]] = None # List of user UIDs
    is_active: bool = True
    restaurant_id: Optional[str] = None
    parent_coupon_id: Optional[int] = None

    class Config:
        from_attributes = True

# Schema for creating a single coupon instance internally (e.g. by the generator)
class CouponCreateInternal(CouponBase):
    code: str # Code is mandatory for an instance

# Schema for the main POST /api/coupons/create request payload
class CouponCreateRequest(BaseModel):
    name: str
    coupon_type: CouponType
    discount_value: Optional[float] = None
    discount_percentage: Optional[float] = None
    menu_item_id: Optional[int] = None
    menu_category_id: Optional[int] = None
    category_offer_type: Optional[CategoryOfferType] = None
    start_date: datetime # Consider date if time is not needed, but datetime is more flexible
    end_date: datetime
    usage_limit: int
    per_user_limit: int
    assigned_user_ids: Optional[List[str]] = None
    total_coupons_to_generate: int = 1
    description: Optional[str] = None
    restaurant_id: Optional[str] = None # For admin to assign to a specific restaurant

    # Basic Pydantic validators can be added here later for conditional logic
    # e.g., if coupon_type == FIXED_AMOUNT, discount_value must be set.

class CouponCodeResponseItem(BaseModel):
    id: int # The DB ID of the coupon instance
    code: str

class CouponOut(CouponBase):
    id: int
    code: str
    created_at: datetime
    # menu_item: Optional[MenuItemOut] = None # Eager load if needed often
    # menu_category: Optional[MenuCategoryOut] = None # Eager load if needed often
    # restaurant: Optional[RestaurantOut] = None # Eager load if needed often

    class Config:
        from_attributes = True

class CouponApplyRequest(BaseModel):
    coupon_code: str
    user_uid: Optional[str] = None # MADE OPTIONAL - To check per-user limits and assigned users. If None, current authenticated user is assumed.
    order_id: Optional[str] = None # MADE OPTIONAL - For context, if discount depends on order items or for logging
    restaurant_id: str # To validate against coupon's restaurant_id if set. Still mandatory for context.

class CouponValidationDetail(BaseModel):
    is_valid: bool
    message: str
    coupon_id: Optional[int] = None
    code: Optional[str] = None
    name: Optional[str] = None
    coupon_type: Optional[CouponType] = None
    discount_value: Optional[float] = None
    discount_percentage: Optional[float] = None
    menu_item_id: Optional[int] = None
    menu_category_id: Optional[int] = None
    category_offer_type: Optional[CategoryOfferType] = None
    # Add any other relevant coupon fields that the frontend might need to display the discount

class CouponUsageBase(BaseModel):
    coupon_id: int
    user_uid: str
    order_id: Optional[str] = None

class CouponUsageCreate(CouponUsageBase):
    pass

class CouponUsageOut(CouponUsageBase):
    id: int
    used_at: datetime
    class Config:
        from_attributes = True

OrderOut.update_forward_refs() # Ensure forward refs are resolved after all definitions

# Standard API Response Schema
class StandardResponse(BaseModel):
    status: str = "success"
    message: Optional[str] = None
    data: Optional[Any] = None

class InventoryChangeType(str, enum.Enum):
    INITIAL_STOCK = "initial_stock"
    MANUAL_UPDATE = "manual_update"
    SALE_DEDUCTION = "sale_deduction"
    SPOILAGE = "spoilage"
    RESTOCK = "restock"
    AUDIT_CORRECTION = "audit_correction"
    TRANSFER_IN = "transfer_in" # For multi-location later
    TRANSFER_OUT = "transfer_out" # For multi-location later

# --- InventoryItem Schemas ---
class InventoryItemBase(BaseModel):
    menu_item_id: int
    quantity: float
    unit: str # E.g., "pieces", "kg", "liters"
    low_stock_threshold: Optional[float] = None
    restaurant_id: str # Must be provided for context

class InventoryItemCreate(InventoryItemBase):
    # For initial registration. Quantity here is the opening stock.
    pass

class InventoryItemUpdate(BaseModel):
    # For adjusting stock. User provides the new absolute quantity.
    new_quantity: float 
    change_type: InventoryChangeType = InventoryChangeType.MANUAL_UPDATE # Or AUDIT_CORRECTION could be a common default
    reason: Optional[str] = None
    notes: Optional[str] = None
    # unit and low_stock_threshold can also be made updatable if needed
    unit: Optional[str] = None 
    low_stock_threshold: Optional[float] = None

class InventoryItemOut(InventoryItemBase):
    id: int
    last_updated_at: datetime
    created_at: datetime
    menu_item: Optional[MenuItemOut] = None # This should now pick up the full MenuItemOut

    class Config:
        from_attributes = True

# --- InventoryUpdateLog Schemas ---
class InventoryUpdateLogBase(BaseModel):
    inventory_item_id: int
    changed_by_user_id: Optional[str] = None
    change_type: InventoryChangeType
    quantity_changed: float
    previous_quantity: float
    new_quantity: float
    reason: Optional[str] = None
    notes: Optional[str] = None

class InventoryUpdateLogCreate(InventoryUpdateLogBase):
    # This schema will be used internally by CRUD operations when stock changes.
    pass

class InventoryUpdateLogOut(InventoryUpdateLogBase):
    id: int
    timestamp: datetime
    user: Optional[UserOut] = None # Include user details if available
    # inventory_item: Optional[InventoryItemOut] = None # Avoid circular deep nesting unless needed

    class Config:
        from_attributes = True

# Update forward refs if InventoryItemOut or InventoryUpdateLogOut are used in other schemas before their definition
# Example: OrderOut.update_forward_refs() if it were to include inventory details directly.
# For now, these are new and likely at the end, so direct forward ref updates might not be needed immediately,
# but good practice if other schemas start referencing them.

# --- Restaurant Table Schemas ---
class TableStatus(str, enum.Enum):
    EMPTY = "empty"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    OUT_OF_SERVICE = "out_of_service"

class RestaurantTableBase(BaseModel):
    table_number: str
    status: TableStatus = TableStatus.EMPTY
    capacity: Optional[int] = None

class RestaurantTableCreate(RestaurantTableBase):
    # restaurant_id will be path parameter or from context
    pass

class RestaurantTableUpdate(BaseModel):
    table_number: Optional[str] = None
    status: Optional[TableStatus] = None
    capacity: Optional[int] = None

class RestaurantTableOut(RestaurantTableBase):
    id: int
    restaurant_id: str
    composed_table_id: Optional[str] = None # New field for slug-id

    class Config:
        from_attributes = True

# Schemas for User Dashboard - Restaurant Specific Progress
class RewardMetDetail(BaseModel):
    threshold: Any
    reward: str
    coupon_code: Optional[str] = None
    claimed: bool

class UpcomingRewardDetail(BaseModel):
    threshold: Any
    reward: str

class SpinProgressDetails(BaseModel):
    current_spin_points: int
    number_of_spins: int
    rewards_met: List[RewardMetDetail]
    upcoming_rewards: List[UpcomingRewardDetail]

class SpendProgressDetails(BaseModel):
    current_spend: float
    rewards_met: List[RewardMetDetail]
    upcoming_rewards: List[UpcomingRewardDetail]

class ClaimedRewardDetail(BaseModel): # For the list within each restaurant's progress
    reward_name: str
    threshold: Optional[Any] = None
    coupon_code: Optional[str] = None
    redeemed: Optional[bool] = False
    claimed_at: Optional[datetime] = None
    class Config: # Added for potential ORM mode if ever needed, though constructed from dicts
        from_attributes = True

class RestaurantProgress(BaseModel):
    restaurant_id: str
    restaurant_name: str
    spin_progress: SpinProgressDetails
    spend_progress: SpendProgressDetails
    claimed_rewards_for_restaurant: List[ClaimedRewardDetail]
    class Config: # Added for potential ORM mode if ever needed
        from_attributes = True

# Main User Dashboard Response Schema
class UserDashboardResponse(BaseModel):
    profile: UserOut
    orders: List[OrderOut] # crud.get_orders_by_user returns List[Dict], OrderOut should match
    loyalty_info: List[LoyaltyOut]
    claimed_rewards: List[ClaimedRewardOut]
    restaurant_specific_progress: List[RestaurantProgress]
    audit_logs: List[AuditLogOut]

    class Config:
        from_attributes = True

