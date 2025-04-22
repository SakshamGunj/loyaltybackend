from fastapi import APIRouter, HTTPException, status, Body
from pydantic import BaseModel, EmailStr
from firebase_admin import auth as firebase_auth, credentials, initialize_app
from app import crud, schemas
from app.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
import firebase_admin
import os
firebase_key = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
router = APIRouter(prefix="/api/auth", tags=["auth"])

# Initialize Firebase Admin SDK (only once)
if not firebase_admin._apps:
    import os
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    cred_path = os.path.join(BASE_DIR, "../../key.json")  # Navigates up to /app/key.json
    cred = credentials.Certificate({
  "type": "service_account",
  "project_id": "spinthewheel-e14a6",
  "private_key_id": "b981e054116fb026314df1967c65faa06fbb68de",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDqQiN+9knxoHto\n6fEdDbvI5fQFA4vVWneofp9YXR8g7BfiulUAm3kREXFt3W7hCCIjqX/VYx+lhhIM\ndF60jiNsRcGJWv3mvkCbGGPW2Yivw9egI5grFldqwTdW073XKYLkkxfva4sf02+l\nDnwt9sfOFmO0QzRbJiS/9PlVd8ChxiMbDGgx2cvvbom26cZGdNQG+GtpdvOU4MsP\nxpe2mG4dYOM1yjH5R74KoA1vpafGL0EJ+5aJmSrZUX0fH2XRt1lT/LyS4/9sy5Gx\nuv2LPz9Jg8W7nahdSR2kFn0V4GqGJ1pTPk/6fDC2p6/2Kz6HqHU/7ioyp03zvYYv\nqWIxJcAtAgMBAAECggEADW/uR8/aVXsaYR38N+msAh3Ypbn6mSonj3l16/RpfvKz\n+wwrqI2CgA1jV4U6YTudc7S7EbMuI0lBu0eokAxQMVt9+sJGqqfynkLjpTUUr1pZ\nQcUQ6zXMnWHIahlavB8UNEbQumnNkO2Iq6vdSSis9OAZZ4NsWycguAcWD0Y/fTf7\neYixlEPvZNN6lRkFaG/duWV8jDLQ9cnO6TZ0OKar0gaGf7a9abVz2pGCx6RCuVUJ\nKMM7KL7Z6zliddB7lYNZKGE8QZlJg/LdRzbOvCQLekBn1ZKNMSrVrT/CMgHnL59u\nlO/yXmPaCVjbVi7JIf1cBaIsuTMwbXBRJ7i1ImZZ8QKBgQD+g0HDsyipEBqR+bPB\ngKb7zX3WhYFVDDzOI0g2F+9jLGK+wLeeM9UlCsy3Ws9sDiclKmvDzZLi6d03z7k/\ngBdYk6FadjN1f0LoPqfqalmoEtjOj1nQVpOJdyjZVU0mpWGU3/mJm1XQSz1uV+uV\nZ13QMmGhDTptwE/CIASjKx0JnQKBgQDroJT0wIIjJN2M4xV3kqkLF+iqvM/dYbiO\np1CJ0yv249N+c1Hdx/FBx856P5meGR9qjtr1WOOf5Y8oPEjBRxdipQ6B8UYTYtMy\nj5XCc7yjZmm4m9XhaK844i1mnZU1tjPsjD3tWi5Dma2pWMeZI2P+YcGyTakZs5dD\n/7fBaq9T0QKBgQC1IVK/ZRTN5QET3GK6lsXANImXD2Jw1Ym8ps1wee5LZT5NRTgo\nZfkOKLZy0zUFULk5MQyKyBX+WbOvUa0j7RQwXLibeb27pDtIr7avFMsD243iy5B+\nve64CU7QBW4nz9E3s4KTFTKoT7PDgNzPckYIsqJajOCFVTUuEb1bJoa+3QKBgGla\noJ+a39VE64bOFlAjlE/wfcixqaOLyRCHwRwO/q5iibMVbvpiJv5Jj4nbnB0zkHd9\nrmtbNlPNOag85C7/UXZ65LS3I6URX+tQhh6uzx6kcQrpKsWhoA8oGjKyrP+aGzde\nMWZKFzuEoECDAKP5TgF0xj2qObzTLwRpd0kVIZWxAoGAAqv3+x4ZRavtqvCJYh/5\n8xkPqvTwn2boXn4C/D+7QM+/hDsK1m/Edt+wZzJTCIf39LGcXQAE6dsxKhQ1s0Zk\nnz9d2xtsvzbc+no1Mdw7YIF+PGbCzkQkNTaTnwO8UXXAV0J2jCPq0gHGiDzPskky\nPYWexfJHxdfW9rN0BbXoyj8=\n-----END PRIVATE KEY-----\n",
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
