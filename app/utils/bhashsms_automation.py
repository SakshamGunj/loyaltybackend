from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests
import logging
import time
import random
import string
import os
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from datetime import datetime

# Configure logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Create a log file with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(log_dir, f"bhashsms_{timestamp}.log")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # This will also print to console
    ]
)

logger = logging.getLogger(__name__)
logger.info("=== Starting new BhashSMS session ===")

class BhashSMSAutomation:
    def __init__(self, headless=True):
        """Initialize the BhashSMS automation class."""
        logger.info("Initializing BhashSMS automation")
        self.is_logged_in = False
        self.session = None
        self.username = "TENVERSE_MEDIA"
        self.password = "123456"
        
        # Set up Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        
        # Add options to suppress DevTools and other messages
        chrome_options.add_argument("--log-level=3")  # Only show fatal errors
        chrome_options.add_argument("--silent")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Disable TensorFlow and other unnecessary features
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # Set environment variables to suppress Chrome logging
        os.environ['WDM_LOG_LEVEL'] = '0'
        os.environ['WDM_PRINT_FIRST_LINE'] = 'False'
        
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

    def login(self, username="TENVERSE_MEDIA", password="123456", max_retries=3):
        """Login to BhashSMS with provided credentials."""
        for attempt in range(1, max_retries + 1):
            try:
                # Navigate to the login page
                url = "https://www.bhashsms.com/loginlanding.php"
                logger.info(f"Navigating to {url} (Attempt {attempt}/{max_retries})")
                self.driver.get(url)
                time.sleep(2)  # Wait for page to load
                
                # Find username and password fields using XPath
                username_field = self.driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div/div[2]/form/input[1]")
                password_field = self.driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div/div[2]/form/input[2]")
                
                # Enter credentials
                username_field.clear()
                username_field.send_keys(username)
                password_field.clear()
                password_field.send_keys(password)
                
                # Find and click the login button
                login_button = self.driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div/div[2]/form/input[3]")
                login_button.click()
                
                # Wait for dashboard page to load
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.url_to_be("https://www.bhashsms.com/index.php")
                    )
                    logger.info("Successfully logged in and reached dashboard")
                    
                    # Create session and store cookies
                    self.session = requests.Session()
                    cookies = self.driver.get_cookies()
                    for cookie in cookies:
                        self.session.cookies.set(cookie['name'], cookie['value'])
                    
                    self.is_logged_in = True
                    return True
                except TimeoutException:
                    if attempt < max_retries:
                        logger.info(f"Retrying login (Attempt {attempt+1}/{max_retries})")
                        time.sleep(2)
                    else:
                        logger.error(f"Failed to login after {max_retries} attempts")
                        self.is_logged_in = False
                        return False
                    
            except Exception as e:
                logger.error(f"Login failed: {e}")
                if attempt < max_retries:
                    time.sleep(2)
                else:
                    self.is_logged_in = False
                    return False
        
        return False

    def get_session(self):
        """Get authenticated session, login if not already logged in"""
        if not self.is_logged_in or not self.session:
            if not self.login():
                return None
        return self.session

    def send_whatsapp_message(self, phone_number: str, parameters: str, template_message: str = None):
        """
        Send a WhatsApp message using the authenticated session
        
        Args:
            phone_number (str): 10-digit phone number
            parameters (str): Comma-separated parameters for template
            template_message (str, optional): Custom template message
        """
        try:
            logger.info("=== Starting WhatsApp Message Send Process ===")
            logger.info(f"Input parameters - Phone: {phone_number}, Parameters: {parameters}, Template: {template_message}")

            # First verify login using Selenium
            logger.info("Verifying login using Selenium...")
            try:
                # Navigate to login page
                url = "https://bhashsms.com/loginlanding.php"
                logger.info(f"Navigating to {url}")
                self.driver.get(url)
                time.sleep(2)  # Wait for page to load

                # Find and fill username
                logger.info("Finding username field...")
                username_field = self.driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div/div[2]/form/input[1]")
                username_field.clear()
                username_field.send_keys("TENVERSE_MEDIA")
                logger.info("Username filled")

                # Find and fill password
                logger.info("Finding password field...")
                password_field = self.driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div/div[2]/form/input[2]")
                password_field.clear()
                password_field.send_keys("123456")
                logger.info("Password filled")

                # Find and click login button
                logger.info("Finding login button...")
                login_button = self.driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div/div[2]/form/input[3]")
                login_button.click()
                logger.info("Login button clicked - waiting for redirect...")
                
                # Wait for redirect to complete
                time.sleep(5)  # Give time for redirect
                
                # Check if we're on the dashboard
                current_url = self.driver.current_url
                logger.info(f"Current URL after login: {current_url}")
                
                if "index.php" in current_url:
                    logger.info("Successfully logged in and reached dashboard")
                    
                    # Create new session and store cookies
                    self.session = requests.Session()
                    cookies = self.driver.get_cookies()
                    for cookie in cookies:
                        self.session.cookies.set(cookie['name'], cookie['value'])
                    
                    self.is_logged_in = True
                    logger.info("Session created and cookies stored")
                    print("Login successful!")  # Print login status
                else:
                    logger.error(f"Failed to reach dashboard. Current URL: {current_url}")
                    print("Login failed!")  # Print login status
                    return {
                        "success": False,
                        "message": "Failed to verify login"
                    }

            except Exception as e:
                logger.error(f"Error during Selenium login verification: {str(e)}", exc_info=True)
                print(f"Login error: {str(e)}")  # Print login error
                return {
                    "success": False,
                    "message": f"Error during login verification: {str(e)}"
                }

            # Now proceed with sending WhatsApp message using the stored session
            logger.info("Proceeding with WhatsApp message sending...")
            
            # Clean and validate phone number
            logger.info("Cleaning and validating phone number...")
            number = self.clean_number(phone_number)
            if not number:
                logger.error(f"Invalid phone number format: {phone_number}")
                return {
                    "success": False,
                    "message": "Invalid phone number. Please provide a valid 10-digit Indian mobile number without country code."
                }
            logger.info(f"Cleaned phone number: {number}")

            # Prepare the payload
            logger.info("Preparing request payload...")
            payload = {
                "parameters": parameters,
                "numbers": number,
                "submitc": "Send Single WA",
                "dtype": "markee",
                "stype": "text",
                "tmessage": template_message or "Hi {{1}},\nAsha from Paddington this side,\n{{2}}.",
                "tai": "1",
                "cano": "1"
            }
            logger.info(f"Payload prepared: {payload}")

            # Make the request
            url = "https://bhashsms.com/pushwa/iframe/singlewa.php"
            logger.info(f"Sending POST request to {url}")
            logger.info(f"Request headers: {dict(self.session.headers)}")
            logger.info(f"Request cookies: {dict(self.session.cookies)}")
            
            response = self.session.post(
                url,
                data=payload,
                timeout=30
            )
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")

            # Check response
            if response.status_code == 200:
                logger.info("Received 200 OK response")
                logger.info(f"Response content: {response.text[:500]}")  # Log first 500 chars of response
                
                if "msgsentsuccess.php" in response.text:
                    logger.info(f"Successfully sent WhatsApp message to {number}")
                    return {
                        "success": True,
                        "message": "WhatsApp message sent successfully",
                        "panel_status": response.status_code,
                        "panel_response": "Message sent successfully"
                    }
                else:
                    logger.error(f"Failed to send WhatsApp message to {number}")
                    logger.error(f"Response content: {response.text[:500]}")
                    return {
                        "success": False,
                        "message": "Failed to send WhatsApp message",
                        "panel_status": response.status_code,
                        "panel_response": response.text[:200]
                    }
            else:
                logger.error(f"API request failed with status code {response.status_code}")
                logger.error(f"Response content: {response.text[:500]}")
                return {
                    "success": False,
                    "message": f"API request failed with status code {response.status_code}",
                    "panel_status": response.status_code,
                    "panel_response": response.text[:200]
                }

        except Exception as e:
            logger.error(f"Error in process: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Error in process: {str(e)}"
            }
        finally:
            logger.info("=== WhatsApp Message Send Process Completed ===")

    def send_otp(self, phone_number: str):
        """
        Send OTP via WhatsApp using the authenticated session
        
        Args:
            phone_number (str): 10-digit phone number
        """
        try:
            # Get authenticated session
            session = self.get_session()
            if not session:
                return {
                    "success": False,
                    "message": "Failed to get authenticated session"
                }

            # Clean and validate phone number
            number = self.clean_number(phone_number)
            if not number:
                return {
                    "success": False,
                    "message": "Invalid phone number. Please provide a valid 10-digit Indian mobile number without country code."
                }

            # Generate OTP
            otp = ''.join(random.choices(string.digits, k=4))

            # Send OTP via WhatsApp
            url = f"http://bhashsms.com/api/sendmsg.php?user={self.username}&pass={self.password}&sender=BUZWAP&phone={number}&text=otp_auth&priority=wa&stype=auth&Params={otp}"
            response = session.get(url, timeout=10)
            
            if response.status_code == 200 and 'error' not in response.text.lower():
                return {
                    "success": True,
                    "message": "OTP sent successfully",
                    "panel_status": response.status_code,
                    "panel_response": response.text,
                    "otp": otp  # Only for testing, remove in production
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to send OTP",
                    "panel_status": response.status_code,
                    "panel_response": response.text
                }

        except Exception as e:
            logger.error(f"Error sending OTP: {str(e)}")
            return {
                "success": False,
                "message": f"Error sending OTP: {str(e)}"
            }

    @staticmethod
    def clean_number(number: str) -> str:
        """Clean and validate phone number"""
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