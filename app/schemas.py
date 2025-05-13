from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    name: str
    number: str
    role: str = "customer"

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    number: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    uid: str
    hashed_password: str
    created_at: datetime
    is_active: bool = True

    class Config:
        orm_mode = True

class UserOut(UserBase):
    uid: str
    created_at: datetime
    is_active: bool

    class Config:
        orm_mode = True

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    number: str  # Phone number to be normalized and checked for duplicates

class RestaurantBase(BaseModel):
    restaurant_id: Optional[str]
    restaurant_name: str
    offers: List[str]
    points_per_rupee: float
    points_per_spin: float = 1.0
    reward_thresholds: List[Dict[str, Any]] = []  # Now a list of thresholds
    spend_thresholds: List[Dict[str, Any]] = []  # Now a list of thresholds
    referral_rewards: Dict[str, Any]
    owner_uid: str
    admin_uid: Optional[str] = None
    created_at: Optional[datetime]

class RestaurantCreate(BaseModel):
    restaurant_id: Optional[str]
    restaurant_name: str
    offers: List[str]
    points_per_rupee: float
    points_per_spin: float = 1.0
    reward_thresholds: List[Dict[str, Any]] = []
    spend_thresholds: List[Dict[str, Any]] = []
    referral_rewards: Dict[str, Any]
    owner_uid: str
    admin_uid: Optional[str] = None

class RestaurantOut(RestaurantBase):
    created_at: datetime
    
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
    id: Optional[int]
    user_id: str
    action: str
    details: Dict[str, Any]
    timestamp: Optional[datetime]

class AuditLogCreate(AuditLogBase):
    pass

class AuditLogOut(AuditLogBase):
    pass

# --- Online Ordering System Schemas ---

from typing import ForwardRef

class MenuCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class MenuCategoryCreate(MenuCategoryBase):
    pass

class MenuCategoryOut(MenuCategoryBase):
    id: int
    class Config:
        from_attributes = True

class MenuItemBase(BaseModel):
    restaurant_id: str
    name: str
    description: Optional[str] = None
    price: float
    available: bool = True
    category_id: int

class MenuItemCreate(MenuItemBase):
    pass

class MenuItemOut(MenuItemBase):
    id: int
    category: Optional[MenuCategoryOut]
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
    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    user_id: str
    status: Optional[str] = "Pending"
    total_cost: float
    payment_status: Optional[str] = "Pending"
    promo_code_id: Optional[int] = None

class OrderCreate(BaseModel):
    restaurant_id: str  # Required field
    items: list[OrderItemCreate]
    promo_code: Optional[str] = None

class OrderStatusHistoryOut(BaseModel):
    status: str
    changed_at: datetime
    changed_by: str

    class Config:
        from_attributes = True

class OrderOut(BaseModel):
    id: str  # Changed to string for "restaurant_id_number" format
    order_number: int  # Added to store the numeric part separately
    created_at: datetime
    items: list[OrderItemOut]
    payment: Optional['PaymentOut']
    promo_code_id: Optional[int] = None
    restaurant_id: str  # Changed to required
    restaurant_name: Optional[str] = None
    status: str
    payment_status: str
    status_history: list[OrderStatusHistoryOut] = []

    class Config:
        from_attributes = True

class PaymentBase(BaseModel):
    amount: float
    status: Optional[str] = "Pending"
    method: Optional[str] = None
    paid_at: Optional[datetime] = None

class PaymentCreate(PaymentBase):
    order_id: str  # Changed to string for "restaurant_id_number" format

class PaymentOut(PaymentBase):
    id: int
    order_id: str  # Changed to string for "restaurant_id_number" format
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

