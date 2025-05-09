from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import restaurants, loyalty, submissions, rewards, audit, spin, referrals, dashboard, admin, analytics, otp, auth
from app.api.endpoints import ordering
from app.models import Base
from app.database import engine
from app.static_server import add_dashboard_static
from app.api.endpoints.timezone_middleware import TimezoneMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Loyalty Backend", version="0.1.0")

# CORS (allow all for now, restrict in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware to convert datetime values to IST in API responses
# Disabled to fix response issues
# app.add_middleware(TimezoneMiddleware)

app.include_router(restaurants.router)
app.include_router(loyalty.router)
app.include_router(submissions.router)
app.include_router(rewards.router)
app.include_router(audit.router)
app.include_router(spin.router)
app.include_router(referrals.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(analytics.router)
app.include_router(otp.router)
app.include_router(auth.router)
app.include_router(ordering.router)

add_dashboard_static(app)

@app.get("/")
def root():
    return {"msg": "Loyalty Backend API running"}
