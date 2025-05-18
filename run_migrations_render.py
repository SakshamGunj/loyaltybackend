#!/usr/bin/env python
"""
Migration runner script that simplifies running Alembic migrations
with the Render PostgreSQL database.
"""
import os
import sys
import subprocess
import logging
import argparse
from getpass import getpass
import importlib.util
import psycopg2
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("run_migrations_render")

# Render PostgreSQL connection details
RENDER_USER = "tenversepos_user"
RENDER_PASSWORD = "00TrCMA1p1vsgiib0s3GTe6u8iYZ6Kzt"
RENDER_HOST = "dpg-d0kstu7fte5s738vuil0-a.oregon-postgres.render.com"
RENDER_DBNAME = "tenversepos"
RENDER_DB_URL = f"postgresql://{RENDER_USER}:{RENDER_PASSWORD}@{RENDER_HOST}:5432/{RENDER_DBNAME}"

def verify_render_connection():
    """Test the Render PostgreSQL connection."""
    logger.info("Verifying Render PostgreSQL connection...")
    
    try:
        # Test direct connection with psycopg2
        conn_string = f"host={RENDER_HOST} port=5432 dbname={RENDER_DBNAME} user={RENDER_USER} password={RENDER_PASSWORD}"
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        db_version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        logger.info(f"Successfully connected to Render PostgreSQL: {db_version}")
        return True
    except Exception as e:
        logger.error(f"Render connection test failed: {e}")
        return False

def run_migrations_sqlite():
    """Run Alembic migrations with SQLite."""
    logger.warning("Running migrations with SQLite database (not recommended for production)")
    
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

def run_migrations_render():
    """Run Alembic migrations with Render PostgreSQL."""
    # Verify connection
    if verify_render_connection():
        logger.info("Running migrations with Render PostgreSQL database")
        
        # Set environment variable
        os.environ["DATABASE_URL"] = RENDER_DB_URL
        
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
        logger.error("Could not verify Render PostgreSQL connection.")
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
    print("2. Render PostgreSQL (recommended)")
    choice = input("Select database (2/1) [default=2]: ") or "2"
    
    # Set the appropriate database URL
    if choice == "1":
        os.environ["DATABASE_URL"] = "sqlite:///./loyalty.db"
    else:
        # Verify connection to Render
        if not verify_render_connection():
            logger.error("Could not connect to Render PostgreSQL. Migrations should be created against your production database.")
            return False
        
        # Set the PostgreSQL URL
        os.environ["DATABASE_URL"] = RENDER_DB_URL
    
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
    parser = argparse.ArgumentParser(description="Run database migrations with Render PostgreSQL")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade to the latest migration")
    upgrade_parser.add_argument(
        "--db", choices=["sqlite", "render", "auto"], default="render",
        help="Database to use: sqlite, render, or auto (default: render)")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new migration")
    create_parser.add_argument(
        "message", help="Migration message")
    
    args = parser.parse_args()
    
    if args.command == "upgrade":
        # Determine database to use
        if args.db == "sqlite":
            run_migrations_sqlite()
        elif args.db == "render" or args.db == "auto":  # Default to Render
            run_migrations_render()
    elif args.command == "create":
        create_migration(args.message)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 