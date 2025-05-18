from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import logging
from pathlib import Path
import tempfile
from getpass import getpass
import urllib.parse

logger = logging.getLogger(__name__)

# Base directory for the application
BASE_DIR = Path(__file__).resolve().parent.parent

# Check if running in cloud environments
is_cloud_run = os.getenv("K_SERVICE") is not None or os.getenv("GOOGLE_CLOUD_PROJECT") is not None
is_app_engine = os.getenv("GAE_ENV") is not None
is_koyeb = os.getenv("KOYEB_APP_NAME") is not None

# Use Render PostgreSQL instead of Supabase
RENDER_DB_URL = "postgresql://tenversepos_user:00TrCMA1p1vsgiib0s3GTe6u8iYZ6Kzt@dpg-d0kstu7fte5s738vuil0-a.oregon-postgres.render.com/tenversepos"

# Use Render PostgreSQL by default
DATABASE_URL = os.getenv("DATABASE_URL", RENDER_DB_URL)

# Special handling for Google Cloud environments
if is_cloud_run:
    logger.info("Running in Google Cloud Run environment")
    
    # Check for Cloud SQL connection
    cloud_sql_connection_name = os.getenv("CLOUD_SQL_CONNECTION_NAME")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    db_name = os.getenv("DB_NAME", "loyalty")
    
    if cloud_sql_connection_name and db_user and db_pass:
        # For Cloud SQL with PostgreSQL
        socket_path = f"/cloudsql/{cloud_sql_connection_name}"
        DATABASE_URL = f"postgresql://{db_user}:{db_pass}@/{db_name}?host={socket_path}"
        logger.info(f"Using Cloud SQL connection: {DATABASE_URL.replace(db_pass, '****')}")
    else:
        # Use Render PostgreSQL for Cloud Run
        DATABASE_URL = RENDER_DB_URL
        logger.info("Using Render PostgreSQL in Google Cloud")
            
elif is_koyeb:
    logger.info("Running in Koyeb environment")
    # Use Render PostgreSQL for Koyeb
    DATABASE_URL = RENDER_DB_URL
    logger.info("Using Render PostgreSQL in Koyeb")

# If DATABASE_URL was provided as an environment variable, log it
custom_db_url = os.getenv("DATABASE_URL")
if custom_db_url:
    logger.info("Using database URL from environment variable")
else:
    logger.info("Using Render PostgreSQL database by default")

# Mask password in logs
safe_db_url = DATABASE_URL
if '@' in DATABASE_URL and ':' in DATABASE_URL.split('@')[0]:
    parts = DATABASE_URL.split('@')
    credentials = parts[0].split(':')
    if len(credentials) > 2:
        masked_url = f"{credentials[0]}:{credentials[1]}:****@{parts[1]}"
        safe_db_url = masked_url
    else:
        masked_url = f"{credentials[0]}:****@{parts[1]}"
        safe_db_url = masked_url
logger.info(f"Database URL: {safe_db_url}")

# Configuration options
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    # This should rarely happen now, but keep the code for compatibility
    connect_args = {"check_same_thread": False}
    logger.info("Using SQLite database")
    
    # Make sure the directory exists for SQLite file
    if DATABASE_URL.startswith("sqlite:////tmp/"):
        os.makedirs("/tmp", exist_ok=True)
        logger.info("Ensuring /tmp directory exists")
    elif DATABASE_URL.startswith(f"sqlite:///{tempfile.gettempdir()}"):
        os.makedirs(tempfile.gettempdir(), exist_ok=True)
        logger.info(f"Ensuring {tempfile.gettempdir()} directory exists")
    elif DATABASE_URL.startswith("sqlite:////mnt/data/"):
        os.makedirs("/mnt/data", exist_ok=True)
    elif DATABASE_URL.startswith("sqlite:////app/data/"):
        os.makedirs("/app/data", exist_ok=True)
    elif DATABASE_URL.startswith("sqlite:///./"):
        db_path = Path(DATABASE_URL.replace("sqlite:///./", ""))
        db_dir = BASE_DIR / db_path.parent
        os.makedirs(db_dir, exist_ok=True)
else:
    # PostgreSQL specific configuration
    logger.info("Using PostgreSQL database")
    # Add connection pooling for PostgreSQL
    engine_kwargs = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 3600,
        "pool_pre_ping": True
    }

# Log the connection details (without sensitive info)
logger.info(f"Connecting to database with URL: {safe_db_url}")

# Create engine and session
engine = create_engine(
    DATABASE_URL, 
    connect_args=connect_args, 
    **(engine_kwargs if not DATABASE_URL.startswith("sqlite") else {})
)

# Try to connect to the database right away to validate configuration
try:
    connection = engine.connect()
    result = connection.execute(text("SELECT 1"))
    connection.close()
    logger.info("Successfully validated database connection at startup")
except Exception as e:
    logger.error(f"Database connection validation failed: {e}")
    logger.error(f"Connection URL used (redacted): {safe_db_url}")
    if "Wrong password" in str(e):
        logger.error("Authentication error! Please check your database settings")
    elif "could not translate host name" in str(e):
        logger.error("DNS resolution error! Please check your network connection")
    else:
        logger.error("Please check your database settings and network connectivity")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
