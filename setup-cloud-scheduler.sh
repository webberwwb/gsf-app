#!/bin/bash
# Setup GCP Cloud Scheduler for auto-confirming orders
# Run this script after deploying the backend

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== GCP Cloud Scheduler Setup ===${NC}"
echo ""

# Configuration
PROJECT_ID="focused-mote-477703-f0"
REGION="us-east1"
JOB_NAME="auto-confirm-orders"
BACKEND_URL="https://backend.grainstoryfarm.ca"
TIMEZONE="America/New_York"
SCHEDULE="0 0 * * *"  # Daily at 00:00 EST

echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Job Name: $JOB_NAME"
echo "Schedule: $SCHEDULE ($TIMEZONE)"
echo "Backend URL: $BACKEND_URL"
echo ""

# Check if CRON_SECRET is set
if [ -z "$CRON_SECRET" ]; then
    echo -e "${YELLOW}Warning: CRON_SECRET environment variable not set${NC}"
    echo "Generating a random secret..."
    CRON_SECRET=$(openssl rand -base64 32)
    echo -e "${GREEN}Generated CRON_SECRET: $CRON_SECRET${NC}"
    echo ""
    echo -e "${YELLOW}IMPORTANT: Save this secret and add it to your backend environment variables!${NC}"
    echo ""
    read -p "Press Enter to continue..."
else
    echo -e "${GREEN}Using CRON_SECRET from environment${NC}"
fi

# Set project
echo -e "${YELLOW}Setting GCP project...${NC}"
gcloud config set project $PROJECT_ID

# Check if Cloud Scheduler API is enabled
echo -e "${YELLOW}Checking if Cloud Scheduler API is enabled...${NC}"
if ! gcloud services list --enabled | grep -q "cloudscheduler.googleapis.com"; then
    echo "Enabling Cloud Scheduler API..."
    gcloud services enable cloudscheduler.googleapis.com
else
    echo "Cloud Scheduler API is already enabled"
fi

# Check if job already exists
echo -e "${YELLOW}Checking if job already exists...${NC}"
if gcloud scheduler jobs describe $JOB_NAME --location=$REGION &>/dev/null; then
    echo -e "${YELLOW}Job $JOB_NAME already exists.${NC}"
    read -p "Do you want to delete and recreate it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Deleting existing job..."
        gcloud scheduler jobs delete $JOB_NAME --location=$REGION --quiet
    else
        echo "Exiting without changes."
        exit 0
    fi
fi

# Create the Cloud Scheduler job
echo -e "${YELLOW}Creating Cloud Scheduler job...${NC}"
gcloud scheduler jobs create http $JOB_NAME \
  --schedule="$SCHEDULE" \
  --time-zone="$TIMEZONE" \
  --uri="$BACKEND_URL/api/cron/auto-confirm-orders" \
  --http-method="POST" \
  --headers="X-Cron-Secret=$CRON_SECRET,Content-Type=application/json" \
  --location="$REGION" \
  --description="Auto-confirm orders past their deadline - Runs daily at 00:00 EST" \
  --max-retry-attempts=3 \
  --min-backoff=5s \
  --max-backoff=3600s

echo ""
echo -e "${GREEN}✅ Cloud Scheduler job created successfully!${NC}"
echo ""

# Update backend environment variable with CRON_SECRET
echo -e "${YELLOW}Updating backend Cloud Run service with CRON_SECRET...${NC}"
gcloud run services update gsf-app-backend \
  --update-env-vars CRON_SECRET=$CRON_SECRET \
  --region $REGION \
  --platform managed

echo ""
echo -e "${GREEN}✅ Backend service updated with CRON_SECRET${NC}"
echo ""

# Test the job
read -p "Do you want to test the job now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Running job manually...${NC}"
    gcloud scheduler jobs run $JOB_NAME --location=$REGION
    echo ""
    echo "Waiting for execution (5 seconds)..."
    sleep 5
    echo ""
    echo "Checking logs..."
    gcloud logging read "resource.type=cloud_scheduler_job AND resource.labels.job_id=$JOB_NAME" \
      --limit 5 \
      --format="table(timestamp,severity,textPayload)"
fi

echo ""
echo -e "${GREEN}=== Setup Complete! ===${NC}"
echo ""
echo "Next steps:"
echo "1. Verify the job in GCP Console: https://console.cloud.google.com/cloudscheduler"
echo "2. Monitor execution logs in Cloud Logging"
echo "3. The job will run daily at 00:00 EST"
echo ""
echo "Useful commands:"
echo "  - List jobs: gcloud scheduler jobs list --location=$REGION"
echo "  - View job details: gcloud scheduler jobs describe $JOB_NAME --location=$REGION"
echo "  - Run job manually: gcloud scheduler jobs run $JOB_NAME --location=$REGION"
echo "  - Pause job: gcloud scheduler jobs pause $JOB_NAME --location=$REGION"
echo "  - Resume job: gcloud scheduler jobs resume $JOB_NAME --location=$REGION"
echo ""



