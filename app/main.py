from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import auth, otp, restaurants, loyalty, rewards, referrals, spin, analytics, dashboard, admin, ordering
from app.utils.bhashsms_instance import bhashsms
import logging
import os
from sqlalchemy import text
from app.database import get_db, engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Get environment variables
ENV = os.getenv("ENVIRONMENT", "development")
VERSION = os.getenv("APP_VERSION", "1.0.0")

app = FastAPI(
    title="Loyalty Backend API",
    description="Backend API for the loyalty program system",
    version=VERSION
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
# app.include_router(loyalty.router, prefix="/api/loyalty", tags=["loyalty"])  # Removed loyalty endpoints
app.include_router(rewards.router, prefix="/api/rewards", tags=["rewards"])
app.include_router(referrals.router, prefix="/api/referrals", tags=["referrals"])
app.include_router(spin.router, prefix="/api/spin", tags=["spin"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(ordering.router, tags=["ordering"])

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Loyalty Backend API", "environment": ENV, "version": VERSION}

@app.get("/health", tags=["health"])
async def health_check(db=Depends(get_db)):
    """
    Health check endpoint for monitoring systems.
    Checks database connectivity and returns service status.
    """
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "version": VERSION,
        "environment": ENV,
        "database": db_status
    }

@app.on_event("startup")
async def startup_event():
    """Application startup: log information about the environment"""
    logger.info(f"Starting Loyalty Backend API in {ENV} mode (version: {VERSION})")
    logger.info(f"Database connection established")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    logger.info("Shutting down Loyalty Backend API")
    try:
        if hasattr(bhashsms, 'driver') and bhashsms.driver:
            bhashsms.driver.quit()
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
