#!/bin/bash
# Deploy frontend (user app) to GCP Cloud Run
# Usage: ./deploy-app.sh [region] [service-account-key-path]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/set-gcloud-project.sh"

REGION=${1:-"us-central1"}
SERVICE_ACCOUNT_KEY="${2:-instance/service_accounts/focused-mote-477703-f0-0571d061607f.json}"

echo "Deploying frontend to project: $PROJECT_ID, region: $REGION"

# Authenticate with service account
if [ -f "$SERVICE_ACCOUNT_KEY" ]; then
    echo "🔐 Authenticating with service account: $SERVICE_ACCOUNT_KEY"
    gcloud auth activate-service-account --key-file="$SERVICE_ACCOUNT_KEY" || {
        echo "Error: Failed to authenticate with service account"
        exit 1
    }
    echo "✅ Service account authenticated successfully"
else
    echo "Error: Service account key not found at $SERVICE_ACCOUNT_KEY"
    exit 1
fi

# Function to update frontend version
update_frontend_version() {
    local APP_DIR=$1
    local VERSION=$(date +"%Y.%m.%d.%H%M")
    echo "🔄 Updating frontend version to: $VERSION"
    
    if [ -f "$APP_DIR/public/sw.js" ]; then
        sed -i '' "s/const VERSION = '[^']*'/const VERSION = '$VERSION'/" "$APP_DIR/public/sw.js"
        echo "✅ Service Worker version updated in $APP_DIR/public/sw.js"
        echo "$VERSION"
        return 0
    else
        echo "⚠️  Warning: $APP_DIR/public/sw.js not found"
        exit 1
    fi
}

# Function to extract version from sw.js
get_frontend_version() {
    local APP_DIR=$1
    if [ -f "$APP_DIR/public/sw.js" ]; then
        grep "const VERSION = " "$APP_DIR/public/sw.js" | sed "s/.*const VERSION = '\([^']*\)'.*/\1/"
    else
        echo ""
    fi
}

# Update frontend version
cd app
VERSION=$(update_frontend_version "$(pwd)")
echo "📦 Frontend version: $VERSION"
cd ..

# Build frontend
echo "🏗️  Building frontend..."
cd app
gcloud builds submit --tag gcr.io/$PROJECT_ID/gsf-app-frontend --project=$PROJECT_ID

# Deploy frontend
echo "🚀 Deploying frontend..."
FRONTEND_URL=$(gcloud run deploy gsf-app-frontend \
    --image gcr.io/$PROJECT_ID/gsf-app-frontend:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars "APP_VERSION=$VERSION,VITE_API_BASE_URL=https://backend.grainstoryfarm.ca/api" \
    --project=$PROJECT_ID \
    --format="value(status.url)")

echo "✅ Frontend deployed at: $FRONTEND_URL"

# Update backend's APP_VERSION environment variable to match
echo "🔄 Updating backend APP_VERSION to: $VERSION"
gcloud run services update gsf-app-backend \
    --region=$REGION \
    --update-env-vars "APP_VERSION=$VERSION" \
    --project=$PROJECT_ID

echo "✅ Backend APP_VERSION updated"

cd ..

echo ""
echo "✅ Frontend deployment complete!"
echo "   Version: $VERSION"
echo "   URL: $FRONTEND_URL"
echo "   Backend APP_VERSION: updated to $VERSION"
