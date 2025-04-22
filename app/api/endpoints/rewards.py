from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ... import schemas, crud
from ...database import get_db
from ...auth import get_current_user, TokenData
from typing import List

router = APIRouter(prefix="/api/rewards", tags=["rewards"])

import logging
from datetime import datetime, timedelta

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
    count = db.query(crud.models.ClaimedReward).filter(
        crud.models.ClaimedReward.uid == current_user.uid,
        crud.models.ClaimedReward.restaurant_id == reward.restaurant_id,
        crud.models.ClaimedReward.claimed_at >= datetime.combine(today, datetime.min.time()),
        crud.models.ClaimedReward.claimed_at <= datetime.combine(today, datetime.max.time())
    ).count()
    logger.info(f"User {current_user.uid} claims for restaurant {reward.restaurant_id} today: {count}")
    if count >= 3:
        logger.warning(f"User {current_user.uid} exceeded daily reward claim limit for restaurant {reward.restaurant_id}")
        raise HTTPException(status_code=429, detail="Daily reward claim limit (3) reached for this restaurant.")
    reward_data = reward.dict(exclude={"uid", "coupon_code", "claimed_at", "redeemed", "redeemed_at", "id"})
    # Coupon code is generated server-side in the CRUD layer.
    return crud.create_claimed_reward(db, reward_data, current_user.uid)



@router.post("/validate-coupon")
def validate_coupon(
    coupon_code: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    reward = db.query(crud.models.ClaimedReward).filter(crud.models.ClaimedReward.coupon_code == coupon_code).first()
    if not reward:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return {"valid": True, "reward": reward}

@router.post("/redeem-coupon")
def redeem_coupon(
    coupon_code: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    reward = db.query(crud.models.ClaimedReward).filter(crud.models.ClaimedReward.coupon_code == coupon_code).first()
    if not reward:
        raise HTTPException(status_code=404, detail="Coupon not found")
    # Only admin_uid of restaurant or main admin can redeem
    restaurant = db.query(crud.models.Restaurant).filter(crud.models.Restaurant.restaurant_id == reward.restaurant_id).first()
    main_admin_uid = "qkmgiVcJhYgTpJSITv7PD6kxgn12"
    if current_user.uid != main_admin_uid and current_user.uid != restaurant.admin_uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can redeem coupon.")
    if reward.redeemed:
        raise HTTPException(status_code=400, detail="Coupon already redeemed")
    reward.redeemed = True
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
