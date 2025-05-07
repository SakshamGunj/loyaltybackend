import os
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth, initialize_app
import json
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

# Path to your service account key
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_PATH = os.path.join(BASE_DIR, "key.json")
firebase_key = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")

def initialize_firebase():
    """
    Initialize Firebase Admin SDK using credentials from either:
    1. Environment variable (FIREBASE_SERVICE_ACCOUNT as JSON string)
    2. JSON file path specified in environment variable (FIREBASE_CREDENTIALS_PATH)
    3. Default file path in deploy/firebase-credentials.json
    """
    # Check if app is already initialized
    if firebase_admin._apps:
        logger.info("Firebase already initialized")
        return
    
    # Try environment variable (JSON string)
    cred_json = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    if cred_json:
        try:
            cred_dict = json.loads(cred_json)
            logger.info("Initializing Firebase using FIREBASE_SERVICE_ACCOUNT env variable")
            initialize_app(credentials.Certificate(cred_dict))
            return
        except json.JSONDecodeError:
            logger.warning("Failed to parse FIREBASE_SERVICE_ACCOUNT as JSON")
        except Exception as e:
            logger.warning(f"Error initializing Firebase with env variable: {e}")
    
    # Try file path from environment variable
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    if cred_path and os.path.exists(cred_path):
        try:
            logger.info(f"Initializing Firebase using credentials file: {cred_path}")
            initialize_app(credentials.Certificate(cred_path))
            return
        except Exception as e:
            logger.warning(f"Error initializing Firebase with file {cred_path}: {e}")
    
    # Try default file path
    default_path = os.path.join("deploy", "firebase-credentials.json")
    if os.path.exists(default_path):
        try:
            logger.info(f"Initializing Firebase using default credentials file: {default_path}")
            initialize_app(credentials.Certificate(default_path))
            return
        except Exception as e:
            logger.warning(f"Error initializing Firebase with default file: {e}")
    
    logger.error("Failed to initialize Firebase: No valid credentials found")
    raise ValueError("No valid Firebase credentials found. Please set FIREBASE_SERVICE_ACCOUNT env variable or provide a credentials file.")

def verify_firebase_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        decoded_token = firebase_auth.verify_id_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Firebase token")
    # Extract uid, email, etc.
    return {
        "uid": decoded_token.get("uid"),
        "email": decoded_token.get("email"),
        "role": decoded_token.get("role", "user")  # Optional: add custom claims for role
    }
