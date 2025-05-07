# Loyalty Backend

This is a FastAPI-based loyalty backend system that includes authentication, ordering, loyalty points, referrals, and rewards.

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL (for production) or SQLite (for development)
- Firebase project

### Installation

1. Clone the repository
   ```
   git clone https://github.com/yourusername/loyaltybackend.git
   cd loyaltybackend
   ```

2. Install dependencies
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables (see Configuration section)

4. Run migrations
   ```
   alembic upgrade head
   ```

5. Start the server
   ```
   uvicorn app.main:app --reload --port 8090
   ```

## Configuration

Copy the `env.example` file to `.env` and update the values:

```
cp env.example .env
```

### Important: Managing Firebase Credentials Securely

There are several secure ways to provide Firebase credentials to the application:

1. **Environment Variable (recommended for production)**
   - Export your Firebase service account JSON as a string in the FIREBASE_SERVICE_ACCOUNT environment variable
   - For local development, store this in your `.env` file
   - For deployment, use secret management services like:
     - Google Cloud Secret Manager
     - GitHub Secrets (for GitHub Actions)
     - Environment variables in your hosting platform

2. **Path to Credentials File**
   - Set FIREBASE_CREDENTIALS_PATH to point to a local file
   - Ensure this file is in `.gitignore` to prevent accidental commits
   - For deployment, mount this file as a volume or secret

3. **Default Location (not recommended for production)**
   - Store the file at `deploy/firebase-credentials.json`
   - Ensure this file is in `.gitignore`

**NEVER commit Firebase credential files to version control!**

## API Documentation

For detailed API documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

## Deployment

For deployment instructions, see [deploy/README.md](deploy/README.md).

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Tech Stack
- FastAPI
- SQLite (via SQLAlchemy, DB-agnostic)
- Alembic (migrations)
- JWT Auth (Firebase simulation)
- Modular, scalable, and ready for deployment

## Project Structure
See `/app` for code modules.

---

## Features
- Restaurant management
- Loyalty engine
- Rewards & redemptions
- Spin game
- Referral system
- User/Admin dashboards
- Analytics & audit logs

---

## ENV
Create a `.env` file for secrets/config.

---

# API Documentation

This section details all backend endpoints, their payloads, and response schemas. Use this as a reference for frontend integration.

## Authentication
All endpoints (except OTP) require a valid JWT in the `Authorization` header: `Bearer <token>`.

---

## Restaurants

### Register Restaurant
- **POST** `/api/restaurants/register-restaurant`
- **Payload:**
```json
{
  "restaurant_name": "string",
  "offers": ["string"],
  "points_per_rupee": float,
  "points_per_spin": float,
  "reward_thresholds": [{"points": int, "reward": "string"}],
  "spend_thresholds": [{"amount": float, "reward": "string"}],
  "referral_rewards": {"type": "string", ...},
  "owner_uid": "string",
  "admin_uid": "string"
}
```
- **Response:**
```json
{
  "restaurant_id": "string",
  "restaurant_name": "string",
  "offers": ["string"],
  "points_per_rupee": float,
  "points_per_spin": float,
  "reward_thresholds": [...],
  "spend_thresholds": [...],
  "referral_rewards": {...},
  "owner_uid": "string",
  "admin_uid": "string",
  "created_at": "datetime"
}
```

### Get All Restaurants
- **GET** `/api/restaurants/`
- **Response:** List of Restaurant objects (see above).

### Get Restaurant by ID
- **GET** `/api/restaurants/{restaurant_id}`
- **Response:** Restaurant object.

### Update Restaurant
- **PUT** `/api/restaurants/{restaurant_id}`
- **Payload:** Same as Register Restaurant.
- **Response:** Updated Restaurant object.

---

## Loyalty

### Create Loyalty Record
- **POST** `/api/loyalty/`
- **Payload:**
```json
{
  "uid": "string",
  "restaurant_id": "string",
  "total_points": int,
  "restaurant_points": int,
  "tier": "string",
  "punches": int,
  "redemption_history": [],
  "visited_restaurants": [],
  "last_spin_time": "datetime",
  "spin_history": [],
  "referral_codes": {},
  "referrals_made": [],
  "referred_by": {}
}
```
- **Response:** Loyalty object (same as above).

