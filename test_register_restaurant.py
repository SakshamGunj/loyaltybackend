import requests
import json

# Update this if your server runs elsewhere
BASE_URL = "http://localhost:8080"
REGISTER_URL = f"{BASE_URL}/api/restaurants/register-restaurant"

# Replace this token with a valid admin JWT if your endpoint requires authentication
ADMIN_JWT = "REPLACE_WITH_VALID_ADMIN_JWT"

headers = {
    "Authorization": f"Bearer {ADMIN_JWT}",
    "Content-Type": "application/json"
}

payload = {
    "restaurant_name": "Test Restaurant",
    "offers": ["10% off", "Free drink"],
    "points_per_rupee": 1.5,
    "reward_thresholds": {"10": "Free Coffee", "20": "Free Dessert"},
    "referral_rewards": {"ref1": {"points": 10}},
    "owner_uid": "test_owner_uid"
}

response = requests.post(REGISTER_URL, headers=headers, data=json.dumps(payload))

print("Status Code:", response.status_code)
print("Response Body:", response.text)
