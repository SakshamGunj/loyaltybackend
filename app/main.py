from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import auth, otp, restaurants, loyalty, rewards, referrals, spin, analytics, dashboard, admin, ordering, users, submissions, audit
from app.api.endpoints.timezone_middleware import TimezoneMiddleware
from app.utils.bhashsms_instance import bhashsms

app = FastAPI(
    title="Loyalty Backend API",
    description="Backend API for the loyalty program system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
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

# Add timezone middleware
app.add_middleware(TimezoneMiddleware)

# Include routers - all routers have their own prefixes defined in their modules
app.include_router(auth.router)
app.include_router(otp.router)
app.include_router(restaurants.router)
app.include_router(loyalty.router)
app.include_router(rewards.router)
app.include_router(referrals.router)
app.include_router(spin.router)
app.include_router(analytics.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(ordering.router)
app.include_router(users.router, prefix="/api/users", tags=["users"])  # This router needs prefix
app.include_router(submissions.router)
app.include_router(audit.router)

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
