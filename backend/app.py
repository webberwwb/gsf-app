from flask import Flask, redirect, request
from flask_cors import CORS
from flask_migrate import Migrate
from config import Config
from models import db

def create_app(config_class=Config):
    app = Flask(__name__)
    config = config_class()
    app.config.from_object(config)
    # Set database URI directly since Flask-SQLAlchemy needs it as a string
    app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
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

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=True)

