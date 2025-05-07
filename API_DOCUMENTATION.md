# Loyalty Backend API Documentation

This document provides detailed information about the endpoints available in the Loyalty Backend API.

## Base URL

All API endpoints are relative to the base URL:
```
http://[your-deployment-url]/api/
```

## Authentication

Most endpoints require authentication using a Firebase JWT token in the Authorization header:

```
Authorization: Bearer [firebase_id_token]
```

## Table of Contents

1. [Authentication](#authentication-endpoints)
2. [Restaurants](#restaurant-endpoints)
3. [Loyalty](#loyalty-endpoints)
4. [Rewards](#rewards-endpoints)
5. [Referrals](#referral-endpoints)
6. [Ordering](#ordering-endpoints)
7. [Spin](#spin-endpoints)
8. [OTP](#otp-endpoints)
9. [Dashboard](#dashboard-endpoints)

---

## Authentication Endpoints

Endpoints for user authentication and management.

### POST /auth/signup

Creates a new user in Firebase and the local database.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "secure-password",
  "name": "User Name",
  "number": "9876543210"
}
```

**Response:**
```json
{
  "custom_token": "firebase-custom-token",
  "uid": "firebase-user-uid",
  "email": "user@example.com",
  "name": "User Name"
}
```

**Status Codes:**
- 200: Success
- 400: Invalid input or duplicate phone number
- 500: Server error

### POST /auth/login

Authenticates a user with Firebase and returns a JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "secure-password"
}
```

**Response:**
```json
{
  "id_token": "firebase-id-token",
  "refresh_token": "firebase-refresh-token",
  "expires_in": "3600",
  "uid": "firebase-user-uid",
  "email": "user@example.com"
}
```

**Status Codes:**
- 200: Success
- 401: Invalid credentials
- 500: Server error

### POST /auth/verify-token

Verifies a Firebase ID token and returns user info.

**Request Body:**
```json
"firebase-id-token"
```

**Response:**
```json
{
  "uid": "firebase-user-uid",
  "email": "user@example.com"
}
```

**Status Codes:**
- 200: Success
- 401: Invalid token

### DELETE /auth/delete-number

Deletes a verified phone number from the database.

**Query Parameters:**
- `number`: Phone number to delete (string)

**Response:**
```json
{
  "success": true,
  "message": "Number 9876543210 deleted from database."
}
```

**Status Codes:**
- 200: Success
- 400: Invalid phone number format
- 404: Number not found

---

## Restaurant Endpoints

Endpoints for managing restaurant data.

### GET /restaurants

Lists all restaurants.

**Response:**
```json
[
  {
    "restaurant_id": "restaurant-id",
    "name": "Restaurant Name",
    "owner_uid": "owner-uid",
    "admin_uid": "admin-uid",
    "points_per_rupee": 0.1,
    "points_per_spin": 1.0,
    "reward_thresholds": [
      {"name": "Gold", "points": 100}
    ],
    "spend_thresholds": [
      {"amount": 1000, "reward": "Free Dessert"}
    ],
    "offers": ["10% off", "Free drink"],
    "referral_rewards": {"referral_bonus": 50}
  }
]
```

### POST /restaurants

Registers a new restaurant.

**Request Body:**
```json
{
  "restaurant_id": "restaurant-id",
  "name": "Restaurant Name",
  "owner_uid": "owner-uid",
  "admin_uid": "admin-uid",
  "points_per_rupee": 0.1,
  "points_per_spin": 1.0,
  "reward_thresholds": [
    {"name": "Gold", "points": 100}
  ],
  "spend_thresholds": [
    {"amount": 1000, "reward": "Free Dessert"}
  ],
  "offers": ["10% off", "Free drink"],
  "referral_rewards": {"referral_bonus": 50}
}
```

**Response:** Returns the created restaurant object.

**Status Codes:**
- 200: Success
- 400: Invalid input
- 403: Unauthorized

### GET /restaurants/{restaurant_id}

Gets a specific restaurant.

**Path Parameters:**
- `restaurant_id`: Restaurant ID (string)

**Response:** Returns the restaurant object.

**Status Codes:**
- 200: Success
- 404: Restaurant not found

### PUT /restaurants/{restaurant_id}

Updates a restaurant.

**Path Parameters:**
- `restaurant_id`: Restaurant ID (string)

**Request Body:** Same as POST /restaurants

**Response:** Returns the updated restaurant object.

**Status Codes:**
- 200: Success
- 400: Invalid input
- 403: Unauthorized
- 404: Restaurant not found

---

## Loyalty Endpoints

Endpoints for managing user loyalty data.

### GET /loyalty

Gets loyalty data for the current user.

**Query Parameters:**
- `restaurant_id`: Restaurant ID (string)

**Response:**
```json
{
  "uid": "user-uid",
  "restaurant_id": "restaurant-id",
  "restaurant_points": 150,
  "total_points": 500,
  "tier": "Gold",
  "punches": 5,
  "redemption_history": [],
  "visited_restaurants": ["restaurant-id1", "restaurant-id2"],
  "last_spin_time": "2023-10-01T12:00:00Z",
  "spin_history": [],
  "referral_codes": {},
  "referrals_made": [],
  "referred_by": {}
}
```

### POST /loyalty

Creates loyalty data for a user and restaurant.

**Request Body:**
```json
{
  "restaurant_id": "restaurant-id",
  "restaurant_points": 0,
  "total_points": 0,
  "tier": "Bronze",
  "punches": 0
}
```

**Response:** Returns the created loyalty object.

**Status Codes:**
- 200: Success
- 400: Invalid input
- 409: Loyalty data already exists

### PUT /loyalty/{uid}/{restaurant_id}

Updates loyalty data for a user and restaurant.

**Path Parameters:**
- `uid`: User ID (string)
- `restaurant_id`: Restaurant ID (string)

**Request Body:** Same as POST /loyalty

**Response:** Returns the updated loyalty object.

**Status Codes:**
- 200: Success
- 400: Invalid input
- 404: Loyalty data not found

---

## Rewards Endpoints

Endpoints for managing rewards and coupons.

### POST /rewards

Claims a reward.

**Request Body:**
```json
{
  "restaurant_id": "restaurant-id",
  "reward_name": "Free Coffee",
  "threshold_id": 1,
  "whatsapp": "9876543210",
  "user_name": "User Name"
}
```

**Response:**
```json
{
  "id": 1,
  "uid": "user-uid",
  "restaurant_id": "restaurant-id",
  "reward_name": "Free Coffee",
  "coupon_code": "ABC123",
  "claimed_at": "2023-10-01T12:00:00Z",
  "redeemed": false,
  "redeemed_at": null,
  "threshold_id": 1,
  "whatsapp": "9876543210",
  "user_name": "User Name"
}
```

**Status Codes:**
- 200: Success
- 400: Invalid input
- 429: Daily reward claim limit reached

### POST /rewards/validate-coupon

Validates a coupon code.

**Request Body:**
```json
"ABC123"
```

**Response:**
```json
{
  "valid": true,
  "reward": {
    "id": 1,
    "uid": "user-uid",
    "restaurant_id": "restaurant-id",
    "reward_name": "Free Coffee",
    "coupon_code": "ABC123",
    "claimed_at": "2023-10-01T12:00:00Z",
    "redeemed": false,
    "redeemed_at": null,
    "threshold_id": 1,
    "whatsapp": "9876543210",
    "user_name": "User Name"
  }
}
```

**Status Codes:**
- 200: Success
- 404: Coupon not found

### POST /rewards/redeem-coupon

Redeems a coupon code (admin only).

**Request Body:**
```json
"ABC123"
```

**Response:**
```json
{
  "redeemed": true,
  "reward": {
    "id": 1,
    "uid": "user-uid",
    "restaurant_id": "restaurant-id",
    "reward_name": "Free Coffee",
    "coupon_code": "ABC123",
    "claimed_at": "2023-10-01T12:00:00Z",
    "redeemed": true,
    "redeemed_at": "2023-10-02T15:00:00Z",
    "threshold_id": 1,
    "whatsapp": "9876543210",
    "user_name": "User Name"
  }
}
```

**Status Codes:**
- 200: Success
- 400: Coupon already redeemed
- 403: Unauthorized (not admin)
- 404: Coupon not found
- 429: Daily redemption limit exceeded

### GET /rewards

Lists claimed rewards for the current user.

**Query Parameters:**
- `uid`: User ID for admin requests (optional)

**Response:** Array of claimed reward objects.

**Status Codes:**
- 200: Success
- 403: Unauthorized

---

## Referral Endpoints

Endpoints for managing referral codes and bonuses.

### GET /referrals/code

Gets or generates a referral code for the current user.

**Query Parameters:**
- `restaurant_id`: Restaurant ID (string)

**Response:**
```json
{
  "code": "REF123",
  "restaurant_id": "restaurant-id",
  "created_at": "2023-10-01T12:00:00Z"
}
```

### POST /referrals/apply

Applies a referral code for a user.

**Request Body:**
```json
{
  "code": "REF123",
  "restaurant_id": "restaurant-id",
  "extra_data": {"source": "web"}
}
```

**Response:**
```json
{
  "success": true,
  "points_awarded": 50,
  "referrer_uid": "referrer-user-id"
}
```

**Status Codes:**
- 200: Success
- 400: Invalid code or already applied
- 404: Code not found

---

## Ordering Endpoints

Endpoints for managing orders and menu items.

### GET /ordering/menu

Lists menu items for a restaurant.

**Query Parameters:**
- `restaurant_id`: Restaurant ID (string)

**Response:** Array of menu item objects.

### GET /ordering/menu/categories

Lists menu categories for a restaurant.

**Query Parameters:**
- `restaurant_id`: Restaurant ID (string)

**Response:** Array of menu category objects.

### POST /ordering/order

Places a new order.

**Request Body:**
```json
{
  "restaurant_id": "restaurant-id",
  "items": [
    {
      "item_id": 1,
      "quantity": 2
    }
  ],
  "promo_code": "PROMO10",
  "submission": {
    "customer_name": "User Name",
    "customer_phone": "9876543210",
    "delivery_address": "123 Street"
  },
  "claimed_reward": {}
}
```

**Response:** Returns the created order object.

**Status Codes:**
- 200: Success
- 400: Invalid input
- 404: Items not found

### GET /ordering/orders/history

Gets order history for the current user.

**Query Parameters:**
- `restaurant_id`: Filter by restaurant ID (optional)

**Response:** Array of order objects.

### POST /ordering/order/{order_id}/confirm

Confirms an order (admin only).

**Path Parameters:**
- `order_id`: Order ID (integer)

**Query Parameters:**
- `restaurant_id`: Restaurant ID (string)

**Response:** Updated order object.

**Status Codes:**
- 200: Success
- 403: Unauthorized
- 404: Order not found

### POST /ordering/order/{order_id}/cancel

Cancels an order.

**Path Parameters:**
- `order_id`: Order ID (integer)

**Query Parameters:**
- `restaurant_id`: Restaurant ID (string)

**Response:** Updated order object.

**Status Codes:**
- 200: Success
- 403: Unauthorized
- 404: Order not found

### POST /ordering/order/{order_id}/refund

Refunds an order (admin only).

**Path Parameters:**
- `order_id`: Order ID (integer)

**Query Parameters:**
- `restaurant_id`: Restaurant ID (string)

**Response:** Updated order object.

**Status Codes:**
- 200: Success
- 403: Unauthorized
- 404: Order not found

### GET /ordering/orders

Gets all orders for admin.

**Query Parameters:**
- `restaurant_id`: Filter by restaurant ID (optional)

**Response:** Array of order objects.

**Status Codes:**
- 200: Success
- 403: Unauthorized

### GET /ordering/orders/filter

Filters orders by various criteria.

**Query Parameters:**
- `status`: Order status (optional)
- `start_date`: Start date (optional)
- `end_date`: End date (optional)
- `payment_method`: Payment method (optional)
- `user_id`: User ID (optional)
- `order_id`: Order ID (optional)
- `user_email`: User email (optional)
- `user_phone`: User phone (optional)
- `restaurant_id`: Restaurant ID (optional)

**Response:** Array of filtered order objects.

**Status Codes:**
- 200: Success
- 403: Unauthorized

---

## Spin Endpoints

Endpoints for managing loyalty spins.

### POST /spin

Performs a loyalty spin.

**Request Body:**
```json
{
  "restaurant_id": "restaurant-id"
}
```

**Response:**
```json
{
  "success": true,
  "reward": {
    "type": "points",
    "value": 50,
    "message": "You won 50 points!"
  },
  "updated_loyalty": {
    "uid": "user-uid",
    "restaurant_id": "restaurant-id",
    "restaurant_points": 200,
    "total_points": 550,
    "tier": "Gold",
    "last_spin_time": "2023-10-01T15:30:00Z"
  }
}
```

**Status Codes:**
- 200: Success
- 400: Invalid input
- 403: Unauthorized
- 429: Spin cooldown period active

### GET /spin/rewards

Gets available spin rewards.

**Query Parameters:**
- `restaurant_id`: Restaurant ID (string)

**Response:**
```json
[
  {
    "id": 1,
    "type": "points",
    "value": 50,
    "probability": 0.3,
    "message": "You won 50 points!"
  },
  {
    "id": 2,
    "type": "coupon",
    "value": "10PERCENT",
    "probability": 0.2,
    "message": "You won a 10% discount coupon!"
  }
]
```

---

## OTP Endpoints

Endpoints for OTP verification.

### POST /otp/send

Sends an OTP to a phone number.

**Request Body:**
```json
{
  "number": "9876543210"
}
```

**Response:**
```json
{
  "sent": true,
  "message": "OTP sent successfully",
  "session_id": "otp-session-id"
}
```

**Status Codes:**
- 200: Success
- 400: Invalid phone number
- 429: Rate limit exceeded

### POST /otp/verify

Verifies an OTP.

**Request Body:**
```json
{
  "number": "9876543210",
  "otp": "123456"
}
```

**Response:**
```json
{
  "verified": true,
  "message": "OTP verified successfully"
}
```

**Status Codes:**
- 200: Success
- 400: Invalid OTP
- 404: No active OTP session

---

## Dashboard Endpoints

Endpoints for dashboard data.

### GET /dashboard/admin

Gets admin dashboard data.

**Query Parameters:**
- `restaurant_id`: Restaurant ID (optional)

**Response:**
```json
{
  "total_users": 150,
  "active_users": 50,
  "total_orders": 1000,
  "revenue": 50000,
  "recent_orders": [],
  "top_selling_items": [],
  "loyalty_stats": {
    "total_points_issued": 15000,
    "active_coupons": 25
  }
}
```

**Status Codes:**
- 200: Success
- 403: Unauthorized

### GET /dashboard/user

Gets user dashboard data.

**Query Parameters:**
- `uid`: User ID (optional, admin only)

**Response:**
```json
{
  "total_points": 500,
  "active_rewards": 3,
  "visited_restaurants": 5,
  "recent_orders": [],
  "active_coupons": [],
  "tier_progress": {
    "current_tier": "Silver",
    "next_tier": "Gold",
    "points_needed": 50
  }
}
```

**Status Codes:**
- 200: Success
- 403: Unauthorized 