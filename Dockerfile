FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Environment variables for Firebase config will be provided at runtime
# via Cloud Run deployment command with --set-env-vars or --update-secrets

# Run the application
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT} 