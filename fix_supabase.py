"""
Special script to fix the Supabase connection issues
"""
import os
import sys
import psycopg2
from sqlalchemy import create_engine, text
from getpass import getpass

def test_direct_connection(password):
    """Test direct connection with psycopg2"""
    print("\n===== TESTING DIRECT CONNECTION =====")
    host = "aws-0-ap-south-1.pooler.supabase.com"
    user = "postgres.kkflibczahdddnaujjlz"
    
    try:
        print(f"Connecting with password: {password}")
        conn_string = f"host={host} port=5432 dbname=postgres user={user} password={password} sslmode=require"
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        print("✅ Direct connection successful!")
        return True
    except Exception as e:
        print(f"❌ Direct connection failed: {e}")
        return False

def test_sqlalchemy_connection(password):
    """Test SQLAlchemy connection"""
    print("\n===== TESTING SQLALCHEMY CONNECTION =====")
    host = "aws-0-ap-south-1.pooler.supabase.com"
    user = "postgres.kkflibczahdddnaujjlz"
    
    try:
        print(f"Connecting with password: {password}")
        db_url = f"postgresql://{user}:{password}@{host}:5432/postgres?host={host}"
        engine = create_engine(db_url, pool_size=5, max_overflow=10)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
        
        print("✅ SQLAlchemy connection successful!")
        print(f"Version: {version}")
        return True
    except Exception as e:
        print(f"❌ SQLAlchemy connection failed: {e}")
        return False

def create_database_py_with_password(password):
    """Create a temporary database.py file with hardcoded password"""
    print("\n===== CREATING TEMPORARY database.py WITH PASSWORD =====")
    app_folder = os.path.join(os.getcwd(), "app")
    db_py_path = os.path.join(app_folder, "database.py")
    
    # Create backup of original file
    backup_path = db_py_path + ".backup"
    if not os.path.exists(backup_path):
        with open(db_py_path, 'r') as f:
            content = f.read()
        with open(backup_path, 'w') as f:
            f.write(content)
        print(f"✅ Backup created at {backup_path}")
    
    # Read the current file
    with open(db_py_path, 'r') as f:
        lines = f.readlines()
    
    # Modify the file
    for i, line in enumerate(lines):
        if "SUPABASE_PASSWORD = os.getenv(" in line:
            lines[i] = f'SUPABASE_PASSWORD = "{password}"  # Hardcoded for testing\n'
            print(f"✅ SUPABASE_PASSWORD hardcoded in database.py")
            break
    
    # Write the modified file
    with open(db_py_path, 'w') as f:
        f.writelines(lines)
    
    print("✅ database.py updated successfully")
    return True

def restore_database_py():
    """Restore the original database.py file"""
    print("\n===== RESTORING ORIGINAL database.py =====")
    app_folder = os.path.join(os.getcwd(), "app")
    db_py_path = os.path.join(app_folder, "database.py")
    backup_path = db_py_path + ".backup"
    
    if os.path.exists(backup_path):
        with open(backup_path, 'r') as f:
            content = f.read()
        with open(db_py_path, 'w') as f:
            f.write(content)
        print(f"✅ Original database.py restored from {backup_path}")
        return True
    else:
        print("❌ No backup file found")
        return False

def main():
    """Main function to fix Supabase connection issues"""
    print("\n" + "=" * 80)
    print(" SUPABASE CONNECTION FIXER ".center(80, "="))
    print("=" * 80 + "\n")
    
    password = os.environ.get("SUPABASE_PASSWORD")
    if not password:
        password = getpass("Enter your Supabase password: ")
    
    print(f"Using password: {password}")
    
    # Test direct connection
    direct_ok = test_direct_connection(password)
    
    # Test SQLAlchemy connection
    sqlalchemy_ok = test_sqlalchemy_connection(password)
    
    if direct_ok and sqlalchemy_ok:
        print("\n✅ Both connection methods work! Your password is correct.")
        choice = input("\nDo you want to temporarily hardcode the password in database.py for testing? (y/n): ")
        if choice.lower() == 'y':
            create_database_py_with_password(password)
            print("\nNow run your application with: python -m uvicorn app.main:app --reload")
            print("\nIMPORTANT: When you're done testing, run this script again to restore the original file.")
        
    elif direct_ok:
        print("\n⚠️ Direct connection works but SQLAlchemy connection fails.")
        print("This might be an issue with connection string formatting.")
        
    else:
        print("\n❌ All connection methods failed. Please check your password and network connection.")
    
    # Check if user wants to restore from backup
    if os.path.exists(os.path.join(os.getcwd(), "app", "database.py.backup")):
        choice = input("\nDo you want to restore the original database.py file from backup? (y/n): ")
        if choice.lower() == 'y':
            restore_database_py()

if __name__ == "__main__":
    main() 