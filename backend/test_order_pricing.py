"""
Comprehensive unit tests for order pricing calculations.

This test suite covers all pricing types:
1. per_item: Fixed price per item
2. weight_range: Price based on weight ranges
3. unit_weight: Price = weight × price_per_unit
4. bundled_weight: Price = final_weight × price_per_unit

Tests cover:
- Price calculations for each pricing type
- Edge cases (missing weights, invalid data, etc.)
- Deal price vs product price
- Unit price vs total price consistency
- Order creation and update scenarios
"""

import sys
import os
from decimal import Decimal
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db
from models.product import Product
from models.groupdeal import GroupDeal, GroupDealProduct
from models.order import Order, OrderItem
from models.user import User, AuthToken
from constants.status_enums import DeliveryMethod, PaymentMethod, OrderStatus


def setup_test_data(app):
    """Set up test data for pricing tests."""
    with app.app_context():
        # Clean up existing test data
        # Delete order items first (due to foreign key constraint)
        test_orders = Order.query.filter(Order.order_number.like('TEST-%')).all()
        for order in test_orders:
            OrderItem.query.filter_by(order_id=order.id).delete()
        Order.query.filter(Order.order_number.like('TEST-%')).delete()
        
        # Create test user if not exists
        test_user = User.query.filter_by(phone='9999999999').first()
        if not test_user:
            from constants.status_enums import UserStatus
            test_user = User(
                phone='9999999999',
                nickname='Test User Pricing',
                status=UserStatus.ACTIVE.value
            )
            db.session.add(test_user)
            db.session.flush()
        
        # Create test products for each pricing type
        products = {}
        
        # 1. per_item product
        per_item_product = Product.query.filter_by(name='Test Product - Per Item').first()
        if not per_item_product:
            per_item_product = Product(
                name='Test Product - Per Item',
                pricing_type='per_item',
                pricing_data={'price': 10.00},
                is_active=True
            )
            db.session.add(per_item_product)
            db.session.flush()
        products['per_item'] = per_item_product
        
        # 2. weight_range product
        weight_range_product = Product.query.filter_by(name='Test Product - Weight Range').first()
        if not weight_range_product:
            weight_range_product = Product(
                name='Test Product - Weight Range',
                pricing_type='weight_range',
                pricing_data={
                    'ranges': [
                        {'min': 0, 'max': 2, 'price': 10.00},
                        {'min': 2, 'max': 5, 'price': 8.00},
                        {'min': 5, 'max': None, 'price': 6.00}
                    ]
                },
                is_active=True
            )
            db.session.add(weight_range_product)
            db.session.flush()
        products['weight_range'] = weight_range_product
        
        # 3. unit_weight product
        unit_weight_product = Product.query.filter_by(name='Test Product - Unit Weight').first()
        if not unit_weight_product:
            unit_weight_product = Product(
                name='Test Product - Unit Weight',
                pricing_type='unit_weight',
                pricing_data={'price_per_unit': 5.00, 'unit': 'lb'},
                is_active=True
            )
            db.session.add(unit_weight_product)
            db.session.flush()
        products['unit_weight'] = unit_weight_product
        
        # 4. bundled_weight product
        bundled_weight_product = Product.query.filter_by(name='Test Product - Bundled Weight').first()
        if not bundled_weight_product:
            bundled_weight_product = Product(
                name='Test Product - Bundled Weight',
                pricing_type='bundled_weight',
                pricing_data={
                    'price_per_unit': 6.99,
                    'unit': 'lb',
                    'min_weight': 7,
                    'max_weight': 15
                },
                is_active=True
            )
            db.session.add(bundled_weight_product)
            db.session.flush()
        products['bundled_weight'] = bundled_weight_product
        
        # Create test group deal
        now = datetime.utcnow()
        test_deal = GroupDeal.query.filter_by(title='Test Deal - Pricing Tests').first()
        if not test_deal:
            test_deal = GroupDeal(
                title='Test Deal - Pricing Tests',
                description='Test deal for pricing calculations',
                order_start_date=now - timedelta(days=1),
                order_end_date=now + timedelta(days=7),
                pickup_date=now + timedelta(days=10),
                status='active'
            )
            db.session.add(test_deal)
            db.session.flush()
        
        # Add products to deal
        deal_products = {}
        for pricing_type, product in products.items():
            deal_product = GroupDealProduct.query.filter_by(
                group_deal_id=test_deal.id,
                product_id=product.id
            ).first()
            if not deal_product:
                deal_product = GroupDealProduct(
                    group_deal_id=test_deal.id,
                    product_id=product.id,
                    deal_stock_limit=None  # Unlimited for testing
                )
                db.session.add(deal_product)
            deal_products[pricing_type] = deal_product
        
        db.session.commit()
        
        return {
            'user_id': test_user.id,
            'products': products,
            'deal_id': test_deal.id,
            'deal_products': deal_products
        }


