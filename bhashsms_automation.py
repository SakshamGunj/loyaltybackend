import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException
import os
import json
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import uvicorn
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bhashsms_automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI(title="BhashSMS Automation API", description="API for automating BhashSMS login and data extraction")

class BhashSMSAutomation:
    def __init__(self, headless=True):
        """Initialize the BhashSMS automation class."""
        logger.info("Initializing BhashSMS automation")
        
        # Set up Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Anti-bot detection measures
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # Initialize the WebDriver
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            # Apply additional anti-bot measures
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            if not headless:
                self.driver.maximize_window()
            logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            raise
            
    def login(self, username, password, max_retries=3):
        """Login to BhashSMS with provided credentials."""
        for attempt in range(1, max_retries + 1):
            try:
                # Navigate to the login page
                url = "https://www.bhashsms.com/loginlanding.php"
                logger.info(f"Navigating to {url} (Attempt {attempt}/{max_retries})")
                self.driver.get(url)
                time.sleep(2)  # Wait for page to load
                
                # Check if page loaded properly
                if "BhashSMS" not in self.driver.title:
                    logger.warning(f"Page title doesn't contain 'BhashSMS': {self.driver.title}")
                
                # Find username and password fields using XPath
                logger.info("Locating username field")
                username_field = self.driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div/div[2]/form/input[1]")
                
                logger.info("Locating password field")
                password_field = self.driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div/div[2]/form/input[2]")
                
                # Enter credentials
                logger.info(f"Entering username: {username}")
                username_field.clear()
                username_field.send_keys(username)
                
                logger.info("Entering password: ********")
                password_field.clear()
                password_field.send_keys(password)
                
                # Find and click the login button
                logger.info("Locating login button")
                login_button = self.driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div/div[2]/form/input[3]")
                
                logger.info("Clicking login button")
                login_button.click()
                
                # Check for CAPTCHA (simplified, would need refinement for actual CAPTCHA detection)
                self._check_captcha()
                
                # Wait for dashboard page to load
                try:
                    logger.info("Waiting for dashboard to load")
                    WebDriverWait(self.driver, 10).until(
                        EC.url_to_be("https://www.bhashsms.com/index.php")
                    )
                    logger.info("Successfully logged in and reached dashboard")
                    return True
                except TimeoutException:
                    # Check for error messages
                    error_messages = self._check_for_login_errors()
                    if error_messages:
                        logger.error(f"Login error detected: {error_messages}")
                        # If we have specific error handling logic for certain messages
                        if "Invalid credentials" in error_messages:
                            logger.error("Username or password is incorrect.")
                            return False
                        elif "account locked" in error_messages.lower():
                            logger.error("Account appears to be locked.")
                            return False
                    else:
                        logger.error("Timed out waiting for dashboard page to load")
                    
                    if attempt < max_retries:
                        logger.info(f"Retrying login (Attempt {attempt+1}/{max_retries})")
                        time.sleep(2)  # Wait before retrying
                    else:
                        logger.error(f"Failed to login after {max_retries} attempts")
                        return False
                    
            except (NoSuchElementException, ElementNotInteractableException) as e:
                logger.error(f"Element interaction error: {e}")
                if attempt < max_retries:
                    logger.info(f"Retrying login (Attempt {attempt+1}/{max_retries})")
                    time.sleep(2)  # Wait before retrying
                else:
                    logger.error(f"Failed to login after {max_retries} attempts")
                    return False
            except Exception as e:
                logger.error(f"Login failed: {e}")
                return False
        
        return False
    
    def _check_captcha(self):
        """Check if a CAPTCHA is present and handle it."""
        try:
            # Look for common CAPTCHA indicators (this is simplified - actual implementation would be more specific)
            captcha_indicators = [
                "//img[contains(@src, 'captcha')]",
                "//div[contains(@class, 'captcha')]",
                "//*[contains(text(), 'captcha')]",
                "//*[contains(text(), 'Captcha')]",
                "//*[contains(text(), 'CAPTCHA')]"
            ]
            
            for indicator in captcha_indicators:
                elements = self.driver.find_elements(By.XPATH, indicator)
                if elements:
                    logger.warning(f"CAPTCHA potentially detected via: {indicator}")
                    # Take a screenshot to help diagnose
                    self.driver.save_screenshot("captcha_detected.png")
                    
                    # In a real implementation, you might:
                    # 1. Use a CAPTCHA solving service
                    # 2. Wait for manual intervention
                    # 3. Try alternative login methods
                    
                    logger.error("CAPTCHA detected - automated solving not implemented")
                    return True
                    
            return False
        except Exception as e:
            logger.error(f"Error checking for CAPTCHA: {e}")
            return False
    
    def _check_for_login_errors(self):
        """Check for error messages on the login page."""
        try:
            # Common XPaths or selectors where error messages might appear
            error_selectors = [
                "//div[contains(@class, 'error')]",
                "//span[contains(@class, 'error')]",
                "//p[contains(@class, 'error')]",
                "//div[contains(@class, 'alert')]",
                "//div[contains(@class, 'message')]"
            ]
            
            for selector in error_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    text = element.text.strip()
                    if text:
                        return text
            
            return None
        except Exception as e:
            logger.error(f"Error checking for login errors: {e}")
            return None
            
    def capture_dashboard_content(self):
        """Capture and return the content of the dashboard page."""
        try:
            logger.info("Capturing dashboard content")
            
            # Wait for main dashboard elements to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get page title
            title = self.driver.title
            logger.info(f"Dashboard title: {title}")
            
            # Get main content (can be adjusted based on the actual page structure)
            body_content = self.driver.find_element(By.TAG_NAME, "body").text
            logger.info(f"Captured {len(body_content)} characters of dashboard content")
            
            # Extract specific dashboard elements
            dashboard_data = self._extract_dashboard_elements()
            
            # Take screenshot for visual verification
            screenshot_path = f"bhashsms_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Screenshot saved as {screenshot_path}")
            
            return {
                "title": title,
                "content": body_content,
                "dashboard_data": dashboard_data,
                "screenshot_path": screenshot_path
            }
            
        except Exception as e:
            logger.error(f"Failed to capture dashboard content: {e}")
            return None
    
    def _extract_dashboard_elements(self):
        """Extract specific elements from dashboard."""
        dashboard_data = {}
        
        try:
            # This would need customization based on actual page structure
            # The following are examples and should be adjusted
            
            # Extract username or account info if available
            try:
                user_info_elements = [
                    "//div[contains(@class, 'user-info')]",
                    "//span[contains(@class, 'username')]",
                    "//div[contains(@class, 'account-info')]"
                ]
                
                for selector in user_info_elements:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements and elements[0].is_displayed():
                        dashboard_data["user_info"] = elements[0].text
                        break
            except Exception as e:
                logger.warning(f"Could not extract user info: {e}")
            
            # Extract available SMS balance if present
            try:
                balance_elements = [
                    "//div[contains(text(), 'Balance')]/following-sibling::div",
                    "//span[contains(text(), 'SMS')]/following-sibling::span",
                    "//div[contains(@class, 'balance')]"
                ]
                
                for selector in balance_elements:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements and elements[0].is_displayed():
                        dashboard_data["sms_balance"] = elements[0].text
                        break
            except Exception as e:
                logger.warning(f"Could not extract SMS balance: {e}")
            
            # Extract any notifications or alerts
            try:
                notification_elements = [
                    "//div[contains(@class, 'notification')]",
                    "//div[contains(@class, 'alert')]",
                    "//div[contains(@class, 'message')]"
                ]
                
                notifications = []
                for selector in notification_elements:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.text.strip():
                            notifications.append(element.text.strip())
                
                if notifications:
                    dashboard_data["notifications"] = notifications
            except Exception as e:
                logger.warning(f"Could not extract notifications: {e}")
            
            # Get dashboard nav menu items
            try:
                menu_items = []
                menu_elements = self.driver.find_elements(By.XPATH, "//ul[@class='nav']/li/a")
                for element in menu_elements:
                    if element.is_displayed() and element.text.strip():
                        menu_items.append({
                            "text": element.text.strip(),
                            "href": element.get_attribute("href")
                        })
                
                if menu_items:
                    dashboard_data["menu_items"] = menu_items
            except Exception as e:
                logger.warning(f"Could not extract menu items: {e}")
                
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error extracting dashboard elements: {e}")
            return {"error": str(e)}
    
    def navigate_to_section(self, section_name):
        """Navigate to a specific section of the dashboard."""
        try:
            logger.info(f"Attempting to navigate to section: {section_name}")
            
            # Locate links or buttons that might lead to the section
            potential_elements = self.driver.find_elements(
                By.XPATH, 
                f"//a[contains(text(), '{section_name}')] | "
                f"//button[contains(text(), '{section_name}')] | "
                f"//span[contains(text(), '{section_name}')]"
            )
            
            if not potential_elements:
                logger.warning(f"No elements found for section: {section_name}")
                return False
                
            # Click the first visible element
            for element in potential_elements:
                if element.is_displayed():
                    logger.info(f"Clicking on element: {element.text}")
                    element.click()
                    time.sleep(2)  # Wait for page to load
                    logger.info(f"Navigated to: {self.driver.current_url}")
                    return True
                    
            logger.warning(f"No visible elements found for section: {section_name}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to navigate to section {section_name}: {e}")
            return False
            
    def close(self):
        """Close the browser and release resources."""
        if hasattr(self, 'driver'):
            logger.info("Closing browser")
            self.driver.quit()

