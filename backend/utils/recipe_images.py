"""Resize recipe photos and store them on public Cloud Storage.

The full JPEG keeps its aspect ratio, capped at 960px. A 320px thumbnail is
written beside it. Both objects are public and cached for a year.
"""
import io
import uuid

from flask import current_app

from config import Config
from utils.catalog_images import ensure_thumbnail
from utils.image_urls import gcs_public_url

MAX_EDGE = 960
JPEG_QUALITY = 80

try:
    from PIL import Image, ImageOps, UnidentifiedImageError
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    ImageOps = None
    UnidentifiedImageError = Exception

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    register_heif_opener = None

# iPhone camera roll is HEIC/HEIF. Major brand plus compatible brands in the ftyp box.
_HEIF_BRANDS = {
    b'heic', b'heix', b'hevc', b'hevx', b'heim', b'heis', b'heif', b'mif1', b'msf1',
}
_ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'heic', 'heif'}
_ALLOWED_MIME = {
    'image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp',
    'image/heic', 'image/heif', 'image/heic-sequence', 'image/heif-sequence',
}

try:
    from google.cloud import storage
    from google.oauth2 import service_account
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    storage = None
    service_account = None


def _is_heif(raw):
    if len(raw) < 12 or raw[4:8] != b'ftyp':
        return False
    size = int.from_bytes(raw[:4], 'big')
    end = size if 16 <= size <= len(raw) else min(len(raw), 64)
    chunk = raw[8:end]
    return any(chunk[i:i + 4] in _HEIF_BRANDS for i in range(0, max(len(chunk) - 3, 0), 4))


def supported_recipe_photo(filename, mimetype, raw):
    """True for jpeg/png/gif/webp and iPhone HEIC, by name, type, or bytes."""
    ext = filename.rsplit('.', 1)[-1].lower() if filename and '.' in filename else ''
    if ext in _ALLOWED_EXT:
        return True
    mime = (mimetype or '').split(';', 1)[0].strip().lower()
    if mime in _ALLOWED_MIME:
        return True
    if not raw:
        return False
    if raw[:3] == b'\xff\xd8\xff' or raw[:8] == b'\x89PNG\r\n\x1a\n':
        return True
    if raw[:6] in (b'GIF87a', b'GIF89a'):
        return True
    if len(raw) >= 12 and raw[:4] == b'RIFF' and raw[8:12] == b'WEBP':
        return True
    return _is_heif(raw)


def resize_to_jpeg(raw_bytes, max_edge=MAX_EDGE, quality=JPEG_QUALITY):
    """Shrink so the longest edge is at most max_edge. Never crop."""
    if not PIL_AVAILABLE:
        raise RuntimeError('Pillow is required')
    image = Image.open(io.BytesIO(raw_bytes))
    image = ImageOps.exif_transpose(image)
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
    bucket = client.bucket(Config.GCS_CATALOG_BUCKET)
    blob = bucket.blob(object_name)
    blob.cache_control = 'public, max-age=31536000, immutable'
    blob.upload_from_string(jpeg_bytes, content_type='image/jpeg')
    ensure_thumbnail(bucket, object_name, jpeg_bytes)
    url = gcs_public_url(object_name)
    current_app.logger.info('Uploaded recipe image %s', object_name)
    return url
