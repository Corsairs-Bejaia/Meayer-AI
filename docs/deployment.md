# Deployment Guide

This document explains how to deploy the AI Verification Service to production environments.

## Deploying to Railway

The repository is pre-configured for [Railway](https://railway.app/).

### 1. Prerequisites
- A Railway account.
- Your project pushed to a GitHub repository.

### 2. Steps to Deploy
1. **Connect to GitHub**: In Railway, create a "New Project" and select "Deploy from GitHub repo".
2. **Configure Environment Variables**: Add the following variables in the Railway "Variables" tab:
   - `GOOGLE_API_KEY`: Your Gemini AI key.
   - `LOG_LEVEL`: `info` or `debug`.
   - `VERSION`: `1.0.0`.
   - `SERVICE_NAME`: `Verification-Service`.
3. **Deploy**: Railway will automatically detect the `Dockerfile` and `railway.toml` at the root of the project.

### 3. Monitoring
- **Health Checks**: The service includes a health check at `/api/health`. Railway is configured to monitor this path.
- **Logs**: Real-time logs are available in the Railway dashboard.

## Manual Docker Deployment

If you prefer to run the container manually:

```bash
# Build the image from the root directory
docker build -t verification-service .

# Run the container
docker run -p 8000:8001 --env-file .env verification-service
```
