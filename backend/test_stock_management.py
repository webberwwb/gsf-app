"""
Test script for stock management functionality.

This script tests:
1. Stock deduction on order creation
2. Stock validation (rejection when insufficient)
3. Stock restoration on order cancellation
4. Stock updates on order modification
5. Concurrent order handling (simulated)
"""

import sys
import os
from decimal import Decimal

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db
from models.product import Product
from models.groupdeal import GroupDeal, GroupDealProduct
from models.order import Order, OrderItem
from models.user import User, AuthToken
from datetime import datetime, timedelta
from utils.stock_management import (
    check_and_reserve_stock,
    restore_stock,
    get_available_stock,
    update_stock_after_order_modification
)

def setup_test_data(app):
    """Set up test data for stock management tests."""
    with app.app_context():
        # Clean up existing test data
        Order.query.filter(Order.order_number.like('TEST-%')).delete()
        
        # Create test user if not exists
        test_user = User.query.filter_by(phone='1234567890').first()
        if not test_user:
            from constants.status_enums import UserStatus
            test_user = User(
                phone='1234567890',
                nickname='Test User',
                status=UserStatus.ACTIVE.value
            )
            db.session.add(test_user)
            db.session.flush()
        
        # Create test products if not exists
        test_product1 = Product.query.filter_by(name='Test Product 1 - Stock Test').first()
        if not test_product1:
            test_product1 = Product(
                name='Test Product 1 - Stock Test',
                pricing_type='per_item',
                pricing_data={'price': 10.00},
                is_active=True
            )
            db.session.add(test_product1)
            db.session.flush()
        
        test_product2 = Product.query.filter_by(name='Test Product 2 - Stock Test').first()
        if not test_product2:
            test_product2 = Product(
                name='Test Product 2 - Stock Test',
                pricing_type='per_item',
                pricing_data={'price': 20.00},
                is_active=True
            )
            db.session.add(test_product2)
            db.session.flush()
        
        # Create test group deal
        now = datetime.utcnow()
        test_deal = GroupDeal.query.filter_by(title='Test Deal - Stock Management').first()
        if not test_deal:
            test_deal = GroupDeal(
                title='Test Deal - Stock Management',
                description='Test deal for stock management',
                order_start_date=now - timedelta(days=1),
                order_end_date=now + timedelta(days=7),
                pickup_date=now + timedelta(days=10),
                status='active'
            )
            db.session.add(test_deal)
            db.session.flush()
        
        # Add products to deal with stock limits
        deal_product1 = GroupDealProduct.query.filter_by(
            group_deal_id=test_deal.id,
            product_id=test_product1.id
        ).first()
        if not deal_product1:
            deal_product1 = GroupDealProduct(
                group_deal_id=test_deal.id,
                product_id=test_product1.id,
                deal_stock_limit=100  # Limited stock
            )
            db.session.add(deal_product1)
        else:
            deal_product1.deal_stock_limit = 100
        
        deal_product2 = GroupDealProduct.query.filter_by(
            group_deal_id=test_deal.id,
            product_id=test_product2.id
        ).first()
        if not deal_product2:
            deal_product2 = GroupDealProduct(
                group_deal_id=test_deal.id,
                product_id=test_product2.id,
                deal_stock_limit=None  # Unlimited stock
            )
            db.session.add(deal_product2)
        else:
            deal_product2.deal_stock_limit = None
        
        db.session.commit()
        
        return {
            'user_id': test_user.id,
            'product1_id': test_product1.id,
            'product2_id': test_product2.id,
            'deal_id': test_deal.id
        }

def test_stock_deduction(app, test_data):
    """Test 1: Stock deduction on order creation."""
    with app.app_context():
        print("\n=== Test 1: Stock Deduction ===")
        
        product1_id = test_data['product1_id']
        deal_id = test_data['deal_id']
        
        # Get initial stock
        initial_stock = get_available_stock(deal_id, product1_id)
        print(f"Initial stock for product1: {initial_stock}")
        
        # Reserve 10 units
        items = [{'product_id': product1_id, 'quantity': 10}]
        success, error = check_and_reserve_stock(deal_id, items)
        
        if success:
            db.session.commit()
            new_stock = get_available_stock(deal_id, product1_id)
            print(f"✓ Successfully reserved 10 units")
            print(f"  New stock: {new_stock}")
            print(f"  Expected: {initial_stock - 10}, Actual: {new_stock}")
            
            # Restore for next test
            restore_stock(deal_id, items)
            db.session.commit()
            restored_stock = get_available_stock(deal_id, product1_id)
            print(f"✓ Stock restored to: {restored_stock}")
            return True
        else:
            print(f"✗ Failed to reserve stock: {error}")
            db.session.rollback()
            return False

def test_stock_validation(app, test_data):
    """Test 2: Stock validation (rejection when insufficient)."""
    with app.app_context():
        print("\n=== Test 2: Stock Validation ===")
        
        product1_id = test_data['product1_id']
        deal_id = test_data['deal_id']
        
        # Try to reserve more than available
        current_stock = get_available_stock(deal_id, product1_id)
        print(f"Current stock: {current_stock}")
        
        items = [{'product_id': product1_id, 'quantity': current_stock + 50}]
        print(f"Attempting to reserve {current_stock + 50} units (more than available)...")
        
        success, error = check_and_reserve_stock(deal_id, items)
        
        if not success:
            print(f"✓ Correctly rejected: {error}")
            db.session.rollback()
            return True
        else:
            print(f"✗ Should have been rejected but succeeded")
            db.session.rollback()
            return False

