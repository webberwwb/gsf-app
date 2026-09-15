"""
Shipping fee calculation utilities
"""
from decimal import Decimal
from utils.money import round_money
from utils.cutting import line_product_amount


def get_delivery_fee_config():
    """
    Get the active delivery fee configuration from database
    
    Returns:
        DeliveryFeeConfig: Active delivery fee config, or None if not found
    """
    from models.delivery_fee_config import DeliveryFeeConfig
    config = DeliveryFeeConfig.query.filter_by(is_active=True).first()
    return config


DEFAULT_TIERS = [
    {'threshold': 0, 'fee': 7.99},
    {'threshold': 58.00, 'fee': 5.99},
    {'threshold': 128.00, 'fee': 3.99},
    {'threshold': 150.00, 'fee': 0},
]

DEFAULT_DEPOT = {'lat': 43.8776838, 'lng': -79.3639328, 'label': 'Markham'}


def public_delivery_fee_payload(config=None):
    if config is None:
        config = get_delivery_fee_config()
    tiers = _cfg_get(config, 'tiers') or DEFAULT_TIERS
    depot = _cfg_get(config, 'depot') or DEFAULT_DEPOT
    return {
        'tiers': tiers,
        'depot': depot,
        'region_surcharges': region_surcharges_from(config),
        'distance_surcharges': [],
        'beyond_surcharge': 0,
        'beyond_label': '',
    }


def get_shipping_fee_for_subtotal(subtotal, config=None):
    """
    Calculate shipping fee based on subtotal and delivery fee config
    
    Args:
        subtotal (Decimal): Tier subtotal for threshold lookup
        config (DeliveryFeeConfig, optional): Delivery fee config. If None, will fetch from DB.
        
    Returns:
        Decimal: Shipping fee amount
    """
    if config is None:
        config = get_delivery_fee_config()
    
    if not config or not config.tiers:
        # Fallback to default values if no config found
        if subtotal >= Decimal('150.00'):
            return round_money('0')
        if subtotal >= Decimal('128.00'):
            return round_money('3.99')
        if subtotal >= Decimal('58.00'):
            return round_money('5.99')
        return round_money('7.99')
    
    # Get tiers sorted by threshold (should already be sorted, but ensure it)
    tiers = sorted(config.tiers, key=lambda t: t.get('threshold', 0))
    
    # Find the appropriate tier (highest threshold that's <= subtotal)
    applicable_fee = None
    for tier in tiers:
        threshold = Decimal(str(tier.get('threshold', 0)))
        if subtotal >= threshold:
            applicable_fee = Decimal(str(tier.get('fee', 0)))
        else:
            break
    
    if applicable_fee is not None:
        return round_money(applicable_fee)
    base = Decimal(str(tiers[0].get('fee', 0))) if tiers else Decimal('7.99')
    return round_money(base)


def adjustment_discount(adjustment) -> Decimal:
    """Negative admin discount only; penalties do not affect shipping tier."""
    adj = Decimal(str(adjustment or 0))
    return min(adj, Decimal('0'))


def shipping_tier_base_from_parts(subtotal, credit=0, adjustment=0, cutting_fees=0) -> Decimal:
    """max(0, subtotal - cutting_fees - credit + adjustment_discount)."""
    sub = Decimal(str(subtotal or 0))
    cut = Decimal(str(cutting_fees or 0))
    cr = Decimal(str(credit or 0))
    disc = adjustment_discount(adjustment)
    return round_money(max(Decimal('0'), sub - cut - cr + disc))


def _line_total_price(item) -> Decimal:
    if hasattr(item, 'total_price'):
        return Decimal(str(item.total_price or 0))
    if isinstance(item, dict) and 'total_price' in item:
        return Decimal(str(item['total_price'] or 0))
    if hasattr(item, 'unit_price') and hasattr(item, 'quantity'):
        return Decimal(str(item.unit_price or 0)) * Decimal(str(item.quantity or 0))
    if isinstance(item, dict) and 'unit_price' in item and 'quantity' in item:
        return Decimal(str(item['unit_price'] or 0)) * Decimal(str(item['quantity'] or 0))
    return Decimal('0')


def _product_for_item(item):
    from models.product import Product
    if hasattr(item, 'product') and item.product:
        return item.product
    if isinstance(item, dict) and item.get('product'):
        return item['product']
    product_id = None
    if hasattr(item, 'product_id'):
        product_id = item.product_id
    elif isinstance(item, dict):
        product_id = item.get('product_id')
    if product_id:
        return Product.query.get(product_id)
    return None


def eligible_tier_subtotal_from_items(order_items, tier_base) -> Decimal:
    """Allocate tier_base proportionally across lines that count toward free shipping."""
    if not order_items:
        return round_money(tier_base)

    gross = Decimal('0')
    for item in order_items:
        gross += line_product_amount(item, _line_total_price(item))
    if gross <= 0:
        return Decimal('0')

    base = Decimal(str(tier_base))
    eligible = Decimal('0')
    for item in order_items:
        product = _product_for_item(item)
        if product is not None and not product.counts_toward_free_shipping:
            continue
        line = line_product_amount(item, _line_total_price(item))
        eligible += (line / gross) * base
    return round_money(eligible)


