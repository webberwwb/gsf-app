#!/bin/bash
# Apply Flask-Migrate upgrades to the DB behind the local Cloud SQL tunnel.
# Usage: ./db-upgrade.sh
# Assumes cloud_sql_proxy (or another tunnel) is already listening on 127.0.0.1:3306.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

cd "$BACKEND_DIR"

if [ ! -d venv ]; then
    echo -e "${RED}Error: backend/venv not found${NC}"
    exit 1
fi

if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: backend/.env not found. Using config defaults.${NC}"
fi

if ! lsof -Pi :3306 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}Error: nothing is listening on 127.0.0.1:3306${NC}"
    echo "Start the Cloud SQL tunnel first (e.g. ./backend/start-local.sh or ./backend/restart-proxy.sh)."
    exit 1
fi

echo -e "${GREEN}Tunnel is up on port 3306. Applying flask db upgrade...${NC}"
source venv/bin/activate

python - <<'PY'
from alembic.migration import MigrationContext
from flask_migrate import upgrade
from app import create_app
from models import db

app, _ = create_app()
with app.app_context():
    conn = db.engine.connect()
    ctx = MigrationContext.configure(conn)
    before = ctx.get_current_revision()
    conn.close()
    print(f"current: {before}")
    upgrade()
    conn = db.engine.connect()
    ctx = MigrationContext.configure(conn)
    after = ctx.get_current_revision()
    conn.close()
    print(f"current after upgrade: {after}")
PY

echo -e "${GREEN}Done.${NC}"
