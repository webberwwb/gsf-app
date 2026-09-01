from flask import Blueprint, jsonify, redirect, Response
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

_IMAGE_TYPES = {
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'webp': 'image/webp',
}
_IMAGE_CACHE_CONTROL = 'public, max-age=31536000, immutable'
_gcs_client = None


def _gcs_client_cached():
    global _gcs_client
    if _gcs_client is None:
        from google.cloud import storage
        _gcs_client = storage.Client(project=Config.GCS_PROJECT_ID)
    return _gcs_client


def _image_content_type(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return _IMAGE_TYPES.get(ext, 'image/jpeg')


@api_bp.route('/images/<path:filename>', methods=['GET'])
def serve_image(filename):
    """Stream the GCS object. Browser caches this URL for a year (UUID filenames)."""
    from google.cloud.exceptions import NotFound

    blob = _gcs_client_cached().bucket(Config.GCS_BUCKET_NAME).blob(filename)
    try:
        handle = blob.open('rb')
    except NotFound:
        return jsonify({'error': 'Image not found'}), 404

    def chunks():
        with handle:
            while True:
                data = handle.read(256 * 1024)
                if not data:
                    break
                yield data

    return Response(
        chunks(),
        mimetype=_image_content_type(filename),
        headers={'Cache-Control': _IMAGE_CACHE_CONTROL},
    )

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

