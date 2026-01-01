"""
Shipping fee calculation utilities
"""
from decimal import Decimal


# Shipping configuration
FREE_SHIPPING_THRESHOLD = Decimal('150.00')  # Free shipping for orders >= $150
GTA_SHIPPING_FEE = Decimal('7.99')  # $7.99 for GTA region

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
    
    Rules:
    - Pickup orders: $0 shipping
    - Delivery orders with subtotal >= $150: $0 shipping (free)
    - Delivery orders with subtotal < $150 in GTA: $7.99 shipping
    - Delivery orders with subtotal < $150 outside GTA: $7.99 shipping (can be adjusted later)
    
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
    
    # Free shipping for orders >= $150 (using adjusted subtotal)
    if free_shipping_subtotal >= FREE_SHIPPING_THRESHOLD:
        return Decimal('0.00')
    
    # For delivery orders under $150, check if GTA
    if address:
        # Handle both Address model objects and dict
        city = address.city if hasattr(address, 'city') else address.get('city')
        
        if is_gta_address(city):
            return GTA_SHIPPING_FEE
    
    # Default shipping fee for non-GTA or unknown location
    # For now, we use the same rate, but this can be adjusted
    return GTA_SHIPPING_FEE

