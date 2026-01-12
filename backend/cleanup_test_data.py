"""
Cleanup script to remove test data created by test_stock_management.py

⚠️ WARNING: This will delete data from the database!
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db
from models.product import Product
from models.groupdeal import GroupDeal, GroupDealProduct
from models.order import Order, OrderItem
from models.user import User

def cleanup_test_data():
    """Remove all test data created by the test script."""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("CLEANUP TEST DATA FROM PRODUCTION DATABASE")
        print("=" * 60)
        print()
        
        # Confirm deletion
        print("⚠️  WARNING: This will delete test data from the PRODUCTION database!")
        print()
        print("Test data to be deleted:")
        print("  - Test User: phone='1234567890'")
        print("  - Test Products: 'Test Product 1 - Stock Test', 'Test Product 2 - Stock Test'")
        print("  - Test Group Deal: 'Test Deal - Stock Management'")
        print("  - Related orders, group_deal_products, etc.")
        print()
        
        confirm = input("Type 'DELETE' to confirm deletion: ")
        
        if confirm != 'DELETE':
            print("\n❌ Cleanup cancelled. No data was deleted.")
            return
        
        print("\n🔍 Finding test data...")
        
        # Find test entities
        test_user = User.query.filter_by(phone='1234567890').first()
        test_product1 = Product.query.filter_by(name='Test Product 1 - Stock Test').first()
        test_product2 = Product.query.filter_by(name='Test Product 2 - Stock Test').first()
        test_deal = GroupDeal.query.filter_by(title='Test Deal - Stock Management').first()
        
        deleted_counts = {
            'users': 0,
            'products': 0,
            'group_deals': 0,
            'group_deal_products': 0,
            'orders': 0,
            'order_items': 0
        }
        
        # Delete in correct order to avoid foreign key constraints
        
        # 1. Delete test orders (by user or order number pattern)
        if test_user:
            print(f"\n📋 Deleting orders for test user (ID: {test_user.id})...")
            orders = Order.query.filter_by(user_id=test_user.id).all()
            for order in orders:
                # Delete order items first
                order_items = OrderItem.query.filter_by(order_id=order.id).all()
                for item in order_items:
                    db.session.delete(item)
                    deleted_counts['order_items'] += 1
                
                db.session.delete(order)
                deleted_counts['orders'] += 1
            
            print(f"   ✓ Deleted {deleted_counts['orders']} orders")
            print(f"   ✓ Deleted {deleted_counts['order_items']} order items")
        
        # Also delete orders with TEST- pattern
        print("\n📋 Deleting TEST- orders...")
        test_orders = Order.query.filter(Order.order_number.like('TEST-%')).all()
        for order in test_orders:
            order_items = OrderItem.query.filter_by(order_id=order.id).all()
            for item in order_items:
                db.session.delete(item)
                deleted_counts['order_items'] += 1
            
            db.session.delete(order)
            deleted_counts['orders'] += 1
        
        # 2. Delete group deal products
        if test_deal:
            print(f"\n🔗 Deleting group_deal_products for test deal (ID: {test_deal.id})...")
            deal_products = GroupDealProduct.query.filter_by(group_deal_id=test_deal.id).all()
            for dp in deal_products:
                db.session.delete(dp)
                deleted_counts['group_deal_products'] += 1
            
            print(f"   ✓ Deleted {deleted_counts['group_deal_products']} group_deal_products")
        
        # 3. Delete test group deal
        if test_deal:
            print(f"\n📦 Deleting test group deal (ID: {test_deal.id})...")
            db.session.delete(test_deal)
            deleted_counts['group_deals'] += 1
            print(f"   ✓ Deleted test group deal")
        
        # 4. Delete test products
        if test_product1:
            print(f"\n🏷️  Deleting test product 1 (ID: {test_product1.id})...")
            db.session.delete(test_product1)
            deleted_counts['products'] += 1
            print(f"   ✓ Deleted test product 1")
        
        if test_product2:
            print(f"\n🏷️  Deleting test product 2 (ID: {test_product2.id})...")
            db.session.delete(test_product2)
            deleted_counts['products'] += 1
            print(f"   ✓ Deleted test product 2")
        
        # 5. Delete test user
        if test_user:
            print(f"\n👤 Deleting test user (ID: {test_user.id})...")
            db.session.delete(test_user)
            deleted_counts['users'] += 1
            print(f"   ✓ Deleted test user")
        
        # Commit all deletions
        print("\n💾 Committing changes to database...")
        db.session.commit()
        
        # Print summary
        print("\n" + "=" * 60)
        print("CLEANUP SUMMARY")
        print("=" * 60)
        print(f"Users deleted:              {deleted_counts['users']}")
        print(f"Products deleted:           {deleted_counts['products']}")
        print(f"Group deals deleted:        {deleted_counts['group_deals']}")
        print(f"Group deal products deleted: {deleted_counts['group_deal_products']}")
        print(f"Orders deleted:             {deleted_counts['orders']}")
        print(f"Order items deleted:        {deleted_counts['order_items']}")
        print("=" * 60)
        print()
        
        if sum(deleted_counts.values()) > 0:
            print("✅ Cleanup completed successfully!")
        else:
            print("ℹ️  No test data found to delete.")
        
        print()

if __name__ == '__main__':
    try:
        cleanup_test_data()
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
