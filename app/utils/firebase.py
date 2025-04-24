import os
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
security = HTTPBearer()

# Path to your service account key
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_PATH = os.path.join(BASE_DIR, "key.json")
firebase_key = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")

# Initialize Firebase app if not already initialized
if not firebase_admin._apps:
    cred = credentials.Certificate(
)
    firebase_admin.initialize_app(cred)

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
