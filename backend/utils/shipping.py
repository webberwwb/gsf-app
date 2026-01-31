"""
Shipping fee calculation utilities
"""
from decimal import Decimal


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
        subtotal (Decimal): Order subtotal (excluding products that don't count toward free shipping)
        config (DeliveryFeeConfig, optional): Delivery fee config. If None, will fetch from DB.
        
    Returns:
        Decimal: Shipping fee amount
    """
    if config is None:
        config = get_delivery_fee_config()
    
    if not config or not config.tiers:
        # Fallback to default values if no config found
        if subtotal >= Decimal('150.00'):
            return Decimal('0.00')
        elif subtotal >= Decimal('128.00'):
            return Decimal('3.99')
        elif subtotal >= Decimal('58.00'):
            return Decimal('5.99')
        else:
            return Decimal('7.99')
    
    # Get tiers sorted by threshold (should already be sorted, but ensure it)
    tiers = sorted(config.tiers, key=lambda t: t.get('threshold', 0))
    
    # Find the appropriate tier (highest threshold that's <= subtotal)
    applicable_fee = None
    for tier in tiers:
        threshold = Decimal(str(tier.get('threshold', 0)))
        if subtotal >= threshold:
            applicable_fee = Decimal(str(tier.get('fee', 0)))
        else:
            # Since tiers are sorted, we can break early
            break
    
    # If we found a tier, use it; otherwise use the first tier (base fee)
    if applicable_fee is not None:
        return applicable_fee
    else:
        # This shouldn't happen if tiers[0] has threshold 0, but handle it anyway
        return Decimal(str(tiers[0].get('fee', 0))) if tiers else Decimal('7.99')

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
    """
    Check if a city is in the GTA region
    
    Args:
        city (str): City name from address
        
    Returns:
        bool: True if city is in GTA, False otherwise
    """
    if not city:
        return False
    
    # Normalize city name (lowercase, remove extra spaces)
    normalized_city = city.lower().strip()
    
    return normalized_city in GTA_CITIES


def calculate_shipping_fee(subtotal, delivery_method, address=None, order_items=None):
    """
    Calculate shipping fee based on order details
    
    Rules (configurable via DeliveryFeeConfig):
    - Pickup orders: $0 shipping
    - Delivery orders: Fee calculated based on subtotal thresholds (configurable in admin)
    - Default thresholds: < $58: base fee, >= $58: threshold 1 fee, >= $128: threshold 2 fee, >= $150: free
    
    Note: Products with counts_toward_free_shipping=False are excluded from subtotal
    calculation for free shipping threshold determination.
    
    Args:
        subtotal (Decimal or float): Order subtotal before shipping (full subtotal)
        delivery_method (str): 'pickup' or 'delivery'
        address (Address or dict, optional): Delivery address object or dict with 'city' key
        order_items (list, optional): List of order items with product info. Each item should have:
            - product_id or product object with counts_toward_free_shipping attribute
            - total_price or unit_price * quantity
            
    Returns:
        Decimal: Shipping fee amount
    """
    from constants.status_enums import DeliveryMethod
    
    # Convert subtotal to Decimal if needed
    if not isinstance(subtotal, Decimal):
        subtotal = Decimal(str(subtotal))
    
    # Pickup orders have no shipping fee
    if delivery_method == DeliveryMethod.PICKUP.value:
        return Decimal('0.00')
    
    # Calculate subtotal for free shipping threshold (excluding products that don't count)
    free_shipping_subtotal = subtotal
    if order_items:
        from models.product import Product
        free_shipping_subtotal = Decimal('0.00')
        
        for item in order_items:
            # Get product to check counts_toward_free_shipping flag
            product = None
            if hasattr(item, 'product'):
                product = item.product
            elif hasattr(item, 'product_id'):
                product = Product.query.get(item.product_id)
            elif isinstance(item, dict):
                if 'product' in item:
                    product = item['product']
                elif 'product_id' in item:
                    product = Product.query.get(item['product_id'])
            
            # If product doesn't count toward free shipping, exclude it
            if product and not product.counts_toward_free_shipping:
                continue
            
            # Add item price to free shipping subtotal
            if hasattr(item, 'total_price'):
                free_shipping_subtotal += Decimal(str(item.total_price))
            elif isinstance(item, dict) and 'total_price' in item:
                free_shipping_subtotal += Decimal(str(item['total_price']))
            elif hasattr(item, 'unit_price') and hasattr(item, 'quantity'):
                free_shipping_subtotal += Decimal(str(item.unit_price)) * Decimal(str(item.quantity))
            elif isinstance(item, dict) and 'unit_price' in item and 'quantity' in item:
                free_shipping_subtotal += Decimal(str(item['unit_price'])) * Decimal(str(item['quantity']))
    
    # Calculate shipping fee based on subtotal using dynamic config
    # Note: Currently all regions use the same fee structure
    # The GTA check is kept for potential future use
    return get_shipping_fee_for_subtotal(free_shipping_subtotal)

