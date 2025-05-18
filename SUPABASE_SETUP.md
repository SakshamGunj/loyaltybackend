# Supabase PostgreSQL Setup Guide

This guide explains how to set up and use Supabase PostgreSQL with your loyalty backend application.

## Overview

Your application now uses **Supabase PostgreSQL** for both local development and production environments. The connection has been configured and tested.

## Setting Up Your Environment

### Password Management

Your Supabase password needs to be set as an environment variable:

#### Option 1: Set the environment variable directly

In PowerShell:
```powershell
$env:SUPABASE_PASSWORD="your_password_here"
```

In Command Prompt:
```cmd
set SUPABASE_PASSWORD=your_password_here
```

In Bash/Linux:
```bash
export SUPABASE_PASSWORD="your_password_here"
```

#### Option 2: Use the startup script (recommended)

We've created a comprehensive startup script that will handle setting the password:

```powershell
python start_app.py
```

The script will:
1. Prompt for your password if not already set
2. Test the database connection
3. Start the application with proper configuration

## Running the Application

### Option 1: Using the start_app.py script (recommended)

```powershell
# Start with default settings (port 8000, auto-reload enabled)
python start_app.py

# Custom port
python start_app.py --port 8080

# Disable auto-reload for production
python start_app.py --no-reload

# Skip connection test
python start_app.py --skip-connection-test
```

### Option 2: Manual startup with uvicorn

```powershell
# Set password first
$env:SUPABASE_PASSWORD="your_password_here"

# Then start the application
uvicorn app.main:app --reload
```

## Troubleshooting

### Connection Issues

If you experience connection issues:

1. **Check your password**: Make sure it's correctly set in the environment variable
2. **Network connectivity**: Ensure you can reach the Supabase server
3. **IP restrictions**: Verify your IP is whitelisted in Supabase dashboard
4. **Run the test script**: Use `python simple_test.py` to verify direct connection

### Debug Logs

The application will log connection details and errors. Look for:

- Failed connection attempts with specific error messages
- Successful connection validations
- Database URL being used (with password redacted)

## Database Migration

If you need to run migrations:

```powershell
# Set password first
$env:SUPABASE_PASSWORD="your_password_here"

# Run migrations
alembic upgrade head
```

## Connection Details

Your application uses the following connection parameters:

- **Host**: aws-0-ap-south-1.pooler.supabase.com
- **Port**: 5432
- **Database**: postgres
- **User**: postgres.kkflibczahdddnaujjlz
- **SSL Mode**: require

## Connection Pooling

The application uses SQLAlchemy's connection pooling with these settings:

- **Pool Size**: 10
- **Max Overflow**: 20
- **Pool Recycle**: 3600 seconds (1 hour)
- **Pool Pre-Ping**: Enabled

These settings help optimize database performance and manage connections efficiently.

## Security Notes

1. Never hardcode the database password in your code
2. Do not commit the `.env` file or any file containing your password
3. In production, use a secure method for managing environment variables
4. Consider using a secrets manager for production environments 