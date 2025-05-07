# Deployment Guide for Loyalty Backend

This guide outlines how to deploy the Loyalty Backend to Google Cloud.

## Prerequisites

1. Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install
2. Create a Google Cloud account and project
3. Enable the following APIs in your project:
   - Cloud Run API
   - Cloud SQL Admin API
   - Cloud Build API

## Option 1: Deploy to Google Cloud Run (Recommended)

### Set Up Cloud SQL

1. Create a PostgreSQL Cloud SQL instance:

```bash
gcloud sql instances create loyalty-db \
  --database-version=POSTGRES_13 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --storage-size=10GB \
  --storage-type=SSD
```

2. Set a root password (remember this):

```bash
gcloud sql users set-password postgres \
  --instance=loyalty-db \
  --password=YOUR_SECURE_PASSWORD
```

3. Create a database:

```bash
gcloud sql databases create loyalty \
  --instance=loyalty-db
```

### Securely Store Firebase Credentials

1. Create a Secret in Secret Manager:

```bash
# First, convert the credentials file to a string
CREDS=$(cat deploy/firebase-credentials.json)

# Create the secret
gcloud secrets create firebase-service-account \
  --replication-policy="automatic" \
  --data-file="deploy/firebase-credentials.json"
```

2. You have three options for configuring Firebase credentials:

   a. **Secret Manager (recommended for production):**
   ```bash
   # When deploying to Cloud Run
   gcloud run deploy loyalty-backend \
     --image gcr.io/YOUR_PROJECT_ID/loyalty-backend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars="DB_USER=postgres,DB_PASS=YOUR_SECURE_PASSWORD,DB_NAME=loyalty" \
     --set-env-vars="CLOUD_SQL_CONNECTION_NAME=YOUR_PROJECT_ID:us-central1:loyalty-db" \
     --add-cloudsql-instances=YOUR_PROJECT_ID:us-central1:loyalty-db \
     --update-secrets="FIREBASE_SERVICE_ACCOUNT=firebase-service-account:latest"
   ```

   b. **Environment Variable with JSON content:**
   ```bash
   # Get the content of your credentials file
   CREDS=$(cat deploy/firebase-credentials.json | jq -c . | sed 's/"/\\"/g')
   
   # Set it as an environment variable when deploying
   gcloud run deploy loyalty-backend \
     --image gcr.io/YOUR_PROJECT_ID/loyalty-backend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars="DB_USER=postgres,DB_PASS=YOUR_SECURE_PASSWORD,DB_NAME=loyalty" \
     --set-env-vars="CLOUD_SQL_CONNECTION_NAME=YOUR_PROJECT_ID:us-central1:loyalty-db" \
     --add-cloudsql-instances=YOUR_PROJECT_ID:us-central1:loyalty-db \
     --set-env-vars="FIREBASE_SERVICE_ACCOUNT=${CREDS}"
   ```

   c. **Mount as a file (for App Engine):**
   ```yaml
   # In app.yaml, specify the path
   env_variables:
     FIREBASE_CREDENTIALS_PATH: "/path/in/container/credentials.json"
   ```

### Deploy to Cloud Run

1. Build and deploy using Cloud Build:

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/loyalty-backend
```

2. Deploy to Cloud Run with the SQL connection:

```bash
gcloud run deploy loyalty-backend \
  --image gcr.io/YOUR_PROJECT_ID/loyalty-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="DB_USER=postgres,DB_PASS=YOUR_SECURE_PASSWORD,DB_NAME=loyalty" \
  --set-env-vars="CLOUD_SQL_CONNECTION_NAME=YOUR_PROJECT_ID:us-central1:loyalty-db" \
  --add-cloudsql-instances=YOUR_PROJECT_ID:us-central1:loyalty-db \
  --update-secrets="FIREBASE_SERVICE_ACCOUNT=firebase-service-account:latest"
```

## Option 2: Deploy to App Engine

This option is simpler but has less flexibility.

1. Update the app.yaml file with your environment variables:

```yaml
env_variables:
  DB_USER: "postgres"
  DB_PASS: "YOUR_SECURE_PASSWORD"
  DB_NAME: "loyalty"
  CLOUD_SQL_CONNECTION_NAME: "YOUR_PROJECT_ID:us-central1:loyalty-db"
  FIREBASE_SERVICE_ACCOUNT: "YOUR_ESCAPED_JSON_STRING"
```

2. Deploy the application:

```bash
gcloud app deploy
```

## Database Migrations

Before the application can work, you need to apply migrations to the database:

1. For Cloud Run, you need to run migrations as a one-time job:

```bash
gcloud builds submit --config cloudbuild-migrate.yaml
```

2. For App Engine, use a separate service for migrations.

## Testing the Deployment

1. Check your deployment URL:

```bash
gcloud run services describe loyalty-backend --platform managed --region us-central1 --format "value(status.url)"
```

2. Visit the URL in your browser and append `/docs` to access the Swagger UI.

## Troubleshooting

### Database Connection Issues

If you see errors connecting to the database:

- Verify your Cloud SQL connection name
- Check that the service account has the Cloud SQL Client role
- Confirm the database name, username, and password are correct

### Firebase Authentication Issues

If Firebase authentication fails:

- Check that your Firebase credentials are valid
- Verify the FIREBASE_SERVICE_ACCOUNT environment variable contains correct JSON
- Ensure your Firebase project has the Authentication service enabled
- Check if the Firebase credentials have the correct permissions to verify tokens
- Look for "initialize_firebase" errors in the logs which may indicate credential issues

For local development:
```bash
# Export Firebase credentials as environment variable
export FIREBASE_SERVICE_ACCOUNT=$(cat deploy/firebase-credentials.json)

# Or set path to credentials file
export FIREBASE_CREDENTIALS_PATH=deploy/firebase-credentials.json
```

## Monitoring and Logging

View logs for your service:

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=loyalty-backend" --limit 10
```

Monitor service performance in the Google Cloud Console. 