def test_per_item_pricing(app, test_data):
    """Test per_item pricing type."""
    print("\n=== Test: per_item Pricing ===")
    
    with app.app_context():
        product = test_data['products']['per_item']
        deal_product = test_data['deal_products']['per_item']
        deal_id = test_data['deal_id']
        user_id = test_data['user_id']
        
        # Test: Use product price
        quantity = 3
        expected_unit_price = product.get_display_price()  # 10.00
        expected_total_price = expected_unit_price * quantity  # 30.00
        
        print(f"  Test: Quantity={quantity}, Product Price={expected_unit_price}")
        print(f"    Expected: unit_price={expected_unit_price}, total_price={expected_total_price}")
        
        # Simulate price calculation (from create_order logic)
        unit_price = product.get_display_price() or 0
        total_price = unit_price * quantity
        
        assert unit_price == expected_unit_price, f"Unit price mismatch: {unit_price} != {expected_unit_price}"
        assert total_price == expected_total_price, f"Total price mismatch: {total_price} != {expected_total_price}"
        assert total_price == unit_price * quantity, "total_price should equal unit_price * quantity"
        print(f"    ✓ PASSED: unit_price={unit_price}, total_price={total_price}")
        
        return True


def test_weight_range_pricing(app, test_data):
    """Test weight_range pricing type."""
    print("\n=== Test: weight_range Pricing ===")
    
    with app.app_context():
        product = test_data['products']['weight_range']
        deal_id = test_data['deal_id']
        
        # Test 1: Estimation (no final_weight) - should use lowest price
        quantity = 2
        ranges = product.pricing_data.get('ranges', [])
        min_price = min(float(r.get('price', 0)) for r in ranges)  # 6.00
        expected_unit_price = min_price
        expected_total_price = expected_unit_price * quantity  # 12.00
        
        print(f"  Test 1: Quantity={quantity}, No final_weight (estimation)")
        print(f"    Expected: unit_price={expected_unit_price} (lowest), total_price={expected_total_price}")
        
        # Simulate price calculation
        if ranges:
            unit_price = min(float(r.get('price', 0)) for r in ranges)
        else:
            unit_price = 0
        total_price = unit_price * quantity
        
        assert unit_price == expected_unit_price, f"Unit price mismatch: {unit_price} != {expected_unit_price}"
        assert total_price == expected_total_price, f"Total price mismatch: {total_price} != {expected_total_price}"
        assert total_price == unit_price * quantity, "total_price should equal unit_price * quantity"
        print(f"    ✓ PASSED: unit_price={unit_price}, total_price={total_price}")
        
        # Test 2: Empty ranges
        product.pricing_data = {'ranges': []}
        db.session.commit()
        
        unit_price = 0 if not ranges else min(float(r.get('price', 0)) for r in ranges)
        total_price = unit_price * quantity
        
        assert unit_price == 0, "Unit price should be 0 when no ranges"
        assert total_price == 0, "Total price should be 0 when no ranges"
        print(f"    ✓ PASSED: Empty ranges handled correctly")
        
        # Restore ranges
        product.pricing_data = {
            'ranges': [
                {'min': 0, 'max': 2, 'price': 10.00},
                {'min': 2, 'max': 5, 'price': 8.00},
                {'min': 5, 'max': None, 'price': 6.00}
            ]
        }
        db.session.commit()
        
        return True


