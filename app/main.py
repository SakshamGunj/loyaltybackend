from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import auth, otp, restaurants, loyalty, rewards, referrals, spin, analytics, dashboard, admin, ordering
from app.utils.bhashsms_instance import bhashsms

app = FastAPI(
    title="Loyalty Backend API",
    description="Backend API for the loyalty program system",
    version="1.0.0"
)

# Configure CORS with more specific settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(otp.router, prefix="/api/otp", tags=["otp"])
app.include_router(restaurants.router, prefix="/api/restaurants", tags=["restaurants"])
app.include_router(loyalty.router, prefix="/api/loyalty", tags=["loyalty"])
app.include_router(rewards.router, prefix="/api/rewards", tags=["rewards"])
app.include_router(referrals.router, prefix="/api/referrals", tags=["referrals"])
app.include_router(spin.router, prefix="/api/spin", tags=["spin"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(ordering.router, tags=["ordering"])

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Loyalty Backend API"}

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    try:
        if hasattr(bhashsms, 'driver') and bhashsms.driver:
            bhashsms.driver.quit()
    except Exception:
        pass
