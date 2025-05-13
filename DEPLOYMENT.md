# Loyalty Backend API Deployment Guide

This document provides instructions for deploying the Loyalty Backend API to Koyeb.

## Deployment on Koyeb

### Prerequisites
- A Koyeb account
- Your codebase pushed to a Git repository (GitHub, GitLab, Bitbucket)

### Deployment Steps

1. **Sign in to Koyeb**
   - Go to [app.koyeb.com/auth/signin](https://app.koyeb.com/auth/signin)
   - Sign in with your account

2. **Create a new App**
   - Click on "Create App" button
   - Select "GitHub" as the deployment method
   - Connect your GitHub account if needed
   - Select this repository

3. **Configure Deployment Settings**
   - Name: `loyalty-backend`
   - Region: Select the region closest to your users
   - Instance Type: Select based on your needs (start with Nano)

4. **Configure Build Settings**
   - Build: Use "Buildpack"
   - Runtime: Select "Python"
   - Service Name: `api`
   - Ports: `8000`

5. **Environment Variables**
   At minimum, set the following:
   - `JWT_SECRET`: A secure random string for JWT token generation
   - `ENVIRONMENT`: `production`

6. **Add Persistent Storage (Optional but Recommended)**
   - Go to the "Advanced" section
   - Add a Volume:
     - Mount Path: `/app/data`
     - Size: 1GB (or as needed)

7. **Deploy**
   - Click "Deploy" and wait for the build to complete

8. **Access Your Application**
   - Once deployed, click on the URL provided by Koyeb
   - Test the health endpoint at `/health`
   - API will be available at the provided domain

## Environment Variables

| Name | Description | Default |
|------|-------------|---------|
| `JWT_SECRET` | Secret key for JWT tokens | (required) |
| `ENVIRONMENT` | Application environment | development |
| `APP_VERSION` | Application version | 1.0.0 |
| `DATABASE_URL` | Database connection string | sqlite:///./loyalty.db |

## Health Check

The application provides a health check endpoint at `/health` that can be used by monitoring tools.

## Monitoring

The `/health` endpoint returns the status of critical components:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "database": "healthy"
}
```

## Backup and Restore

When using persistent storage on Koyeb, your SQLite database will be stored in `/app/data/loyalty.db`. 
You should set up a backup strategy to regularly export this data.

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Koyeb Documentation](https://www.koyeb.com/docs)
- [SQLite Documentation](https://www.sqlite.org/docs.html) 