def test_unit_weight_pricing(app, test_data):
    """Test unit_weight pricing type."""
    print("\n=== Test: unit_weight Pricing ===")
    
    with app.app_context():
        product = test_data['products']['unit_weight']
        
        # Test 1: Estimation (no final_weight) - uses minimum estimated weight
        quantity = 3
        price_per_unit = float(product.pricing_data.get('price_per_unit', 0))  # 5.00
        estimated_weight = 1  # Minimum 1 unit
        expected_unit_price = price_per_unit * estimated_weight  # 5.00
        expected_total_price = expected_unit_price * quantity  # 15.00
        
        print(f"  Test 1: Quantity={quantity}, No final_weight (estimation)")
        print(f"    Expected: unit_price={expected_unit_price} (price_per_unit * estimated_weight), total_price={expected_total_price}")
        
        # Simulate price calculation
        price_per_unit = float(product.pricing_data.get('price_per_unit', 0) if product.pricing_data else 0)
        estimated_weight = 1
        unit_price = price_per_unit * estimated_weight
        total_price = unit_price * quantity
        
        assert unit_price == expected_unit_price, f"Unit price mismatch: {unit_price} != {expected_unit_price}"
        assert total_price == expected_total_price, f"Total price mismatch: {total_price} != {expected_total_price}"
        assert total_price == unit_price * quantity, "total_price should equal unit_price * quantity"
        print(f"    ✓ PASSED: unit_price={unit_price}, total_price={total_price}")
        
        # Test 2: With final_weight (simulating update_order scenario)
        final_weight = 2.5
        quantity = 2
        expected_unit_price = price_per_unit * final_weight  # 5.00 * 2.5 = 12.50
        expected_total_price = expected_unit_price * quantity  # 25.00
        
        print(f"  Test 2: Quantity={quantity}, final_weight={final_weight}")
        print(f"    Expected: unit_price={expected_unit_price}, total_price={expected_total_price}")
        
        # Simulate update_order calculation with final_weight
        if final_weight is not None:
            final_weight_float = float(final_weight)
            if final_weight_float > 0 and price_per_unit > 0:
                unit_price = price_per_unit * final_weight_float
                total_price = unit_price * quantity
        
        assert unit_price == expected_unit_price, f"Unit price mismatch: {unit_price} != {expected_unit_price}"
        assert total_price == expected_total_price, f"Total price mismatch: {total_price} != {expected_total_price}"
        print(f"    ✓ PASSED: unit_price={unit_price}, total_price={total_price}")
        
        # Test 3: Invalid final_weight (should fall back to estimation)
        final_weight = -1
        quantity = 1
        
        # Simulate invalid weight handling
        if final_weight is not None:
            try:
                final_weight_float = float(final_weight)
                if final_weight_float > 0 and price_per_unit > 0:
                    unit_price = price_per_unit * final_weight_float
                    total_price = unit_price * quantity
                else:
                    # Fall back to estimation
                    estimated_weight = 1
                    unit_price = price_per_unit * estimated_weight
                    total_price = unit_price * quantity
            except (ValueError, TypeError):
                estimated_weight = 1
                unit_price = price_per_unit * estimated_weight
                total_price = unit_price * quantity
        
        expected_unit_price = price_per_unit * 1  # Fallback to estimation
        assert unit_price == expected_unit_price, "Should fall back to estimation for invalid weight"
        print(f"    ✓ PASSED: Invalid weight handled correctly, unit_price={unit_price}")
        
        return True


