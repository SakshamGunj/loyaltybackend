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
import pickle  # For saving cookies
import requests  # For making HTTP requests

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
                    # After successful login, save cookies and session
                    self.save_cookies()
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
    
    def get_cookies_dict(self):
        """Get cookies as a dictionary for API requests."""
        if not hasattr(self, 'driver'):
            logger.error("No WebDriver available to get cookies")
            return {}
            
        try:
            cookies_dict = {}
            selenium_cookies = self.driver.get_cookies()
            
            for cookie in selenium_cookies:
                cookies_dict[cookie['name']] = cookie['value']
                
            return cookies_dict
        except Exception as e:
            logger.error(f"Error getting cookies as dictionary: {e}")
            return {}
    
    def save_cookies(self):
        """Save the browser's cookies and session information."""
        try:
            # Get cookies from the WebDriver
            cookies = self.driver.get_cookies()
            cookies_dict = self.get_cookies_dict()
            
            # Get session details
            session_storage = self.driver.execute_script("return window.sessionStorage;")
            local_storage = self.driver.execute_script("return window.localStorage;")
            
            # Extract current URL and headers
            current_url = self.driver.current_url
            
            # Create a session info dictionary
            session_info = {
                "cookies": cookies,
                "cookies_dict": cookies_dict,
                "session_storage": session_storage,
                "local_storage": local_storage,
                "current_url": current_url,
                "timestamp": datetime.now().isoformat()
            }
            
            # Save to file
            filename = "bhashsms_session.json"
            with open(filename, "w") as f:
                json.dump(session_info, f, indent=2, default=str)
                
            # Save cookies in pickle format (can be loaded directly into requests)
            pickle_filename = "bhashsms_cookies.pkl"
            with open(pickle_filename, "wb") as f:
                pickle.dump(cookies, f)
                
            logger.info(f"Saved session information to {filename} and {pickle_filename}")
            
            # Print cookies and session to console
            print("\n" + "="*50)
            print("COOKIES AND SESSION INFORMATION")
            print("="*50)
            print("\nCookies (dictionary format for API requests):")
            print("-"*50)
            for cookie_name, cookie_value in cookies_dict.items():
                print(f"{cookie_name}: {cookie_value}")
            
            print("\nFull Session Information saved to:")
            print(f"- {filename} (JSON format)")
            print(f"- {pickle_filename} (Pickle format for direct loading)")
            print("="*50 + "\n")
            
            return cookies_dict
        except Exception as e:
            logger.error(f"Error saving cookies and session information: {e}")
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

    def send_whatsapp_message(self, phone_number, template_code="7854", template_message="{{1}} Your Auth Otp", dtype="authh", stype="text", tai="1", cano="1"):
        """
        Send a WhatsApp message using captured cookies.
        
        Args:
            phone_number (str): Phone number to send WhatsApp to (without country code)
            template_code (str): Template code to use
            template_message (str): Template message with variables
            dtype (str): Message type
            stype (str): Sending type
            tai (str): Template attribute ID
            cano (str): Campaign number
            
        Returns:
            dict: Response information
        """
        try:
            if not hasattr(self, 'driver'):
                logger.error("No active session to send WhatsApp message")
                return {"success": False, "message": "No active session"}
            
            logger.info(f"Sending WhatsApp message to {phone_number}")
            
            # Get cookies for authentication
            cookies = self.get_cookies_dict()
            if not cookies:
                logger.error("No cookies available to authenticate request")
                return {"success": False, "message": "No cookies available"}
            
            # Prepare URL and headers
            url = "https://bhashsms.com/pushwa/iframe/singlewa.php"
            
            headers = {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "accept-encoding": "gzip, deflate, br, zstd",
                "accept-language": "en-US,en;q=0.9",
                "cache-control": "max-age=0",
                "connection": "keep-alive",
                "origin": "https://bhashsms.com",
                "referer": "https://bhashsms.com/pushwa/iframe/singlewa.php",
                "sec-ch-ua": "\"Google Chrome\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"Windows\"",
                "sec-fetch-dest": "iframe",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "same-origin",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
            }
            
            # Prepare form data
            form_data = {
                "parameters": template_code,
                "numbers": phone_number,
                "submitc": "Send Single WA",
                "dtype": dtype,
                "stype": stype,
                "tmessage": template_message,
                "tai": tai,
                "cano": cano
            }
            
            # Two approaches - using requests directly with cookies or via Selenium
            
            # Approach 1: Using requests library with cookies
            try:
                logger.info(f"Sending WhatsApp message to {phone_number} using requests")
                response = requests.post(
                    url,
                    data=form_data,
                    cookies=cookies,
                    headers=headers
                )
                
                # Check for successful redirect
                success = False
                message = "Unknown status"
                
                if "msgsentsuccess.php" in response.text:
                    success = True
                    message = "Message sent successfully"
                    logger.info(f"WhatsApp message sent successfully to {phone_number}")
                else:
                    logger.warning(f"WhatsApp message may have failed for {phone_number}: {response.text[:200]}")
                
                return {
                    "success": success,
                    "message": message,
                    "status_code": response.status_code,
                    "response_text": response.text[:500] + "..." if len(response.text) > 500 else response.text
                }
                
            except Exception as e:
                logger.error(f"Error sending WhatsApp message via requests: {e}")
                
                # Fall back to Selenium approach if requests fails
                logger.info("Falling back to Selenium approach")
            
            # Approach 2: Using Selenium directly
            # Navigate to the form page
            self.driver.get(url)
            time.sleep(2)
            
            try:
                # Fill out the form
                self.driver.find_element(By.NAME, "parameters").value = template_code
                self.driver.find_element(By.NAME, "numbers").clear()
                self.driver.find_element(By.NAME, "numbers").send_keys(phone_number)
                self.driver.find_element(By.NAME, "dtype").value = dtype
                self.driver.find_element(By.NAME, "stype").value = stype
                self.driver.find_element(By.NAME, "tmessage").value = template_message
                self.driver.find_element(By.NAME, "tai").value = tai
                self.driver.find_element(By.NAME, "cano").value = cano
                
                # Submit the form
                submit_button = self.driver.find_element(By.NAME, "submitc")
                submit_button.click()
                
                # Wait for response or redirect
                time.sleep(3)
                
                # Check for success
                current_url = self.driver.current_url
                if "msgsentsuccess.php" in current_url:
                    logger.info(f"WhatsApp message sent successfully to {phone_number}")
                    return {
                        "success": True,
                        "message": "Message sent successfully",
                        "current_url": current_url
                    }
                else:
                    logger.warning(f"WhatsApp message may have failed for {phone_number}")
                    return {
                        "success": False,
                        "message": "Message may have failed",
                        "current_url": current_url,
                        "page_source": self.driver.page_source[:500] + "..." if len(self.driver.page_source) > 500 else self.driver.page_source
                    }
                    
            except Exception as e:
                logger.error(f"Error sending WhatsApp message via Selenium: {e}")
                return {"success": False, "message": f"Error: {str(e)}"}
                
        except Exception as e:
            logger.error(f"Error in send_whatsapp_message: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}

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
    cookies: dict = None

class WhatsAppMessageRequest(BaseModel):
    phone_number: str
    template_code: str = "7854"
    template_message: str = "{{1}} Your Auth Otp"
    dtype: str = "authh"
    stype: str = "text"
    tai: str = "1"
    cano: str = "1"

class WhatsAppMessageResponse(BaseModel):
    success: bool
    message: str
    details: dict = None

# Global variables to track the latest automation run
latest_screenshot = None
latest_run_time = None
latest_run_status = "Not run"
latest_cookies = None
latest_automation = None  # Keep a reference to the latest automation instance

# Function to run in background
async def run_automation(username: str, password: str, headless: bool = True):
    global latest_screenshot, latest_run_time, latest_run_status, latest_cookies, latest_automation
    
    latest_run_status = "In progress"
    latest_run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        automation = BhashSMSAutomation(headless=headless)
        latest_automation = automation  # Store the automation instance globally
        
        try:
            logger.info(f"Starting BhashSMS login automation for user {username}")
            
            # Perform login
            login_success = automation.login(username, password)
            
            if login_success:
                # Get and save cookies
                latest_cookies = automation.get_cookies_dict()
                
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
                        "screenshot_path": dashboard_data.get("screenshot_path"),
                        "cookies": latest_cookies
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
            # Don't close the browser here - we want to keep it active for further requests
            # We'll close it when the application shuts down
            pass
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
        "screenshot_available": latest_screenshot is not None,
        "cookies_available": latest_cookies is not None
    })

