"""
Data Migration Script: SQLite to PostgreSQL

This script migrates data from your SQLite database to PostgreSQL (Supabase).
Before running, ensure you have the correct PostgreSQL connection string.
"""

import sqlite3
import psycopg2
import os
import logging
import time
from dotenv import load_dotenv
from getpass import getpass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("migration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("data_migration")

# Load environment variables from .env file if it exists
load_dotenv()

# Source SQLite Database
SQLITE_DB_PATH = "loyalty.db"

# Get Supabase password
SUPABASE_PASSWORD = os.getenv("SUPABASE_PASSWORD")
if not SUPABASE_PASSWORD:
    try:
        SUPABASE_PASSWORD = getpass("Enter your Supabase database password: ")
    except:
        logger.error("Unable to get password from terminal. Please set SUPABASE_PASSWORD environment variable.")
        exit(1)

# Target PostgreSQL (Supabase) Database with Session Pooler
PG_CONNECTION_STRING = os.getenv(
    "PG_CONNECTION_STRING",
    f"postgresql://postgres.kkflibczahdddnaujjlz:{SUPABASE_PASSWORD}@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"
)

# Tables to migrate (in order to respect foreign key constraints)
TABLES = [
    "users",
    "restaurants",
    "menu_categories",
    "menu_items", 
    "menu_item_components",
    "orders",
    "order_items",
    "payments",
    "order_status_history",
    "verified_phone_numbers",
    "coupons",
    "restaurant_tables",
    "inventory_items",
    "inventory_transactions",
    # Add any other tables as needed
]

def get_table_columns(cursor, table_name):
    """Get the column names for a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in cursor.fetchall()]
    return columns

def get_pg_table_columns(cursor, table_name):
    """Get the column names for a PostgreSQL table."""
    cursor.execute(f"""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    columns = [column[0] for column in cursor.fetchall()]
    return columns

def copy_table_data(sqlite_cursor, pg_cursor, pg_conn, table_name):
    """Copy data from SQLite table to PostgreSQL table."""
    try:
        # Get column names from both databases
        sqlite_columns = get_table_columns(sqlite_cursor, table_name)
        pg_columns = get_pg_table_columns(pg_cursor, table_name)
        
        # Find common columns
        common_columns = [col for col in sqlite_columns if col in pg_columns]
        
        # Log what columns we're migrating
        logger.info(f"Migrating {len(common_columns)} columns for table {table_name}")
        logger.info(f"Common columns: {', '.join(common_columns)}")
        
        # Get data from SQLite
        sqlite_cursor.execute(f"SELECT {', '.join(common_columns)} FROM {table_name}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            logger.info(f"No data to migrate for table {table_name}")
            return 0
        
        # Prepare PostgreSQL table (disable triggers temporarily)
        pg_cursor.execute(f"ALTER TABLE {table_name} DISABLE TRIGGER ALL")
        
        # Insert data into PostgreSQL
        placeholders = ', '.join(['%s'] * len(common_columns))
        insert_query = f"""
            INSERT INTO {table_name} ({', '.join(common_columns)})
            VALUES ({placeholders})
            ON CONFLICT DO NOTHING
        """
        
        # Execute in batches to avoid memory issues
        batch_size = 100
        total_rows = len(rows)
        for i in range(0, total_rows, batch_size):
            batch = rows[i:i+batch_size]
            pg_cursor.executemany(insert_query, batch)
            pg_conn.commit()
            logger.info(f"Migrated {min(i+batch_size, total_rows)}/{total_rows} rows for table {table_name}")
        
        # Re-enable triggers
        pg_cursor.execute(f"ALTER TABLE {table_name} ENABLE TRIGGER ALL")
        
        return len(rows)
    except Exception as e:
        logger.error(f"Error migrating table {table_name}: {e}")
        pg_conn.rollback()
        return 0

def main():
    """Main migration function."""
    start_time = time.time()
    
    try:
        # Connect to SQLite database
        logger.info(f"Connecting to SQLite database: {SQLITE_DB_PATH}")
        sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Connect to PostgreSQL database
        logger.info("Connecting to PostgreSQL database using Session Pooler")
        pg_conn = psycopg2.connect(PG_CONNECTION_STRING)
        pg_cursor = pg_conn.cursor()
        
        total_migrated = 0
        
        # Migrate each table
        for table in TABLES:
            logger.info(f"Starting migration of table: {table}")
            rows_migrated = copy_table_data(sqlite_cursor, pg_cursor, pg_conn, table)
            total_migrated += rows_migrated
            logger.info(f"Successfully migrated {rows_migrated} rows from table {table}")
        
        # Clean up
        sqlite_cursor.close()
        sqlite_conn.close()
        pg_cursor.close()
        pg_conn.close()
        
        elapsed_time = time.time() - start_time
        logger.info(f"Migration completed in {elapsed_time:.2f} seconds")
        logger.info(f"Total rows migrated: {total_migrated}")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    logger.info("Starting SQLite to PostgreSQL migration")
    exit_code = main()
    if exit_code == 0:
        logger.info("Migration completed successfully")
    else:
        logger.error("Migration failed")
    exit(exit_code) 