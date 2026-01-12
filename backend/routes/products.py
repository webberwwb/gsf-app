from flask import Blueprint, jsonify, request
from models import db
from models.product import Product
from models.groupdeal import GroupDeal, GroupDealProduct
from models.product_sales_stats import ProductSalesStats
from models.user import AuthToken, User
from datetime import datetime, timezone, date, timedelta
from models.base import utc_now
from sqlalchemy import func, desc

def get_user_id_optional():
    """Get user_id if authenticated, otherwise return None (optional auth for group deal endpoint)"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.replace('Bearer ', '').strip()
    else:
        token = auth_header.strip()
    
    if not token:
        return None  # Not authenticated, but that's OK for this endpoint
    
    auth_token = AuthToken.query.filter_by(token=token, is_revoked=False).first()
    if not auth_token or not auth_token.is_valid():
        return None  # Invalid/expired token, but that's OK for this endpoint
    
    # Get user
    user = User.query.get(auth_token.user_id)
    if not user or not user.is_active:
        return None  # User not found or inactive
    
    return user.id

products_bp = Blueprint('products', __name__)

@products_bp.route('/products', methods=['GET'])
def get_products():
    """Get all products (admin can see all, public sees only active)
    
    Query params:
    - sort: 'popularity' (sort by sales), 'name', 'created_at' (default)
    - days: number of days for popularity calculation (default: 30)
    """
    try:
        # Check if admin request (has auth header)
        show_all = request.headers.get('Authorization') is not None
        
        # Get query parameters
        sort_by = request.args.get('sort', 'created_at')
        days = request.args.get('days', 30, type=int)
        
        # Build base query
        if show_all:
            # Admin: show all products
            query = Product.query
        else:
            # Public: show only active products
            query = Product.query.filter_by(is_active=True)
        
        # Apply sorting
        if sort_by == 'popularity':
            # Sort by sales in last N days
            start_date = date.today() - timedelta(days=days)
            stats_subquery = db.session.query(
                ProductSalesStats.product_id,
                func.sum(ProductSalesStats.quantity_sold).label('total_sold')
            ).filter(
                ProductSalesStats.sale_date >= start_date
            ).group_by(
                ProductSalesStats.product_id
            ).subquery()
            
            query = query.outerjoin(
                stats_subquery, Product.id == stats_subquery.c.product_id
            ).order_by(
                desc(stats_subquery.c.total_sold),
                Product.created_at.desc()
            )
        elif sort_by == 'name':
            query = query.order_by(Product.name.asc())
        else:
            query = query.order_by(Product.created_at.desc())
        
        products = query.all()
        
        # For public API, optionally include sales stats if requested
        include_stats = request.args.get('include_stats', 'false').lower() == 'true'
        products_data = []
        
        if include_stats:
            start_date = date.today() - timedelta(days=days)
            for product in products:
                product_dict = product.to_dict()
                
                # Get sales stats
                stats_query = db.session.query(
                    func.sum(ProductSalesStats.quantity_sold).label('total_sold'),
                    func.sum(ProductSalesStats.order_count).label('total_orders')
                ).filter(
                    ProductSalesStats.product_id == product.id,
                    ProductSalesStats.sale_date >= start_date
                ).first()
                
                product_dict['sales_stats'] = {
                    'total_sold': int(stats_query.total_sold) if stats_query.total_sold else 0,
                    'total_orders': int(stats_query.total_orders) if stats_query.total_orders else 0
                }
                
                products_data.append(product_dict)
        else:
            products_data = [product.to_dict() for product in products]
        
        return jsonify({
            'products': products_data
        }), 200
    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch products',
            'message': str(e)
        }), 500

@products_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a single product by ID"""
    try:
        product = Product.query.get_or_404(product_id)
        return jsonify({
            'product': product.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            'error': 'Product not found',
            'message': str(e)
        }), 404

@products_bp.route('/group-deals', methods=['GET'])
def get_group_deals():
    """Get all active, upcoming, and ready-for-pickup group deals"""
    try:
        # Get active, upcoming, preparing, and ready_for_pickup deals (excluding soft-deleted)
        # These statuses should be visible to users so they can see their orders
        now = utc_now()
        deals = GroupDeal.query.filter(
            GroupDeal.status.in_(['active', 'upcoming', 'preparing', 'ready_for_pickup']),
            GroupDeal.deleted_at.is_(None)
        ).order_by(GroupDeal.order_start_date.desc()).all()
        
        # Include products for each deal
        deals_data = []
        for deal in deals:
            deal_dict = deal.to_dict()
            # Get products for this deal
            deal_products = GroupDealProduct.query.filter_by(group_deal_id=deal.id).all()
            products_data = []
            for dp in deal_products:
                product = Product.query.get(dp.product_id)
                if product and product.is_active:
                    product_dict = product.to_dict()
                    # Add deal-specific price if set
                    if dp.deal_price:
                        product_dict['deal_price'] = float(dp.deal_price)
                    product_dict['deal_stock_limit'] = dp.deal_stock_limit
                    products_data.append(product_dict)
            deal_dict['products'] = products_data
            deals_data.append(deal_dict)
        
        return jsonify({
            'deals': deals_data
        }), 200
    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch group deals',
            'message': str(e)
        }), 500

@products_bp.route('/group-deals/<int:deal_id>', methods=['GET'])
def get_group_deal(deal_id):
    """Get a single group deal by ID with products. Orders are accessed via /orders endpoint."""
    try:
        deal = GroupDeal.query.filter(
            GroupDeal.id == deal_id,
            GroupDeal.deleted_at.is_(None)
        ).first_or_404()
        deal_dict = deal.to_dict()
        
        # Get products for this deal
        deal_products = GroupDealProduct.query.filter_by(group_deal_id=deal.id).all()
        products_data = []
        for dp in deal_products:
            product = Product.query.get(dp.product_id)
            if product:
                product_dict = product.to_dict()
                # Add deal-specific price if set
                if dp.deal_price:
                    product_dict['deal_price'] = float(dp.deal_price)
                product_dict['deal_stock_limit'] = dp.deal_stock_limit
                products_data.append(product_dict)
        
        deal_dict['products'] = products_data
        
        # Don't return order data - allow users to place multiple orders per group deal
        # Orders should be accessed via the /orders endpoint
        
        response_data = {
            'deal': deal_dict
        }
        
        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({
            'error': 'Group deal not found',
            'message': str(e)
        }), 404

