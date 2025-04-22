from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ... import schemas, crud
from ...database import get_db
from ...auth import get_current_user, TokenData
from ...utils.rate_limiter import rate_limiter_spin
from ... import schemas, crud
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/api/spin", tags=["spin"])

SPIN_REWARDS = [
    {"type": "points", "value": 5},
    {"type": "points", "value": 10},
    {"type": "none", "value": 0},
    {"type": "offer", "value": "Free Drink"},
]

from datetime import datetime
from fastapi import Query

@router.get("/checksspin")
def check_spins_left(
    uid: str = Query(...),
    restaurant_id: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns a dict {restaurant_id: spins_left} for the given user for today (max 1 spin per restaurant per day).
    If restaurant_id is provided, only return spins left for that restaurant.
    If no loyalty record exists, spins_left is 0.
    """
    today = datetime.utcnow().date()
    if restaurant_id:
        loyalty = db.query(crud.models.Loyalty).filter(
            crud.models.Loyalty.uid == uid,
            crud.models.Loyalty.restaurant_id == restaurant_id
        ).first()
        spins_left = 1
        if loyalty:
            if loyalty.last_spin_time and loyalty.last_spin_time.date() == today:
                spins_left = 0
        else:
            spins_left = 0
        return {restaurant_id: spins_left}
    else:
        loyalties = db.query(crud.models.Loyalty).filter(crud.models.Loyalty.uid == uid).all()
        result = {}
        for loyalty in loyalties:
            rid = loyalty.restaurant_id
            spins_today = 0
            if loyalty.last_spin_time and loyalty.last_spin_time.date() == today:
                spins_today = 1
            result[rid] = 1 - spins_today
        return result

@router.post("/wheel")
def spin_wheel(
    uid: str,
    restaurant_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    if current_user.role != "admin" and uid != current_user.uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    # Rate limiting
    key = f"spin:{uid}:{restaurant_id}"
    if not rate_limiter_spin.is_allowed(key):
        raise HTTPException(status_code=429, detail="Spin allowed once every 24 hours")
    loyalty = crud.get_loyalty(db, uid, restaurant_id)
    now = datetime.utcnow()
    if loyalty:
        if loyalty.last_spin_time and (now - loyalty.last_spin_time) < timedelta(hours=24):
            raise HTTPException(status_code=429, detail="Spin allowed once every 24 hours")
    else:
        loyalty = crud.create_loyalty(db, schemas.LoyaltyCreate(uid=uid, restaurant_id=restaurant_id))
    outcome = random.choice(SPIN_REWARDS)
    # Update loyalty
    spin_entry = {"time": now.isoformat(), "outcome": outcome}
    history = loyalty.spin_history or []
    history.append(spin_entry)
    loyalty.spin_history = history
    loyalty.last_spin_time = now
    if outcome["type"] == "points":
        loyalty.total_points += outcome["value"]
        loyalty.restaurant_points += outcome["value"]
    # TODO: handle offer/coupon type outcomes
    db.commit()
    db.refresh(loyalty)
    # Log to AuditLog
    crud.create_audit_log(db, schemas.AuditLogCreate(user_id=uid, action="spin_wheel", details={"outcome": outcome, "restaurant_id": restaurant_id}, timestamp=now))
    return {"result": outcome, "loyalty": loyalty}
