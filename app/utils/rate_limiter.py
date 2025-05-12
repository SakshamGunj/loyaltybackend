from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict

class SimpleRateLimiter:
    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period
        self.history = defaultdict(list)

    def is_allowed(self, key: str):
        now = time.time()
        window = now - self.period
        self.history[key] = [t for t in self.history[key] if t > window]
        if len(self.history[key]) >= self.calls:
            return False
        self.history[key].append(now)
        return True

rate_limiter_spin = SimpleRateLimiter(3, 24*3600)  # 3 spins per 24h
rate_limiter_referral = SimpleRateLimiter(5, 3600)  # 5 referrals per hour
rate_limiter_referral_total = SimpleRateLimiter(10, 365*24*3600)  # 10 per year (per restaurant)
rate_limiter_redeem_coupon = SimpleRateLimiter(1, 24*3600)  # 1 redemption per 24h (per user per restaurant)
