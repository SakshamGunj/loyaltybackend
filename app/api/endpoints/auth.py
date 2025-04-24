from fastapi import APIRouter, HTTPException, status, Body
from pydantic import BaseModel, EmailStr
from firebase_admin import auth as firebase_auth, credentials, initialize_app
from app import crud, schemas
from app.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
import firebase_admin
import os
router = APIRouter(prefix="/api/auth", tags=["auth"])

# Initialize Firebase Admin SDK (only once)
if not firebase_admin._apps:
    cred = credentials.Certificate({
  "type": "service_account",
  "project_id": "spinthewheel-e14a6",
  "private_key_id": "c75ac56f4ca8c7ab7d16600285dfd558e64d1069",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDJ/VuhkOPUROOt\neqOI2u6dD0NpwAsYY2Q0UzDa9dsnRTxWUMRMXYfU0wtHiHpkzsMvyfw5cCsIxjYX\nNeaCFpSTfsaJCZ949FxrY3YJ7yBDN9npKMrerxiGWwma0AdPYkk1q5unIEPFVy7g\nv0/BpGOPKLj4zMnxS8v7BWJqBKQRDUHFHoPZxbxig5eVdA03apvc8o9VJ05gJ/d9\n83nY8JFjd2+1YTx+he7ViEPdvJ6R6c0cZ4TKGhKR7lh3omrqCbQleSKdWVJuY28F\njcA5j3lUFyoJwyU0+OSxcWGsPpMqvwRJFfagyuqxrhOlxqXWweA5qDoYFjf/EtcZ\nLXeZhmTLAgMBAAECggEAXRjXKOpc97MgtQ53XVZ68Aze51jKRF1bC/rj46e5cKoq\nmyXys7fQKTl0U24F63yY3efcxqR6UTr6J0yCh6bcp/agjvzOcbM+/YgEGaQLXK/b\nUempR2WwigxfqukC1YXZdFE6Fpd6ZPQ/+Pp0Si34bT05tAK/eOWUiIf8yhyFeg2u\ngzuQ2lxQXi4w/7iAx03oV2aYuowzN9S53Qnyd3M/48AbMzHEJI4I06FFKR8YxjZR\nY9LT/GtLj2s5asILUmQOc5ZwGH0L+JFIt9WARD6tImD7FjzsofiM9cIzaMLLVwj/\nXHnt8fk7TAf5h84AzYHnx9hltEHXHG31pLNubCKYgQKBgQDnLpScOV2dXUKLY9Hr\non4rRq3aVO8l/BEw61WZfjrY7Nw9Q5Hn3B1lEsLvcn1+aM9KNMJma/65bGawBioE\nF7d/woykgqQnAFgnaW+B3hCQeKCue/hcNL/skF5NYoTG3hbx85ittnm5EEm+2EZG\n8WsVk230Rquo02TO9SFfApASYQKBgQDfrIFtzjr59olY9mEfZZNefW2kDs5BI1s5\nNZy2BIUli/sGnflfdoFxfanqGn5IghD4wkjkz5P7x0ec3cmCDpWo2tKPtTMj4+fX\nvtju3N6DsGh8ec7C1yACtBu7HxPAlpc8lBe/xX2+0MYsBbIQUYsoMzOZH4KQ8rfC\nuU1hBZreqwKBgQCqf5IevbgrLPK89ruFO2wt4oypr2ZI72SGXand8FjaT6YGkOT0\nyUPsnS+jhR7EsevfYJXXD+LnQelh/MnUBuHQmd08HxWNphVdy8bvUqWIx05KISgE\naOr7P2YtUHF4cacefnel9iRDtp2M4NjDzZ0aZob7V3uWoYGBmQwplCxJQQKBgAbR\nrYh5dxbTy1ApAsEAScPhswwDX4pg15Eg70wlSyHf6KFFA6tDY6LgH+QBNsRjIr1S\nvwIqyeotIyPHJzON2kYxlaXH8m0vr4vGR7rQhQAiyqyw0frisBklAItt4R5H+Qhh\nw2+XR8QffUsuSUVyFvn8xZ/vc/2TSMLo/1Dr6NLNAoGAGVNQ6gV36TxrqrW8d3cj\nYnTWcGOqni47HVeHmsi/oQiced45laqi9/ZeVItblaR44wHyEpHcMJuMjPIge4at\nmnn55VLarQ0VhkBELbWn2Wc3WBRUZWG7AYvE6BZmPnvtiIs7sQnEiJMbc9uDhEif\n7f4Gnj4uE8lXS6/R4qC7U8s=\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-fbsvc@spinthewheel-e14a6.iam.gserviceaccount.com",
  "client_id": "116109310815956345340",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40spinthewheel-e14a6.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
)
    initialize_app(cred)

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    number: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/login")
def login(request: LoginRequest):
    """
    Authenticates user with Firebase Auth REST API and returns an ID token.
    """
    import requests
    import os
    FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "AIzaSyALZiqfQXlCGqRCI_NN3127oZhIkFd6unk")
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {
        "email": request.email,
        "password": request.password,
        "returnSecureToken": True
    }
    try:
        resp = requests.post(url, json=payload)
        data = resp.json()
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail=f"Login failed: {data.get('error', {}).get('message', 'Unknown error')}")
        return {
            "id_token": data["idToken"],
            "refresh_token": data["refreshToken"],
            "expires_in": data["expiresIn"],
            "uid": data["localId"],
            "email": data["email"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {e}")

from app.models import VerifiedPhoneNumber

import logging
import traceback

@router.delete("/delete-number")
def delete_number(number: str, db: Session = Depends(get_db)):
    """
    Delete a phone number from the VerifiedPhoneNumber table (and optionally User table). Accepts a number, normalizes it, deletes if found. Logs the operation.
    """
    import logging
    logger = logging.getLogger("delete_number")
    def clean_number(number: str) -> str:
        number = number.strip()
        if number.startswith('+91') and len(number) == 13:
            number = number[3:]
        elif number.startswith('91') and len(number) == 12:
            number = number[2:]
        if len(number) == 10 and number.isdigit():
            return number
        return None
    cleaned_number = clean_number(number)
    logger.info(f"Request to delete number: {number}, cleaned: {cleaned_number}")
    if not cleaned_number:
        return {"success": False, "message": "Invalid phone number format."}
    # Delete from VerifiedPhoneNumber
    found = db.query(VerifiedPhoneNumber).filter_by(number=cleaned_number).first()
    if found:
        db.delete(found)
        db.commit()
        logger.info(f"Deleted {cleaned_number} from VerifiedPhoneNumber.")
        # Optionally, also delete from User table if you want
        # user = db.query(User).filter_by(number=cleaned_number).first()
        # if user:
        #     db.delete(user)
        #     db.commit()
        return {"success": True, "message": f"Number {cleaned_number} deleted from database."}
    else:
        logger.warning(f"Number {cleaned_number} not found in VerifiedPhoneNumber.")
        return {"success": False, "message": "Number not found in database."}


@router.post("/signup")
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """
    Signup endpoint: Accepts name, email, and number. Cleans and normalizes the number, checks for duplicates in VerifiedPhoneNumber. If unique, creates user in Firebase (name/email only) and local DB (including number). If duplicate, returns error and does not create user or send OTP.
    Logs every step and error for debugging.
    """
    logger = logging.getLogger("signup")
    logger.info(f"Received signup request: email={request.email}, name={request.name}, number={request.number}")

    def clean_number(number: str) -> str:
        number = number.strip()
        if number.startswith('+91') and len(number) == 13:
            number = number[3:]
        elif number.startswith('91') and len(number) == 12:
            number = number[2:]
        if len(number) == 10 and number.isdigit():
            return number
        return None

    cleaned_number = clean_number(request.number)
    logger.info(f"Cleaned number: {cleaned_number}")
    if not cleaned_number:
        logger.warning(f"Invalid phone number provided: {request.number}")
        raise HTTPException(status_code=400, detail="Invalid phone number. Please provide a valid 10-digit Indian mobile number without country code.")

    # Check for duplicate number in verified table
    existing = db.query(VerifiedPhoneNumber).filter_by(number=cleaned_number).first()
    logger.info(f"Duplicate check in VerifiedPhoneNumber: found={bool(existing)}")
    if existing:
        logger.warning(f"Duplicate phone number attempted: {cleaned_number}")
        raise HTTPException(status_code=400, detail="This number is already associated with an existing account.")

    # Optionally, check in User table if you want to prevent duplicate numbers even if not verified
    # user_exists = db.query(User).filter_by(number=cleaned_number).first()
    # logger.info(f"Duplicate check in User table: found={bool(user_exists)}")
    # if user_exists:
    #     logger.warning(f"Duplicate phone number in User table: {cleaned_number}")
    #     raise HTTPException(status_code=400, detail="This number is already associated with an existing account.")

    try:
        logger.info(f"Creating user in Firebase: email={request.email}, name={request.name}")
        user_record = firebase_auth.create_user(
            email=request.email,
            password=request.password,
            display_name=request.name
        )
        from datetime import datetime
        user = schemas.UserBase(uid=user_record.uid, name=request.name, email=request.email, created_at=datetime.utcnow())
        db_user = crud.create_user(db, user)
        logger.info(f"User created in DB with UID: {user_record.uid}")
        # Optionally: add number to user model if not present
        # db_user.number = cleaned_number
        # db.commit()
        db.add(VerifiedPhoneNumber(number=cleaned_number))
        db.commit()
        logger.info(f"VerifiedPhoneNumber added: {cleaned_number}")
        token = firebase_auth.create_custom_token(user_record.uid)
        logger.info(f"Custom token generated for UID: {user_record.uid}")
        return {"custom_token": token.decode('utf-8'), "uid": user_record.uid, "email": request.email, "name": request.name}
    except Exception as e:
        db.rollback()
        logger.error(f"Exception during signup: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=f"Signup failed: {e}")



@router.post("/verify-token")
def verify_token(id_token: str = Body(...)):
    """
    Accept a Firebase ID token from the frontend, verify it, and return user info.
    The ID token must be obtained from Firebase JS SDK after login or sign-in-with-custom-token.
    """
    try:
        decoded = firebase_auth.verify_id_token(id_token)
        return {"uid": decoded["uid"], "email": decoded.get("email")}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Firebase ID token: {e}")
