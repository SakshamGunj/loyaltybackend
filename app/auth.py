from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from .utils.firebase import verify_firebase_token

class TokenData(BaseModel):
    uid: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = "user"  # 'user' or 'admin'

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    user_info = verify_firebase_token(credentials)
    return TokenData(uid=user_info["uid"], email=user_info.get("email"), role=user_info.get("role", "user"))
