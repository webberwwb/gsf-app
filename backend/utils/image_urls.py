"""Browser URLs for images stored in Cloud Storage.

Catalog photos (products/ and recipes/) are public objects. List views use a
sibling thumbnail. Delivery photos stay on the backend proxy.
"""
from urllib.parse import unquote

from config import Config

_API_IMAGE_MARKER = '/api/images/'
_GCS_HOST_MARKER = 'storage.googleapis.com/'
_CATALOG_FOLDERS = ('products', 'recipes')


def gcs_public_url(object_name):
    base = (Config.GCS_PUBLIC_URL_BASE or '').rstrip('/')
    name = (object_name or '').lstrip('/')
    return f'{base}/{name}'


def proxy_image_url(object_name):
    base = (Config.IMAGE_PROXY_BASE or '').rstrip('/')
    name = (object_name or '').lstrip('/')
    return f'{base}/{name}'


def image_object_name(url):
    if not url or not isinstance(url, str):
        return None
    idx = url.find(_API_IMAGE_MARKER)
    if idx != -1:
        return unquote(url[idx + len(_API_IMAGE_MARKER):]).lstrip('/').split('?', 1)[0]
    idx = url.find(_GCS_HOST_MARKER)
    if idx != -1:
        rest = url[idx + len(_GCS_HOST_MARKER):]
        parts = rest.split('/', 1)
        if len(parts) == 2:
            return unquote(parts[1].split('?', 1)[0])
    return None


def is_catalog_object(object_name):
    name = (object_name or '').lstrip('/')
    folder = name.split('/', 1)[0]
    return folder in _CATALOG_FOLDERS and '/' in name


def thumbnail_object_name(object_name):
    """products/abc.png -> products/thumbs/abc.jpg. None for non-catalog objects."""
    name = (object_name or '').lstrip('/')
    if not is_catalog_object(name):
        return None
    parts = name.split('/')
    folder = parts[0]
    filename = parts[-1]
    if not filename or filename == 'thumbs':
        return None
    stem = filename.rsplit('.', 1)[0]
    if not stem:
        return None
    return f'{folder}/thumbs/{stem}.jpg'


def public_image_url(url):
    """Full-size browser URL. Catalog objects point at Cloud Storage."""
    if not url or not isinstance(url, str):
        return url
    name = image_object_name(url)
    if not name:
        return url
    if is_catalog_object(name):
        return gcs_public_url(name)
    return proxy_image_url(name)


def thumbnail_url(url):
    """Public thumbnail URL, or None when this image has no catalog thumb."""
    if not url or not isinstance(url, str):
        return None
    name = image_object_name(url)
    thumb = thumbnail_object_name(name) if name else None
    if not thumb:
        return None
    return gcs_public_url(thumb)


def public_image_urls(urls):
    if not urls:
        return urls
    return [public_image_url(u) for u in urls]


def thumbnail_urls(urls):
    if not urls:
        return []
    return [thumbnail_url(u) for u in urls]