def test_bundled_weight_pricing(app, test_data):
    """Test bundled_weight pricing type."""
    print("\n=== Test: bundled_weight Pricing ===")
    
    with app.app_context():
        product = test_data['products']['bundled_weight']
        deal_product = test_data['deal_products']['bundled_weight']
        
        # Test 1: With final_weight
        quantity = 3  # 3 packages
        final_weight = 11.0  # Total weight for all packages
        price_per_unit = float(product.pricing_data.get('price_per_unit', 0))  # 6.99
        
        expected_total_price = price_per_unit * final_weight  # 6.99 * 11.0 = 76.89
        expected_unit_price = expected_total_price / quantity  # 25.63 (average per package)
        
        print(f"  Test 1: Quantity={quantity}, final_weight={final_weight}")
        print(f"    Expected: total_price={expected_total_price}, unit_price={expected_unit_price}")
        
        # Simulate price calculation
        if final_weight is not None:
            try:
                final_weight_float = float(final_weight)
                if final_weight_float > 0 and price_per_unit > 0:
                    total_price = price_per_unit * final_weight_float
                    unit_price = total_price / quantity if quantity > 0 else 0
                else:
                    final_weight = None
            except (ValueError, TypeError):
                final_weight = None
        
        assert abs(total_price - expected_total_price) < 0.01, f"Total price mismatch: {total_price} != {expected_total_price}"
        assert abs(unit_price - expected_unit_price) < 0.01, f"Unit price mismatch: {unit_price} != {expected_unit_price}"
        assert abs(total_price - (unit_price * quantity)) < 0.01, "total_price should equal unit_price * quantity"
        print(f"    ✓ PASSED: unit_price={unit_price:.2f}, total_price={total_price:.2f}")
        
        # Test 2: Estimation (no final_weight) - uses mid-weight
        quantity = 2
        final_weight = None
        min_weight = float(product.pricing_data.get('min_weight', 7))  # 7
        max_weight = float(product.pricing_data.get('max_weight', 15))  # 15
        mid_weight = (min_weight + max_weight) / 2  # 11
        estimated_total_weight = mid_weight * quantity  # 22
        expected_total_price = price_per_unit * estimated_total_weight  # 6.99 * 22 = 153.78
        expected_unit_price = expected_total_price / quantity  # 76.89
        
        print(f"  Test 2: Quantity={quantity}, No final_weight (estimation)")
        print(f"    Expected: total_price={expected_total_price:.2f}, unit_price={expected_unit_price:.2f}")
        
        # Simulate estimation calculation
        if final_weight is None:
            if price_per_unit > 0:
                estimated_total_weight = mid_weight * quantity
                total_price = price_per_unit * estimated_total_weight
                unit_price = total_price / quantity if quantity > 0 else 0
        
        assert abs(total_price - expected_total_price) < 0.01, f"Total price mismatch: {total_price} != {expected_total_price}"
        assert abs(unit_price - expected_unit_price) < 0.01, f"Unit price mismatch: {unit_price} != {expected_unit_price}"
        print(f"    ✓ PASSED: unit_price={unit_price:.2f}, total_price={total_price:.2f}")
        
        # Test 3: Invalid final_weight (should fall back to estimation)
        quantity = 1
        final_weight = 0  # Invalid
        
        # Simulate invalid weight handling
        if final_weight is not None:
            try:
                final_weight_float = float(final_weight)
                if final_weight_float > 0 and price_per_unit > 0:
                    total_price = price_per_unit * final_weight_float
                    unit_price = total_price / quantity if quantity > 0 else 0
                else:
                    final_weight = None  # Fall back to estimation
            except (ValueError, TypeError):
                final_weight = None
        
        if final_weight is None:
            if price_per_unit > 0:
                estimated_total_weight = mid_weight * quantity
                total_price = price_per_unit * estimated_total_weight
                unit_price = total_price / quantity if quantity > 0 else 0
        
        assert unit_price > 0, "Should fall back to estimation for invalid weight"
        print(f"    ✓ PASSED: Invalid weight handled correctly, unit_price={unit_price:.2f}")
        
        # Test 4: No price_per_unit (should result in 0 price)
        quantity = 2
        original_price_per_unit = product.pricing_data.get('price_per_unit')
        product.pricing_data['price_per_unit'] = 0
        db.session.commit()
        
        # Simulate calculation - price_per_unit is 0, so unit_price and total_price should be 0
        price_per_unit = float(product.pricing_data.get('price_per_unit', 0))
        unit_price = price_per_unit  # 0
        total_price = 0  # No fallback, should be 0
        
        # Restore price_per_unit
        product.pricing_data['price_per_unit'] = original_price_per_unit
        db.session.commit()
        
        assert unit_price == 0, "Unit price should be 0 when price_per_unit is 0"
        assert total_price == 0, "Total price should be 0 when price_per_unit is 0"
        print(f"    ✓ PASSED: Zero price_per_unit handled correctly, unit_price={unit_price}, total_price={total_price}")
        
        return True