### Get Loyalty
- **GET** `/api/loyalty/{uid}/{restaurant_id}`
- **Response:** Loyalty object.

### List Loyalties
- **GET** `/api/loyalty/?uid={uid}`
- **Response:** List of Loyalty objects.

---

## Submissions

### Create Submission
- **POST** `/api/submissions/`
- **Payload:**
```json
{
  "uid": "string",
  "restaurant_id": "string",
  "amount_spent": float,
  "points_earned": int
}
```
- **Response:** Submission object.

### Get Submission
- **GET** `/api/submissions/{submission_id}`
- **Response:** Submission object.

### List Submissions
- **GET** `/api/submissions/?uid={uid}`
- **Response:** List of Submission objects.

---

## Rewards

### Claim Reward
- **POST** `/api/rewards/`
- **Payload:**
```json
{
  "restaurant_id": "string",
  "reward_name": "string",
  "threshold_id": int,
  "whatsapp_number": "string",
  "user_name": "string"
}
```
- **Response:**
```json
{
  "id": int,
  "uid": "string",
  "restaurant_id": "string",
  "reward_name": "string",
  "threshold_id": int,
  "whatsapp_number": "string",
  "user_name": "string",
  "claimed_at": "datetime",
  "redeemed": bool,
  "redeemed_at": "datetime",
  "coupon_code": "string"
}
```

### Validate Coupon
- **POST** `/api/rewards/validate-coupon`
- **Payload:**
```json
{
  "coupon_code": "string"
}
```
- **Response:**
```json
{
  "valid": true,
  "reward": { ...claimed reward object... }
}
```

### Redeem Coupon
- **POST** `/api/rewards/redeem-coupon`
- **Payload:**
```json
{
  "coupon_code": "string"
}
```
- **Response:**
```json
{
  "redeemed": true,
  "reward": { ...claimed reward object... }
}
```

### List Claimed Rewards
- **GET** `/api/rewards/?uid={uid}`
- **Response:** List of ClaimedReward objects.

### Get Claimed Reward
- **GET** `/api/rewards/{reward_id}`
- **Response:** ClaimedReward object.

---

## Spin

### Spin Wheel
- **POST** `/api/spin/wheel`
- **Payload:**
```json
{
  "uid": "string",
  "restaurant_id": "string"
}
```
- **Response:**
```json
{
  "result": {"type": "points"|"offer"|..., "value": int|string},
  "loyalty": { ...loyalty object... }
}
```

---

## Referrals

### Get Referral Code
- **GET** `/api/referrals/code?uid={uid}&restaurant_id={restaurant_id}`
- **Response:**
```json
{
  "referral_code": "string"
}
```

### Apply Referral
- **POST** `/api/referrals/apply`
- **Payload:**
```json
{
  "referral_code": "string",
  "referred_uid": "string",
  "restaurant_id": "string"
}
```
- **Response:**
```json
{
  "msg": "Referral applied",
  "referrer": "string",
  "referred": "string"
}
```

---

## OTP (Phone Auth)

### Send OTP
- **POST** `/api/otp/send`
- **Payload:**
```json
{
  "number": "string"
}
```
- **Response:**
```json
{
  "success": true|false,
  "message": "string",
  "panel_status": int,
  "panel_response": "string"
}
```

### Verify OTP
- **POST** `/api/otp/verify`
- **Payload:**
```json
{
  "number": "string",
  "otp": "string"
}
```
- **Response:**
```json
{
  "success": true|false,
  "message": "string"
}
```

---

## Dashboards

### User Dashboard
- **GET** `/api/userdashboard/?uid={uid}`
- **Response:**
```json
{
  "dashboard": [ ...summary objects... ],
  "loyalties": [ ... ],
  "submissions": [ ... ],
  "claimed_rewards": [ ... ],
  "audit_logs": [ ... ]
}
```

### Admin Dashboard
- **GET** `/admin/?restaurant_id={restaurant_id}`
- **Response:**
```json
{
  "users": [ ...loyalties... ],
  "submissions": [ ... ],
  "claimed_rewards": [ ... ],
  "audit_logs": [ ... ]
}
```

