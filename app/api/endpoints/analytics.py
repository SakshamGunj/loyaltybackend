from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ... import crud
from ...database import get_db

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/referral-analytics")
def referral_analytics(restaurant_id: int = None, db: Session = Depends(get_db)):
    total_referrals = 0
    coupons_issued = 0
    rewards_used = 0
    loyalties = crud.list_loyalties(db)
    for l in loyalties:
        if restaurant_id and l.restaurant_id != restaurant_id:
            continue
        total_referrals += len(l.referrals_made or [])
        # Assume coupons issued = rewards claimed for demo
        coupons_issued += len(l.redemption_history or [])
        # Assume rewards used = claimed_rewards for demo
        rewards_used += len(l.redemption_history or [])
    return {
        "total_referrals": total_referrals,
        "coupons_issued": coupons_issued,
        "rewards_used": rewards_used,
    }

@router.get("/referral-leaderboard")
def referral_leaderboard(restaurant_id: int = None, db: Session = Depends(get_db)):
    loyalties = crud.list_loyalties(db)
    leaderboard = []
    for l in loyalties:
        if restaurant_id and l.restaurant_id != restaurant_id:
            continue
        leaderboard.append({"uid": l.uid, "referrals": len(l.referrals_made or [])})
    leaderboard.sort(key=lambda x: x["referrals"], reverse=True)
    return leaderboard[:10]
