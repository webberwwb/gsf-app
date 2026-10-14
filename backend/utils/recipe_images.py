"""Resize recipe photos and store them on the public image proxy.

The JPEG keeps its aspect ratio. The URL is a stable /api/images/recipes/<uuid>.jpg
with a year-long public cache. No signed URL.
"""
import io
import uuid

from flask import current_app

from config import Config
from utils.image_urls import proxy_image_url

MAX_EDGE = 960
JPEG_QUALITY = 80

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

try:
    from google.cloud import storage
    from google.oauth2 import service_account
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    storage = None
    service_account = None


def resize_to_jpeg(raw_bytes, max_edge=MAX_EDGE, quality=JPEG_QUALITY):
    """Shrink so the longest edge is at most max_edge. Never crop."""
    if not PIL_AVAILABLE:
        raise RuntimeError('Pillow is required')
    image = Image.open(io.BytesIO(raw_bytes))
    if image.mode in ('RGBA', 'LA', 'P'):
        rgb = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        mask = image.split()[-1] if image.mode in ('RGBA', 'LA') else None
        rgb.paste(image, mask=mask)
        image = rgb
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    image.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    image.save(output, format='JPEG', quality=quality, optimize=True)
    return output.getvalue(), image.size


def _gcs_client():
    if not GCS_AVAILABLE:
        return None
    creds_path = __import__('os').environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if creds_path and __import__('os').path.exists(creds_path):
        credentials = service_account.Credentials.from_service_account_file(creds_path)
        return storage.Client(credentials=credentials, project=Config.GCS_PROJECT_ID)
    return storage.Client(project=Config.GCS_PROJECT_ID)


def store_recipe_jpeg(jpeg_bytes):
    """Upload JPEG bytes and return the public proxy URL."""
    if not GCS_AVAILABLE:
        raise RuntimeError('Image upload not available')
    client = _gcs_client()
    if not client:
        raise RuntimeError('GCS client not available')
    object_name = f'recipes/{uuid.uuid4()}.jpg'
    bucket = client.bucket(Config.GCS_BUCKET_NAME)
    blob = bucket.blob(object_name)
    blob.cache_control = 'public, max-age=31536000, immutable'
    blob.upload_from_string(jpeg_bytes, content_type='image/jpeg')
    url = proxy_image_url(object_name)
    current_app.logger.info('Uploaded recipe image %s', object_name)
    return url
