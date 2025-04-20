from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ... import schemas, crud
from ...database import get_db
from typing import List

router = APIRouter(prefix="/api/audit", tags=["audit"])

@router.post("/", response_model=schemas.AuditLogOut)
def create_audit_log(audit: schemas.AuditLogCreate, db: Session = Depends(get_db)):
    return crud.create_audit_log(db, audit)

@router.get("/", response_model=List[schemas.AuditLogOut])
def list_audit_logs(uid: str = None, db: Session = Depends(get_db)):
    return crud.list_audit_logs(db, uid=uid)
