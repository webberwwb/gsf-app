#!/bin/bash
# Restart Cloud SQL Proxy and test connection

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Set service account credentials
export GOOGLE_APPLICATION_CREDENTIALS="../instance/service_accounts/focused-mote-477703-f0-0571d061607f.json"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Restarting Cloud SQL Proxy...${NC}"

# Kill existing proxy
if lsof -Pi :3306 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "Stopping existing Cloud SQL Proxy..."
    pkill -f cloud_sql_proxy || true
    sleep 2
fi

# Check if Cloud SQL Proxy exists
if [ ! -f "./cloud_sql_proxy" ]; then
    echo -e "${RED}Error: cloud_sql_proxy not found${NC}"
    echo "Downloading Cloud SQL Proxy..."
    curl -o cloud_sql_proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.darwin.amd64
    chmod +x cloud_sql_proxy
fi

# Start Cloud SQL Proxy
echo -e "${GREEN}Starting Cloud SQL Proxy...${NC}"
./cloud_sql_proxy focused-mote-477703-f0:us-central1:gsf-app-mysql --port=3306 --address=127.0.0.1 > /tmp/cloud_sql_proxy.log 2>&1 &
PROXY_PID=$!

# Wait for proxy to be ready
echo "Waiting for Cloud SQL Proxy to be ready..."
for i in {1..30}; do
    if lsof -Pi :3306 -sTCP:LISTEN -t >/dev/null 2>&1; then
        sleep 2
        # Check for errors
        if tail -10 /tmp/cloud_sql_proxy.log 2>/dev/null | grep -qi "tls: bad certificate\|connection aborted\|error\|failed"; then
            echo -e "${RED}Error detected in Cloud SQL Proxy logs:${NC}"
            tail -10 /tmp/cloud_sql_proxy.log
            kill $PROXY_PID 2>/dev/null || true
            exit 1
        fi
        echo -e "${GREEN}Cloud SQL Proxy is ready!${NC}"
        echo ""
        echo "Proxy PID: $PROXY_PID"
        echo "Log file: /tmp/cloud_sql_proxy.log"
        echo ""
        echo "To test the connection, run:"
        echo "  python test-db-connection.py"
        exit 0
    fi
    sleep 1
done

echo -e "${RED}Error: Cloud SQL Proxy failed to start${NC}"
echo "Last 10 lines of proxy log:"
tail -10 /tmp/cloud_sql_proxy.log 2>/dev/null || echo "No log file"
kill $PROXY_PID 2>/dev/null || true
exit 1



