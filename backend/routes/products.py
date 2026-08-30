from flask import Blueprint, jsonify, request
from models import db
from models.product import Product
from models.product_category import ProductCategory
from models.groupdeal import GroupDeal, GroupDealProduct, deal_product_to_dict
from models.product_sales_stats import ProductSalesStats
from models.user import AuthToken, User
from datetime import datetime, timezone, date, timedelta
from models.base import utc_now
from sqlalchemy import func, desc
from constants.status_enums import GroupDealStatus

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

def get_current_user_optional():
    """Get user object if authenticated, otherwise return None (optional auth for group deal endpoint)"""
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
    
    return user

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
        sort_by = request.args.get('sort', 'custom')
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
        elif sort_by == 'custom':
            query = query.order_by(Product.sort_order.asc(), Product.created_at.desc())
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
        
        # Move out of stock items to the bottom (on top of existing sort)
        # Out of stock = stock_limit is 0 (not None, which means unlimited)
        products_data.sort(key=lambda p: (p.get('stock_limit') == 0 if p.get('stock_limit') is not None else False, 0))
        
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
    """Get all group deals. Admin users can see draft deals, regular users cannot."""
    try:
        # Get current user to check if they're admin
        current_user = get_current_user_optional()
        is_admin = current_user and current_user.is_admin
        
        # Build query based on user role
        now = utc_now()
        if is_admin:
            # Admin users can see all deals including draft
            statuses = ['draft', 'active', 'upcoming', 'preparing', 'ready_for_pickup', 'closed', 'completed']
        else:
            # Regular users can see active, upcoming, closed, and completed deals (but not draft)
            statuses = ['active', 'upcoming', 'preparing', 'ready_for_pickup', 'closed', 'completed']
        
        from sqlalchemy.orm import joinedload
        
        deals = GroupDeal.query.filter(
            GroupDeal.status.in_(statuses),
            GroupDeal.deleted_at.is_(None)
        ).order_by(GroupDeal.order_start_date.desc()).all()
        
        # Batch load all products for all deals to avoid N+1 queries
        deal_ids = [deal.id for deal in deals]
        deal_products_query = GroupDealProduct.query.filter(
            GroupDealProduct.group_deal_id.in_(deal_ids)
        ).all()
        
        # Group by deal_id
        deal_products_map = {}
        for dp in deal_products_query:
            if dp.group_deal_id not in deal_products_map:
                deal_products_map[dp.group_deal_id] = []
            deal_products_map[dp.group_deal_id].append(dp)
        
        # Batch load all products
        product_ids = [dp.product_id for dp in deal_products_query]
        products_query = Product.query.filter(
            Product.id.in_(product_ids),
            Product.is_active == True
        ).all()
        products_map = {p.id: p for p in products_query}
        
        # Build response
        deals_data = []
        for deal in deals:
            deal_dict = deal.to_dict()
            deal_products = deal_products_map.get(deal.id, [])
            
            products_data = []
            for dp in deal_products:
                product = products_map.get(dp.product_id)
                if product:
                    product_dict = deal_product_to_dict(dp, product=product)
                    products_data.append(product_dict)
            
            # Sort products: out of stock last, discount first, then sort_order
            _sort_deal_products(products_data)
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

def _sort_deal_products(products_data):
    """Out of stock last, discount products first, then sort_order."""
    products_data.sort(key=lambda p: (
        p.get('deal_stock_limit') == 0 if p.get('deal_stock_limit') is not None else False,
        not bool(p.get('is_discount')),
        p.get('sort_order', 0),
        p.get('id', 0)
    ))
    return products_data


def _get_open_deal_statuses(is_admin: bool) -> list:
    """Statuses for storefront 'not ended' group deals (excludes completed)."""
    statuses = [
        GroupDealStatus.UPCOMING.value,
        GroupDealStatus.ACTIVE.value,
        GroupDealStatus.CLOSED.value,
        GroupDealStatus.PREPARING.value,
        GroupDealStatus.READY_FOR_PICKUP.value,
    ]
    if is_admin:
        statuses.append(GroupDealStatus.DRAFT.value)
    return statuses


def _query_open_group_deals(is_admin: bool):
    """Query all non-completed group deals visible to the current user."""
    return GroupDeal.query.filter(
        GroupDeal.status.in_(_get_open_deal_statuses(is_admin)),
        GroupDeal.deleted_at.is_(None)
    ).order_by(GroupDeal.order_start_date.desc())


def _serialize_group_deal_with_products(deal):
    """Build deal dict with nested products (same shape as list/detail endpoints)."""
    deal_dict = deal.to_dict()
    deal_products = GroupDealProduct.query.filter_by(group_deal_id=deal.id).all()
    products_data = []
    for dp in deal_products:
        product = Product.query.get(dp.product_id)
        if product:
            products_data.append(deal_product_to_dict(dp, product=product))
    _sort_deal_products(products_data)
    deal_dict['products'] = products_data
    return deal_dict


@products_bp.route('/group-deals/open', methods=['GET'])
def get_open_group_deals():
    """
    All storefront group deals that have not ended (excludes completed).
    Non-admins never see draft. Returns lightweight deal metadata without products.
    """
    try:
        current_user = get_current_user_optional()
        is_admin = bool(current_user and getattr(current_user, 'is_admin', False))
        deals = _query_open_group_deals(is_admin).all()
        return jsonify({
            'deals': [deal.to_dict() for deal in deals]
        }), 200
    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch open group deals',
            'message': str(e)
        }), 500


@products_bp.route('/group-deals/latest', methods=['GET'])
def get_latest_group_deal():
    """
    Latest storefront group deal (backward compatible).
    Uses the same open-deal filter as /group-deals/open but returns only the newest one.
    """
    try:
        current_user = get_current_user_optional()
        is_admin = bool(current_user and getattr(current_user, 'is_admin', False))
        deal = _query_open_group_deals(is_admin).first()
        if not deal:
            return jsonify({'deal': None}), 200
        return jsonify({'deal': _serialize_group_deal_with_products(deal)}), 200
    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch latest group deal',
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

        current_user = get_current_user_optional()
        is_admin = bool(current_user and getattr(current_user, 'is_admin', False))
        if deal.status == GroupDealStatus.DRAFT.value and not is_admin:
            return jsonify({
                'error': 'Group deal not found',
                'message': 'Deal not found'
            }), 404

        deal_dict = _serialize_group_deal_with_products(deal)
        return jsonify({'deal': deal_dict}), 200
    except Exception as e:
        return jsonify({
            'error': 'Group deal not found',
            'message': str(e)
        }), 404

@products_bp.route('/product-categories', methods=['GET'])
def get_product_categories():
    """Get all active product categories (public endpoint)"""
    try:
        # Only show active categories
        categories = ProductCategory.query.filter_by(
            is_active=True
        ).order_by(
            ProductCategory.sort_order.asc(),
            ProductCategory.created_at.asc()
        ).all()
        
        return jsonify({
            'categories': [category.to_dict() for category in categories]
        }), 200
    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch product categories',
            'message': str(e)
        }), 500

