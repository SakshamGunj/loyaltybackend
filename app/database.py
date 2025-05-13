from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Base directory for the application
BASE_DIR = Path(__file__).resolve().parent.parent

# Check if running in cloud environments
is_cloud_run = os.getenv("K_SERVICE") is not None
is_koyeb = os.getenv("KOYEB_APP_NAME") is not None

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
elif is_koyeb:
    logger.info("Running in Koyeb environment")
    # For Koyeb, ensure db path is in a persistent location if volume is mounted
    if os.path.isdir('/app/data'):
        DATABASE_URL = "sqlite:////app/data/loyalty.db"
        logger.info("Using persistent storage for SQLite in Koyeb")
    else:
        # If no volume is mounted, use local file (note: this will be ephemeral)
        DATABASE_URL = "sqlite:///./loyalty.db" 
        logger.warning("No persistent storage detected, database will be ephemeral")

logger.info(f"Database URL: {DATABASE_URL}")

# Configuration options
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    logger.info("Using SQLite database")
    
    # Make sure the directory exists for SQLite file
    if DATABASE_URL.startswith("sqlite:////app/data/"):
        os.makedirs("/app/data", exist_ok=True)
    elif DATABASE_URL.startswith("sqlite:///./"):
        db_path = Path(DATABASE_URL.replace("sqlite:///./", ""))
        db_dir = BASE_DIR / db_path.parent
        os.makedirs(db_dir, exist_ok=True)
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
