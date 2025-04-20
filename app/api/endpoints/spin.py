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
