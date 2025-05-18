"""
Standalone test script for Render PostgreSQL connection
"""
import psycopg2
from sqlalchemy import create_engine, text

def main():
    print("\n" + "=" * 80)
    print(" RENDER POSTGRESQL CONNECTION TESTER ".center(80, "="))
    print("=" * 80 + "\n")
    
    # Connection details
    user = "tenversepos_user"
    password = "00TrCMA1p1vsgiib0s3GTe6u8iYZ6Kzt"
    host = "dpg-d0kstu7fte5s738vuil0-a.oregon-postgres.render.com"
    dbname = "tenversepos"
    url = f"postgresql://{user}:{password}@{host}:5432/{dbname}"
    
    # Test direct connection
    print("\n===== TESTING DIRECT CONNECTION =====")
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
        direct_ok = True
    except Exception as e:
        print(f"❌ Direct connection failed: {e}")
        direct_ok = False
    
    # Test SQLAlchemy connection
    print("\n===== TESTING SQLALCHEMY CONNECTION =====")
    try:
        engine = create_engine(url, pool_size=5, max_overflow=10)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
        
        print("✅ SQLAlchemy connection successful!")
        print(f"Version: {version}")
        sqlalchemy_ok = True
    except Exception as e:
        print(f"❌ SQLAlchemy connection failed: {e}")
        sqlalchemy_ok = False
    
    # Summary
    if direct_ok and sqlalchemy_ok:
        print("\n✅ All connection tests passed!")
    else:
        print("\n❌ Some connection tests failed. Please check your connection settings.")

if __name__ == "__main__":
    main() 