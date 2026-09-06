# Deployment Guide

## Security Setup

This project uses **Google Secret Manager** to store sensitive credentials securely instead of environment variables.

### Secrets in Secret Manager

The following secrets are stored in Google Secret Manager:
- `mysql-user` - Database username
- `mysql-password` - Database password
- `secret-key` - Flask SECRET_KEY
- `twilio-account-sid` - Twilio Account SID
- `twilio-auth-token` - Twilio Auth Token
- `google-oauth-client-secret` - Google OAuth Client Secret
- `cron-secret` - Cron job authentication secret
- `google-maps-api-key` - Google Maps API Key (for frontend builds)
- `stripe-secret-key` - Stripe secret key (`STRIPE_SECRET_KEY`)
- `stripe-publishable-key` - Stripe publishable key (`STRIPE_PUBLISHABLE_KEY`)
- `stripe-webhook-secret` - Stripe webhook signing secret (`STRIPE_WEBHOOK_SECRET`)
- `stripe-dashboard-base` - Stripe Dashboard URL (`STRIPE_DASHBOARD_BASE`)

To copy Stripe values from local `backend/.env` into Secret Manager (values are not printed):

```bash
./scripts/upsert-stripe-secrets.sh
```

### Deployment Scripts

#### Deploy All Services
```bash
./deploy-all.sh
```
Deploys backend, frontend, and admin with version synchronization.

#### Deploy Backend Only
```bash
./deploy-backend.sh
```
Deploys backend using secrets from Secret Manager.

#### Deploy Frontend Only
```bash
./deploy-app.sh
```
Deploys frontend and updates backend's APP_VERSION environment variable.

#### Deploy Admin Only
```bash
cd admin
gcloud builds submit --tag gcr.io/focused-mote-477703-f0/gsf-app-admin
gcloud run deploy gsf-app-admin --image gcr.io/focused-mote-477703-f0/gsf-app-admin:latest --region us-central1
```

### Updating Secrets

To update a secret value:
```bash
echo -n "new-secret-value" | gcloud secrets versions add SECRET_NAME --data-file=- --project=focused-mote-477703-f0
```

Example:
```bash
echo -n "new-password-123" | gcloud secrets versions add mysql-password --data-file=- --project=focused-mote-477703-f0
```

### Why Secret Manager?

Previously, we passed credentials as plain environment variables via YAML files. This had security risks:
1. ❌ Credentials could be accidentally committed to git
2. ❌ Credentials visible in deployment commands and logs
3. ❌ No audit trail of who accessed credentials

With Secret Manager:
1. ✅ Credentials stored encrypted in Google Cloud
2. ✅ Access controlled by IAM permissions
3. ✅ Full audit trail of access
4. ✅ Automatic rotation support
5. ✅ Version history of all changes

### Non-sensitive Environment Variables

Non-sensitive configuration (like URLs, port numbers, etc.) are still passed as regular environment variables via the deployment scripts.

### Local Development

For local development, use the `.env` file which is git-ignored. See `backend/.env` for the template.
