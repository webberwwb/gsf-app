#!/bin/bash
# Deploy all services to GCP Cloud Run
# This is the single deployment script for the entire project
# Usage: ./deploy-all.sh [region] [service-account-key-path]

set -e

PROJECT_ID="focused-mote-477703-f0"
REGION=${1:-"us-central1"}
USE_SERVICE_ACCOUNT=${USE_SERVICE_ACCOUNT:-"true"}
SERVICE_ACCOUNT_KEY="${2:-instance/service_accounts/focused-mote-477703-f0-0571d061607f.json}"

echo "Deploying to project: $PROJECT_ID, region: $REGION"

# Always authenticate with service account first (required for Cloud Build)
if [ -f "$SERVICE_ACCOUNT_KEY" ]; then
    echo "Authenticating with service account: $SERVICE_ACCOUNT_KEY"
    gcloud auth activate-service-account --key-file="$SERVICE_ACCOUNT_KEY" || {
        echo "Error: Failed to authenticate with service account"
        exit 1
    }
else
    echo "Error: Service account key not found at $SERVICE_ACCOUNT_KEY"
    echo "Please ensure the service account key exists at: $SERVICE_ACCOUNT_KEY"
    exit 1
fi

# Set the project
gcloud config set project $PROJECT_ID

# Enable required APIs (skip if already enabled or if you don't have permission)
echo "Checking/enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com --project=$PROJECT_ID 2>/dev/null || echo "APIs may already be enabled or require additional permissions. Continuing..."

# Deploy Backend
echo "Building and deploying backend..."
cd backend
BUILD_OUTPUT=$(gcloud builds submit --tag gcr.io/$PROJECT_ID/gsf-app-backend --project=$PROJECT_ID 2>&1)
BUILD_EXIT=$?
echo "$BUILD_OUTPUT" | grep -v "ERROR: (gcloud.builds.submit)$" || true
if [ $BUILD_EXIT -ne 0 ] && ! echo "$BUILD_OUTPUT" | grep -q "ERROR: (gcloud.builds.submit)$"; then exit $BUILD_EXIT; fi
BACKEND_URL=$(gcloud run deploy gsf-app-backend \
    --image gcr.io/$PROJECT_ID/gsf-app-backend \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --add-cloudsql-instances $PROJECT_ID:us-central1:gsf-app-mysql \
    --set-env-vars MYSQL_DATABASE=gsf_app,GOOGLE_OAUTH_REDIRECT_URI=https://backend.grainstoryfarm.ca/api/auth/google/callback,ADMIN_FRONTEND_URL=https://admin.grainstoryfarm.ca \
    --project=$PROJECT_ID \
    --format="value(status.url)")

echo "Backend deployed at: $BACKEND_URL"

# Deploy Frontend
echo "Building and deploying frontend..."
cd ../app
BUILD_OUTPUT=$(gcloud builds submit --tag gcr.io/$PROJECT_ID/gsf-app-frontend --project=$PROJECT_ID 2>&1)
BUILD_EXIT=$?
echo "$BUILD_OUTPUT" | grep -v "ERROR: (gcloud.builds.submit)$" || true
if [ $BUILD_EXIT -ne 0 ] && ! echo "$BUILD_OUTPUT" | grep -q "ERROR: (gcloud.builds.submit)$"; then exit $BUILD_EXIT; fi
FRONTEND_URL=$(gcloud run deploy gsf-app-frontend \
    --image gcr.io/$PROJECT_ID/gsf-app-frontend \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars VITE_API_BASE_URL=$BACKEND_URL/api \
    --project=$PROJECT_ID \
    --format="value(status.url)")

echo "Frontend deployed at: $FRONTEND_URL"

# Deploy Admin
echo "Building and deploying admin..."
cd ../admin
BUILD_OUTPUT=$(gcloud builds submit --tag gcr.io/$PROJECT_ID/gsf-app-admin --project=$PROJECT_ID 2>&1)
BUILD_EXIT=$?
echo "$BUILD_OUTPUT" | grep -v "ERROR: (gcloud.builds.submit)$" || true
if [ $BUILD_EXIT -ne 0 ] && ! echo "$BUILD_OUTPUT" | grep -q "ERROR: (gcloud.builds.submit)$"; then exit $BUILD_EXIT; fi
ADMIN_URL=$(gcloud run deploy gsf-app-admin \
    --image gcr.io/$PROJECT_ID/gsf-app-admin \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars VITE_API_BASE_URL=$BACKEND_URL/api \
    --project=$PROJECT_ID \
    --format="value(status.url)")

echo "Admin deployed at: $ADMIN_URL"

# Map custom domain to frontend
echo "Mapping custom domain app.grainstoryfarm.ca to frontend..."
gcloud beta run domain-mappings create \
    --service gsf-app-frontend \
    --domain app.grainstoryfarm.ca \
    --region $REGION \
    --project=$PROJECT_ID 2>/dev/null || {
    echo "Domain mapping may already exist. Checking status..."
    gcloud beta run domain-mappings describe app.grainstoryfarm.ca \
        --region $REGION \
        --project=$PROJECT_ID 2>/dev/null && echo "Domain mapping exists!" || echo "Note: Domain mapping creation may require additional permissions. Create it manually via Cloud Console if needed."
}

# Map custom domain to admin
echo "Mapping custom domain admin.grainstoryfarm.ca to admin..."
gcloud beta run domain-mappings create \
    --service gsf-app-admin \
    --domain admin.grainstoryfarm.ca \
    --region $REGION \
    --project=$PROJECT_ID 2>/dev/null || {
    echo "Domain mapping may already exist. Checking status..."
    gcloud beta run domain-mappings describe admin.grainstoryfarm.ca \
        --region $REGION \
        --project=$PROJECT_ID 2>/dev/null && echo "Domain mapping exists!" || echo "Note: Domain mapping creation may require additional permissions. Create it manually via Cloud Console if needed."
}

echo ""
echo "Deployment complete!"
echo "Backend URL: $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"
echo "Admin URL: $ADMIN_URL"
echo "Custom domains:"
echo "  - app.grainstoryfarm.ca (may take a few minutes to propagate)"
echo "  - admin.grainstoryfarm.ca (may take a few minutes to propagate)"

