from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ... import schemas, crud
from ...database import get_db
from ...auth import get_current_user, TokenData
from typing import List

router = APIRouter(prefix="/api/loyalty", tags=["loyalty"])

@router.post("/", response_model=schemas.LoyaltyOut)
def create_loyalty(
    loyalty: schemas.LoyaltyCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    if current_user.role != "admin" and loyalty.uid != current_user.uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return crud.create_loyalty(db, loyalty)

@router.get("/", response_model=List[schemas.LoyaltyOut])
def list_loyalties(
    uid: str = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    if current_user.role != "admin" and uid and uid != current_user.uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return crud.list_loyalties(db, uid=uid or current_user.uid)

@router.get("/{uid}/{restaurant_id}", response_model=schemas.LoyaltyOut)
def get_loyalty(
    uid: str, restaurant_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    if current_user.role != "admin" and uid != current_user.uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    loyalty = crud.get_loyalty(db, uid, restaurant_id)
    if not loyalty:
        raise HTTPException(status_code=404, detail="Loyalty record not found")
    return loyalty
