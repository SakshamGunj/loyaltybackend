# Migrating from SQLite to Supabase PostgreSQL

This guide explains how to migrate your loyalty backend application from SQLite to Supabase PostgreSQL.

## Current Configuration 

The application is currently configured to use SQLite for local development. This works well for testing purposes but has limitations for production use.

## Prerequisites

1. A Supabase account and project
2. The correct Supabase connection string from your Supabase dashboard

## Step 1: Locate your Supabase connection information

1. Go to your Supabase dashboard: https://app.supabase.com/
2. Select your project 
3. Navigate to "Project Settings" > "Database"
4. Look for the connection string in the "Connection Pooling" or "Connection string" section
   - It should look something like: `postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`
5. Make sure you have either:
   - Set up "Network Restrictions" to allow your IP address
   - Or disabled "Database Network Restrictions" to allow all IPs (not recommended for production)

## Step 2: Update database.py with the correct connection string

1. Open `app/database.py`
2. Replace the SUPABASE_URL constant with your correct connection string:

```python
# Use Supabase PostgreSQL URL, falling back to SQLite for local development if not set
SUPABASE_URL = "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres"
DATABASE_URL = os.getenv("DATABASE_URL", SUPABASE_URL)
```

## Step 3: Update alembic configuration

1. Open `alembic.ini` and update the `sqlalchemy.url` with your connection string:

```ini
sqlalchemy.url = postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
```

2. Open `alembic/env.py` and uncomment or update the Supabase URL:

```python
# Override the URL with environment variable if present
if os.environ.get('DATABASE_URL'):
    config.set_main_option('sqlalchemy.url', os.environ.get('DATABASE_URL'))
else:
    # Use Supabase URL as a default if not set in environment
    supabase_url = "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres"
    config.set_main_option('sqlalchemy.url', supabase_url)
```

## Step 4: Test your connection

1. Run the `supabase_test.py` script to verify your connection works:

```bash
python supabase_test.py
```

2. If successful, you should see:
   ```
   Connection successful!
   PostgreSQL version: [version info]
   Connection closed successfully.
   ```

## Step 5: Run migrations

1. Run your Alembic migrations to set up the database schema:

```bash
alembic upgrade head
```

## Step 6: Migrate existing data (optional)

If you need to migrate existing data from SQLite to PostgreSQL:

1. Use a tool like `pgloader` (for simple migrations)
2. Or write a custom Python script that reads from SQLite and writes to PostgreSQL

## Step 7: Update application configuration

1. For local development, you can continue using the default Supabase URL
2. For production deployment, set the `DATABASE_URL` environment variable

## Troubleshooting

### Cannot connect to Supabase

1. Verify your connection string is correct
2. Check if your IP is allowed in Supabase network settings
3. Ensure your password is correctly encoded in the URL
4. Try connecting with a different PostgreSQL client like pgAdmin

### Migration errors

1. If you encounter migration errors, the schema might be different between SQLite and PostgreSQL
2. You may need to reset your migrations or create a new migration specific to PostgreSQL

### Increased latency

1. If your application seems slower, it may be due to network latency to the Supabase servers
2. Consider implementing caching or connection pooling for frequently accessed data 