from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ... import schemas, crud
from ...database import get_db
from ...auth.custom_auth import get_current_user, TokenData
from ...utils.rate_limiter import rate_limiter_referral, rate_limiter_referral_total
from ... import schemas, crud
from typing import Dict
import random, string

router = APIRouter(prefix="/api/referrals", tags=["referrals"])

# Generate a referral code for a user/restaurant
@router.get("/code")
def get_referral_code(
    uid: str,
    restaurant_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    if current_user.role != "admin" and uid != current_user.uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    # Rate limit: 5 codes/hour
    key = f"referral_code:{uid}:{restaurant_id}"
    if not rate_limiter_referral.is_allowed(key):
        raise HTTPException(status_code=429, detail="Referral code generation rate limit exceeded")
    loyalty = crud.get_loyalty(db, uid, restaurant_id)
    if not loyalty:
        loyalty = crud.create_loyalty(db, schemas.LoyaltyCreate(uid=uid, restaurant_id=restaurant_id))
    codes = loyalty.referral_codes or {}
    if str(restaurant_id) not in codes:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        codes[str(restaurant_id)] = code
        loyalty.referral_codes = codes
        db.commit()
        db.refresh(loyalty)
    # Log
    crud.create_audit_log(db, schemas.AuditLogCreate(user_id=uid, action="generate_referral_code", details={"restaurant_id": restaurant_id}, timestamp=None))
    return {"referral_code": loyalty.referral_codes[str(restaurant_id)]}

# Process a referral
@router.post("/apply")
def apply_referral(
    referral_code: str,
    referred_uid: str,
    restaurant_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    if current_user.role != "admin" and referred_uid != current_user.uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    # Rate limit: 5/hour, 10/restaurant
    key = f"referral_apply:{referred_uid}:{restaurant_id}"
    total_key = f"referral_apply_total:{referred_uid}:{restaurant_id}"
    if not rate_limiter_referral.is_allowed(key):
        raise HTTPException(status_code=429, detail="Referral rate limit exceeded (5/hour)")
    if not rate_limiter_referral_total.is_allowed(total_key):
        raise HTTPException(status_code=429, detail="Max 10 referrals per restaurant")
    # Find the referring user
    referrer_loyalties = db.query(crud.models.Loyalty).filter(crud.models.Loyalty.restaurant_id == restaurant_id).all()
    referrer = None
    for l in referrer_loyalties:
        codes = l.referral_codes or {}
        if codes.get(str(restaurant_id)) == referral_code:
            referrer = l
            break
    if not referrer:
        raise HTTPException(status_code=404, detail="Invalid referral code")
    if referrer.uid == referred_uid:
        raise HTTPException(status_code=400, detail="Self-referral not allowed")
    referred_loyalty = crud.get_loyalty(db, referred_uid, restaurant_id)
    if not referred_loyalty:
        referred_loyalty = crud.create_loyalty(db, schemas.LoyaltyCreate(uid=referred_uid, restaurant_id=restaurant_id))
    # Prevent duplicate referral
    if referred_loyalty.referred_by and referred_loyalty.referred_by.get("referrer_uid"):
        raise HTTPException(status_code=400, detail="Already referred")
    # Reward both users (for demo: +20 points)
    referrer.restaurant_points += 20
    referred_loyalty.restaurant_points += 20
    referred_loyalty.referred_by = {"referrer_uid": referrer.uid, "code": referral_code}
    referrer.referrals_made = (referrer.referrals_made or []) + [referred_uid]
    db.commit()
    # Log
    crud.create_audit_log(db, schemas.AuditLogCreate(user_id=referred_uid, action="apply_referral", details={"referrer": referrer.uid, "restaurant_id": restaurant_id}, timestamp=None))
    return {"msg": "Referral applied", "referrer": referrer.uid, "referred": referred_uid}
