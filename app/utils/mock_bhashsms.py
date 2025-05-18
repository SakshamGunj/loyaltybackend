"""
Mock implementation of BhashSMS automation for cloud environments
This avoids the Selenium dependency which doesn't work well in serverless environments
"""
import logging
import random
import string
import time

logger = logging.getLogger(__name__)

class MockBhashSMSAutomation:
    """Mock implementation of BhashSMS automation for cloud environments"""
    
    def __init__(self, headless=True):
        """Initialize the mock BhashSMS automation class."""
        logger.info("Initializing Mock BhashSMS automation for cloud environment")
        self.is_logged_in = False
        self.session = None
        
    def login(self, username="MOCK_USER", password="MOCK_PASS", max_retries=3):
        """Mock login that always succeeds"""
        logger.info("Mock BhashSMS login (always succeeds in cloud environment)")
        self.is_logged_in = True
        return True

    def get_session(self):
        """Get authenticated session"""
        if not self.is_logged_in:
            self.login()
        return "mock-session"

    def send_whatsapp_message(self, phone_number: str, parameters: str, template_message: str = None):
        """Mock sending a WhatsApp message"""
        logger.info(f"MOCK: Would send WhatsApp to {phone_number} with params: {parameters}")
        return {
            "success": True,
            "message": "WhatsApp message mock sent (cloud environment)",
            "status_code": 200,
            "response_text": "Mock response - no actual message sent in cloud environment"
        }
    
    def send_otp(self, phone_number: str):
        """Mock sending an OTP"""
        # Generate a random 6-digit OTP
        otp = ''.join(random.choices('0123456789', k=6))
        logger.info(f"MOCK: Generated OTP {otp} for {phone_number}")
        
        return {
            "success": True,
            "message": "OTP mock sent (cloud environment)",
            "otp": otp,
            "panel_status": 200,
            "panel_response": "Mock response - no actual OTP sent in cloud environment"
        }
    
    @staticmethod
    def clean_number(number: str) -> str:
        """Clean and validate a phone number"""
        # Remove any non-digit characters
        cleaned = ''.join(filter(str.isdigit, number))
        
        # If it starts with country code (e.g., 91), remove it
        if len(cleaned) > 10 and cleaned.startswith('91'):
            cleaned = cleaned[2:]
        
        # Validate it's a 10-digit number
        if len(cleaned) != 10:
            return None
            
        return cleaned

# Create a global instance
bhashsms = MockBhashSMSAutomation() 