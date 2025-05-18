"""
Test script for Supabase PostgreSQL connection.
This will attempt to connect to your Supabase database and report any errors.
"""
import psycopg2
import sys
import os
from getpass import getpass

# Get password securely if not provided
password = os.environ.get('SUPABASE_PASSWORD')
if not password:
    try:
        password = getpass("Enter your Supabase database password: ")
    except:
        # If running in an environment where getpass doesn't work
        print("Please set your password in the 'password' variable below or as SUPABASE_PASSWORD environment variable")
        password = "YOUR_PASSWORD_HERE"  # Replace this with your actual password

# Supabase host
host = "aws-0-ap-south-1.pooler.supabase.com"

# Connection parameters - using explicit TCP/IP connection
params = {
    'host': host,  # Force TCP/IP connection
    'port': '5432',
    'database': 'postgres',
    'user': 'postgres.kkflibczahdddnaujjlz',
    'password': password,
    'sslmode': 'require',  # Force SSL for security
}

print(f"Attempting to connect to Supabase PostgreSQL database at {params['host']} with user {params['user']}...")

try:
    # Construct connection string explicitly
    conn_string = f"host={host} port={params['port']} dbname={params['database']} user={params['user']} password={password} sslmode={params['sslmode']}"
    
    # Attempt connection
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    
    # Try a simple query
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()
    
    print("Connection successful!")
    print(f"PostgreSQL version: {db_version[0]}")
    
    # Close communication with PostgreSQL database
    cursor.close()
    conn.close()
    
    # If we get here, connection was successful
    print("Connection closed successfully.")
    sys.exit(0)
    
except psycopg2.OperationalError as e:
    print(f"Connection failed: {e}")
    
    # Check if it's a DNS error
    if "could not translate host name" in str(e):
        print("\nPossible DNS resolution issue:")
        print("1. Verify the hostname is correct")
        print("2. Check your network connection")
        print("3. Try pinging the host manually")
    
    # Check if it's an authentication error
    elif "password authentication failed" in str(e) or "Wrong password" in str(e):
        print("\nAuthentication failed:")
        print("1. Verify your database password in the Supabase dashboard")
        print("2. Make sure you're using the database password, not your Supabase account password")
        print("3. Check if special characters in password need to be URL-encoded")
    
    # Other possible errors
    else:
        print("\nOther connection issues:")
        print("1. Check your firewall settings")
        print("2. Verify the port is correct (default is 5432)")
        print("3. Ensure your IP is allowed in Supabase network settings")
        print("4. Try the Transaction Pooler connection instead (port 6543)")
    
    sys.exit(1)
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1) 