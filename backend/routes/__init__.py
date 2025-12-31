from flask import Blueprint, jsonify, request, redirect, Response
from models import db
from config import Config
import os

api_bp = Blueprint('api', __name__)

@api_bp.route('/', methods=['GET'])
def root():
    """Root endpoint - redirect to health check"""
    return redirect('/api/health', code=302)

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with database connectivity test"""
    try:
        # Test database connection
        db.session.execute(db.text('SELECT 1'))
        db_status = 'connected'
        db_error = None
    except Exception as e:
        db_status = 'disconnected'
        db_error = str(e)
    
    status_code = 200 if db_status == 'connected' else 503
    
    return jsonify({
        'status': 'healthy' if db_status == 'connected' else 'unhealthy',
        'message': 'API is running',
        'database': {
            'status': db_status,
            'error': db_error
        }
    }), status_code

@api_bp.route('/test', methods=['GET'])
def test():
    """Test endpoint"""
    return jsonify({
        'message': 'Backend is working!',
        'data': {
            'timestamp': '2024-01-01T00:00:00Z'
        }
    }), 200

@api_bp.route('/images/<path:filename>', methods=['GET'])
def serve_image(filename):
    """Serve images from GCS bucket (proxy endpoint) - public access"""
    try:
        from google.cloud import storage
        from config import Config
        
        # Initialize GCS client
        creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if creds_path and os.path.exists(creds_path):
            from google.oauth2 import service_account
            credentials = service_account.Credentials.from_service_account_file(creds_path)
            gcs_client = storage.Client(credentials=credentials, project=Config.GCS_PROJECT_ID)
        else:
            gcs_client = storage.Client(project=Config.GCS_PROJECT_ID)
        
        bucket_name = Config.GCS_BUCKET_NAME
        bucket = gcs_client.bucket(bucket_name)
        blob = bucket.blob(filename)
        
        # Check if blob exists
        if not blob.exists():
            return jsonify({'error': 'Image not found'}), 404
        
        # Download image data
        image_data = blob.download_as_bytes()
        
        # Get content type from blob metadata or infer from filename
        content_type = blob.content_type or 'image/jpeg'
        if not content_type.startswith('image/'):
            # Infer from extension
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            content_type_map = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'webp': 'image/webp'
            }
            content_type = content_type_map.get(ext, 'image/jpeg')
        
        # Return image with proper headers
        return Response(
            image_data,
            mimetype=content_type,
            headers={
                'Cache-Control': 'public, max-age=31536000'  # Cache for 1 year
            }
        )
        
    except ImportError:
        return jsonify({'error': 'GCS not available'}), 503
    except Exception as e:
        return jsonify({
            'error': 'Failed to serve image',
            'message': str(e)
        }), 500

def _get_version_from_sw_js():
    """Helper function to extract version from sw.js file"""
    import re
    # Try multiple paths to find sw.js:
    # 1. Copied into Docker image during build (app_version_sw.js)
    # 2. Relative path from backend directory (for local dev)
    # 3. Environment variable (for Cloud Run if set during deployment)
    
    # Check environment variable first (can be set during deployment)
    env_version = os.environ.get('APP_VERSION')
    if env_version:
        return env_version
    
    # Try paths in order of preference
    possible_paths = [
        '/app/app_version_sw.js',  # Docker image path
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'public', 'sw.js'),  # Local dev
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'dist', 'sw.js'),  # Local prod build
    ]
    
    for sw_js_path in possible_paths:
        if os.path.exists(sw_js_path):
            try:
                with open(sw_js_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extract version from: const VERSION = '2025.12.29.2330'
                    match = re.search(r"const VERSION = ['\"]([^'\"]+)['\"]", content)
                    if match:
                        return match.group(1)
            except Exception:
                continue
    
    return 'unknown'

@api_bp.route('/version', methods=['GET'])
def get_version():
    """Get latest app version from service worker file"""
    try:
        version = _get_version_from_sw_js()
        
        return jsonify({
            'app_version': version,
            'api_version': version,  # API version matches app version
            'status': 'success'
        }), 200
    except Exception as e:
        return jsonify({
            'app_version': 'unknown',
            'api_version': 'unknown',
            'status': 'error',
            'message': str(e)
        }), 200

@api_bp.route('/api-version', methods=['GET'])
def get_api_version():
    """Get API version (same as app version)"""
    try:
        version = _get_version_from_sw_js()
        return jsonify({
            'api_version': version,
            'status': 'success'
        }), 200
    except Exception as e:
        return jsonify({
            'api_version': 'unknown',
            'status': 'error',
            'message': str(e)
        }), 200

# Add your API routes here
# @api_bp.route('/your-endpoint', methods=['GET', 'POST'])
# def your_endpoint():
#     # Your logic here
#     return jsonify({'message': 'Success'}), 200

