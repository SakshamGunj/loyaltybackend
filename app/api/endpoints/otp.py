from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
import random
import string
import requests
import logging
import time
logger = logging.getLogger("otp")
router = APIRouter(prefix="/api/otp", tags=["otp"])

# In-memory store for OTPs (for demo; replace with Redis or DB in prod)
otp_store = {}
OTP_EXPIRY_SECONDS = 120  # 2 minutes

class OTPRequest(BaseModel):
    number: str

class OTPVerify(BaseModel):
    number: str
    otp: str

# Define response models
class OTPResponse(BaseModel):
    success: bool
    message: str
    panel_status: Optional[int] = None
    panel_response: Optional[str] = None

class OTPVerifyResponse(BaseModel):
    success: bool
    message: str

@router.post("/send", response_model=OTPResponse)
def send_otp(request: OTPRequest):
    """
    Accepts phone number (without +91), generates OTP, sends via BhashSMS API, stores OTP with expiry.
    """
    import re
    import random
    import string
    import requests
    import time

    def clean_number(number: str) -> str:
        number = number.strip()
        # Remove '+91' if present and length is 13
        if number.startswith('+91') and len(number) == 13:
            number = number[3:]
        # Remove '91' if present and length is 12
        elif number.startswith('91') and len(number) == 12:
            number = number[2:]
        # If after removing, or originally, it's 10 digits, accept
        if len(number) == 10 and number.isdigit():
            return number
        # Reject all other cases
        return None

    number = clean_number(request.number)
    logger.info(number)
    if not number:
        return {"success": False, "message": "Invalid phone number. Please provide a valid 10-digit Indian mobile number without country code."}

    otp = ''.join(random.choices(string.digits, k=4))
    otp_store[number] = {"otp": otp, "timestamp": int(time.time())}

    # BhashSMS API
    url = f"http://bhashsms.com/api/sendmsg.php?user=TENVERSE_MEDIA&pass=123456&sender=BUZWAP&phone={number}&text=otp_auth&priority=wa&stype=auth&Params={otp}"
    logger.info(url)
    try:
        resp = requests.get(url, timeout=10)
        response_text = resp.text
        if resp.status_code != 200 or 'error' in response_text.lower():
            return {"success": False, "message": "Failed to send OTP. Wrong number or SMS API error.", "panel_status": resp.status_code, "panel_response": response_text}
    except Exception as e:
        return {"success": False, "message": f"Failed to send OTP: {e}"}
    return {"success": True, "message": "OTP sent via WhatsApp", "panel_status": resp.status_code, "panel_response": response_text}


from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import VerifiedPhoneNumber

@router.post("/verify", response_model=OTPVerifyResponse)
def verify_otp(request: OTPVerify, db: Session = Depends(get_db)):
    """
    Accepts phone number and OTP, checks validity and expiry (2 minutes). On success, stores the normalized 10-digit phone number in the VerifiedPhoneNumber table (if not already present).
    """
    import time
    def clean_number(number: str) -> str:
        number = number.strip()
        # Remove '+91' if present and length is 13
        if number.startswith('+91') and len(number) == 13:
            number = number[3:]
        # Remove '91' if present and length is 12
        elif number.startswith('91') and len(number) == 12:
            number = number[2:]
        # If after removing, or originally, it's 10 digits, accept
        if len(number) == 10 and number.isdigit():
            return number
        # Reject all other cases
        return None

    number = clean_number(request.number)
    if not number:
        raise HTTPException(status_code=400, detail="Invalid phone number. Please provide a valid 10-digit Indian mobile number without country code.")
    entry = otp_store.get(number)
    if not entry:
        raise HTTPException(status_code=400, detail="No OTP sent to this number")
    if int(time.time()) - entry["timestamp"] > OTP_EXPIRY_SECONDS:
        del otp_store[number]
        raise HTTPException(status_code=400, detail="OTP expired")
    if request.otp != entry["otp"]:
        raise HTTPException(status_code=400, detail="OTP does not match")
    del otp_store[number]

    # Store verified number in DB if not already present
    existing = db.query(VerifiedPhoneNumber).filter_by(number=number).first()
    if not existing:
        try:
            db.add(VerifiedPhoneNumber(number=number))
            db.commit()
        except Exception:
            db.rollback()  # In case of race condition/duplicate
    return {"success": True, "message": "OTP verified and number stored as verified."}

