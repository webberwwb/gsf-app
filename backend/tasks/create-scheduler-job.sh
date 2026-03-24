#!/bin/bash
# Create Cloud Scheduler job with user account (not service account)
# Run this with your personal gcloud account that has Cloud Scheduler permissions

set -e

PROJECT_ID="focused-mote-477703-f0"
REGION="us-central1"
BACKEND_URL="https://backend.grainstoryfarm.ca"

# Get CRON_SECRET from Secret Manager
echo "📋 Fetching CRON_SECRET from Secret Manager..."
CRON_SECRET=$(gcloud secrets versions access latest --secret="cron-secret" --project=$PROJECT_ID)

if [ -z "$CRON_SECRET" ]; then
    echo "❌ Error: CRON_SECRET not found"
    exit 1
fi

echo "✅ CRON_SECRET retrieved"

# Create daily job for group deal status updates (00:01 EDT)
echo "Creating daily group deal status update job..."
gcloud scheduler jobs create http gsf-app-daily-status-update \
    --location=$REGION \
    --schedule="1 0 * * *" \
    --uri="$BACKEND_URL/api/cron/update-group-deal-statuses" \
    --http-method=POST \
    --headers="X-Cron-Secret=$CRON_SECRET" \
    --headers="Content-Type=application/json" \
    --time-zone="America/New_York" \
    --attempt-deadline=300s \
    --project=$PROJECT_ID

echo "✅ Daily status update job created"

echo ""
echo "✅ Cloud Scheduler setup complete!"
echo ""
echo "Job created:"
echo "  gsf-app-daily-status-update - Runs daily at 00:01 EDT"
