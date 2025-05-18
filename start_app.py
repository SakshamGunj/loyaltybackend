#!/usr/bin/env python
"""
Comprehensive startup script for loyalty backend application.
This script ensures proper database connectivity and sets up the environment.
"""
import os
import sys
import subprocess
import time
import logging
import argparse
import psycopg2
from getpass import getpass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("start_app")

def test_database_connection(password):
    """Test the Supabase PostgreSQL direct connection."""
    logger.info("Testing direct database connection...")
    
    # Connection parameters
    params = {
        'host': 'aws-0-ap-south-1.pooler.supabase.com',
        'port': '5432',
        'database': 'postgres',
        'user': 'postgres.kkflibczahdddnaujjlz',
        'password': password,
        'sslmode': 'require',
    }
    
    try:
        # Construct connection string
        conn_string = f"host={params['host']} port={params['port']} dbname={params['database']} user={params['user']} password={params['password']} sslmode={params['sslmode']}"
        
        # Connect to PostgreSQL
        start_time = time.time()
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        
        # Execute a simple query
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        
        # Close connection
        cursor.close()
        conn.close()
        
        # Print results
        elapsed_time = time.time() - start_time
        logger.info("✅ Database connection successful!")
        logger.info(f"PostgreSQL version: {version}")
        logger.info(f"Connection time: {elapsed_time:.2f} seconds")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def run_app(port=8000, reload=True):
    """Run the FastAPI application with uvicorn."""
    # Set environment variables
    env = os.environ.copy()
    
    # Build command
    reload_flag = "--reload" if reload else ""
    cmd = f"uvicorn app.main:app {reload_flag} --host 0.0.0.0 --port {port}"
    
    logger.info(f"Starting application: {cmd}")
    try:
        # Use shell=True to ensure the command works in PowerShell
        subprocess.run(cmd, shell=True, check=True, env=env)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        sys.exit(0)

def main():
    """Main function to parse arguments and run the app."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Start the loyalty backend application")
    parser.add_argument(
        "--port", type=int, default=8000,
        help="Port to run the application on (default: 8000)")
    parser.add_argument(
        "--no-reload", action="store_true",
        help="Disable auto-reload on code changes")
    parser.add_argument(
        "--skip-connection-test", action="store_true",
        help="Skip the database connection test")
    
    args = parser.parse_args()
    
    # Display banner
    print("\n" + "=" * 80)
    print(" LOYALTY BACKEND - SUPABASE POSTGRESQL EDITION ".center(80, "="))
    print("=" * 80 + "\n")
    
    # Check for existing password
    supabase_password = os.environ.get("SUPABASE_PASSWORD")
    if not supabase_password:
        logger.info("No SUPABASE_PASSWORD environment variable found.")
        supabase_password = getpass("Enter your Supabase database password: ")
        os.environ["SUPABASE_PASSWORD"] = supabase_password
        logger.info("Password set for this session.")
    else:
        logger.info("Using existing SUPABASE_PASSWORD from environment.")
    
    # Test connection if needed
    if not args.skip_connection_test:
        connection_ok = test_database_connection(supabase_password)
        if not connection_ok:
            logger.error("Database connection test failed!")
            choice = input("Continue anyway? (y/n): ")
            if choice.lower() != 'y':
                sys.exit(1)
    
    # Display configuration info
    print("\n" + "-" * 80)
    print(" CONFIGURATION ".center(80, "-"))
    print("-" * 80)
    print(f"Database: Supabase PostgreSQL")
    print(f"Host: aws-0-ap-south-1.pooler.supabase.com")
    print(f"Port: 8000")
    print(f"Auto-reload: {'Enabled' if not args.no_reload else 'Disabled'}")
    print("-" * 80 + "\n")
    
    # Run the application
    logger.info("Starting FastAPI application...")
    run_app(port=args.port, reload=not args.no_reload)

if __name__ == "__main__":
    main() 