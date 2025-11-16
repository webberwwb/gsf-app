from flask import Blueprint, jsonify, request, redirect, Response
from models import db
import os

api_bp = Blueprint('api', __name__)

@api_bp.route('/', methods=['GET'])
def root():
    """Root endpoint - redirect to health check"""
    return redirect('/api/health', code=302)

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'API is running'
    }), 200

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

# Add your API routes here
# @api_bp.route('/your-endpoint', methods=['GET', 'POST'])
# def your_endpoint():
#     # Your logic here
#     return jsonify({'message': 'Success'}), 200

