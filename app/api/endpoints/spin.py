from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from ... import schemas, crud
from ...database import get_db
from ...auth.custom_auth import get_current_user, TokenData
from ...utils.rate_limiter import rate_limiter_spin
from ... import schemas, crud
from datetime import datetime, timedelta
import random

router = APIRouter(tags=["spin"])

SPIN_REWARDS = [
    {"type": "points", "value": 5},
    {"type": "points", "value": 10},
    {"type": "none", "value": 0},
    {"type": "offer", "value": "Free Drink"},
]

from datetime import datetime
from fastapi import Query

# Maximum spins per day
MAX_SPINS_PER_DAY = 3

# The checkspin endpoint
@router.get("/checkspin")
@router.get("/checksspin")  # Original URL with typo for backward compatibility
def check_spins_left(
    uid: str = Query(...),
    restaurant_id: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns a dict {restaurant_id: spins_left} for the given user for today (max 3 spins per restaurant per day).
    If restaurant_id is provided, only return spins left for that restaurant.
    If no loyalty record exists, spins_left is MAX_SPINS_PER_DAY.
    """
    today = datetime.utcnow().date()
    
    if restaurant_id:
        # Check for a specific restaurant
        loyalty = db.query(crud.models.Loyalty).filter(
            crud.models.Loyalty.uid == uid,
            crud.models.Loyalty.restaurant_id == restaurant_id
        ).first()
        
        spins_left = MAX_SPINS_PER_DAY
        if loyalty:
            spins_today = 0
            # Count spins made today
            if loyalty.spin_history:
                for spin in loyalty.spin_history:
                    try:
                        # Check if the spin was made today
                        spin_time = datetime.fromisoformat(spin.get('time', ''))
                        if spin_time.date() == today:
                            spins_today += 1
                    except (ValueError, TypeError):
                        pass
            
            spins_left = max(0, MAX_SPINS_PER_DAY - spins_today)
        
        return {restaurant_id: spins_left}
    else:
        # Get spins left for all restaurants
        loyalties = db.query(crud.models.Loyalty).filter(crud.models.Loyalty.uid == uid).all()
        result = {}
        
        for loyalty in loyalties:
            rid = loyalty.restaurant_id
            spins_today = 0
            
            # Count spins made today
            if loyalty.spin_history:
                for spin in loyalty.spin_history:
                    try:
                        # Check if the spin was made today
                        spin_time = datetime.fromisoformat(spin.get('time', ''))
                        if spin_time.date() == today:
                            spins_today += 1
                    except (ValueError, TypeError):
                        pass
            
            result[rid] = max(0, MAX_SPINS_PER_DAY - spins_today)
        
        return result

@router.post("/wheel")
def spin_wheel(
    uid: str,
    restaurant_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Perform a spin with 3 spins per day limit.
    """
    if current_user.role != "admin" and uid != current_user.uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    
    # Check daily spin limit
    today = datetime.utcnow().date()
    loyalty = crud.get_loyalty(db, uid, restaurant_id)
    
    # If loyalty record doesn't exist, create it
    if not loyalty:
        loyalty = crud.create_loyalty(db, schemas.LoyaltyCreate(uid=uid, restaurant_id=restaurant_id))
        spins_today = 0
    else:
        # Count spins made today
        spins_today = 0
        if loyalty.spin_history:
            for spin in loyalty.spin_history:
                try:
                    spin_time = datetime.fromisoformat(spin.get('time', ''))
                    if spin_time.date() == today:
                        spins_today += 1
                except (ValueError, TypeError):
                    pass
    
    # Check if max spins reached
    if spins_today >= MAX_SPINS_PER_DAY:
        raise HTTPException(status_code=429, detail=f"Maximum {MAX_SPINS_PER_DAY} spins allowed per day")
    
    # Perform the spin
    now = datetime.utcnow()
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
    
    # Calculate spins left after this spin
    spins_left = MAX_SPINS_PER_DAY - (spins_today + 1)
    
    return {
        "result": outcome, 
        "loyalty": loyalty,
        "spins_left": spins_left
    }
