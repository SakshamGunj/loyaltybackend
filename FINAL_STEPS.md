# Final Steps for Using Supabase with Your Application

We've successfully set up the configuration files to use Supabase PostgreSQL with your application and verified that we can connect to the database using the test script. Here's a practical approach to complete the migration:

## 1. Set up environment variables

Create a `.env` file to store your database credentials:

```
# .env file
SUPABASE_PASSWORD=your_actual_password_here
```

## 2. Continue using SQLite for development

Since we're having issues with the direct Supabase connection in Alembic migrations, I recommend the following approach:

1. Continue using SQLite for local development and testing
2. Use Supabase for production deployments

This dual-database approach is common and will make development easier.

## 3. Set up your production environment to use Supabase

When deploying to production:

```bash
# Set this environment variable in your production environment
export SUPABASE_PASSWORD=your_actual_password_here
```

## 4. Manual database setup in Supabase

### Option A: Use Supabase SQL Editor to create schema

1. Extract your current SQLite schema using:
```bash
sqlite3 loyalty.db .schema > schema.sql
```

2. Modify the schema.sql file to use PostgreSQL syntax:
   - Replace `INTEGER PRIMARY KEY` with `SERIAL PRIMARY KEY`
   - Replace `DATETIME` with `TIMESTAMP`
   - Remove SQLite-specific statements

3. Run the modified SQL in Supabase's SQL Editor

### Option B: Use the Supabase migration tool

1. Export your data using the provided `data_migration.py` script:
```powershell
$env:SUPABASE_PASSWORD="your_actual_password_here"
python data_migration.py
```

## 5. Test your application with both databases

For local development:
```bash
# SQLite (default when SUPABASE_PASSWORD is not set)
uvicorn app.main:app --reload
```

For production:
```bash
# PostgreSQL (when SUPABASE_PASSWORD is set)
SUPABASE_PASSWORD=your_password uvicorn app.main:app
```

## 6. Additional considerations

### Database-specific features

Be mindful of database-specific features:
- SQLite is more forgiving with data types
- PostgreSQL has stricter type checking
- Transactions and constraints may behave differently

### Connection pooling

For production, consider implementing connection pooling:
```python
# In database.py
if not DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        pool_pre_ping=True
    )
```

### Environment-specific configuration

Your code already detects cloud environments (Cloud Run, App Engine, Koyeb). Make sure to set the `SUPABASE_PASSWORD` environment variable in those environments.

### Security best practices

1. Never commit your database password to version control
2. Use environment variables for sensitive information
3. Consider using a secret management service for production credentials
4. Enable SSL/TLS for all database connections

## 7. Next steps for full migration

When you're ready to fully migrate to Supabase:

1. Export all data from SQLite
2. Import data to Supabase
3. Test extensively in a staging environment
4. Switch production configuration to use Supabase

Remember that the main advantage of your current setup is that it can work with both databases seamlessly, falling back to SQLite when Supabase credentials aren't available. 