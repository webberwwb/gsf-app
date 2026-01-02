#!/usr/bin/env python3
"""Test database connection locally"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up path for imports
sys.path.insert(0, os.path.dirname(__file__))

from config import Config
from models import db
from app import create_app

def test_connection():
    """Test database connection"""
    print("Testing database connection...")
    print("-" * 50)
    
    config = Config()
    
    # Print connection details (without password)
    print(f"MYSQL_HOST: {config.MYSQL_HOST}")
    print(f"MYSQL_PORT: {config.MYSQL_PORT}")
    print(f"MYSQL_USER: {config.MYSQL_USER}")
    print(f"MYSQL_DATABASE: {config.MYSQL_DATABASE}")
    print(f"MYSQL_PASSWORD: {'*' * len(config.MYSQL_PASSWORD) if config.MYSQL_PASSWORD else '(empty)'}")
    print(f"Is Cloud Run: {config._is_cloud_run}")
    print("-" * 50)
    
    # Get database URI (mask password)
    db_uri = config.SQLALCHEMY_DATABASE_URI
    if '@' in db_uri:
        parts = db_uri.split('@')
        if ':' in parts[0]:
            user_pass = parts[0].split('://')[1]
            if ':' in user_pass:
                user = user_pass.split(':')[0]
                masked_uri = db_uri.replace(user_pass, f"{user}:***")
            else:
                masked_uri = db_uri
        else:
            masked_uri = db_uri
    else:
        masked_uri = db_uri
    
    print(f"Database URI: {masked_uri}")
    print("-" * 50)
    
    # Create app and test connection
    app = create_app()
    with app.app_context():
        try:
            print("Attempting to connect...")
            result = db.session.execute(db.text('SELECT 1 as test'))
            row = result.fetchone()
            if row and row[0] == 1:
                print("✅ Database connection successful!")
                return True
            else:
                print("❌ Database connection returned unexpected result")
                return False
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)


