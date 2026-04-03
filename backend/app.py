from flask import Flask, redirect, request
from flask_cors import CORS
from flask_migrate import Migrate
from flask_socketio import SocketIO
from config import Config
from models import db

# Global socketio instance (initialized in create_app)
socketio = None

def create_app(config_class=Config):
    global socketio
    
    app = Flask(__name__)
    config = config_class()
    app.config.from_object(config)
    # Set database URI directly since Flask-SQLAlchemy needs it as a string
    app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
    
    # Configure logging for Cloud Run (logs to stdout)
    import logging
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )
    logger = logging.getLogger(__name__)
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Initialize SocketIO with CORS support and gevent async mode
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent', logger=True, engineio_logger=True)
    
    # Register WebSocket handlers
    from websockets import register_websocket_handlers
    register_websocket_handlers(socketio)
    
    # Test database connection on startup
    logger = logging.getLogger(__name__)
    with app.app_context():
        try:
            db.session.execute(db.text('SELECT 1'))
            logger.info("Database connection successful")
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            logger.error(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[0]}@***")
    
    # CORS configuration - allow all origins
    # Note: When supports_credentials=True, we can't use origins="*", so we'll handle it manually
    CORS(app, 
         resources={r"/api/*": {
             "origins": "*",
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
             "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept"],
             "expose_headers": ["Content-Type"],
             "supports_credentials": False  # Set to False when using wildcard origin
         }},
         automatic_options=True)
    
    # Handle CORS headers for all responses
    @app.after_request
    def after_request(response):
        # Get the origin from the request
        origin = request.headers.get('Origin')
        
        # Allow all origins (since we're not using credentials)
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
        else:
            response.headers['Access-Control-Allow-Origin'] = '*'
        
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept'
        response.headers['Access-Control-Expose-Headers'] = 'Content-Type'
        
        # Handle preflight requests
        if request.method == 'OPTIONS':
            response.headers['Access-Control-Max-Age'] = '86400'  # Cache for 24 hours
        
        return response
    
    # Register blueprints
    from routes import api_bp
    try:
        from routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
    except ImportError:
        # Auth routes not available yet
        pass
    try:
        from routes.products import products_bp
        app.register_blueprint(products_bp, url_prefix='/api')
    except ImportError:
        # Products routes not available yet
        pass
    try:
        from routes.orders import orders_bp
        app.register_blueprint(orders_bp, url_prefix='/api')
    except ImportError:
        # Orders routes not available yet
        pass
    try:
        from routes.addresses import addresses_bp
        app.register_blueprint(addresses_bp, url_prefix='/api')
    except ImportError:
        # Addresses routes not available yet
        pass
    try:
        from routes.admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/api/admin')
    except ImportError:
        # Admin routes not available yet
        pass
    try:
        from routes.cron import cron_bp
        app.register_blueprint(cron_bp, url_prefix='/api')
    except ImportError:
        # Cron routes not available yet
        pass
    try:
        from routes.constants import constants_bp
        app.register_blueprint(constants_bp)
    except ImportError:
        # Constants routes not available yet
        pass
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Add root route
    @app.route('/')
    def root():
        """Root endpoint - redirect to health check"""
        return redirect('/api/health', code=302)
    
    # Note: Database migrations are handled by Flask-Migrate
    # Run: flask db upgrade to apply migrations

    return app, socketio

if __name__ == '__main__':
    app, socketio = create_app()
    # Use gevent mode for both development and production consistency
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)

