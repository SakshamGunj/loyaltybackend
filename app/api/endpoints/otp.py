from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
import random
import string
import requests
import time

router = APIRouter(prefix="/api/otp", tags=["otp"])

# In-memory store for OTPs (for demo; replace with Redis or DB in prod)
otp_store = {}
OTP_EXPIRY_SECONDS = 300  # 5 minutes

class OTPRequest(BaseModel):
    number: str

class OTPVerify(BaseModel):
    number: str
    otp: str

@router.post("/send")
def send_otp(request: OTPRequest):
    # Generate 4-digit OTP
    otp = ''.join(random.choices(string.digits, k=4))
    otp_store[request.number] = {"otp": otp, "timestamp": int(time.time())}
    # Prepare multipart/form-data payload
    files = {
        'parameters': (None, otp),
        'numbers': (None, request.number),
        'submitc': (None, 'Send Single WA'),
        'dtype': (None, 'authh'),
        'stype': (None, 'text'),
        'tmessage': (None, f"{otp} Your Auth Otp"),
        'tai': (None, '1'),
        'cano': (None, '1'),
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Origin': 'http://panelwa.tenversemedia.tech',
        'Referer': 'http://panelwa.tenversemedia.tech/pushwa/iframe/singlewa.php',
        # Content-Type will be set by requests automatically for multipart
    }
    url = "http://panelwa.tenversemedia.tech/pushwa/iframe/singlewa.php"
    try:
        resp = requests.post(url, files=files, headers=headers, timeout=10, verify=False)
        response_text = resp.text
        if resp.status_code != 200:
            return {"success": False, "message": f"Failed to send OTP", "panel_status": resp.status_code, "panel_response": response_text}
    except Exception as e:
        return {"success": False, "message": f"Failed to send OTP: {e}"}
    return {"success": True, "message": "OTP sent via WhatsApp", "panel_status": resp.status_code, "panel_response": response_text}

@router.post("/verify")
def verify_otp(request: OTPVerify):
    entry = otp_store.get(request.number)
    if not entry:
        raise HTTPException(status_code=400, detail="No OTP sent to this number")
    if int(time.time()) - entry["timestamp"] > OTP_EXPIRY_SECONDS:
        del otp_store[request.number]
        raise HTTPException(status_code=400, detail="OTP expired")
    if request.otp != entry["otp"]:
        raise HTTPException(status_code=400, detail="OTP does not match")
    del otp_store[request.number]
    return {"success": True, "message": "OTP verified"}