# Pydantic models for API
class LoginRequest(BaseModel):
    username: str
    password: str
    headless: bool = True

class LoginResponse(BaseModel):
    success: bool
    message: str
    dashboard_data: dict = None
    screenshot_url: str = None

# Global variables to track the latest automation run
latest_screenshot = None
latest_run_time = None
latest_run_status = "Not run"

# Function to run in background
async def run_automation(username: str, password: str, headless: bool = True):
    global latest_screenshot, latest_run_time, latest_run_status
    
    latest_run_status = "In progress"
    latest_run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        automation = BhashSMSAutomation(headless=headless)
        
        try:
            logger.info(f"Starting BhashSMS login automation for user {username}")
            
            # Perform login
            login_success = automation.login(username, password)
            
            if login_success:
                # Capture dashboard content after successful login
                dashboard_data = automation.capture_dashboard_content()
                
                if dashboard_data:
                    latest_screenshot = dashboard_data.get("screenshot_path")
                    latest_run_status = "Success"
                    
                    # Save the data to a JSON file for later retrieval
                    result_data = {
                        "success": True,
                        "timestamp": datetime.now().isoformat(),
                        "title": dashboard_data.get("title"),
                        "dashboard_data": dashboard_data.get("dashboard_data"),
                        "screenshot_path": dashboard_data.get("screenshot_path")
                    }
                    
                    # Save only first 1000 chars of content to keep file size reasonable
                    content = dashboard_data.get("content", "")
                    if content:
                        result_data["content_preview"] = content[:1000]
                    
                    # Generate a unique filename
                    result_filename = f"bhashsms_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    
                    with open(result_filename, "w", encoding="utf-8") as f:
                        json.dump(result_data, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"Automation result saved to {result_filename}")
                else:
                    latest_run_status = "Failed: Could not capture dashboard"
                    logger.error("Automation failed: Could not capture dashboard content")
            else:
                latest_run_status = "Failed: Login unsuccessful"
                logger.error("Automation failed: Could not log in")
                
        except Exception as e:
            latest_run_status = f"Error: {str(e)}"
            logger.error(f"Automation error: {e}")
            raise
        finally:
            # Always close the browser
            automation.close()
    except Exception as e:
        latest_run_status = f"Critical error: {str(e)}"
        logger.error(f"Critical automation error: {e}")

