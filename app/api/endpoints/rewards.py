from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ... import schemas, crud
from ...database import get_db
from ...auth import get_current_user, TokenData
from typing import List

router = APIRouter(prefix="/api/rewards", tags=["rewards"])

@router.post("/", response_model=schemas.ClaimedRewardOut)
def create_claimed_reward(
    reward: schemas.ClaimedRewardCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    # Ignore uid and coupon_code from the body, always use current_user.uid and generate coupon_code
    reward_data = reward.dict(exclude={"uid", "coupon_code", "claimed_at", "redeemed", "redeemed_at", "id"})
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
