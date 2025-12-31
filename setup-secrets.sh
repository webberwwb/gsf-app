#!/bin/bash
# Create secrets in Secret Manager (run once, then use deploy-all.sh for deployments)
# Usage: ./setup-secrets.sh [service-account-key-path]

set -e

PROJECT_ID="focused-mote-477703-f0"

# Use service account only if explicitly provided
if [ -n "$1" ] && [ -f "$1" ]; then
    gcloud auth activate-service-account --key-file="$1" || exit 1
fi

gcloud config set project $PROJECT_ID
gcloud services enable secretmanager.googleapis.com --project=$PROJECT_ID 2>/dev/null || true

# Load from backend/.env if exists
if [ -f "backend/.env" ]; then
    export ENV_FILE="backend/.env"
    eval $(python3 <<'PYEOF'
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
            value = value.replace('\\', '\\\\').replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')
            print('export {}="{}"'.format(key, value))
PYEOF
    )
fi

create_secret() {
    local SECRET_NAME=$1
    local SECRET_VALUE=$2
    [ -z "$SECRET_VALUE" ] && return
    if gcloud secrets describe "$SECRET_NAME" --project=$PROJECT_ID >/dev/null 2>&1; then
        echo -n "$SECRET_VALUE" | gcloud secrets versions add "$SECRET_NAME" --data-file=- --project=$PROJECT_ID
    else
        echo -n "$SECRET_VALUE" | gcloud secrets create "$SECRET_NAME" --data-file=- --replication-policy="automatic" --project=$PROJECT_ID
    fi
}

create_secret "mysql-user" "${MYSQL_USER:-gsf_app_user}"
create_secret "mysql-password" "$MYSQL_PASSWORD"
create_secret "secret-key" "$SECRET_KEY"
create_secret "twilio-account-sid" "$TWILIO_ACCOUNT_SID"
create_secret "twilio-auth-token" "$TWILIO_AUTH_TOKEN"
create_secret "google-oauth-client-secret" "$GOOGLE_OAUTH_CLIENT_SECRET"

# Grant access to Cloud Run compute service account (used by Cloud Run revisions)
# Use project number format: PROJECT_NUM-compute@developer.gserviceaccount.com
PROJECT_NUM=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)" 2>/dev/null || echo "")
if [ -n "$PROJECT_NUM" ]; then
    COMPUTE_SA="${PROJECT_NUM}-compute@developer.gserviceaccount.com"
    for SECRET in mysql-user mysql-password secret-key twilio-account-sid twilio-auth-token google-oauth-client-secret; do
        gcloud secrets describe "$SECRET" --project=$PROJECT_ID >/dev/null 2>&1 && \
        gcloud secrets add-iam-policy-binding "$SECRET" \
            --member="serviceAccount:${COMPUTE_SA}" \
            --role="roles/secretmanager.secretAccessor" \
            --project=$PROJECT_ID 2>/dev/null || true
    done
fi

echo "Secrets setup complete!"

