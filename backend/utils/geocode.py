"""Geocode an address once and cache lat/lng on the row."""
import os

import requests


def _maps_key():
    return (
        os.environ.get('GOOGLE_MAPS_SERVER_API_KEY')
        or os.environ.get('GOOGLE_MAPS_API_KEY')
        or ''
    ).strip()


def geocode_query(query):
    key = _maps_key()
    if not key or not query:
        return None
    try:
        response = requests.get(
            'https://maps.googleapis.com/maps/api/geocode/json',
            params={'address': query, 'key': key, 'region': 'ca'},
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()
        if data.get('status') != 'OK' or not data.get('results'):
            return None
        result = data['results'][0]
        loc = (result.get('geometry') or {}).get('location') or {}
        lat = loc.get('lat')
        lng = loc.get('lng')
        if lat is None or lng is None:
            return None
        return {
            'lat': float(lat),
            'lng': float(lng),
            'place_id': result.get('place_id'),
        }
    except Exception:
        return None


def address_query_string(address):
    if address is None:
        return ''
    if isinstance(address, dict):
        parts = [
            address.get('address_line1'),
            address.get('address_line2'),
            address.get('city'),
            address.get('postal_code'),
            address.get('country') or 'Canada',
        ]
    else:
        parts = [
            getattr(address, 'address_line1', None),
            getattr(address, 'address_line2', None),
            getattr(address, 'city', None),
            getattr(address, 'postal_code', None),
            getattr(address, 'country', None) or 'Canada',
        ]
    return ', '.join(str(p).strip() for p in parts if p and str(p).strip())


def apply_coords_from_payload(address, data):
    if not address or not data:
        return address
    lat = data.get('latitude')
    lng = data.get('longitude')
    place_id = data.get('place_id')
    if lat is not None and lng is not None and lat != '' and lng != '':
        try:
            address.latitude = float(lat)
            address.longitude = float(lng)
        except (TypeError, ValueError):
            pass
        else:
            if place_id:
                address.place_id = place_id
            return address
    return ensure_address_coords(address)


def ensure_address_coords(address):
    if address is None:
        return None
    if getattr(address, 'latitude', None) is not None and getattr(address, 'longitude', None) is not None:
        return address
    result = geocode_query(address_query_string(address))
    if not result:
        return address
    address.latitude = result['lat']
    address.longitude = result['lng']
    if result.get('place_id'):
        address.place_id = result['place_id']
    return address
