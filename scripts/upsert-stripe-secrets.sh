#!/bin/bash
# Copy Stripe values from backend/.env into Secret Manager without printing them.
# Usage: ./scripts/upsert-stripe-secrets.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=/dev/null
source "$ROOT_DIR/set-gcloud-project.sh"

ENV_FILE="$ROOT_DIR/backend/.env"
if [ ! -f "$ENV_FILE" ]; then
  echo "Error: $ENV_FILE not found"
  exit 1
fi

extract_env() {
  python3 - "$1" "$ENV_FILE" <<'PY'
import sys
from pathlib import Path
key, path = sys.argv[1], Path(sys.argv[2])
for raw in path.read_text().splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    name, value = line.split("=", 1)
    if name == key:
        sys.stdout.write(value)
        raise SystemExit(0)
raise SystemExit(f"missing {key}")
PY
}

upsert_secret() {
  local env_key="$1"
  local secret_name="$2"
  local tmp
  tmp="$(mktemp)"
  chmod 600 "$tmp"
  extract_env "$env_key" > "$tmp"
  if [ ! -s "$tmp" ]; then
    rm -f "$tmp"
    echo "Error: $env_key is empty in backend/.env"
    exit 1
  fi
  if gcloud secrets describe "$secret_name" --project="$PROJECT_ID" >/dev/null 2>&1; then
    gcloud secrets versions add "$secret_name" --data-file="$tmp" --project="$PROJECT_ID" >/dev/null
    echo "Updated secret $secret_name"
  else
    gcloud secrets create "$secret_name" \
      --data-file="$tmp" \
      --replication-policy=automatic \
      --project="$PROJECT_ID" >/dev/null
    echo "Created secret $secret_name"
  fi
  rm -f "$tmp"
}

upsert_secret STRIPE_SECRET_KEY stripe-secret-key
upsert_secret STRIPE_PUBLISHABLE_KEY stripe-publishable-key
upsert_secret STRIPE_WEBHOOK_SECRET stripe-webhook-secret
upsert_secret STRIPE_DASHBOARD_BASE stripe-dashboard-base

echo "Stripe secrets are in Secret Manager (values not printed)."