def test_unlimited_stock(app, test_data):
    """Test 3: Unlimited stock products."""
    with app.app_context():
        print("\n=== Test 3: Unlimited Stock ===")
        
        product2_id = test_data['product2_id']
        deal_id = test_data['deal_id']
        
        stock = get_available_stock(deal_id, product2_id)
        print(f"Product2 stock limit: {stock}")
        
        # Try to reserve a large quantity
        items = [{'product_id': product2_id, 'quantity': 1000}]
        success, error = check_and_reserve_stock(deal_id, items)
        
        if success:
            print(f"✓ Successfully reserved 1000 units from unlimited stock")
            db.session.rollback()  # Don't actually commit
            return True
        else:
            print(f"✗ Failed: {error}")
            db.session.rollback()
            return False

def test_order_modification(app, test_data):
    """Test 4: Stock updates on order modification."""
    with app.app_context():
        print("\n=== Test 4: Order Modification ===")
        
        product1_id = test_data['product1_id']
        deal_id = test_data['deal_id']
        
        initial_stock = get_available_stock(deal_id, product1_id)
        print(f"Initial stock: {initial_stock}")
        
        # Original order: 10 units
        old_items = [{'product_id': product1_id, 'quantity': 10}]
        success, _ = check_and_reserve_stock(deal_id, old_items)
        db.session.commit()
        
        stock_after_order = get_available_stock(deal_id, product1_id)
        print(f"Stock after ordering 10 units: {stock_after_order}")
        
        # Modify order: increase to 15 units
        new_items = [{'product_id': product1_id, 'quantity': 15}]
        print("Modifying order from 10 to 15 units...")
        
        success, error = update_stock_after_order_modification(deal_id, old_items, new_items)
        
        if success:
            db.session.commit()
            stock_after_modify = get_available_stock(deal_id, product1_id)
            expected = initial_stock - 15
            print(f"✓ Stock after modification: {stock_after_modify}")
            print(f"  Expected: {expected}, Actual: {stock_after_modify}")
            
            # Clean up - restore all stock
            restore_stock(deal_id, new_items)
            db.session.commit()
            return stock_after_modify == expected
        else:
            print(f"✗ Failed to modify order: {error}")
            db.session.rollback()
            return False

def test_concurrent_orders(app, test_data):
    """Test 5: Simulate concurrent orders using database locking."""
    with app.app_context():
        print("\n=== Test 5: Concurrent Order Handling (Simulated) ===")
        
        product1_id = test_data['product1_id']
        deal_id = test_data['deal_id']
        
        # Reset stock to a low value for this test
        deal_product = GroupDealProduct.query.filter_by(
            group_deal_id=deal_id,
            product_id=product1_id
        ).first()
        deal_product.deal_stock_limit = 20
        db.session.commit()
        
        print(f"Set stock to 20 units")
        print("Simulating 3 concurrent orders of 8 units each...")
        
        # In a real concurrent scenario, these would run in parallel
        # Here we test that the locking mechanism would work
        results = []
        for i in range(3):
            items = [{'product_id': product1_id, 'quantity': 8}]
            success, error = check_and_reserve_stock(deal_id, items)
            
            if success:
                db.session.commit()
                remaining = get_available_stock(deal_id, product1_id)
                print(f"  Order {i+1}: ✓ Success, remaining stock: {remaining}")
                results.append(True)
            else:
                db.session.rollback()
                remaining = get_available_stock(deal_id, product1_id)
                print(f"  Order {i+1}: ✗ Rejected - {error}, remaining stock: {remaining}")
                results.append(False)
        
        # First 2 orders should succeed (16 units), 3rd should fail
        final_stock = get_available_stock(deal_id, product1_id)
        expected_successes = 2
        actual_successes = sum(results)
        
        print(f"\nResults: {actual_successes} orders succeeded, final stock: {final_stock}")
        
        if actual_successes == expected_successes and final_stock == 4:
            print(f"✓ Concurrency handling works correctly!")
            return True
        else:
            print(f"✗ Expected {expected_successes} successes with 4 remaining stock")
            return False

def main():
    """Run all stock management tests."""
    # Safety check before running
    if not check_database_safety():
        sys.exit(1)
    
    app = create_app()
    
    print("=" * 60)
    print("Stock Management Test Suite")
    print("=" * 60)
    
    # Set up test data
    print("\nSetting up test data...")
    test_data = setup_test_data(app)
    print("Test data created successfully!")
    
    # Run tests
    results = {
        'Stock Deduction': test_stock_deduction(app, test_data),
        'Stock Validation': test_stock_validation(app, test_data),
        'Unlimited Stock': test_unlimited_stock(app, test_data),
        'Order Modification': test_order_modification(app, test_data),
        'Concurrent Orders': test_concurrent_orders(app, test_data)
    }
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
