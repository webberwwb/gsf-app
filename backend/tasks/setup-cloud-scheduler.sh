#!/bin/bash
# Setup Cloud Scheduler jobs for GSF App
# This script creates Cloud Scheduler jobs to run cron tasks

set -e

PROJECT_ID="focused-mote-477703-f0"
REGION="us-central1"
BACKEND_URL="https://backend.grainstoryfarm.ca"

# Get CRON_SECRET from Secret Manager
echo "📋 Fetching CRON_SECRET from Secret Manager..."
CRON_SECRET=$(gcloud secrets versions access latest --secret="cron-secret" --project=$PROJECT_ID 2>/dev/null || echo "")

if [ -z "$CRON_SECRET" ]; then
    echo "❌ Error: CRON_SECRET not found in Secret Manager"
    echo "   Please create the secret first:"
    echo "   gcloud secrets create cron-secret --data-file=- --project=$PROJECT_ID"
    echo "   (Then paste the secret value and press Ctrl+D)"
    exit 1
fi

echo "✅ CRON_SECRET retrieved from Secret Manager"

# Enable Cloud Scheduler API
echo "Enabling Cloud Scheduler API..."
gcloud services enable cloudscheduler.googleapis.com --project=$PROJECT_ID 2>/dev/null || echo "API may already be enabled, continuing..."

# Create or update daily job for group deal status updates
echo "Creating/updating daily group deal status update job..."
gcloud scheduler jobs create http gsf-app-daily-status-update \
    --location=$REGION \
    --schedule="1 0 * * *" \
    --uri="$BACKEND_URL/api/cron/update-group-deal-statuses" \
    --http-method=POST \
    --headers="X-Cron-Secret=$CRON_SECRET" \
    --headers="Content-Type=application/json" \
    --time-zone="America/New_York" \
    --attempt-deadline=300s \
    --project=$PROJECT_ID 2>/dev/null || {
    
    echo "Job already exists, updating..."
    gcloud scheduler jobs update http gsf-app-daily-status-update \
        --location=$REGION \
        --schedule="1 0 * * *" \
        --uri="$BACKEND_URL/api/cron/update-group-deal-statuses" \
        --update-headers="X-Cron-Secret=$CRON_SECRET,Content-Type=application/json" \
        --time-zone="America/New_York" \
        --attempt-deadline=300s \
        --project=$PROJECT_ID
}

echo "✅ Daily status update job created/updated"


# List all jobs
echo ""
echo "📋 Current Cloud Scheduler jobs:"
gcloud scheduler jobs list --location=$REGION --project=$PROJECT_ID

echo ""
echo "✅ Cloud Scheduler setup complete!"
echo ""
echo "Job created:"
echo "  gsf-app-daily-status-update - Runs daily at 00:01 EDT"
echo ""
echo "To manually trigger the job for testing:"
echo "  gcloud scheduler jobs run gsf-app-daily-status-update --location=$REGION --project=$PROJECT_ID"
