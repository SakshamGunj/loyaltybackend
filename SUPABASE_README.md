# Supabase PostgreSQL Migration Guide

## Overview

This project includes tools and instructions for migrating from SQLite to Supabase PostgreSQL. Follow the steps below to set up and test your Supabase connection.

## Files Included

1. `supabase_migration_guide.md` - Detailed step-by-step migration instructions
2. `supabase_test.py` - Tool to test your Supabase connection
3. `data_migration.py` - Script to migrate data from SQLite to PostgreSQL

## Quick Start

1. **Verify your Supabase connection details** in the [Supabase Dashboard](https://app.supabase.com/)
   - Get the connection string from Project Settings > Database
   - Ensure your IP is allowlisted in network settings

2. **Test your connection**:
   ```bash
   # Update the connection details in supabase_test.py first
   python supabase_test.py
   ```

3. **Configure your application**:
   - Update `app/database.py` with your Supabase URL
   - Update `alembic.ini` and `alembic/env.py` as described in the migration guide

4. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

5. **Migrate data** (optional):
   ```bash
   # Update connection details in data_migration.py first
   python data_migration.py
   ```

## Common Issues

### Connection Problems

- **DNS Resolution Error**: Verify the hostname is correct
- **Authentication Error**: Check your password and that your IP is allowed
- **SSL/TLS Error**: Ensure your Postgres driver supports SSL connections

### Data Type Differences

Be aware of these common SQLite to PostgreSQL data type differences:

- SQLite's `INTEGER PRIMARY KEY` becomes PostgreSQL's `SERIAL` or `BIGSERIAL`
- SQLite's `TEXT` becomes PostgreSQL's `TEXT` or `VARCHAR`
- SQLite handles booleans differently than PostgreSQL

### Performance Considerations

- Be aware of increased latency when connecting to a remote database
- Consider implementing connection pooling
- Review and optimize any database-intensive operations

## Need More Help?

- Review the full migration guide: `supabase_migration_guide.md`
- Consult [Supabase documentation](https://supabase.com/docs)
- Check [SQLAlchemy documentation](https://docs.sqlalchemy.org/) for specific PostgreSQL configuration