#!/bin/bash
# Test cron endpoints locally
# This script helps test the cron endpoints before deploying to Cloud Scheduler

set -e

# Default values
BACKEND_URL="${BACKEND_URL:-http://localhost:8080}"
CRON_SECRET="${CRON_SECRET:-your-secret-key-here}"

echo "Testing cron endpoints..."
echo "Backend URL: $BACKEND_URL"
echo ""

# Test health endpoint
echo "1. Testing health endpoint..."
curl -s "$BACKEND_URL/api/cron/health" | python3 -m json.tool
echo ""
echo ""

# Test hourly status update
echo "2. Testing hourly group deal status update..."
curl -s -X POST \
    -H "X-Cron-Secret: $CRON_SECRET" \
    -H "Content-Type: application/json" \
    "$BACKEND_URL/api/cron/update-group-deal-statuses" | python3 -m json.tool
echo ""
echo ""

# Test daily auto-confirm
echo "3. Testing daily auto-confirm orders..."
curl -s -X POST \
    -H "X-Cron-Secret: $CRON_SECRET" \
    -H "Content-Type: application/json" \
    "$BACKEND_URL/api/cron/auto-confirm-orders" | python3 -m json.tool
echo ""
echo ""

echo "✅ All tests completed!"
echo ""
echo "To test against production:"
echo "  BACKEND_URL=https://backend.grainstoryfarm.ca CRON_SECRET=<your-secret> ./test-cron-locally.sh"
