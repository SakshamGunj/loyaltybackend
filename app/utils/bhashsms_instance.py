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