DEFAULT_REGION_LABEL = 'GTA默认区域'
DEFAULT_REGION_SURCHARGES = [
    {
        'label': 'Waterloo / Kitchener / Guelph',
        'surcharge': 4,
        'cities': ['Waterloo', 'Kitchener', 'Guelph', 'Kitchener-Waterloo'],
    },
    {
        'label': 'Whitby / Pickering / Ajax / Hamilton / Burlington',
        'surcharge': 2,
        'cities': ['Whitby', 'Pickering', 'Ajax', 'Hamilton', 'Burlington'],
    },
]


def _cfg_get(config, key, default=None):
    if config is None:
        return default
    if isinstance(config, dict):
        return config.get(key, default)
    return getattr(config, key, default)


def address_coords(address):
    if not address:
        return None
    if isinstance(address, dict):
        lat = address.get('latitude', address.get('lat'))
        lng = address.get('longitude', address.get('lng'))
    else:
        lat = getattr(address, 'latitude', None)
        if lat is None:
            lat = getattr(address, 'lat', None)
        lng = getattr(address, 'longitude', None)
        if lng is None:
            lng = getattr(address, 'lng', None)
    if lat is None or lng is None or lat == '' or lng == '':
        return None
    try:
        return {'lat': float(lat), 'lng': float(lng)}
    except (TypeError, ValueError):
        return None


def distance_km(a, b):
    if not a or not b:
        return None
    try:
        lat1 = float(a['lat'])
        lng1 = float(a['lng'])
        lat2 = float(b['lat'])
        lng2 = float(b['lng'])
    except (TypeError, ValueError, KeyError):
        return None
    from math import atan2, cos, radians, sin, sqrt
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    x = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 6371 * 2 * atan2(sqrt(x), sqrt(1 - x))


def city_key(city):
    return ''.join(ch for ch in str(city or '').lower() if ch.isalnum())


def city_from_address(address):
    if not address:
        return ''
    if isinstance(address, str):
        return address
    if isinstance(address, dict):
        return address.get('city') or address.get('locality') or ''
    return getattr(address, 'city', None) or ''


def _as_region_groups(raw):
    groups = []
    if not raw:
        return groups
    for group in raw:
        try:
            cities = [str(city).strip() for city in (group.get('cities') or []) if str(city).strip()]
        except AttributeError:
            continue
        if not cities:
            continue
        try:
            surcharge = float(group.get('surcharge') or 0)
        except (TypeError, ValueError):
            surcharge = 0.0
        groups.append({
            'label': group.get('label') or '',
            'surcharge': surcharge,
            'cities': cities,
        })
    return groups


def region_surcharges_from(config):
    groups = _as_region_groups(_cfg_get(config, 'region_surcharges'))
    if groups:
        return groups
    groups = _as_region_groups(_cfg_get(config, 'distance_surcharges'))
    if groups:
        return groups
    return [
        {
            'label': group['label'],
            'surcharge': group['surcharge'],
            'cities': list(group['cities']),
        }
        for group in DEFAULT_REGION_SURCHARGES
    ]


def match_region_surcharge(config, address):
    city = city_from_address(address)
    key = city_key(city)
    groups = region_surcharges_from(config)
    if not key:
        return {
            'surcharge': Decimal('0'),
            'label': DEFAULT_REGION_LABEL,
            'city': city,
            'region': None,
            'matched': False,
        }
    for group in groups:
        if any(city_key(item) == key for item in group['cities']):
            return {
                'surcharge': round_money(group['surcharge']),
                'label': group['label'],
                'city': city,
                'region': group,
                'matched': True,
            }
    return {
        'surcharge': Decimal('0'),
        'label': DEFAULT_REGION_LABEL,
        'city': city,
        'region': None,
        'matched': False,
    }


def region_surcharge_for_address(config, address):
    return match_region_surcharge(config, address)['surcharge']


def calculate_shipping_fee(subtotal, delivery_method, address=None, order_items=None, config=None):
    """
    Calculate shipping fee based on order details.

    ``subtotal`` is shipping_tier_base (after credit + adjustment discount).
    When order_items is provided, tier_base is allocated proportionally across
    eligible lines (counts_toward_free_shipping=True).
    Delivery adds a city-region surcharge on top of the subtotal tier.
    """
    from constants.status_enums import DeliveryMethod

    if not isinstance(subtotal, Decimal):
        subtotal = Decimal(str(subtotal))

    if delivery_method == DeliveryMethod.PICKUP.value:
        return Decimal('0.00')

    if config is None:
        config = get_delivery_fee_config()

    tier_subtotal = subtotal
    if order_items:
        tier_subtotal = eligible_tier_subtotal_from_items(order_items, subtotal)

    base = get_shipping_fee_for_subtotal(tier_subtotal, config=config)
    return round_money(base + region_surcharge_for_address(config, address))
