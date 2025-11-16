from flask import Blueprint, jsonify, request
from models import db
from models.product import Product
from models.groupdeal import GroupDeal, GroupDealProduct
from datetime import datetime

products_bp = Blueprint('products', __name__)

@products_bp.route('/products', methods=['GET'])
def get_products():
    """Get all products (admin can see all, public sees only active)"""
    try:
        # Check if admin request (has auth header)
        show_all = request.headers.get('Authorization') is not None
        
        if show_all:
            # Admin: show all products
            products = Product.query.order_by(Product.created_at.desc()).all()
        else:
            # Public: show only active products
            products = Product.query.filter_by(is_active=True).all()
        
        return jsonify({
            'products': [product.to_dict() for product in products]
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
    """Get all active and upcoming group deals"""
    try:
        # Get active and upcoming deals
        now = datetime.utcnow()
        deals = GroupDeal.query.filter(
            GroupDeal.status.in_(['active', 'upcoming'])
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
                    # Use deal price if available, otherwise use product sale price
                    if dp.deal_price:
                        product_dict['deal_price'] = float(dp.deal_price)
                    else:
                        product_dict['deal_price'] = product_dict['sale_price']
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
    """Get a single group deal by ID with products"""
    try:
        deal = GroupDeal.query.get_or_404(deal_id)
        deal_dict = deal.to_dict()
        
        # Get products for this deal
        deal_products = GroupDealProduct.query.filter_by(group_deal_id=deal.id).all()
        products_data = []
        for dp in deal_products:
            product = Product.query.get(dp.product_id)
            if product:
                product_dict = product.to_dict()
                if dp.deal_price:
                    product_dict['deal_price'] = float(dp.deal_price)
                else:
                    product_dict['deal_price'] = product_dict['sale_price']
                product_dict['deal_stock_limit'] = dp.deal_stock_limit
                products_data.append(product_dict)
        
        deal_dict['products'] = products_data
        return jsonify({
            'deal': deal_dict
        }), 200
    except Exception as e:
        return jsonify({
            'error': 'Group deal not found',
            'message': str(e)
        }), 404

