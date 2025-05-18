import os
import psycopg2
import urllib.parse

# Get password
password = os.environ.get('SUPABASE_PASSWORD', 'Gunj7250504240@')

# URL encode the password
url_encoded_password = urllib.parse.quote_plus(password)

print(f"Original password: {password}")
print(f"URL encoded password: {url_encoded_password}")

# Connection parameters
host = "aws-0-ap-south-1.pooler.supabase.com"
user = "postgres.kkflibczahdddnaujjlz"

# Try with URL encoded password
print("\nAttempting connection with URL encoded password...")
try:
    conn_string = f"host={host} port=5432 dbname=postgres user={user} password={url_encoded_password} sslmode=require"
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    cursor.execute("SELECT version()")
    version = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    print("✅ Connection successful with URL encoded password!")
except Exception as e:
    print(f"❌ Connection failed with URL encoded password: {e}")

# Try with original password
print("\nAttempting connection with original password...")
try:
    conn_string = f"host={host} port=5432 dbname=postgres user={user} password={password} sslmode=require"
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    cursor.execute("SELECT version()")
    version = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    print("✅ Connection successful with original password!")
except Exception as e:
    print(f"❌ Connection failed with original password: {e}") 