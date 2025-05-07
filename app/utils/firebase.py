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
    cred = credentials.Certificate({
  "type": "service_account",
  "project_id": "spinthewheel-e14a6",
  "private_key_id": "a6572c7004d1d1b130a31c5cff6e994f6486a799",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC715CzA/jT5JO5\ngoU+fZpa6mgTnd15dpC8/UtDk8Nx6rk1QouQHGzN4qKjRM7GFyC5MWWq8hJotY15\nWnBIPTNKaRN/fTXcuOCdzznDsNfhl82zNsycErKuWxjJAB6mxy8HGB+3qiXr5aIo\nuqIj9ugj0SfbLpClWvhUZxWVpczmr9b00mRFD9+OrpbFe8DJhi91yXGqYshqlFuU\ndhmFnUgMwnk4kTirB/sFQaHDRf6wMypSC1zwcQEVMDaNEKv2R1WlN2IiF/bL/8/9\nSxz/4gKE7CCC7OnTSzwjtlPRc5SXwSxhQWBHNPyMdyGIpEB1+mDfXZUxrYUhWyHM\n8itQ6YHJAgMBAAECggEAAXjwHsfpReVmeV95D1eXI6vvWL/ihcyZ+gMi39AmY1V+\nNCG5MCvzRNq/uB4DYFIqheq0ZFzUK9AMpLKG5ygxYy6utTpGcw91VYwknDCZswJ7\nmT8l3osfk+/eolml35gIzyctRe/4lUr53SVvGveyt+ewbPDCDUU7/w6TM/Sczp0Z\no52k5MdrZaJL/oTGKS2cqaEsgEgZLgIsEiSjRXLvAdCkNx22t0fQWm9O3aChQUX+\n1puJW5rUFTa2yziKxgZkFQeP6qD/KUaHE5PpXd2T5Jl9Olfoj4q+sjtBDI63A7OR\nBFAsBJI4v40pp8IK+Ng4fqenTg1HGy2YnO1Em2h+AQKBgQDhAwCkkHTHPJEtFVTW\nj+Qu26Kg98+nFEFobLP1Rh7YutA9R4PfJi94R6YdMRDzTACmnRBZW/qnXo8B5Owf\ntWukNJbHDWvhxx8nDjdZLX+yUfnRBxDnV4jXohK1vvDI5xLD04KqbttMgQz/+hQN\n3Jd42vFQiQEImAaLRkuxdDZKyQKBgQDVthx6FfCHZYcizSVJ+lvK2E7umlbvSPFl\nQ9wdLajZExUtRTa6cEIZHtWMS0wRWEMaXfF4u63pd/mDn+TlvIlIVQXToyNN0Uf4\nig4i9tkRtig9rWAOfBJ4wBaCN97PPJ0B8xX16sTRmpZe/ZVoJp/wuaylv1CbcDBF\nxMKIHA3/AQKBgQC1xMUqK4AKywTEFK1aPxcoO0lfG5Fl+Vj1UIr3otOcZR1/w1vm\nUmSal9a7Uj3NLSKBdfQVG9aaiiqgbxvIabgxCEKdPlxeIYsq87MGmVjE5rAWicy/\n9diXyVev9jVxNinUg/LUV4VUghPMXWsB36eFe+jhFCv/k0AGFp1jFuwc8QKBgEzm\nMK0Fg/1UXSH6q3ZJLgp5dz2IL8v+dU448tVU/rLNmQsnIqBHkKE1ZSYMWhzLo6mz\nMBZ/gf7GevQP7u9zvfpXDbevth5kNf+Kvbd7F3S2FRjMcAoGPydQB0loDTaI2v4+\nmCJbDeNWOtGHceF+NIMMbMFfbAPihJw2RsFvRuIBAoGAKdJdXcGumSAEKmqrc3MZ\nm0FYAy9UAptfl8ZOCGivFc5Ry2ALp6dWFx/1MZml4R0YvZbjTHWus6GlF7hgykQa\nDc78qSnj6rU8VvOkRlpeKRN9FxB91MFa6NkjfQiOi/2Auskqgxn9k+A0OvLzIfoX\nF5ZOpULfbE/7EoRrmJoQ8Ec=\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-fbsvc@spinthewheel-e14a6.iam.gserviceaccount.com",
  "client_id": "116109310815956345340",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40spinthewheel-e14a6.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}


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
