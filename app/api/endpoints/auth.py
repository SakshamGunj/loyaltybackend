from fastapi import APIRouter, HTTPException, status, Body, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from ... import crud, schemas
from ...database import get_db
from ...auth.custom_auth import (
    authenticate_user,
    create_user_token,
    get_password_hash,
    get_current_user,
    TokenData
)
from typing import Optional

router = APIRouter(prefix="/api/auth", tags=["auth"])

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    number: str
    role: str = "customer"  # Default role

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: schemas.UserOut

@router.post("/signup", response_model=TokenResponse)
def signup(
    user_data: SignupRequest,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    # Check if user already exists
    db_user = crud.get_user_by_email(db, email=user_data.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user_create = schemas.UserCreate(
        email=user_data.email,
        password=user_data.password,  # Pass the plain password, hashing will be done in crud
        name=user_data.name,
        number=user_data.number,
        role=user_data.role
    )
    user = crud.create_user(db, user_create)
    
    # Generate token
    access_token = create_user_token(user)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login user and return JWT token."""
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate token
    access_token = create_user_token(user)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=schemas.UserOut)
def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information."""
    user = crud.get_user(db, current_user.uid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user
