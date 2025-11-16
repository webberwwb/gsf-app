# GSF App - Group Buy Poultry Products PWA

A Progressive Web App (PWA) for ecommerce group buy poultry products that are only available on certain days. Users can place orders, optionally pay online, and track their orders.

## Tech Stack

### Frontend
- **Vue 3** - Progressive JavaScript framework
- **Vite** - Build tool and dev server
- **Vue Router** - Client-side routing
- **Axios** - HTTP client for API calls
- **Nginx** - Web server for production

### Backend
- **Flask** - Python web framework
- **Flask-SQLAlchemy** - ORM for database operations
- **Flask-CORS** - Cross-Origin Resource Sharing support
- **PyMySQL** - MySQL database connector
- **Gunicorn** - WSGI HTTP Server for production

### Infrastructure
- **Google Cloud Platform (GCP)**
  - Cloud Run - Serverless container platform
  - Cloud Build - CI/CD pipeline
  - Cloud SQL - Managed MySQL database (to be configured)
  - Service Accounts - Authentication and authorization

## Project Structure

```
gsf-app/
├── backend/              # Flask backend application
│   ├── app.py           # Application factory
│   ├── config.py        # Configuration settings
│   ├── routes.py        # API routes
│   ├── wsgi.py          # WSGI entry point
│   ├── requirements.txt # Python dependencies
│   ├── Dockerfile       # Backend container image
│   ├── cloud-run.yaml   # Cloud Run configuration
│   ├── deploy.sh        # Deployment script
│   └── models/          # Database models
│       ├── __init__.py
│       └── base.py      # Base model class
├── app/                 # Vue.js app frontend (app.grainstoryfarm.ca)
│   ├── src/
│   │   ├── api/         # API client configuration
│   │   ├── router/      # Vue Router configuration
│   │   ├── views/       # Vue components/pages
│   │   ├── App.vue      # Root component
│   │   └── main.js      # Application entry point
│   ├── index.html       # HTML template
│   ├── package.json     # Node.js dependencies
│   ├── vite.config.js   # Vite configuration
│   ├── Dockerfile       # Frontend container image
│   ├── nginx.conf       # Nginx configuration
│   ├── docker-entrypoint.sh # Container entrypoint
│   ├── cloud-run.yaml   # Cloud Run configuration
│   └── deploy.sh        # Deployment script
├── cloudbuild.yaml      # Cloud Build CI/CD configuration
├── deploy-all.sh        # Deploy all services script
├── instance/             # Local instance files (git-ignored)
│   └── service_accounts/ # Service account credentials
└── README.md            # This file

```

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 20+
- MySQL (or Cloud SQL)
- Docker (for containerized deployment)

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the backend directory:
```env
SECRET_KEY=your-secret-key-here
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=gsf_app
```

5. Start the backend (includes Cloud SQL Proxy):
```bash
./start-local.sh
```

Or manually:
```bash
# Start Cloud SQL Proxy in one terminal
./start-proxy.sh

# In another terminal, start Flask
source venv/bin/activate
python app.py
```

The backend will be available at `http://localhost:5001`

### App Frontend Setup

1. Navigate to app directory:
```bash
cd app
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file in the app directory (optional, defaults to `/api`):
```env
VITE_API_BASE_URL=http://localhost:5000/api
```

4. Run the development server:
```bash
npm run dev
```

The app frontend will be available at `http://localhost:3000`

## Deployment to GCP

### Prerequisites
- Google Cloud SDK installed and configured
- GCP project: `focused-mote-477703-f0`
- Service account credentials in `instance/service_accounts/`
- Cloud SQL instance created (for database)

### Service Account Setup

The project uses a service account for deployment. The credentials are stored in:
```
instance/service_accounts/focused-mote-477703-f0-0571d061607f.json
```

**Note:** This file is git-ignored and should not be committed to version control.

### Deployment

Deploy all services (backend, app frontend, and admin frontend) using the single deployment script:

```bash
./deploy-all.sh us-central1
```

Or with custom service account path:
```bash
./deploy-all.sh us-central1 path/to/service-account.json
```

This script will:
1. Build and deploy backend to Cloud Run
2. Build and deploy app frontend to Cloud Run
3. Build and deploy admin frontend to Cloud Run
4. Map custom domains (app.grainstoryfarm.ca and admin.grainstoryfarm.ca)

### Custom Domain Setup

The application uses custom domains:
- **App Frontend:** `app.grainstoryfarm.ca` → `gsf-app-frontend`
- **Backend:** `backend.grainstoryfarm.ca` → `gsf-app-backend`

Domain mappings are already configured in Cloud Run. To manage them:

```bash
# List domain mappings
gcloud beta run domain-mappings list --region us-central1 --project=focused-mote-477703-f0

# Describe a domain mapping
gcloud beta run domain-mappings describe --domain=app.grainstoryfarm.ca --region us-central1 --project=focused-mote-477703-f0
```

### Environment Variables

Set the following secrets in Google Cloud Secret Manager for the backend:
- `mysql-host` - MySQL host address
- `mysql-user` - MySQL username
- `mysql-password` - MySQL password

Update `backend/cloud-run.yaml` to reference these secrets.

For the app frontend, set the `VITE_API_BASE_URL` environment variable in Cloud Run to point to your backend URL.

## Database Setup

1. Create a Cloud SQL MySQL instance in GCP
2. Create the database: `gsf_app`
3. Set up database migrations using Skeema (similar to reference project) or Flask-Migrate
4. Configure connection using Cloud SQL Proxy or private IP

## Service Account Configuration

1. Create a service account in GCP Console
2. Grant necessary permissions:
   - Cloud Run Admin
   - Cloud Build Service Account
   - Cloud SQL Client (if using Cloud SQL)
3. Download the service account key JSON file
4. Store it securely (not in git) and reference it in your deployment scripts

## API Endpoints

### Health Check
- `GET /api/health` - Returns API health status

### Test
- `GET /api/test` - Test endpoint

More endpoints will be added as features are developed.

## Next Steps

1. Set up database models for:
   - Products (poultry items)
   - Orders
   - Users/Customers
   - Payment transactions

2. Implement PWA features:
   - Service worker for offline support
   - Web app manifest
   - Push notifications

3. Add authentication and authorization

4. Implement payment integration

5. Add order tracking functionality

## License

[Add your license here]

