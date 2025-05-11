from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import VerifiedPhoneNumber
from app.utils.bhashsms_instance import bhashsms
import logging
import time

router = APIRouter(prefix="/api/otp", tags=["otp"])
logger = logging.getLogger(__name__)

# Store OTPs temporarily (in production, use Redis or similar)
otp_store = {}
OTP_EXPIRY_SECONDS = 120  # 2 minutes

class OTPRequest(BaseModel):
    number: str

class OTPVerify(BaseModel):
    number: str
    otp: str

class OTPResponse(BaseModel):
    success: bool
    message: str
    panel_status: Optional[int] = None
    panel_response: Optional[str] = None

class OTPVerifyResponse(BaseModel):
    success: bool
    message: str

class WhatsAppMessageRequest(BaseModel):
    phone_number: str
    parameters: str
    template_message: Optional[str] = "Hi {{1}},\nAsha from Paddington this side,\n{{2}}."
    dtype: str = "markee"
    stype: str = "text"
    tai: str = "1"
    cano: str = "1"

class WhatsAppMessageResponse(BaseModel):
    success: bool
    message: str
    panel_status: Optional[int] = None
    panel_response: Optional[str] = None

@router.post("/send-whatsapp", response_model=WhatsAppMessageResponse)
async def send_whatsapp_message(request: WhatsAppMessageRequest):
    """
    Send a WhatsApp message using BhashSMS
    """
    try:
        # First ensure we're logged in
        if not bhashsms.is_logged_in:
            login_success = bhashsms.login()
            if not login_success:
                raise HTTPException(
                    status_code=401,
                    detail="Failed to authenticate with BhashSMS"
                )

        # Send the WhatsApp message
        result = bhashsms.send_whatsapp_message(
            phone_number=request.phone_number,
            parameters=request.parameters,
            template_message=request.template_message
        )

        return WhatsAppMessageResponse(
            success=result.get("success", False),
            message=result.get("message", "Unknown error"),
            panel_status=result.get("status_code"),
            panel_response=result.get("response_text")
        )

    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send WhatsApp message: {str(e)}"
        )

@router.post("/send")
async def send_otp(number: str):
    """
    Send OTP via WhatsApp
    """
    try:
        # First ensure we're logged in
        if not bhashsms.is_logged_in:
            login_success = bhashsms.login()
            if not login_success:
                raise HTTPException(
                    status_code=401,
                    detail="Failed to authenticate with BhashSMS"
                )

        # Send OTP using the send_otp method
        result = bhashsms.send_otp(phone_number=number)

        if result.get("success"):
            # Store OTP for verification
            otp_store[number] = {
                "otp": result.get("otp"),
                "timestamp": int(time.time())
            }

        return {
            "success": result.get("success", False),
            "message": result.get("message", "Unknown error"),
            "panel_status": result.get("panel_status"),
            "panel_response": result.get("panel_response")
        }

    except Exception as e:
        logger.error(f"Error sending OTP: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send OTP: {str(e)}"
        )

@router.post("/verify", response_model=OTPVerifyResponse)
def verify_otp(request: OTPVerify, db: Session = Depends(get_db)):
    """
    Verify OTP and store verified phone number
    """
    number = request.number
    if not number:
        raise HTTPException(status_code=400, detail="Invalid phone number")
    
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
            db.rollback()
    
    return {"success": True, "message": "OTP verified and number stored as verified."}