# API endpoints
@app.post("/api/bhashsms/login", response_model=LoginResponse)
async def bhashsms_login(login_data: LoginRequest, background_tasks: BackgroundTasks):
    """
    Trigger a login to BhashSMS and return the status.
    The actual work happens in the background.
    """
    try:
        # Start the automation in the background
        background_tasks.add_task(
            run_automation, 
            login_data.username, 
            login_data.password, 
            login_data.headless
        )
        
        return JSONResponse({
            "success": True,
            "message": "Login process started in background. Check status endpoint for results.",
            "job_id": datetime.now().strftime("%Y%m%d%H%M%S")
        })
    except Exception as e:
        logger.error(f"API error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start automation: {str(e)}")

@app.get("/api/bhashsms/status")
async def bhashsms_status():
    """Get the status of the latest automation run."""
    return JSONResponse({
        "status": latest_run_status,
        "last_run": latest_run_time,
        "screenshot_available": latest_screenshot is not None
    })

@app.get("/api/bhashsms/screenshot")
async def bhashsms_screenshot():
    """Get the latest screenshot."""
    if latest_screenshot and os.path.exists(latest_screenshot):
        return FileResponse(latest_screenshot)
    else:
        raise HTTPException(status_code=404, detail="No screenshot available")

@app.get("/")
async def root():
    return {"message": "BhashSMS Automation API is running. Use /api/bhashsms/login to start automation."}

def main():
    """Main function to demonstrate BhashSMS automation (for standalone use)."""
    username = "TENVERSE_MEDIA"
    password = "123456"
    
    automation = BhashSMSAutomation(headless=True)
    
    try:
        logger.info("Starting BhashSMS login automation")
        
        # Perform login
        login_success = automation.login(username, password)
        
        if login_success:
            # Capture dashboard content after successful login
            dashboard_data = automation.capture_dashboard_content()
            
            if dashboard_data:
                # Print summary of captured data
                print("\n" + "="*50)
                print(f"Dashboard Title: {dashboard_data['title']}")
                print("="*50)
                print("Dashboard Content Preview (first 500 chars):")
                print("-"*50)
                print(dashboard_data['content'][:500] + "...")
                print("-"*50)
                
                # Print extracted dashboard elements if available
                if "dashboard_data" in dashboard_data and dashboard_data["dashboard_data"]:
                    print("Extracted Dashboard Elements:")
                    print("-"*50)
                    for key, value in dashboard_data["dashboard_data"].items():
                        print(f"{key}: {value}")
                    print("-"*50)
                
                print(f"Full content captured ({len(dashboard_data['content'])} chars)")
                print(f"Screenshot saved as: {dashboard_data['screenshot_path']}")
                print("="*50 + "\n")
            
            logger.info("Automation completed successfully")
        else:
            logger.error("Automation failed: Could not log in")
            
    finally:
        # Always close the browser
        automation.close()


if __name__ == "__main__":
    # If run directly, decide whether to run standalone or as API
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--api":
        # Run as API server
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        # Run standalone automation
        main() 