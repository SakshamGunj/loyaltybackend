"""
Check database connection using SQLAlchemy
This tests the connection exactly how the FastAPI app does it
"""
import os
import time
import sys
from sqlalchemy import create_engine, text

# Get password from environment variable
password = os.environ.get('SUPABASE_PASSWORD')
if not password:
    print("Error: SUPABASE_PASSWORD environment variable is not set.")
    sys.exit(1)

# Set up the database URL exactly like in database.py
SUPABASE_HOST = "aws-0-ap-south-1.pooler.supabase.com"
DATABASE_URL = f"postgresql://postgres.kkflibczahdddnaujjlz:{password}@{SUPABASE_HOST}:5432/postgres?host={SUPABASE_HOST}"

print(f"Testing connection to: {DATABASE_URL.replace(password, '****')}")

# Set up connection with the same parameters as the application
engine_kwargs = {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_recycle": 3600,
    "pool_pre_ping": True
}

try:
    start_time = time.time()
    
    # Create engine and connect
    engine = create_engine(DATABASE_URL, **engine_kwargs)
    
    # Test connection
    with engine.connect() as connection:
        # Execute a test query
        result = connection.execute(text("SELECT version()"))
        version = result.scalar()
    
    end_time = time.time()
    
    # Print results
    print("✅ SQLAlchemy connection successful!")
    print(f"PostgreSQL version: {version}")
    print(f"Connection time: {end_time - start_time:.2f} seconds")
    
except Exception as e:
    print(f"❌ SQLAlchemy connection failed: {e}")
    sys.exit(1) 