"""
Test script for Render PostgreSQL connection
"""
import psycopg2
from sqlalchemy import create_engine, text

RENDER_DB_URL = "postgresql://tenversepos_user:00TrCMA1p1vsgiib0s3GTe6u8iYZ6Kzt@dpg-d0kstu7fte5s738vuil0-a.oregon-postgres.render.com/tenversepos"

def test_direct_connection():
    """Test direct connection with psycopg2"""
    print("\n===== TESTING DIRECT CONNECTION =====")
    
    # Parse the connection URL
    user = "tenversepos_user"
    password = "00TrCMA1p1vsgiib0s3GTe6u8iYZ6Kzt"
    host = "dpg-d0kstu7fte5s738vuil0-a.oregon-postgres.render.com"
    dbname = "tenversepos"
    
    try:
        conn_string = f"host={host} port=5432 dbname={dbname} user={user} password={password}"
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"✅ Direct connection successful!")
        print(f"Version: {version}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Direct connection failed: {e}")
        return False

def test_sqlalchemy_connection():
    """Test SQLAlchemy connection"""
    print("\n===== TESTING SQLALCHEMY CONNECTION =====")
    
    try:
        engine = create_engine(RENDER_DB_URL, pool_size=5, max_overflow=10)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
        
        print("✅ SQLAlchemy connection successful!")
        print(f"Version: {version}")
        return True
    except Exception as e:
        print(f"❌ SQLAlchemy connection failed: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print(" RENDER POSTGRESQL CONNECTION TESTER ".center(80, "="))
    print("=" * 80 + "\n")
    
    # Test direct connection
    direct_ok = test_direct_connection()
    
    # Test SQLAlchemy connection
    sqlalchemy_ok = test_sqlalchemy_connection()
    
    if direct_ok and sqlalchemy_ok:
        print("\n✅ All connection tests passed!")
    else:
        print("\n❌ Some connection tests failed. Please check your connection settings.") 