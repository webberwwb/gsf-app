from flask import Flask, redirect
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
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
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
        from routes.admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/api/admin')
    except ImportError:
        # Admin routes not available yet
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

