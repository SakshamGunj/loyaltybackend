"""
Script to set up the Render PostgreSQL database from scratch without using Alembic
"""
import os
import psycopg2
import logging
from sqlalchemy import create_engine, text
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("setup_render_db")

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

def run_data_migration():
    """Run the data migration to create all tables."""
    logger.info("Starting data migration to create all tables...")
    
    if not verify_render_connection():
        logger.error("Failed to connect to Render PostgreSQL. Aborting migration.")
        return False
    
    # Create engine for SQLAlchemy
    engine = create_engine(RENDER_DB_URL)
    
    try:
        with engine.connect() as conn:
            # Create tables in the correct order to respect foreign key constraints
            
            # 1. Create users table
            logger.info("Creating users table...")
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                uid VARCHAR NOT NULL, 
                name VARCHAR, 
                email VARCHAR, 
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                role VARCHAR,
                hashed_password VARCHAR,
                number VARCHAR,
                is_active BOOLEAN DEFAULT TRUE,
                restaurant_id VARCHAR,
                designation VARCHAR,
                permissions JSONB,
                PRIMARY KEY (uid)
            )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_email ON users (email)"))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email_unique ON users (email)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_uid ON users (uid)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_number ON users (number)"))
            
            # 2. Create restaurants table
            logger.info("Creating restaurants table...")
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS restaurants (
                restaurant_id VARCHAR NOT NULL, 
                restaurant_name VARCHAR, 
                offers JSONB, 
                points_per_rupee FLOAT, 
                reward_thresholds JSONB, 
                referral_rewards JSONB, 
                owner_uid VARCHAR,
                address VARCHAR,
                city VARCHAR,
                state VARCHAR,
                pin_code VARCHAR,
                contact_phone VARCHAR,
                contact_number VARCHAR,
                logo_url VARCHAR,
                banner_url VARCHAR,
                description TEXT,
                cuisine_type VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                PRIMARY KEY (restaurant_id), 
                FOREIGN KEY(owner_uid) REFERENCES users (uid)
            )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_restaurants_restaurant_id ON restaurants (restaurant_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_restaurants_restaurant_name ON restaurants (restaurant_name)"))
            
            # 3. Create menu_categories table
            logger.info("Creating menu_categories table...")
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS menu_categories (
                id SERIAL PRIMARY KEY,
                restaurant_id VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                description VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (restaurant_id) REFERENCES restaurants (restaurant_id)
            )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_menu_categories_restaurant_id ON menu_categories (restaurant_id)"))
            
            # 4. Create menu_items table
            logger.info("Creating menu_items table...")
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS menu_items (
                id SERIAL PRIMARY KEY,
                restaurant_id VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                description VARCHAR,
                price FLOAT NOT NULL,
                available BOOLEAN DEFAULT TRUE,
                category_id INTEGER,
                image_url VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (restaurant_id) REFERENCES restaurants (restaurant_id),
                FOREIGN KEY (category_id) REFERENCES menu_categories (id)
            )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_menu_items_restaurant_id ON menu_items (restaurant_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_menu_items_category_id ON menu_items (category_id)"))
            
            # 5. Create combo_menu_items table
            logger.info("Creating combo_menu_items table...")
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS combo_menu_items (
                id SERIAL PRIMARY KEY,
                restaurant_id VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                description VARCHAR,
                price FLOAT NOT NULL,
                available BOOLEAN DEFAULT TRUE,
                items JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (restaurant_id) REFERENCES restaurants (restaurant_id)
            )
            """))
            
            # 6. Create promo_codes table
            logger.info("Creating promo_codes table...")
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS promo_codes (
                id SERIAL PRIMARY KEY,
                code VARCHAR UNIQUE,
                description VARCHAR,
                discount_percent FLOAT,
                discount_amount FLOAT,
                active BOOLEAN DEFAULT TRUE,
                valid_from TIMESTAMP,
                valid_to TIMESTAMP,
                usage_limit INTEGER,
                used_count INTEGER DEFAULT 0,
                restaurant_id VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (restaurant_id) REFERENCES restaurants (restaurant_id)
            )
            """))
            
            # 7. Create coupons table
            logger.info("Creating coupons table...")
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS coupons (
                id SERIAL PRIMARY KEY,
                code VARCHAR NOT NULL,
                description VARCHAR,
                discount_type VARCHAR NOT NULL,
                discount_value FLOAT NOT NULL,
                min_order_value FLOAT,
                max_discount FLOAT,
                is_active BOOLEAN DEFAULT TRUE,
                start_date TIMESTAMP NOT NULL,
                end_date TIMESTAMP NOT NULL,
                usage_limit INTEGER,
                used_count INTEGER DEFAULT 0,
                restaurant_id VARCHAR NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (restaurant_id) REFERENCES restaurants (restaurant_id)
            )
            """))
            
            # 8. Create coupon_redemptions table
            logger.info("Creating coupon_redemptions table...")
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS coupon_redemptions (
                id SERIAL PRIMARY KEY,
                coupon_id INTEGER NOT NULL,
                user_id VARCHAR NOT NULL,
                discount_amount FLOAT NOT NULL,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (coupon_id) REFERENCES coupons (id),
                FOREIGN KEY (user_id) REFERENCES users (uid)
            )
            """))
            
            # 9. Create orders table
            logger.info("Creating orders table...")
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS orders (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR DEFAULT 'Pending',
                total_cost FLOAT NOT NULL,
                payment_status VARCHAR DEFAULT 'Pending',
                restaurant_id VARCHAR,
                restaurant_name VARCHAR,
                order_number INTEGER,
                customer_uid VARCHAR,
                FOREIGN KEY (user_id) REFERENCES users (uid),
                FOREIGN KEY (restaurant_id) REFERENCES restaurants (restaurant_id),
                FOREIGN KEY (customer_uid) REFERENCES users (uid)
            )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_user_id ON orders (user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_restaurant_id ON orders (restaurant_id)"))
            
            # 10. Create order_items table
            logger.info("Creating order_items table...")
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS order_items (
                id SERIAL PRIMARY KEY,
                order_id VARCHAR NOT NULL,
                item_id INTEGER,
                quantity INTEGER DEFAULT 1,
                price FLOAT NOT NULL,
                options JSONB,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (item_id) REFERENCES menu_items (id)
            )
            """))
            
            # 11. Create order_status_history table
            logger.info("Creating order_status_history table...")
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS order_status_history (
                id SERIAL PRIMARY KEY,
                order_id VARCHAR NOT NULL,
                status VARCHAR NOT NULL,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                changed_by VARCHAR NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
            """))
            
            # 12. Create payments table
            logger.info("Creating payments table...")
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                order_id VARCHAR NOT NULL,
                amount FLOAT NOT NULL,
                method VARCHAR NOT NULL,
                status VARCHAR DEFAULT 'Pending',
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paid_at TIMESTAMP,
                transaction_id VARCHAR,
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
            """))
            
            # 13. Create verified_phone_numbers table
            logger.info("Creating verified_phone_numbers table...")
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS verified_phone_numbers (
                id SERIAL PRIMARY KEY,
                number VARCHAR NOT NULL UNIQUE,
                verification_code VARCHAR,
                verified BOOLEAN DEFAULT FALSE,
                verified_at TIMESTAMP,
                user_id VARCHAR,
                FOREIGN KEY (user_id) REFERENCES users (uid)
            )
            """))
            
            # 14. Create inventory_items table
            logger.info("Creating inventory_items table...")
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS inventory_items (
                id SERIAL PRIMARY KEY,
                restaurant_id VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                description VARCHAR,
                quantity FLOAT NOT NULL,
                unit VARCHAR NOT NULL,
                last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (restaurant_id) REFERENCES restaurants (restaurant_id)
            )
            """))
            
            # 15. Create inventory_transactions table
            logger.info("Creating inventory_transactions table...")
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS inventory_transactions (
                id SERIAL PRIMARY KEY,
                inventory_item_id INTEGER NOT NULL,
                quantity FLOAT NOT NULL,
                transaction_type VARCHAR NOT NULL,
                notes VARCHAR,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (inventory_item_id) REFERENCES inventory_items (id)
            )
            """))
            
            # 16. Create restaurant_tables table
            logger.info("Creating restaurant_tables table...")
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS restaurant_tables (
                id SERIAL PRIMARY KEY,
                restaurant_id VARCHAR NOT NULL,
                table_number VARCHAR NOT NULL,
                capacity INTEGER NOT NULL,
                status VARCHAR DEFAULT 'Available',
                qr_code_url VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (restaurant_id) REFERENCES restaurants (restaurant_id),
                UNIQUE (restaurant_id, table_number)
            )
            """))
            
            # 17. Create audit_logs table
            logger.info("Creating audit_logs table...")
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR,
                action VARCHAR,
                details JSONB,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                order_id VARCHAR,
                FOREIGN KEY (user_id) REFERENCES users (uid),
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
            """))
            
            # 18. Create loyalty table
            logger.info("Creating loyalty table...")
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS loyalty (
                id SERIAL PRIMARY KEY,
                uid VARCHAR,
                restaurant_id VARCHAR,
                total_points INTEGER DEFAULT 0,
                restaurant_points INTEGER DEFAULT 0,
                tier VARCHAR,
                punches INTEGER DEFAULT 0,
                redemption_history JSONB,
                visited_restaurants JSONB,
                last_spin_time TIMESTAMP,
                spin_history JSONB,
                referral_codes JSONB,
                referrals_made JSONB,
                referred_by JSONB,
                FOREIGN KEY (uid) REFERENCES users (uid),
                FOREIGN KEY (restaurant_id) REFERENCES restaurants (restaurant_id)
            )
            """))
            
            # 19. Create claimed_rewards table
            logger.info("Creating claimed_rewards table...")
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS claimed_rewards (
                id SERIAL PRIMARY KEY,
                uid VARCHAR,
                restaurant_id VARCHAR,
                reward_name VARCHAR,
                threshold_id INTEGER,
                whatsapp_number VARCHAR,
                user_name VARCHAR,
                claimed_at TIMESTAMP,
                redeemed BOOLEAN DEFAULT FALSE,
                redeemed_at TIMESTAMP,
                FOREIGN KEY (uid) REFERENCES users (uid),
                FOREIGN KEY (restaurant_id) REFERENCES restaurants (restaurant_id)
            )
            """))
            
            # 20. Create submissions table
            logger.info("Creating submissions table...")
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS submissions (
                submission_id SERIAL PRIMARY KEY,
                uid VARCHAR,
                restaurant_id VARCHAR,
                amount_spent FLOAT,
                points_earned INTEGER,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (uid) REFERENCES users (uid),
                FOREIGN KEY (restaurant_id) REFERENCES restaurants (restaurant_id)
            )
            """))
            
            # Create all indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_loyalty_uid ON loyalty (uid)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_loyalty_restaurant_id ON loyalty (restaurant_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_claimed_rewards_uid ON claimed_rewards (uid)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_claimed_rewards_restaurant_id ON claimed_rewards (restaurant_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_submissions_uid ON submissions (uid)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_submissions_restaurant_id ON submissions (restaurant_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id ON audit_logs (user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_audit_logs_order_id ON audit_logs (order_id)"))
            
            # Add alembic_version table and set version to the latest
            logger.info("Creating alembic_version table...")
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL,
                PRIMARY KEY (version_num)
            )
            """))
            
            # Insert the latest version ID from alembic migrations
            conn.execute(text("DELETE FROM alembic_version"))
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('61fbc8887b89')"))  # Latest migration version
            
            conn.commit()
            logger.info("Database schema created successfully!")
            return True
            
    except Exception as e:
        logger.error(f"Error creating database schema: {e}")
        return False

