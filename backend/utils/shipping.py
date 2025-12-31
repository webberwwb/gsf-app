"""
Shipping fee calculation utilities
"""
from decimal import Decimal


# Shipping configuration
FREE_SHIPPING_THRESHOLD = Decimal('150.00')  # Free shipping for orders >= $150
GTA_SHIPPING_FEE = Decimal('7.50')  # $7.50 for GTA region

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


def calculate_shipping_fee(subtotal, delivery_method, address=None):
    """
    Calculate shipping fee based on order details
    
    Rules:
    - Pickup orders: $0 shipping
    - Delivery orders with subtotal >= $150: $0 shipping (free)
    - Delivery orders with subtotal < $150 in GTA: $7.50 shipping
    - Delivery orders with subtotal < $150 outside GTA: $7.50 shipping (can be adjusted later)
    
    Args:
        subtotal (Decimal or float): Order subtotal before shipping
        delivery_method (str): 'pickup' or 'delivery'
        address (Address or dict, optional): Delivery address object or dict with 'city' key
        
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
    
    # Free shipping for orders >= $150
    if subtotal >= FREE_SHIPPING_THRESHOLD:
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

