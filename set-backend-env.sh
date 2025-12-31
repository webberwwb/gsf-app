#!/bin/bash
# Helper script to set backend environment variables in Cloud Run
# Usage: ./set-backend-env.sh [region]
#
# Set environment variables before running:
#   export TWILIO_ACCOUNT_SID="your-sid"
#   export TWILIO_AUTH_TOKEN="your-token"
#   export GOOGLE_OAUTH_CLIENT_ID="your-client-id"
#   export GOOGLE_OAUTH_CLIENT_SECRET="your-secret"
#   export MYSQL_USER="your-user"
#   export MYSQL_PASSWORD="your-password"
#   export SECRET_KEY="your-secret-key"
#
# Then run: ./set-backend-env.sh

set -e

PROJECT_ID="focused-mote-477703-f0"
REGION=${1:-"us-central1"}
SERVICE_NAME="gsf-app-backend"

echo "Setting environment variables for $SERVICE_NAME in region $REGION..."

# Load environment variables from backend/.env file if it exists
ENV_FILE="backend/.env"
if [ -f "$ENV_FILE" ]; then
    echo "Loading environment variables from $ENV_FILE..."
    export ENV_FILE="$ENV_FILE"
    # Use Python to safely parse .env file
    eval $(python3 <<'PYEOF'
import sys
import os

env_file = os.environ.get('ENV_FILE', 'backend/.env')
with open(env_file, 'r') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            # Escape special characters for bash
            value = value.replace('\\', '\\\\').replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')
            print('export {}="{}"'.format(key, value))
PYEOF
    )
    echo "Environment variables loaded from .env file"
fi

# Build environment variables to update
# Update variables individually to avoid comma parsing issues
HAS_VARS=false

echo "Updating environment variables..."

if [ -n "$TWILIO_ACCOUNT_SID" ]; then
    echo "  Setting TWILIO_ACCOUNT_SID..."
    gcloud run services update $SERVICE_NAME \
        --region $REGION \
        --update-env-vars TWILIO_ACCOUNT_SID="$TWILIO_ACCOUNT_SID" \
        --project=$PROJECT_ID --quiet
    HAS_VARS=true
fi

if [ -n "$TWILIO_AUTH_TOKEN" ]; then
    echo "  Setting TWILIO_AUTH_TOKEN..."
    gcloud run services update $SERVICE_NAME \
        --region $REGION \
        --update-env-vars TWILIO_AUTH_TOKEN="$TWILIO_AUTH_TOKEN" \
        --project=$PROJECT_ID --quiet
    HAS_VARS=true
fi

if [ -n "$GOOGLE_OAUTH_CLIENT_ID" ]; then
    echo "  Setting GOOGLE_OAUTH_CLIENT_ID..."
    gcloud run services update $SERVICE_NAME \
        --region $REGION \
        --update-env-vars GOOGLE_OAUTH_CLIENT_ID="$GOOGLE_OAUTH_CLIENT_ID" \
        --project=$PROJECT_ID --quiet
    HAS_VARS=true
fi

if [ -n "$GOOGLE_OAUTH_CLIENT_SECRET" ]; then
    echo "  Setting GOOGLE_OAUTH_CLIENT_SECRET..."
    gcloud run services update $SERVICE_NAME \
        --region $REGION \
        --update-env-vars GOOGLE_OAUTH_CLIENT_SECRET="$GOOGLE_OAUTH_CLIENT_SECRET" \
        --project=$PROJECT_ID --quiet
    HAS_VARS=true
fi

if [ -n "$MYSQL_USER" ]; then
    echo "  Setting MYSQL_USER..."
    gcloud run services update $SERVICE_NAME \
        --region $REGION \
        --update-env-vars MYSQL_USER="$MYSQL_USER" \
        --project=$PROJECT_ID --quiet
    HAS_VARS=true
fi

if [ -n "$MYSQL_PASSWORD" ]; then
    echo "  Setting MYSQL_PASSWORD..."
    gcloud run services update $SERVICE_NAME \
        --region $REGION \
        --update-env-vars MYSQL_PASSWORD="$MYSQL_PASSWORD" \
        --project=$PROJECT_ID --quiet
    HAS_VARS=true
fi

if [ -n "$SECRET_KEY" ]; then
    echo "  Setting SECRET_KEY..."
    gcloud run services update $SERVICE_NAME \
        --region $REGION \
        --update-env-vars SECRET_KEY="$SECRET_KEY" \
        --project=$PROJECT_ID --quiet
    HAS_VARS=true
fi

if [ -n "$TWILIO_VERIFY_SERVICE_SID" ]; then
    echo "  Setting TWILIO_VERIFY_SERVICE_SID..."
    gcloud run services update $SERVICE_NAME \
        --region $REGION \
        --update-env-vars TWILIO_VERIFY_SERVICE_SID="$TWILIO_VERIFY_SERVICE_SID" \
        --project=$PROJECT_ID --quiet
    HAS_VARS=true
fi

# Note: ADMIN_ALLOWED_EMAILS is skipped due to comma parsing issues
# It can be set manually via Cloud Console if needed

if [ "$HAS_VARS" = false ]; then
    echo "Error: No environment variables set!"
    echo "Please set the required environment variables before running this script."
    echo ""
    echo "Example:"
    echo "  export TWILIO_ACCOUNT_SID=\"your-sid\""
    echo "  export TWILIO_AUTH_TOKEN=\"your-token\""
    echo "  export GOOGLE_OAUTH_CLIENT_ID=\"your-client-id\""
    echo "  ./set-backend-env.sh"
    exit 1
fi

echo ""
echo "All environment variables updated successfully!"

echo ""
echo "Environment variables updated successfully!"
echo ""
echo "To verify, run:"
echo "  gcloud run services describe $SERVICE_NAME --region $REGION --project=$PROJECT_ID --format='value(spec.template.spec.containers[0].env)'"

