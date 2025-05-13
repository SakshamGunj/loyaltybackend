from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ... import schemas, crud
from ...database import get_db
from ...auth.custom_auth import get_current_user, TokenData
from typing import List

router = APIRouter(prefix="/api/loyalty", tags=["loyalty"])

# All loyalty endpoints have been removed