@app.get("/api/bhashsms/cookies")
async def bhashsms_cookies():
    """Get the latest cookies."""
    if latest_cookies:
        return JSONResponse(latest_cookies)
    else:
        raise HTTPException(status_code=404, detail="No cookies available")

@app.get("/api/bhashsms/screenshot")
async def bhashsms_screenshot():
    """Get the latest screenshot."""
    if latest_screenshot and os.path.exists(latest_screenshot):
        return FileResponse(latest_screenshot)
    else:
        raise HTTPException(status_code=404, detail="No screenshot available")

@app.post("/api/bhashsms/send-whatsapp", response_model=WhatsAppMessageResponse)
async def send_whatsapp_message(message_data: WhatsAppMessageRequest):
    """
    Send a WhatsApp message using the BhashSMS platform.
    Requires a successful login first.
    """
    global latest_automation, latest_cookies
    
    if latest_automation is None:
        raise HTTPException(status_code=400, detail="No active session. Please login first.")
    
    if latest_run_status != "Success":
        raise HTTPException(status_code=400, detail=f"Login is not successful. Current status: {latest_run_status}")
    
    try:
        result = latest_automation.send_whatsapp_message(
            phone_number=message_data.phone_number,
            template_code=message_data.template_code,
            template_message=message_data.template_message,
            dtype=message_data.dtype,
            stype=message_data.stype,
            tai=message_data.tai,
            cano=message_data.cano
        )
        
        return {
            "success": result.get("success", False),
            "message": result.get("message", "Unknown result"),
            "details": result
        }
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send WhatsApp message: {str(e)}")

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
                
                # Example: Send a WhatsApp message
                phone_number = "7250504240"  # As requested in the prompt
                print(f"\nSending WhatsApp message to {phone_number}...\n")
                
                result = automation.send_whatsapp_message(
                    phone_number=phone_number,
                    template_code="7854",
                    template_message="{{1}} Your Auth Otp",
                    dtype="authh",
                    stype="text",
                    tai="1",
                    cano="1"
                )
                
                print("\n" + "="*50)
                print("WhatsApp Message Result:")
                print("="*50)
                print(f"Success: {result.get('success', False)}")
                print(f"Message: {result.get('message', 'Unknown')}")
                
                if 'response_text' in result:
                    print("\nResponse Preview:")
                    print("-"*50)
                    print(result['response_text'][:200] + "..." if len(result['response_text']) > 200 else result['response_text'])
                    
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
        try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
        finally:
            # Clean up resources when the application exits
            if latest_automation:
                logger.info("Closing automation resources")
                latest_automation.close()
    else:
        # Run standalone automation
        main() 