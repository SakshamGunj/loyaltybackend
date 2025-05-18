"""
Script to modify the existing database structure to match the model
"""
import psycopg2
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("fix_database")

# Render PostgreSQL connection details
RENDER_USER = "tenversepos_user"
RENDER_PASSWORD = "00TrCMA1p1vsgiib0s3GTe6u8iYZ6Kzt"
RENDER_HOST = "dpg-d0kstu7fte5s738vuil0-a.oregon-postgres.render.com"
RENDER_DBNAME = "tenversepos"

def main():
    print("\n" + "=" * 80)
    print(" DATABASE STRUCTURE FIX ".center(80, "="))
    print("=" * 80 + "\n")
    
    try:
        # Connect directly with psycopg2
        conn_string = f"host={RENDER_HOST} port=5432 dbname={RENDER_DBNAME} user={RENDER_USER} password={RENDER_PASSWORD}"
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Connected to the database successfully")
        
        # Check the current users table structure
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'")
        columns = [row[0] for row in cursor.fetchall()]
        print(f"Current columns in users table: {columns}")
        
        # Add number column if it doesn't exist
        if 'number' not in columns:
            print("Adding 'number' column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS number VARCHAR")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_number ON users (number)")
            print("✅ Added 'number' column to users table")
        else:
            print("'number' column already exists in users table")
        
        # Add restaurant_id column if it doesn't exist
        if 'restaurant_id' not in columns:
            print("Adding 'restaurant_id' column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS restaurant_id VARCHAR")
            print("✅ Added 'restaurant_id' column to users table")
        else:
            print("'restaurant_id' column already exists in users table")
            
        # Add designation column if it doesn't exist
        if 'designation' not in columns:
            print("Adding 'designation' column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS designation VARCHAR")
            print("✅ Added 'designation' column to users table")
        else:
            print("'designation' column already exists in users table")
            
        # Add permissions column if it doesn't exist
        if 'permissions' not in columns:
            print("Adding 'permissions' column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS permissions JSONB")
            print("✅ Added 'permissions' column to users table")
        else:
            print("'permissions' column already exists in users table")
        
        # Check the current verified_phone_numbers table structure
        try:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'verified_phone_numbers'")
            columns = [row[0] for row in cursor.fetchall()]
            print(f"Current columns in verified_phone_numbers table: {columns}")
            
            # Rename phone_number column to number if it exists
            if 'phone_number' in columns and 'number' not in columns:
                print("Renaming 'phone_number' column to 'number' in verified_phone_numbers table...")
                cursor.execute("ALTER TABLE verified_phone_numbers RENAME COLUMN phone_number TO number")
                print("✅ Renamed 'phone_number' column to 'number' in verified_phone_numbers table")
            elif 'number' in columns:
                print("'number' column already exists in verified_phone_numbers table")
            else:
                print("Neither 'phone_number' nor 'number' column found in verified_phone_numbers table")
        except Exception as e:
            print(f"Error checking verified_phone_numbers table: {e}")
        
        # Check the current restaurants table structure
        try:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'restaurants'")
            columns = [row[0] for row in cursor.fetchall()]
            print(f"Current columns in restaurants table: {columns}")
            
            # Add contact_phone column if it doesn't exist
            if 'contact_phone' not in columns:
                print("Adding 'contact_phone' column to restaurants table...")
                cursor.execute("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS contact_phone VARCHAR")
                print("✅ Added 'contact_phone' column to restaurants table")
            else:
                print("'contact_phone' column already exists in restaurants table")
                
            # Add email column if it doesn't exist
            if 'email' not in columns:
                print("Adding 'email' column to restaurants table...")
                cursor.execute("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS email VARCHAR")
                print("✅ Added 'email' column to restaurants table")
                
            # Add tax_id column if it doesn't exist
            if 'tax_id' not in columns:
                print("Adding 'tax_id' column to restaurants table...")
                cursor.execute("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS tax_id VARCHAR")
                print("✅ Added 'tax_id' column to restaurants table")
                
            # Add currency column if it doesn't exist
            if 'currency' not in columns:
                print("Adding 'currency' column to restaurants table...")
                cursor.execute("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS currency VARCHAR DEFAULT 'INR'")
                print("✅ Added 'currency' column to restaurants table")
                
            # Add timezone column if it doesn't exist
            if 'timezone' not in columns:
                print("Adding 'timezone' column to restaurants table...")
                cursor.execute("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS timezone VARCHAR DEFAULT 'Asia/Kolkata'")
                print("✅ Added 'timezone' column to restaurants table")
                
            # Add points_per_spin column if it doesn't exist
            if 'points_per_spin' not in columns:
                print("Adding 'points_per_spin' column to restaurants table...")
                cursor.execute("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS points_per_spin FLOAT DEFAULT 1.0")
                print("✅ Added 'points_per_spin' column to restaurants table")
                
            # Add spend_thresholds column if it doesn't exist
            if 'spend_thresholds' not in columns:
                print("Adding 'spend_thresholds' column to restaurants table...")
                cursor.execute("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS spend_thresholds JSONB DEFAULT '[]'::jsonb")
                print("✅ Added 'spend_thresholds' column to restaurants table")
                
            # Add opening_time column if it doesn't exist
            if 'opening_time' not in columns:
                print("Adding 'opening_time' column to restaurants table...")
                cursor.execute("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS opening_time VARCHAR")
                print("✅ Added 'opening_time' column to restaurants table")
                
            # Add closing_time column if it doesn't exist
            if 'closing_time' not in columns:
                print("Adding 'closing_time' column to restaurants table...")
                cursor.execute("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS closing_time VARCHAR")
                print("✅ Added 'closing_time' column to restaurants table")
                
            # Add is_open column if it doesn't exist
            if 'is_open' not in columns:
                print("Adding 'is_open' column to restaurants table...")
                cursor.execute("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS is_open BOOLEAN DEFAULT TRUE")
                print("✅ Added 'is_open' column to restaurants table")
                
            # Add weekly_off_days column if it doesn't exist
            if 'weekly_off_days' not in columns:
                print("Adding 'weekly_off_days' column to restaurants table...")
                cursor.execute("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS weekly_off_days JSONB DEFAULT '[]'::jsonb")
                print("✅ Added 'weekly_off_days' column to restaurants table")
                
            # Add accepted_payment_modes column if it doesn't exist
            if 'accepted_payment_modes' not in columns:
                print("Adding 'accepted_payment_modes' column to restaurants table...")
                cursor.execute("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS accepted_payment_modes JSONB DEFAULT '[]'::jsonb")
                print("✅ Added 'accepted_payment_modes' column to restaurants table")
                
            # Add allow_manual_discount column if it doesn't exist
            if 'allow_manual_discount' not in columns:
                print("Adding 'allow_manual_discount' column to restaurants table...")
                cursor.execute("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS allow_manual_discount BOOLEAN DEFAULT FALSE")
                print("✅ Added 'allow_manual_discount' column to restaurants table")
                
            # Add bill_number_prefix column if it doesn't exist
            if 'bill_number_prefix' not in columns:
                print("Adding 'bill_number_prefix' column to restaurants table...")
                cursor.execute("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS bill_number_prefix VARCHAR")
                print("✅ Added 'bill_number_prefix' column to restaurants table")
                
            # Add bill_series_start column if it doesn't exist
            if 'bill_series_start' not in columns:
                print("Adding 'bill_series_start' column to restaurants table...")
                cursor.execute("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS bill_series_start INTEGER DEFAULT 1")
                print("✅ Added 'bill_series_start' column to restaurants table")
                
            # Add show_tax_breakdown_on_invoice column if it doesn't exist
            if 'show_tax_breakdown_on_invoice' not in columns:
                print("Adding 'show_tax_breakdown_on_invoice' column to restaurants table...")
                cursor.execute("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS show_tax_breakdown_on_invoice BOOLEAN DEFAULT FALSE")
                print("✅ Added 'show_tax_breakdown_on_invoice' column to restaurants table")
                
            # Add enable_tips_collection column if it doesn't exist
            if 'enable_tips_collection' not in columns:
                print("Adding 'enable_tips_collection' column to restaurants table...")
                cursor.execute("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS enable_tips_collection BOOLEAN DEFAULT FALSE")
                print("✅ Added 'enable_tips_collection' column to restaurants table")
                
            # Add admin_uid column if it doesn't exist
            if 'admin_uid' not in columns:
                print("Adding 'admin_uid' column to restaurants table...")
                cursor.execute("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS admin_uid VARCHAR")
                print("✅ Added 'admin_uid' column to restaurants table")
                
        except Exception as e:
            print(f"Error checking/updating restaurants table: {e}")
        
        print("\n✅ Database structure updated successfully!")
        
    except Exception as e:
        print(f"\n❌ Error updating database structure: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    main() 