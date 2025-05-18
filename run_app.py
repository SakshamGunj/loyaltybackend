#!/usr/bin/env python
"""
Application runner script with database connection verification.
This script helps ensure the database connection is working before starting the app.
"""
import os
import sys
import subprocess
import importlib.util
import argparse
import logging
from getpass import getpass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("run_app")

def verify_supabase_connection():
    """Test the Supabase connection using the test script."""
    print("Verifying Supabase PostgreSQL connection...")
    
    # Use the test script for verification
    try:
        # Import the test script module
        spec = importlib.util.spec_from_file_location("supabase_test", "supabase_test.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # If we get here, it means the import succeeded, now let's use it
        # We'll capture stdout/stderr to prevent double printing
        import io
        from contextlib import redirect_stdout, redirect_stderr
        
        f = io.StringIO()
        with redirect_stdout(f), redirect_stderr(f):
            try:
                # Execute the script's main logic
                module.conn = module.psycopg2.connect(module.conn_string)
                module.cursor = module.conn.cursor()
                module.cursor.execute("SELECT version();")
                module.db_version = module.cursor.fetchone()
                module.cursor.close()
                module.conn.close()
                connection_successful = True
            except Exception as e:
                logger.error(f"Connection test failed: {e}")
                connection_successful = False
        
        output = f.getvalue()
        if "Connection successful" in output or connection_successful:
            logger.info("Supabase connection verified successfully!")
            return True
        else:
            logger.error("Failed to connect to Supabase.")
            logger.error(output)
            return False
            
    except Exception as e:
        logger.error(f"Error running Supabase connection test: {e}")
        return False

def run_with_sqlite():
    """Run the application with SQLite database."""
    logger.warning("Running with SQLite database (not recommended for production)")
    # Clear any existing Supabase password to force SQLite usage
    if "SUPABASE_PASSWORD" in os.environ:
        del os.environ["SUPABASE_PASSWORD"]
    
    # Explicitly set DATABASE_URL to force SQLite
    os.environ["DATABASE_URL"] = "sqlite:///./loyalty.db"
    
    # Run uvicorn
    run_uvicorn()

def run_with_supabase():
    """Run the application with Supabase database."""
    # Check if password is already set
    if not os.environ.get("SUPABASE_PASSWORD"):
        password = getpass("Enter your Supabase database password: ")
        os.environ["SUPABASE_PASSWORD"] = password
    
    # Verify connection
    if verify_supabase_connection():
        logger.info("Running with Supabase PostgreSQL database")
        run_uvicorn()
    else:
        logger.error("Could not verify Supabase connection. Please check your password.")
        choice = input("Do you want to retry with a different password? (y/n): ")
        if choice.lower() == 'y':
            # Clear the existing password and try again
            if "SUPABASE_PASSWORD" in os.environ:
                del os.environ["SUPABASE_PASSWORD"]
            run_with_supabase()
        else:
            choice = input("Do you want to fall back to SQLite for development? (y/n): ")
            if choice.lower() == 'y':
                run_with_sqlite()
            else:
                logger.info("Exiting...")
                sys.exit(1)

def run_uvicorn(port=8000, reload=True):
    """Run the uvicorn server with the app."""
    reload_flag = "--reload" if reload else ""
    cmd = f"uvicorn app.main:app {reload_flag} --host 0.0.0.0 --port {port}"
    
    logger.info(f"Starting application: {cmd}")
    try:
        # Use shell=True to ensure the command works in PowerShell
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        sys.exit(0)

def main():
    """Main function to parse arguments and run the app."""
    parser = argparse.ArgumentParser(description="Run the loyalty backend application")
    parser.add_argument(
        "--db", choices=["sqlite", "supabase", "auto"], default="supabase",
        help="Database to use: sqlite, supabase, or auto (default: supabase)")
    parser.add_argument(
        "--port", type=int, default=8000,
        help="Port to run the application on (default: 8000)")
    parser.add_argument(
        "--no-reload", action="store_true",
        help="Disable auto-reload on code changes")
    
    args = parser.parse_args()
    
    # Determine database to use
    if args.db == "sqlite":
        run_with_sqlite()
    elif args.db == "supabase" or args.db == "auto":  # Default to Supabase
        run_with_supabase()

if __name__ == "__main__":
    main() 