### Admin User Detail
- **GET** `/admin/{restaurant_id}/user/{uid}`
- **Response:**
```json
{
  "loyalty": { ... },
  "claimed_rewards": [ ... ],
  "submissions": [ ... ]
}
```

---

## Analytics

### Referral Analytics
- **GET** `/api/analytics/referral-analytics?restaurant_id={restaurant_id}`
- **Response:**
```json
{
  "total_referrals": int,
  "coupons_issued": int,
  "rewards_used": int
}
```

### Referral Leaderboard
- **GET** `/api/analytics/referral-leaderboard?restaurant_id={restaurant_id}`
- **Response:**
```json
[
  { "uid": "string", "referrals": int }
]
```

---

## Audit Logs

### Create Audit Log
- **POST** `/api/audit/`
- **Payload:**
```json
{
  "user_id": "string",
  "action": "string",
  "details": { ... },
  "timestamp": "datetime"
}
```
- **Response:** AuditLog object.

### List Audit Logs
- **GET** `/api/audit/?uid={uid}`
- **Response:** List of AuditLog objects.

---

## Data Types
- All timestamps are ISO 8601 strings.
- All IDs (`uid`, `restaurant_id`, etc.) are strings unless otherwise noted.
- All lists/objects follow the schemas in `app/schemas.py`.

---

For any questions or to see an example payload/response for a specific endpoint, please refer to the backend code or ask the backend team.

# BhashSMS Web Automation

This script automates the login process for the BhashSMS portal and captures dashboard content.

## Features

- Automated login to BhashSMS portal
- Dashboard content capture
- Screenshot functionality
- Detailed logging
- REST API integration for headless operation

## Prerequisites

- Python 3.6+
- Chrome browser installed
- ChromeDriver (will be automatically managed)

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Standalone Mode

Run the script directly for a one-time automation:

```bash
python bhashsms_automation.py
```

By default, the script:
1. Opens Chrome browser in headless mode
2. Navigates to BhashSMS login page
3. Logs in with the credentials defined in the script
4. Captures the dashboard content
5. Takes a screenshot
6. Saves logs to bhashsms_automation.log

### API Mode

Run the script as an API server:

```bash
python bhashsms_automation.py --api
```

This starts a FastAPI server on port 8000 with the following endpoints:

- `GET /` - Check if the API is running
- `POST /api/bhashsms/login` - Trigger a login operation (runs in background)
- `GET /api/bhashsms/status` - Check the status of the latest run
- `GET /api/bhashsms/screenshot` - Get the latest screenshot

#### API Usage Example

```bash
# Trigger a login operation
curl -X POST http://localhost:8000/api/bhashsms/login \
  -H "Content-Type: application/json" \
  -d '{"username": "TENVERSE_MEDIA", "password": "123456"}'

# Check status
curl http://localhost:8000/api/bhashsms/status

# Get screenshot (download)
curl http://localhost:8000/api/bhashsms/screenshot --output screenshot.png
```

## Configuration

To modify the behavior, edit the `bhashsms_automation.py` file:

- Change credentials in the `main()` function for standalone mode
- Set `headless=False` in `BhashSMSAutomation()` if you want to see the browser (standalone mode only)
- Modify XPaths if the website structure changes

## Output

The script generates:
- Console output showing login status and dashboard content preview
- Log file (`bhashsms_automation.log`) with detailed execution information
- Screenshots with timestamps (`bhashsms_dashboard_YYYYMMDD_HHMMSS.png`)
- Result JSON files with extracted data (`bhashsms_result_YYYYMMDD_HHMMSS.json`)

## Integration with Other Systems

The API mode allows you to integrate this automation with other systems:

- Call the API endpoints from your own application
- Schedule regular runs using cron or similar tools
- Build a frontend to display results

## Troubleshooting

If you encounter issues:
1. Check that Chrome is installed and up to date
2. Verify your internet connection
3. Make sure the provided credentials are correct
4. Review the log file for error messages
5. For API mode, check the returned status messages

## Note

This script is for educational purposes. Use responsibly and in accordance with BhashSMS terms of service.
