from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import logging

logger = logging.getLogger(__name__)

# Check if running in Google Cloud environment
is_cloud_run = os.getenv("K_SERVICE") is not None

# Default to SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./loyalty.db")

# Special handling for Google Cloud SQL if detected
if is_cloud_run:
    logger.info("Running in Google Cloud environment, configuring Cloud SQL")
    cloud_sql_connection_name = os.getenv("CLOUD_SQL_CONNECTION_NAME")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    db_name = os.getenv("DB_NAME", "loyalty")
    
    if cloud_sql_connection_name and db_user and db_pass:
        socket_path = f"/cloudsql/{cloud_sql_connection_name}"
        
        # PostgreSQL connection string for Cloud SQL using Unix socket
        DATABASE_URL = f"postgresql://{db_user}:{db_pass}@/{db_name}?host={socket_path}"
        logger.info(f"Using Cloud SQL connection: {DATABASE_URL.replace(db_pass, '****')}")
    else:
        logger.warning("Cloud SQL environment variables not found, falling back to SQLite")

# Configuration options
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    logger.info("Using SQLite database")
else:
    logger.info(f"Using database: {DATABASE_URL.split('@')[0]}")

# Create engine and session
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
