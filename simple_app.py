"""
Simple FastAPI application for Google App Engine
"""
from fastapi import FastAPI
import os
import logging
from typing import Dict, Any

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

@app.get("/")
async def read_root() -> Dict[str, str]:
    return {"message": "Welcome to the Loyalty Backend API", "environment": ENV, "version": VERSION}

@app.get("/health", tags=["health"])
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for monitoring systems.
    """
    return {
        "status": "healthy",
        "version": VERSION,
        "environment": ENV
    }

@app.on_event("startup")
async def startup_event() -> None:
    """Application startup: log information about the environment"""
    logger.info(f"Starting Loyalty Backend API in {ENV} mode (version: {VERSION})")

@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup resources on shutdown"""
    logger.info("Shutting down Loyalty Backend API") 