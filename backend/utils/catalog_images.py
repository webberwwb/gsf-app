"""Write public catalog originals and their 320px JPEG thumbnails."""
import io

from utils.image_urls import thumbnail_object_name

THUMB_EDGE = 320
THUMB_QUALITY = 75
CACHE_CONTROL = 'public, max-age=31536000, immutable'

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None


def encode_thumbnail(raw_bytes, max_edge=THUMB_EDGE, quality=THUMB_QUALITY):
    """JPEG whose longest edge is at most max_edge. Never crops."""
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
    return output.getvalue()


def upload_public(bucket, object_name, data, content_type):
    """Upload a catalog object. Public read comes from the bucket prefix policy."""
    blob = bucket.blob(object_name)
    blob.cache_control = CACHE_CONTROL
    blob.upload_from_string(data, content_type=content_type)
    return blob


def ensure_thumbnail(bucket, object_name, source_bytes):
    """Upload the sibling thumb when this object is a catalog original."""
    thumb_name = thumbnail_object_name(object_name)
    if not thumb_name or thumb_name == object_name.lstrip('/'):
        return None
    # Already a thumb object (products/thumbs/...).
    if '/thumbs/' in object_name:
        return None
    jpeg = encode_thumbnail(source_bytes)
    upload_public(bucket, thumb_name, jpeg, 'image/jpeg')
    return thumb_name
