"""Utility functions for updating product sales statistics"""
from models import db
from models.product_sales_stats import ProductSalesStats
from models.order import Order, OrderItem
from datetime import datetime, timezone, date

def update_product_sales_stats(order):
    """Update product sales statistics when an order is created/confirmed
    
    Args:
        order: Order instance with items relationship loaded
    """
    if not order or not order.items:
        return
    
    # Use order creation date for sale_date
    sale_date = order.created_at.date() if order.created_at else date.today()
    
    # Track products in this order to avoid double-counting order_count
    products_in_order = set()
    
    for item in order.items:
        product_id = item.product_id
        quantity = item.quantity
        
        # Get or create stats record for this product and date
        stats = ProductSalesStats.query.filter_by(
            product_id=product_id,
            sale_date=sale_date
        ).first()
        
        if not stats:
            stats = ProductSalesStats(
                product_id=product_id,
                sale_date=sale_date,
                quantity_sold=0,
                order_count=0
            )
            db.session.add(stats)
        
        # Update quantity sold
        stats.quantity_sold += quantity
        
        # Update order count (only once per product per order)
        if product_id not in products_in_order:
            stats.order_count += 1
            products_in_order.add(product_id)
    
    # Commit changes
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

def get_product_sales_by_date_range(product_id, start_date, end_date):
    """Get aggregated sales for a product within date range
    
    Args:
        product_id: Product ID
        start_date: Start date (date object)
        end_date: End date (date object)
    
    Returns:
        dict with total_quantity_sold, total_order_count, and daily_breakdown
    """
    from sqlalchemy import and_
    
    stats = ProductSalesStats.query.filter(
        and_(
            ProductSalesStats.product_id == product_id,
            ProductSalesStats.sale_date >= start_date,
            ProductSalesStats.sale_date <= end_date
        )
    ).order_by(ProductSalesStats.sale_date.desc()).all()
    
    total_quantity = sum(s.quantity_sold for s in stats)
    total_orders = sum(s.order_count for s in stats)
    
    return {
        'total_quantity_sold': total_quantity,
        'total_order_count': total_orders,
        'daily_breakdown': [s.to_dict() for s in stats]
    }

def get_popular_products(days=30, limit=10):
    """Get top selling products in the last N days
    
    Args:
        days: Number of days to look back (default: 30)
        limit: Maximum number of products to return (default: 10)
    
    Returns:
        List of tuples: (product_id, total_sold)
    """
    from sqlalchemy import func, desc
    from datetime import timedelta
    from models.product import Product
    
    start_date = date.today() - timedelta(days=days)
    
    # Aggregate sales stats
    popular = db.session.query(
        ProductSalesStats.product_id,
        func.sum(ProductSalesStats.quantity_sold).label('total_sold')
    ).filter(
        ProductSalesStats.sale_date >= start_date
    ).group_by(
        ProductSalesStats.product_id
    ).order_by(
        desc('total_sold')
    ).limit(limit).all()
    
    return [(product_id, int(total_sold)) for product_id, total_sold in popular]






