from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    uid: str
    name: Optional[str]
    email: Optional[EmailStr]
    created_at: Optional[datetime]

class RestaurantBase(BaseModel):
    restaurant_id: Optional[int]
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

class RestaurantCreate(RestaurantBase):
    points_per_spin: float = 1.0
    reward_thresholds: List[Dict[str, Any]] = []
    spend_thresholds: List[Dict[str, Any]] = []
    admin_uid: Optional[str] = None

class RestaurantOut(RestaurantBase):
    points_per_spin: float = 1.0
    reward_thresholds: List[Dict[str, Any]] = []
    spend_thresholds: List[Dict[str, Any]] = []
    admin_uid: Optional[str] = None


class LoyaltyBase(BaseModel):
    id: Optional[int]
    uid: str
    restaurant_id: int
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
    restaurant_id: int
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
    restaurant_id: int
    reward_name: str
    threshold_id: Optional[int]
    whatsapp_number: Optional[str]
    user_name: Optional[str]
    claimed_at: Optional[datetime]
    redeemed: bool = False
    redeemed_at: Optional[datetime]
    coupon_code: Optional[str] = None  # New field
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
