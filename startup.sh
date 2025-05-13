#!/bin/bash
set -e

echo "Starting Loyalty Backend application..."

# Run database migrations
echo "Running database migrations..."
python -m alembic upgrade head

# Start the application
echo "Starting web server..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT 