import sqlite3
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get database path from environment or use default
def get_db_path():
    from app.database import DATABASE_URL
    if DATABASE_URL.startswith('sqlite:///'):
        return DATABASE_URL[10:]
    return "loyalty.db"  # Default

def run_migration():
    db_path = get_db_path()
    logger.info(f"Starting database migration on {db_path}")
    
    # Check if database exists
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return False
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Helper function to check if a column exists in a table
    def column_exists(table, column):
        try:
            cursor.execute(f"SELECT {column} FROM {table} LIMIT 1")
            return True
        except sqlite3.OperationalError:
            return False
    
    # Helper function to add a column if it doesn't exist
    def add_column_if_missing(table, column, type_def):
        if not column_exists(table, column):
            logger.info(f"Adding column {column} to table {table}")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type_def}")
            return True
        else:
            logger.info(f"Column {column} already exists in table {table}")
            return False
    
    try:
        # Begin transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Add image_url column to menu_items table
        add_column_if_missing("menu_items", "image_url", "TEXT")
        
        # Add created_at column to menu_items table
        add_column_if_missing("menu_items", "created_at", "TIMESTAMP")
        
        # Add created_at column to menu_categories table
        add_column_if_missing("menu_categories", "created_at", "TIMESTAMP")
        
        # Add options column to order_items table
        add_column_if_missing("order_items", "options", "TEXT")
        
        # Add transaction_id column to payments table
        add_column_if_missing("payments", "transaction_id", "TEXT")
        
        # Add processed_at column to payments table
        add_column_if_missing("payments", "processed_at", "TIMESTAMP")
        
        # Add order_id column to audit_logs table
        add_column_if_missing("audit_logs", "order_id", "INTEGER")
        
        # Add created_at column to promo_codes table
        add_column_if_missing("promo_codes", "created_at", "TIMESTAMP")
        
        # Add restaurant_id column to promo_codes table
        add_column_if_missing("promo_codes", "restaurant_id", "TEXT")
        
        # Commit the transaction
        conn.commit()
        logger.info("Migration completed successfully")
        return True
        
    except Exception as e:
        # Rollback in case of error
        conn.rollback()
        logger.error(f"Migration failed: {e}")
        return False
        
    finally:
        # Close connection
        conn.close()

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("Database migration completed successfully.")
    else:
        print("Database migration failed. Check logs for details.") 