def drop_all_tables():
    """Drop all existing tables to start fresh."""
    logger.info("Dropping all existing tables...")
    
    if not verify_render_connection():
        logger.error("Failed to connect to Render PostgreSQL. Aborting operation.")
        return False
    
    # Create engine for SQLAlchemy
    engine = create_engine(RENDER_DB_URL)
    
    try:
        with engine.connect() as conn:
            # Drop the alembic_version table first
            conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
            
            # Drop tables in reverse order of creation to handle foreign key constraints
            conn.execute(text("DROP TABLE IF EXISTS submissions"))
            conn.execute(text("DROP TABLE IF EXISTS claimed_rewards"))
            conn.execute(text("DROP TABLE IF EXISTS loyalty"))
            conn.execute(text("DROP TABLE IF EXISTS audit_logs"))
            conn.execute(text("DROP TABLE IF EXISTS restaurant_tables"))
            conn.execute(text("DROP TABLE IF EXISTS inventory_transactions"))
            conn.execute(text("DROP TABLE IF EXISTS inventory_items"))
            conn.execute(text("DROP TABLE IF EXISTS verified_phone_numbers"))
            conn.execute(text("DROP TABLE IF EXISTS payments"))
            conn.execute(text("DROP TABLE IF EXISTS order_status_history"))
            conn.execute(text("DROP TABLE IF EXISTS order_items"))
            conn.execute(text("DROP TABLE IF EXISTS orders"))
            conn.execute(text("DROP TABLE IF EXISTS coupon_redemptions"))
            conn.execute(text("DROP TABLE IF EXISTS coupons"))
            conn.execute(text("DROP TABLE IF EXISTS promo_codes"))
            conn.execute(text("DROP TABLE IF EXISTS combo_menu_items"))
            conn.execute(text("DROP TABLE IF EXISTS combo_item_components"))
            conn.execute(text("DROP TABLE IF EXISTS menu_items"))
            conn.execute(text("DROP TABLE IF EXISTS menu_categories"))
            conn.execute(text("DROP TABLE IF EXISTS restaurants"))
            conn.execute(text("DROP TABLE IF EXISTS users"))
            
            conn.commit()
            logger.info("All existing tables dropped successfully.")
            return True
    except Exception as e:
        logger.error(f"Error dropping tables: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print(" RENDER POSTGRESQL DATABASE SETUP ".center(80, "="))
    print("=" * 80 + "\n")
    
    print("This will drop all existing tables and recreate them with the correct schema.")
    choice = input("Do you want to continue? (y/n): ")
    if choice.lower() != 'y':
        print("Operation cancelled.")
        sys.exit(0)
    
    if drop_all_tables():
        print("\n✅ All existing tables dropped successfully.")
    else:
        print("\n❌ Failed to drop tables. Check the logs for details.")
        sys.exit(1)
    
    if run_data_migration():
        print("\n✅ Database setup completed successfully!")
    else:
        print("\n❌ Database setup failed. Check the logs for details.") 