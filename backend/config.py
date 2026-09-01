import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Cloud SQL connection name (for Cloud Run)
    CLOUD_SQL_CONNECTION_NAME = os.environ.get('CLOUD_SQL_CONNECTION_NAME', 'focused-mote-477703-f0:us-central1:gsf-app-mysql')
    
    # MySQL Database configuration
    # For Cloud Run: use Unix socket via Cloud SQL Proxy
    # For local dev: use TCP connection (via Cloud SQL Proxy or direct IP)
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or '127.0.0.1'  # Local proxy default
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'gsf_app_user'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or ''
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'gsf_app'
    
    # Determine if running on Cloud Run (has K_SERVICE env var)
    _is_cloud_run = os.environ.get('K_SERVICE') is not None
    
    def _get_database_uri(self):
        """Build database URI based on environment"""
        import logging
        logger = logging.getLogger(__name__)

        # User/password must be URL-encoded (e.g. ; $ " @ in MYSQL_PASSWORD break parsing otherwise)
        user = quote_plus(self.MYSQL_USER or '', safe='')
        password = quote_plus(self.MYSQL_PASSWORD or '', safe='')
        
        # Cloud Run provides DB_SOCKET_PATH when Cloud SQL is connected
        db_socket_path = os.environ.get('DB_SOCKET_PATH')
        k_service = os.environ.get('K_SERVICE')
        
        logger.info(f"DB Config - K_SERVICE: {k_service}, DB_SOCKET_PATH: {db_socket_path}, _is_cloud_run: {self._is_cloud_run}")
        
        if self._is_cloud_run:
            # Cloud Run: use Unix socket at /cloudsql/CONNECTION_NAME
            # Cloud Run automatically mounts the socket when --add-cloudsql-instances is used
            socket_path = f"/cloudsql/{self.CLOUD_SQL_CONNECTION_NAME}"
            logger.info(f"Using Cloud Run Unix socket: {socket_path}")
            return (
                f"mysql+pymysql://{user}:{password}@/{self.MYSQL_DATABASE}"
                f"?unix_socket={socket_path}"
            )
        
        # Local dev: use TCP connection
        logger.info(f"Using local TCP connection: {self.MYSQL_HOST}:{self.MYSQL_PORT}")
        return (
            f"mysql+pymysql://{user}:{password}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )
    
    # Set SQLALCHEMY_DATABASE_URI as a property that evaluates dynamically
    SQLALCHEMY_DATABASE_URI = property(lambda self: self._get_database_uri())
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Check connection health before using
        'pool_recycle': 300,  # Recycle connections after 5 minutes
        'pool_size': 5,  # Smaller pool for Cloud Run (was 10)
        'max_overflow': 10,  # Reduced overflow (was 20)
        'pool_timeout': 30,  # Timeout waiting for connection from pool
        'echo_pool': False,  # Set to True for debugging
        'connect_args': {
            'ssl_disabled': True,
            'charset': 'utf8mb4',
            'connect_timeout': 10,  # Connection timeout in seconds
            'read_timeout': 30,  # Read timeout in seconds
            'write_timeout': 30  # Write timeout in seconds
        }
    }
    
    # Twilio Verify configuration
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_VERIFY_SERVICE_SID = os.environ.get('TWILIO_VERIFY_SERVICE_SID', 'VA9f6a6a1fd2013d3ed38ec4e7552a369e')
    
    # Google OAuth configuration for Admin
    GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
    GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
    GOOGLE_OAUTH_REDIRECT_URI = os.environ.get('GOOGLE_OAUTH_REDIRECT_URI', 'https://backend.grainstoryfarm.ca/api/auth/google/callback')
    ADMIN_FRONTEND_URL = os.environ.get('ADMIN_FRONTEND_URL', 'https://admin.grainstoryfarm.ca')
    APP_FRONTEND_URL = os.environ.get('APP_FRONTEND_URL', 'https://app.grainstoryfarm.ca')
    
    # Admin allowed email domains (comma-separated)
    ADMIN_ALLOWED_DOMAINS = os.environ.get('ADMIN_ALLOWED_DOMAINS', '').split(',') if os.environ.get('ADMIN_ALLOWED_DOMAINS') else []
    
    # Admin allowed email addresses (comma-separated) - takes precedence over domains
    ADMIN_ALLOWED_EMAILS = [email.strip() for email in os.environ.get('ADMIN_ALLOWED_EMAILS', '').split(',') if email.strip()] if os.environ.get('ADMIN_ALLOWED_EMAILS') else []
    
    # Google Cloud Storage configuration for product images
    GCS_BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME', 'gsf-app-product-images')
    GCS_PROJECT_ID = os.environ.get('GCS_PROJECT_ID', 'focused-mote-477703-f0')
    # Public URL base for images (e.g., https://storage.googleapis.com/gsf-app-product-images/)
    GCS_PUBLIC_URL_BASE = os.environ.get('GCS_PUBLIC_URL_BASE', f'https://storage.googleapis.com/{GCS_BUCKET_NAME}')
    # Stable browser-facing image URL (proxied at /api/images/<object>).
    IMAGE_PROXY_BASE = os.environ.get(
        'IMAGE_PROXY_BASE',
        'https://backend.grainstoryfarm.ca/api/images',
    ).rstrip('/')

    # Stripe (sandbox/test keys locally; never commit live secrets)
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    STRIPE_DASHBOARD_BASE = os.environ.get('STRIPE_DASHBOARD_BASE', 'https://dashboard.stripe.com/test')


class TestConfig(Config):
    """In-memory SQLite for automated tests — never prod MySQL."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {}
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    def _get_database_uri(self):
        return self.SQLALCHEMY_DATABASE_URI

