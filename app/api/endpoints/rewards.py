from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ... import schemas, crud
from ...database import get_db
from ...auth import get_current_user, TokenData
from typing import List
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/rewards", tags=["rewards"])

import logging
from datetime import datetime, timedelta
# Keep imports for backward compatibility
from ...utils.timezone import ist_now, utc_to_ist

# Define response models for reward endpoints
class CouponValidateResponse(BaseModel):
    valid: bool
    reward: Optional[schemas.ClaimedRewardOut]

class CouponRedeemResponse(BaseModel):
    redeemed: bool
    reward: schemas.ClaimedRewardOut

@router.post("/", response_model=schemas.ClaimedRewardOut)
def create_claimed_reward(
    reward: schemas.ClaimedRewardCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Claim a reward for the current user. The server will ALWAYS generate a unique coupon code for the reward.
    The client should NOT send a coupon_code; any provided value will be ignored.
    Enforces a daily limit of 3 claims per user per restaurant.
    """
    logger = logging.getLogger("rewards")
    # Enforce daily limit
    today = datetime.utcnow().date()
    # Use UTC times for database queries
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    count = db.query(crud.models.ClaimedReward).filter(
        crud.models.ClaimedReward.uid == current_user.uid,
        crud.models.ClaimedReward.restaurant_id == reward.restaurant_id,
        crud.models.ClaimedReward.claimed_at >= today_start,
        crud.models.ClaimedReward.claimed_at <= today_end
    ).count()
    logger.info(f"User {current_user.uid} claims for restaurant {reward.restaurant_id} today: {count}")
    if count >= 3:
        logger.warning(f"User {current_user.uid} exceeded daily reward claim limit for restaurant {reward.restaurant_id}")
        raise HTTPException(status_code=429, detail="Daily reward claim limit (3) reached for this restaurant.")
    reward_data = reward.dict(exclude={"uid", "coupon_code", "claimed_at", "redeemed", "redeemed_at", "id"})
    # Coupon code is generated server-side in the CRUD layer.
    return crud.create_claimed_reward(db, reward_data, current_user.uid)



@router.post("/validate-coupon", response_model=CouponValidateResponse)
def validate_coupon(
    coupon_code: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    reward = db.query(crud.models.ClaimedReward).filter(crud.models.ClaimedReward.coupon_code == coupon_code).first()
    if not reward:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return {"valid": True, "reward": reward}

@router.post("/redeem-coupon", response_model=CouponRedeemResponse)
def redeem_coupon(
    coupon_code: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Redeem a coupon for a customer. 
    Enforces a limit of ONE coupon redemption per customer per day.
    Only admin users can redeem coupons.
    """
    logger = logging.getLogger("rewards")
    reward = db.query(crud.models.ClaimedReward).filter(crud.models.ClaimedReward.coupon_code == coupon_code).first()
    if not reward:
        raise HTTPException(status_code=404, detail="Coupon not found")
    
    # Only admin_uid of restaurant or main admin can redeem
    restaurant = db.query(crud.models.Restaurant).filter(crud.models.Restaurant.restaurant_id == reward.restaurant_id).first()
    main_admin_uid = "qkmgiVcJhYgTpJSITv7PD6kxgn12"
    if current_user.uid != main_admin_uid and current_user.uid != restaurant.admin_uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can redeem coupon.")
    
    # Check if the coupon has already been redeemed
    if reward.redeemed:
        raise HTTPException(status_code=400, detail="Coupon already redeemed")
    
    # Enforce daily redemption limit (1 per day per customer)
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    # Count redemptions for the user who owns this coupon (reward.uid)
    redemption_count = db.query(crud.models.ClaimedReward).filter(
        crud.models.ClaimedReward.uid == reward.uid,
        crud.models.ClaimedReward.redeemed == True,
        crud.models.ClaimedReward.redeemed_at >= today_start,
        crud.models.ClaimedReward.redeemed_at <= today_end
    ).count()
    
    logger.info(f"User {reward.uid} redemptions today: {redemption_count}")
    if redemption_count >= 1:
        logger.warning(f"User {reward.uid} exceeded daily redemption limit")
        raise HTTPException(
            status_code=429, 
            detail="Daily redemption limit exceeded. Only one coupon can be redeemed per day."
        )
    
    # Mark as redeemed and set timestamp
    reward.redeemed = True
    reward.redeemed_at = datetime.utcnow()
    db.commit()
    db.refresh(reward)
    
    return {"redeemed": True, "reward": reward}

@router.get("/", response_model=List[schemas.ClaimedRewardOut])
def list_claimed_rewards(
    uid: str = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    if current_user.role != "admin" and uid and uid != current_user.uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return crud.list_claimed_rewards(db, uid=uid or current_user.uid)

@router.get("/{reward_id}", response_model=schemas.ClaimedRewardOut)
def get_claimed_reward(
    reward_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    reward = crud.get_claimed_reward(db, reward_id)
    if not reward:
        raise HTTPException(status_code=404, detail="Claimed reward not found")
    if current_user.role != "admin" and reward.uid != current_user.uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return reward
