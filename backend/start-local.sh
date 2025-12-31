#!/bin/bash
# Start local backend with Cloud SQL Proxy

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

echo -e "${GREEN}Starting local backend development server...${NC}"
echo ""

# Check if Cloud SQL Proxy exists
if [ ! -f "./cloud_sql_proxy" ]; then
    echo -e "${RED}Error: cloud_sql_proxy not found${NC}"
    echo "Downloading Cloud SQL Proxy..."
    curl -o cloud_sql_proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.darwin.amd64
    chmod +x cloud_sql_proxy
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Warning: venv not found. Creating virtual environment...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Check if proxy is already running and healthy
PROXY_PID=""
if lsof -Pi :3306 -sTCP:LISTEN -t >/dev/null 2>&1; then
    # Check if proxy is healthy by looking for recent errors in logs
    if tail -5 /tmp/cloud_sql_proxy.log 2>/dev/null | grep -qi "tls: bad certificate\|connection aborted"; then
        echo -e "${YELLOW}Cloud SQL Proxy is running but has errors. Restarting...${NC}"
        pkill -f cloud_sql_proxy || true
        sleep 2
        # Start fresh proxy
        echo -e "${GREEN}Starting Cloud SQL Proxy...${NC}"
        ./cloud_sql_proxy focused-mote-477703-f0:us-central1:gsf-app-mysql --port=3306 --address=127.0.0.1 > /tmp/cloud_sql_proxy.log 2>&1 &
        PROXY_PID=$!
    else
        echo -e "${GREEN}Cloud SQL Proxy is already running on port 3306${NC}"
        PROXY_PID=""
    fi
else
    # Start Cloud SQL Proxy in background
    echo -e "${GREEN}Starting Cloud SQL Proxy...${NC}"
    # Use service account credentials directly (set above)
    ./cloud_sql_proxy focused-mote-477703-f0:us-central1:gsf-app-mysql --port=3306 --address=127.0.0.1 > /tmp/cloud_sql_proxy.log 2>&1 &
    PROXY_PID=$!
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down...${NC}"
    if [ ! -z "$PROXY_PID" ]; then
        echo "Stopping Cloud SQL Proxy (PID: $PROXY_PID)"
        kill $PROXY_PID 2>/dev/null || true
    fi
    # Don't kill proxy if we didn't start it
    exit 0
}

# Trap SIGINT and SIGTERM
trap cleanup SIGINT SIGTERM

# Wait for proxy to be ready (check if port 3306 is listening)
if [ ! -z "$PROXY_PID" ]; then
    echo "Waiting for Cloud SQL Proxy to be ready..."
    for i in {1..30}; do
        if lsof -Pi :3306 -sTCP:LISTEN -t >/dev/null 2>&1; then
            # Wait a bit more for proxy to fully initialize
            sleep 2
            # Check if proxy is actually working by checking log for errors
            if tail -10 /tmp/cloud_sql_proxy.log 2>/dev/null | grep -qi "tls: bad certificate\|connection aborted\|error\|failed\|invalid"; then
                echo -e "${RED}Error detected in Cloud SQL Proxy logs${NC}"
                tail -10 /tmp/cloud_sql_proxy.log
                kill $PROXY_PID 2>/dev/null || true
                exit 1
            fi
            echo -e "${GREEN}Cloud SQL Proxy is ready!${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}Error: Cloud SQL Proxy failed to start${NC}"
            echo "Last 10 lines of proxy log:"
            tail -10 /tmp/cloud_sql_proxy.log 2>/dev/null || echo "No log file"
            kill $PROXY_PID 2>/dev/null || true
            exit 1
        fi
        sleep 1
    done
else
    echo -e "${GREEN}Using existing Cloud SQL Proxy${NC}"
    # Still verify it's healthy
    if tail -5 /tmp/cloud_sql_proxy.log 2>/dev/null | grep -qi "tls: bad certificate\|connection aborted"; then
        echo -e "${YELLOW}Warning: Proxy logs show potential issues. Consider restarting.${NC}"
    fi
fi

# Activate virtual environment and start Flask
echo -e "${GREEN}Starting Flask backend...${NC}"
echo ""
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found. Using defaults.${NC}"
fi

# Start Flask app
export FLASK_APP=app.py
python app.py

