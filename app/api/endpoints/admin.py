from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ... import schemas, crud
from ...database import get_db
from typing import List

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/")
def admin_dashboard(restaurant_id: int = None, db: Session = Depends(get_db)):
    # Filter by restaurant if provided
    users = crud.list_loyalties(db)
    submissions = crud.list_submissions(db)
    claimed_rewards = crud.list_claimed_rewards(db)
    audit_logs = crud.list_audit_logs(db)
    return {
        "users": users,
        "submissions": submissions,
        "claimed_rewards": claimed_rewards,
        "audit_logs": audit_logs,
    }

@router.get("/{restaurant_id}/user/{uid}")
def admin_user_detail(restaurant_id: int, uid: str, db: Session = Depends(get_db)):
    loyalty = crud.get_loyalty(db, uid, restaurant_id)
    claimed_rewards = crud.list_claimed_rewards(db, uid=uid)
    submissions = crud.list_submissions(db, uid=uid)
    return {
        "loyalty": loyalty,
        "claimed_rewards": claimed_rewards,
        "submissions": submissions,
    }
