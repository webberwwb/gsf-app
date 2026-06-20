"""
Shipping fee calculation utilities
"""
from decimal import Decimal
from utils.money import round_money


def get_delivery_fee_config():
    """
    Get the active delivery fee configuration from database
    
    Returns:
        DeliveryFeeConfig: Active delivery fee config, or None if not found
    """
    from models.delivery_fee_config import DeliveryFeeConfig
    config = DeliveryFeeConfig.query.filter_by(is_active=True).first()
    return config


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


def shipping_tier_base_from_parts(subtotal, credit=0, adjustment=0) -> Decimal:
    """max(0, subtotal - credit + adjustment_discount)."""
    sub = Decimal(str(subtotal or 0))
    cr = Decimal(str(credit or 0))
    disc = adjustment_discount(adjustment)
    return round_money(max(Decimal('0'), sub - cr + disc))


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
        gross += _line_total_price(item)
    if gross <= 0:
        return Decimal('0')

    base = Decimal(str(tier_base))
    eligible = Decimal('0')
    for item in order_items:
        product = _product_for_item(item)
        if product is not None and not product.counts_toward_free_shipping:
            continue
        line = _line_total_price(item)
        eligible += (line / gross) * base
    return round_money(eligible)


# GTA cities (case-insensitive matching)
GTA_CITIES = {
    'toronto',
    'north york',
    'northyork',
    'scarborough',
    'etobicoke',
    'york',
    'east york',
    'eastyork',
    'mississauga',
    'brampton',
    'markham',
    'vaughan',
    'richmond hill',
    'richmondhill',
    'ajax',
    'pickering',
    'whitby',
    'oshawa',
    'oakville',
    'burlington',
    'milton',
    'aurora',
    'newmarket',
    'georgina',
    'king',
    'whitchurch-stouffville',
    'caledon',
}


def is_gta_address(city):
    if not city:
        return False
    normalized_city = city.lower().strip()
    return normalized_city in GTA_CITIES


def calculate_shipping_fee(subtotal, delivery_method, address=None, order_items=None):
    """
    Calculate shipping fee based on order details.

    ``subtotal`` is shipping_tier_base (after credit + adjustment discount).
    When order_items is provided, tier_base is allocated proportionally across
    eligible lines (counts_toward_free_shipping=True).
    """
    from constants.status_enums import DeliveryMethod

    if not isinstance(subtotal, Decimal):
        subtotal = Decimal(str(subtotal))

    if delivery_method == DeliveryMethod.PICKUP.value:
        return Decimal('0.00')

    tier_subtotal = subtotal
    if order_items:
        tier_subtotal = eligible_tier_subtotal_from_items(order_items, subtotal)

    return get_shipping_fee_for_subtotal(tier_subtotal)
