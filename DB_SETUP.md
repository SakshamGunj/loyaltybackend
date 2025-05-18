# Database Setup and Management

This document explains how to set up and manage the database for your loyalty backend application.

## Database Configuration

The application now uses **Supabase PostgreSQL** for both local development and production environments.

## Setting Up Your Environment

### Setting the Supabase Password

You need to set your Supabase database password for the application to connect to PostgreSQL:

#### Option 1: Using the Environment Variable Directly

In PowerShell:
```powershell
$env:SUPABASE_PASSWORD="your_actual_password_here"
```

In Command Prompt:
```cmd
set SUPABASE_PASSWORD=your_actual_password_here
```

In Bash/Linux:
```bash
export SUPABASE_PASSWORD="your_actual_password_here"
```

#### Option 2: Using the Helper Script

We've included a helper script to set the environment variable:

```powershell
python set_supabase_password.py
```

This will prompt you for your password and provide instructions for setting the environment variable.

### Testing the Database Connection

To test your Supabase PostgreSQL connection:

```powershell
python supabase_test.py
```

## Running the Application

### Using the Application Runner

The easiest way to run the application is with the `run_app.py` script:

```powershell
# Run with Supabase PostgreSQL (default)
python run_app.py

# Force using SQLite (not recommended, for emergency development only)
python run_app.py --db sqlite

# Run on a different port
python run_app.py --port 5000
```

### Manually Running with Uvicorn

```powershell
# Set the Supabase password first
$env:SUPABASE_PASSWORD="your_password_here"

# Then start the application
uvicorn app.main:app --reload
```

## Managing Database Migrations

We use Alembic for database migrations. The `run_migrations.py` script simplifies working with migrations:

### Running Migrations

```powershell
# Upgrade to the latest migration with Supabase (default)
python run_migrations.py upgrade

# Force using SQLite (not recommended)
python run_migrations.py upgrade --db sqlite
```

### Creating New Migrations

After making changes to your models, create a new migration:

```powershell
python run_migrations.py create "add_new_field_to_users"
```

This will prompt you to select which database to use for creating the migration. **Always prefer to create migrations against your production database** (Supabase PostgreSQL) to ensure compatibility.

## Data Migration

If you need to migrate data from SQLite to Supabase (one-time operation):

```powershell
$env:SUPABASE_PASSWORD="your_password_here"
python data_migration.py
```

## Troubleshooting

### Connection Issues

1. Verify your Supabase password in the Supabase dashboard
2. Make sure you're using the database password, not your Supabase account password
3. Check if special characters in your password need to be URL-encoded
4. Ensure your IP address is whitelisted in Supabase

### Database URL

You can explicitly specify the database URL by setting the `DATABASE_URL` environment variable:

```powershell
$env:DATABASE_URL="postgresql://postgres.kkflibczahdddnaujjlz:your_password@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"
```

### Pool Connection Settings

For production deployments, the application uses the following connection pool settings:
- Pool size: 10
- Max overflow: 20
- Pool recycle: 3600 seconds
- Pool pre-ping: Enabled

These settings help optimize database performance and connection management.

## Emergency Fallback to SQLite

In case of any issues with Supabase connectivity, you can still use SQLite as a temporary fallback for local development only. This is not recommended for production use.

```powershell
# Force application to use SQLite
python run_app.py --db sqlite

# Force migrations to use SQLite
python run_migrations.py upgrade --db sqlite
``` 