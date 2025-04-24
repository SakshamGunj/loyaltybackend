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
  "private_key_id": "c75ac56f4ca8c7ab7d16600285dfd558e64d1069",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDJ/VuhkOPUROOt\neqOI2u6dD0NpwAsYY2Q0UzDa9dsnRTxWUMRMXYfU0wtHiHpkzsMvyfw5cCsIxjYX\nNeaCFpSTfsaJCZ949FxrY3YJ7yBDN9npKMrerxiGWwma0AdPYkk1q5unIEPFVy7g\nv0/BpGOPKLj4zMnxS8v7BWJqBKQRDUHFHoPZxbxig5eVdA03apvc8o9VJ05gJ/d9\n83nY8JFjd2+1YTx+he7ViEPdvJ6R6c0cZ4TKGhKR7lh3omrqCbQleSKdWVJuY28F\njcA5j3lUFyoJwyU0+OSxcWGsPpMqvwRJFfagyuqxrhOlxqXWweA5qDoYFjf/EtcZ\nLXeZhmTLAgMBAAECggEAXRjXKOpc97MgtQ53XVZ68Aze51jKRF1bC/rj46e5cKoq\nmyXys7fQKTl0U24F63yY3efcxqR6UTr6J0yCh6bcp/agjvzOcbM+/YgEGaQLXK/b\nUempR2WwigxfqukC1YXZdFE6Fpd6ZPQ/+Pp0Si34bT05tAK/eOWUiIf8yhyFeg2u\ngzuQ2lxQXi4w/7iAx03oV2aYuowzN9S53Qnyd3M/48AbMzHEJI4I06FFKR8YxjZR\nY9LT/GtLj2s5asILUmQOc5ZwGH0L+JFIt9WARD6tImD7FjzsofiM9cIzaMLLVwj/\nXHnt8fk7TAf5h84AzYHnx9hltEHXHG31pLNubCKYgQKBgQDnLpScOV2dXUKLY9Hr\non4rRq3aVO8l/BEw61WZfjrY7Nw9Q5Hn3B1lEsLvcn1+aM9KNMJma/65bGawBioE\nF7d/woykgqQnAFgnaW+B3hCQeKCue/hcNL/skF5NYoTG3hbx85ittnm5EEm+2EZG\n8WsVk230Rquo02TO9SFfApASYQKBgQDfrIFtzjr59olY9mEfZZNefW2kDs5BI1s5\nNZy2BIUli/sGnflfdoFxfanqGn5IghD4wkjkz5P7x0ec3cmCDpWo2tKPtTMj4+fX\nvtju3N6DsGh8ec7C1yACtBu7HxPAlpc8lBe/xX2+0MYsBbIQUYsoMzOZH4KQ8rfC\nuU1hBZreqwKBgQCqf5IevbgrLPK89ruFO2wt4oypr2ZI72SGXand8FjaT6YGkOT0\nyUPsnS+jhR7EsevfYJXXD+LnQelh/MnUBuHQmd08HxWNphVdy8bvUqWIx05KISgE\naOr7P2YtUHF4cacefnel9iRDtp2M4NjDzZ0aZob7V3uWoYGBmQwplCxJQQKBgAbR\nrYh5dxbTy1ApAsEAScPhswwDX4pg15Eg70wlSyHf6KFFA6tDY6LgH+QBNsRjIr1S\nvwIqyeotIyPHJzON2kYxlaXH8m0vr4vGR7rQhQAiyqyw0frisBklAItt4R5H+Qhh\nw2+XR8QffUsuSUVyFvn8xZ/vc/2TSMLo/1Dr6NLNAoGAGVNQ6gV36TxrqrW8d3cj\nYnTWcGOqni47HVeHmsi/oQiced45laqi9/ZeVItblaR44wHyEpHcMJuMjPIge4at\nmnn55VLarQ0VhkBELbWn2Wc3WBRUZWG7AYvE6BZmPnvtiIs7sQnEiJMbc9uDhEif\n7f4Gnj4uE8lXS6/R4qC7U8s=\n-----END PRIVATE KEY-----\n",
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
