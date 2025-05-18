"""
Simple connection test for Supabase PostgreSQL
"""
import os
import psycopg2
import time
import sys
import urllib.parse

def test_connection(use_url_encoding=True):
    # Get password from environment variable
    password = os.environ.get('SUPABASE_PASSWORD')
    if not password:
        print("Error: SUPABASE_PASSWORD environment variable is not set.")
        sys.exit(1)
    
    # URL encode the password if requested
    if use_url_encoding:
        password = urllib.parse.quote_plus(password)
        print("Using URL-encoded password")
    else:
        print("Using password as-is (not URL-encoded)")
    
    # Connection parameters
    params = {
        'host': 'aws-0-ap-south-1.pooler.supabase.com',
        'port': '5432',
        'database': 'postgres',
        'user': 'postgres.kkflibczahdddnaujjlz',
        'password': password,
        'sslmode': 'require',
    }

    print(f"Testing connection to {params['host']} with user {params['user']}...")
    
    try:
        # Construct connection string
        conn_string = f"host={params['host']} port={params['port']} dbname={params['database']} user={params['user']} password={params['password']} sslmode={params['sslmode']}"
        
        # Start timing
        start_time = time.time()
        
        # Connect to PostgreSQL
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        
        # Execute a simple query
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        
        # End timing
        end_time = time.time()
        
        # Close connection
        cursor.close()
        conn.close()
        
        # Print results
        print("✅ Connection successful!")
        print(f"PostgreSQL version: {version}")
        print(f"Connection time: {end_time - start_time:.2f} seconds")
        return True
        
    except Exception as e:
        # End timing
        end_time = time.time()
        
        # Print error
        print(f"❌ Connection failed: {e}")
        print(f"Time spent: {end_time - start_time:.2f} seconds")
        return False

if __name__ == "__main__":
    # Test with URL encoding first (which is how our app will connect)
    print("-" * 50)
    print("TEST 1: With URL encoding")
    success1 = test_connection(use_url_encoding=True)
    
    # Also test without URL encoding to see if direct psycopg2 connection behaves differently
    print("\n" + "-" * 50)
    print("TEST 2: Without URL encoding")
    success2 = test_connection(use_url_encoding=False)
    
    print("\n" + "-" * 50)
    if success1 and success2:
        print("Both connection methods successful!")
        sys.exit(0)
    elif success1:
        print("Only URL encoded connection successful.")
        sys.exit(0)  # Still exit with 0 since this is what the app will use
    elif success2:
        print("Only non-URL encoded connection successful. Application may fail!")
        sys.exit(1)
    else:
        print("All connection methods failed.")
        sys.exit(1) 