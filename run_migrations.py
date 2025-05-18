#!/usr/bin/env python
"""
Migration runner script that simplifies running Alembic migrations
with the correct database connection.
"""
import os
import sys
import subprocess
import logging
import argparse
from getpass import getpass
import importlib.util

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("run_migrations")

def verify_supabase_connection():
    """Test the Supabase connection using the test script."""
    logger.info("Verifying Supabase PostgreSQL connection...")
    
    try:
        # Import the test script module
        spec = importlib.util.spec_from_file_location("supabase_test", "supabase_test.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # If we get here, it means the import succeeded, now test the connection
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
        
        if connection_successful:
            logger.info("Supabase connection verified successfully!")
            return True
        else:
            logger.error("Failed to connect to Supabase.")
            return False
            
    except Exception as e:
        logger.error(f"Error running Supabase connection test: {e}")
        return False

def run_migrations_sqlite():
    """Run Alembic migrations with SQLite."""
    logger.warning("Running migrations with SQLite database (not recommended for production)")
    
    # Clear any existing Supabase password to force SQLite usage
    if "SUPABASE_PASSWORD" in os.environ:
        del os.environ["SUPABASE_PASSWORD"]
    
    # Define environment variable for SQLite
    os.environ["DATABASE_URL"] = "sqlite:///./loyalty.db"
    
    # Run Alembic
    cmd = "alembic upgrade head"
    try:
        logger.info(f"Running: {cmd}")
        subprocess.run(cmd, shell=True, check=True)
        logger.info("Migrations completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Migration failed: {e}")
        return False

def run_migrations_supabase():
    """Run Alembic migrations with Supabase."""
    # Check if password is already set
    if not os.environ.get("SUPABASE_PASSWORD"):
        password = getpass("Enter your Supabase database password: ")
        os.environ["SUPABASE_PASSWORD"] = password
    
    # Verify connection
    if verify_supabase_connection():
        logger.info("Running migrations with Supabase PostgreSQL database")
        
        # Construct the PostgreSQL URL
        supabase_host = "aws-0-ap-south-1.pooler.supabase.com"
        supabase_password = os.environ.get("SUPABASE_PASSWORD")
        supabase_url = f"postgresql://postgres.kkflibczahdddnaujjlz:{supabase_password}@{supabase_host}:5432/postgres?host={supabase_host}"
        
        # Set environment variable
        os.environ["DATABASE_URL"] = supabase_url
        
        # Run Alembic
        cmd = "alembic upgrade head"
        try:
            logger.info(f"Running: {cmd}")
            subprocess.run(cmd, shell=True, check=True)
            logger.info("Migrations completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Migration failed: {e}")
            return False
    else:
        logger.error("Could not verify Supabase connection. Please check your password.")
        choice = input("Do you want to retry with a different password? (y/n): ")
        if choice.lower() == 'y':
            # Clear the existing password and try again
            if "SUPABASE_PASSWORD" in os.environ:
                del os.environ["SUPABASE_PASSWORD"]
            return run_migrations_supabase()
        else:
            choice = input("Do you want to fall back to SQLite for development? (y/n): ")
            if choice.lower() == 'y':
                return run_migrations_sqlite()
            else:
                logger.info("Exiting...")
                sys.exit(1)

def create_migration(message):
    """Create a new migration."""
    # Check if we have a database connection before creating migration
    print("\nSelect database for migration creation:")
    print("1. SQLite (local development)")
    print("2. Supabase PostgreSQL (recommended)")
    choice = input("Select database (2/1) [default=2]: ") or "2"
    
    # Set the appropriate database URL
    if choice == "1":
        os.environ["DATABASE_URL"] = "sqlite:///./loyalty.db"
        if "SUPABASE_PASSWORD" in os.environ:
            del os.environ["SUPABASE_PASSWORD"]
    else:
        # Make sure we have a Supabase connection
        if not os.environ.get("SUPABASE_PASSWORD"):
            password = getpass("Enter your Supabase database password: ")
            os.environ["SUPABASE_PASSWORD"] = password
        
        # Verify connection
        if not verify_supabase_connection():
            logger.error("Could not connect to Supabase. Migrations should be created against your production database.")
            return False
        
        # Construct and set the PostgreSQL URL
        supabase_host = "aws-0-ap-south-1.pooler.supabase.com"
        supabase_password = os.environ.get("SUPABASE_PASSWORD")
        supabase_url = f"postgresql://postgres.kkflibczahdddnaujjlz:{supabase_password}@{supabase_host}:5432/postgres?host={supabase_host}"
        os.environ["DATABASE_URL"] = supabase_url
    
    # Create the migration
    cmd = f'alembic revision --autogenerate -m "{message}"'
    try:
        logger.info(f"Creating migration: {cmd}")
        subprocess.run(cmd, shell=True, check=True)
        logger.info("Migration created successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create migration: {e}")
        return False

def main():
    """Main function to parse arguments and run migrations."""
    parser = argparse.ArgumentParser(description="Run database migrations")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade to the latest migration")
    upgrade_parser.add_argument(
        "--db", choices=["sqlite", "supabase", "auto"], default="supabase",
        help="Database to use: sqlite, supabase, or auto (default: supabase)")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new migration")
    create_parser.add_argument(
        "message", help="Migration message")
    
    args = parser.parse_args()
    
    if args.command == "upgrade":
        # Determine database to use
        if args.db == "sqlite":
            run_migrations_sqlite()
        elif args.db == "supabase" or args.db == "auto":  # Default to Supabase
            run_migrations_supabase()
    elif args.command == "create":
        create_migration(args.message)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 