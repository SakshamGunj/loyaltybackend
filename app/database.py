from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import logging
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)

# Base directory for the application
BASE_DIR = Path(__file__).resolve().parent.parent

# Check if running in cloud environments
is_cloud_run = os.getenv("K_SERVICE") is not None or os.getenv("GOOGLE_CLOUD_PROJECT") is not None
is_app_engine = os.getenv("GAE_ENV") is not None
is_koyeb = os.getenv("KOYEB_APP_NAME") is not None

# Default to SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./loyalty.db")

# Special handling for Google App Engine - this needs /tmp directory
if is_app_engine:
    logger.info("Running in Google App Engine environment")
    
    # Create a unique filename in /tmp to avoid conflicts
    db_file = tempfile.gettempdir() + "/loyalty_" + str(os.getpid()) + ".db"
    DATABASE_URL = f"sqlite:///{db_file}"
    
    # Ensure directory has proper permissions
    try:
        # Make sure /tmp exists and is writable
        os.makedirs(tempfile.gettempdir(), exist_ok=True)
        if os.path.exists(db_file):
            os.chmod(db_file, 0o666)  # Full read/write permissions
    except Exception as e:
        logger.error(f"Error setting permissions: {e}")
    
    logger.info(f"Using App Engine writable path: {DATABASE_URL}")

# Special handling for Google Cloud environments
elif is_cloud_run:
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
        # If Cloud SQL not configured, check for persistent disk
        if os.path.isdir('/mnt/data'):
            # Use Cloud Storage mounted as persistent disk
            DATABASE_URL = "sqlite:////mnt/data/loyalty.db"
            logger.info("Using persistent disk for SQLite in Google Cloud")
        else:
            # Fallback to local SQLite (will be ephemeral in Cloud Run)
            DATABASE_URL = "sqlite:///./loyalty.db"
            logger.warning("No persistent storage detected, database will be ephemeral")
            
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