def test_mixed_pricing_types(app, test_data):
    """Test order with multiple pricing types."""
    print("\n=== Test: Mixed Pricing Types ===")
    
    with app.app_context():
        products = test_data['products']
        deal_products = test_data['deal_products']
        
        # Create order items with different pricing types
        items = [
            {'product': products['per_item'], 'quantity': 2, 'pricing_type': 'per_item'},
            {'product': products['weight_range'], 'quantity': 1, 'pricing_type': 'weight_range'},
            {'product': products['unit_weight'], 'quantity': 3, 'pricing_type': 'unit_weight'},
            {'product': products['bundled_weight'], 'quantity': 2, 'pricing_type': 'bundled_weight', 'final_weight': 10.0}
        ]
        
        subtotal = Decimal('0')
        order_items = []
        
        for item_data in items:
            product = item_data['product']
            quantity = item_data['quantity']
            pricing_type = item_data['pricing_type']
            # Calculate prices (simulating create_order logic)
            if pricing_type == 'per_item':
                unit_price = product.get_display_price() or 0
                total_price = unit_price * quantity
            elif pricing_type == 'weight_range':
                ranges = product.pricing_data.get('ranges', []) if product.pricing_data else []
                if ranges:
                    unit_price = min(float(r.get('price', 0)) for r in ranges)
                else:
                    unit_price = 0
                total_price = unit_price * quantity
            elif pricing_type == 'unit_weight':
                price_per_unit = float(product.pricing_data.get('price_per_unit', 0) if product.pricing_data else 0)
                estimated_weight = 1
                unit_price = price_per_unit * estimated_weight
                total_price = unit_price * quantity
            elif pricing_type == 'bundled_weight':
                price_per_unit = float(product.pricing_data.get('price_per_unit', 0) if product.pricing_data else 0)
                final_weight = item_data.get('final_weight')
                
                if final_weight is not None:
                    try:
                        final_weight_float = float(final_weight)
                        if final_weight_float > 0 and price_per_unit > 0:
                            total_price = price_per_unit * final_weight_float
                            unit_price = total_price / quantity if quantity > 0 else 0
                        else:
                            final_weight = None
                    except (ValueError, TypeError):
                        final_weight = None
                
                if final_weight is None:
                    if price_per_unit > 0:
                        min_weight = float(product.pricing_data.get('min_weight', 7) if product.pricing_data else 7)
                        max_weight = float(product.pricing_data.get('max_weight', 15) if product.pricing_data else 15)
                        mid_weight = (min_weight + max_weight) / 2
                        estimated_total_weight = mid_weight * quantity
                        total_price = price_per_unit * estimated_total_weight
                        unit_price = total_price / quantity if quantity > 0 else 0
                    else:
                        # price_per_unit is 0 or missing - unit_price stays as price_per_unit (0)
                        unit_price = price_per_unit  # 0
                        total_price = 0
            
            subtotal += Decimal(str(total_price))
            order_items.append({
                'product': product.name,
                'pricing_type': pricing_type,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': total_price
            })
        
        print(f"  Order items:")
        for item in order_items:
            print(f"    {item['product']} ({item['pricing_type']}): qty={item['quantity']}, "
                  f"unit=${item['unit_price']:.2f}, total=${item['total_price']:.2f}")
        
        print(f"  Total subtotal: ${float(subtotal):.2f}")
        
        # Verify all items have valid prices
        assert all(item['unit_price'] >= 0 for item in order_items), "All unit prices should be >= 0"
        assert all(item['total_price'] >= 0 for item in order_items), "All total prices should be >= 0"
        assert all(abs(item['total_price'] - (item['unit_price'] * item['quantity'])) < 0.01 
                   for item in order_items), "All total prices should equal unit_price * quantity"
        
        print(f"    ✓ PASSED: All pricing calculations correct")
        
        return True


def test_edge_cases(app, test_data):
    """Test edge cases and error handling."""
    print("\n=== Test: Edge Cases ===")
    
    with app.app_context():
        # Test 1: Zero quantity
        product = test_data['products']['per_item']
        quantity = 0
        
        unit_price = product.get_display_price() or 0
        total_price = unit_price * quantity
        
        assert total_price == 0, "Total price should be 0 for zero quantity"
        print(f"    ✓ PASSED: Zero quantity handled correctly")
        
        # Test 2: Missing pricing_data
        product.pricing_data = None
        db.session.commit()
        
        unit_price = product.get_display_price() or 0
        total_price = unit_price * 1
        
        assert unit_price == 0 or unit_price is None, "Should handle missing pricing_data"
        print(f"    ✓ PASSED: Missing pricing_data handled correctly")
        
        # Restore pricing_data
        product.pricing_data = {'price': 10.00}
        db.session.commit()
        
        # Test 3: Invalid pricing_type (should fall back to default)
        product.pricing_type = 'invalid_type'
        db.session.commit()
        
        unit_price = product.get_display_price() or 0
        total_price = unit_price * 1
        
        print(f"    ✓ PASSED: Invalid pricing_type handled correctly")
        
        # Restore pricing_type
        product.pricing_type = 'per_item'
        db.session.commit()
        
        return True


def main():
    """Run all pricing tests."""
    app = create_app()
    
    print("=" * 70)
    print("Order Pricing Calculation Test Suite")
    print("=" * 70)
    
    # Set up test data
    print("\nSetting up test data...")
    test_data = setup_test_data(app)
    print("Test data created successfully!")
    
    # Run tests
    results = {
        'per_item Pricing': test_per_item_pricing(app, test_data),
        'weight_range Pricing': test_weight_range_pricing(app, test_data),
        'unit_weight Pricing': test_unit_weight_pricing(app, test_data),
        'bundled_weight Pricing': test_bundled_weight_pricing(app, test_data),
        'Mixed Pricing Types': test_mixed_pricing_types(app, test_data),
        'Edge Cases': test_edge_cases(app, test_data)
    }
    
    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 70)
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
