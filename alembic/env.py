from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
import os
import sys
import getpass

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.models import Base
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# Override the URL with environment variable if present
if os.environ.get('DATABASE_URL'):
    config.set_main_option('sqlalchemy.url', os.environ.get('DATABASE_URL'))
elif os.environ.get('SUPABASE_PASSWORD'):
    # Use the password from environment variable
    url = config.get_main_option('sqlalchemy.url')
    if 'postgresql://' in url and '@' in url:
        user_part = url.split('@')[0].replace('postgresql://', '')
        host_part = url.split('@')[1]
        
        # Insert password after the username
        if ':' in user_part and user_part.endswith(':'):
            # URL already has colon for password placeholder
            user_with_pass = f"{user_part}{os.environ.get('SUPABASE_PASSWORD')}"
        else:
            # Need to add colon
            user_with_pass = f"{user_part}:{os.environ.get('SUPABASE_PASSWORD')}"
            
        # Make sure we're using TCP/IP connection (not Unix socket)
        # Extract host and append extra parameters if needed
        if '?' in host_part:
            host_base, params = host_part.split('?', 1)
            if 'host=' not in params:
                host_part = f"{host_base}?host={host_base.split(':')[0]}&{params}"
        else:
            # No existing parameters, just add the host parameter
            host_name = host_part.split(':')[0]
            host_part = f"{host_part}?host={host_name}"
            
        new_url = f"postgresql://{user_with_pass}@{host_part}"
        config.set_main_option('sqlalchemy.url', new_url)
else:
    # Prompt for password if not in environment
    try:
        url = config.get_main_option('sqlalchemy.url')
        if 'postgresql://' in url and '@' in url:
            print("Database password required for Supabase connection.")
            password = getpass.getpass("Enter your Supabase database password: ")
            
            user_part = url.split('@')[0].replace('postgresql://', '')
            host_part = url.split('@')[1]
            
            # Insert password
            if ':' in user_part and user_part.endswith(':'):
                user_with_pass = f"{user_part}{password}"
            else:
                user_with_pass = f"{user_part}:{password}"
            
            # Make sure we're using TCP/IP connection (not Unix socket)
            # Extract host and append extra parameters if needed
            if '?' in host_part:
                host_base, params = host_part.split('?', 1)
                if 'host=' not in params:
                    host_part = f"{host_base}?host={host_base.split(':')[0]}&{params}"
            else:
                # No existing parameters, just add the host parameter
                host_name = host_part.split(':')[0]
                host_part = f"{host_part}?host={host_name}"
                
            new_url = f"postgresql://{user_with_pass}@{host_part}"
            config.set_main_option('sqlalchemy.url', new_url)
    except:
        # If we can't get a password (e.g., in a non-interactive environment)
        # Fall back to SQLite for safety
        print("WARNING: No database password provided. Falling back to SQLite.")
        config.set_main_option('sqlalchemy.url', "sqlite:///./loyalty.db")

def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
