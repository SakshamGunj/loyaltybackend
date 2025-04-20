# Loyalty Backend

Production-grade backend for a restaurant loyalty, gamification, and referral system.

## Tech Stack
- FastAPI
- SQLite (via SQLAlchemy, DB-agnostic)
- Alembic (migrations)
- JWT Auth (Firebase simulation)
- Modular, scalable, and ready for deployment

## Setup
1. `pip install -r requirements.txt`
2. `uvicorn app.main:app --reload`

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
