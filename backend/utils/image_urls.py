"""Normalize product image URLs to the backend proxy.

The SPA stores https://backend.grainstoryfarm.ca/api/images/<object> and never
reformats it. /api/images/<object> streams the GCS object with a long cache.
"""
from urllib.parse import unquote

from config import Config

_API_IMAGE_MARKER = '/api/images/'
_GCS_HOST_MARKER = 'storage.googleapis.com/'


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


def public_image_url(url):
    """Stable backend proxy URL. Frontend uses this as-is."""
    if not url or not isinstance(url, str):
        return url
    name = image_object_name(url)
    if not name:
        return url
    return proxy_image_url(name)


def public_image_urls(urls):
    if not urls:
        return urls
    return [public_image_url(u) for u in urls]
