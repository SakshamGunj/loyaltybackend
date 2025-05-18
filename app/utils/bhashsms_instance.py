"""
BhashSMS instance provider - uses different implementations based on environment
"""
import os
import logging

logger = logging.getLogger(__name__)

# Detect if we're running in a cloud environment
is_cloud_run = os.getenv("K_SERVICE") is not None or os.getenv("GOOGLE_CLOUD_PROJECT") is not None
is_app_engine = os.getenv("GAE_ENV") is not None
is_koyeb = os.getenv("KOYEB_APP_NAME") is not None
is_cloud = is_cloud_run or is_app_engine or is_koyeb

if is_cloud:
    logger.info("Running in cloud environment, using mock BhashSMS implementation")
    from app.utils.mock_bhashsms import bhashsms
else:
    logger.info("Running in local environment, using real BhashSMS implementation")
    try:
        from app.utils.bhashsms_automation import BhashSMSAutomation
        
        class LazyBhashSMS:
            def __init__(self):
                self._instance = None
        
            def __getattr__(self, name):
                if self._instance is None:
                    self._instance = BhashSMSAutomation(headless=True)
                return getattr(self._instance, name)
        
        # Create a global instance
        bhashsms = LazyBhashSMS()
    except ImportError:
        logger.warning("Could not import BhashSMSAutomation, falling back to mock implementation")
        from app.utils.mock_bhashsms import bhashsms 