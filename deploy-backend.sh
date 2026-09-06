#!/bin/bash
# Deploy backend to GCP Cloud Run using Google Secret Manager
# Usage: ./deploy-backend.sh [region] [service-account-key-path]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/set-gcloud-project.sh"

REGION=${1:-"us-central1"}
SERVICE_ACCOUNT_KEY="${2:-instance/service_accounts/focused-mote-477703-f0-0571d061607f.json}"

echo "Deploying backend to project: $PROJECT_ID, region: $REGION"

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

# Get current frontend version for APP_VERSION
VERSION=$(date +"%Y.%m.%d.%H%M")
echo "📦 Version: $VERSION"

# Build backend
echo "🏗️  Building backend..."
cd backend
gcloud builds submit --tag gcr.io/$PROJECT_ID/gsf-app-backend --project=$PROJECT_ID

# Create temporary env vars file for non-sensitive values
cd ..
cat > backend-env-temp.yaml <<EOF
APP_VERSION: "$VERSION"
ENVIRONMENT: production
MYSQL_HOST: /cloudsql/$PROJECT_ID:us-central1:gsf-app-mysql
MYSQL_PORT: "3306"
MYSQL_DATABASE: gsf_app
TWILIO_VERIFY_SERVICE_SID: VA9f6a6a1fd2013d3ed38ec4e7552a369e
ADMIN_ALLOWED_EMAILS: info@digitelf.com,grainstoryfarm@gmail.com,harris010908@gmail.com
GOOGLE_OAUTH_CLIENT_ID: 304694762003-ngilk1cidevokj46vb9amu3led74qbo1.apps.googleusercontent.com
GOOGLE_OAUTH_REDIRECT_URI: https://backend.grainstoryfarm.ca/api/auth/google/callback
ADMIN_FRONTEND_URL: https://admin.grainstoryfarm.ca
APP_FRONTEND_URL: https://app.grainstoryfarm.ca
EOF

# Deploy backend with secrets from Secret Manager
echo "🚀 Deploying backend with Secret Manager..."
CLOUDSQL_INSTANCE="$PROJECT_ID:us-central1:gsf-app-mysql"
gcloud run deploy gsf-app-backend \
    --image gcr.io/$PROJECT_ID/gsf-app-backend:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --add-cloudsql-instances $CLOUDSQL_INSTANCE \
    --env-vars-file backend-env-temp.yaml \
    --set-secrets "MYSQL_USER=mysql-user:latest,MYSQL_PASSWORD=mysql-password:latest,SECRET_KEY=secret-key:latest,TWILIO_ACCOUNT_SID=twilio-account-sid:latest,TWILIO_AUTH_TOKEN=twilio-auth-token:latest,GOOGLE_OAUTH_CLIENT_SECRET=google-oauth-client-secret:latest,CRON_SECRET=cron-secret:latest,STRIPE_SECRET_KEY=stripe-secret-key:latest,STRIPE_PUBLISHABLE_KEY=stripe-publishable-key:latest,STRIPE_WEBHOOK_SECRET=stripe-webhook-secret:latest,STRIPE_DASHBOARD_BASE=stripe-dashboard-base:latest" \
    --memory 1Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 1 \
    --no-cpu-throttling \
    --project=$PROJECT_ID

# Clean up temporary file
rm -f backend-env-temp.yaml

echo ""
echo "✅ Backend deployment complete!"
echo "   Version: $VERSION"
echo "   Secrets used from Google Secret Manager"
