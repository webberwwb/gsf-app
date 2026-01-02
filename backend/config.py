import os
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
                f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@/{self.MYSQL_DATABASE}"
                f"?unix_socket={socket_path}"
            )
        
        # Local dev: use TCP connection
        logger.info(f"Using local TCP connection: {self.MYSQL_HOST}:{self.MYSQL_PORT}")
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )
    
    # Set SQLALCHEMY_DATABASE_URI as a property that evaluates dynamically
    SQLALCHEMY_DATABASE_URI = property(lambda self: self._get_database_uri())
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20
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

