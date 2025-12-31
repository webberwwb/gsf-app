#!/bin/bash
# Deploy all services to GCP Cloud Run
# Usage: ./deploy-all.sh [region] [service-account-key-path]
# Prerequisites: Run ./setup-secrets.sh once (secrets are reused automatically)

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

# Function to wait for build to complete
wait_for_build() {
    local BUILD_ID=$1
    local PROJECT=$2
    echo "Waiting for build $BUILD_ID to complete..."
    while true; do
        STATUS=$(gcloud builds describe $BUILD_ID --project=$PROJECT --format="value(status)" 2>/dev/null || echo "UNKNOWN")
        case $STATUS in
            SUCCESS)
                echo "Build completed successfully!"
                return 0
                ;;
            FAILURE|CANCELLED|EXPIRED|TIMEOUT)
                echo "Build failed with status: $STATUS"
                return 1
                ;;
            QUEUED|WORKING|PENDING)
                echo "Build status: $STATUS. Waiting..."
                sleep 10
                ;;
            *)
                echo "Unknown build status: $STATUS. Waiting..."
                sleep 10
                ;;
        esac
    done
}

# Deploy Backend
echo "Building and deploying backend..."
cd backend
set +e
BUILD_OUTPUT=$(gcloud builds submit --async --tag gcr.io/$PROJECT_ID/gsf-app-backend --project=$PROJECT_ID 2>&1)
BUILD_EXIT=$?
set -e
echo "$BUILD_OUTPUT"
if [ $BUILD_EXIT -ne 0 ]; then
    echo "Error: Failed to submit build"
    exit $BUILD_EXIT
fi
# Extract build ID
BUILD_ID=$(echo "$BUILD_OUTPUT" | grep 'builds/' | sed -E 's/.*builds\/([a-f0-9-]+).*/\1/' | head -1)
if [ -z "$BUILD_ID" ]; then
    echo "Error: Could not extract build ID from output"
    exit 1
fi
wait_for_build $BUILD_ID $PROJECT_ID || {
    echo "Error: Backend build failed"
    exit 1
}

ENV_VARS="MYSQL_DATABASE=gsf_app,GOOGLE_OAUTH_REDIRECT_URI=https://backend.grainstoryfarm.ca/api/auth/google/callback,ADMIN_FRONTEND_URL=https://admin.grainstoryfarm.ca"
SECRETS="MYSQL_USER=mysql-user:latest,MYSQL_PASSWORD=mysql-password:latest,SECRET_KEY=secret-key:latest,TWILIO_ACCOUNT_SID=twilio-account-sid:latest,TWILIO_AUTH_TOKEN=twilio-auth-token:latest,GOOGLE_OAUTH_CLIENT_SECRET=google-oauth-client-secret:latest"

BACKEND_URL=$(gcloud run deploy gsf-app-backend \
    --image gcr.io/$PROJECT_ID/gsf-app-backend \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --add-cloudsql-instances $PROJECT_ID:us-central1:gsf-app-mysql \
    --update-env-vars "$ENV_VARS" \
    --remove-env-vars MYSQL_USER,MYSQL_PASSWORD,SECRET_KEY,TWILIO_ACCOUNT_SID,TWILIO_AUTH_TOKEN,GOOGLE_OAUTH_CLIENT_SECRET \
    --update-secrets "$SECRETS" \
    --project=$PROJECT_ID \
    --format="value(status.url)")

echo "Backend deployed at: $BACKEND_URL"

# Deploy Frontend
echo "Building and deploying frontend..."
cd ../app
set +e
BUILD_OUTPUT=$(gcloud builds submit --async --tag gcr.io/$PROJECT_ID/gsf-app-frontend --project=$PROJECT_ID 2>&1)
BUILD_EXIT=$?
set -e
echo "$BUILD_OUTPUT"
if [ $BUILD_EXIT -ne 0 ]; then
    echo "Error: Failed to submit build"
    exit $BUILD_EXIT
fi
# Extract build ID
BUILD_ID=$(echo "$BUILD_OUTPUT" | grep 'builds/' | sed -E 's/.*builds\/([a-f0-9-]+).*/\1/' | head -1)
if [ -z "$BUILD_ID" ]; then
    echo "Error: Could not extract build ID from output"
    exit 1
fi
wait_for_build $BUILD_ID $PROJECT_ID || {
    echo "Error: Frontend build failed"
    exit 1
}
FRONTEND_URL=$(gcloud run deploy gsf-app-frontend \
    --image gcr.io/$PROJECT_ID/gsf-app-frontend \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --update-env-vars VITE_API_BASE_URL=$BACKEND_URL/api \
    --project=$PROJECT_ID \
    --format="value(status.url)")

echo "Frontend deployed at: $FRONTEND_URL"

# Deploy Admin
echo "Building and deploying admin..."
cd ../admin
set +e
BUILD_OUTPUT=$(gcloud builds submit --async --tag gcr.io/$PROJECT_ID/gsf-app-admin --project=$PROJECT_ID 2>&1)
BUILD_EXIT=$?
set -e
echo "$BUILD_OUTPUT"
if [ $BUILD_EXIT -ne 0 ]; then
    echo "Error: Failed to submit build"
    exit $BUILD_EXIT
fi
# Extract build ID
BUILD_ID=$(echo "$BUILD_OUTPUT" | grep 'builds/' | sed -E 's/.*builds\/([a-f0-9-]+).*/\1/' | head -1)
if [ -z "$BUILD_ID" ]; then
    echo "Error: Could not extract build ID from output"
    exit 1
fi
wait_for_build $BUILD_ID $PROJECT_ID || {
    echo "Error: Admin build failed"
    exit 1
}
ADMIN_URL=$(gcloud run deploy gsf-app-admin \
    --image gcr.io/$PROJECT_ID/gsf-app-admin \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --update-env-vars VITE_API_BASE_URL=$BACKEND_URL/api \
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
