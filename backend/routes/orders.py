from flask import Blueprint, jsonify, request, current_app
from models import db
from models.order import Order, OrderItem
from models.groupdeal import GroupDeal
from models.product import Product
from models.user import User, AuthToken
from datetime import datetime, timezone
from models.base import utc_now
import random
import string

orders_bp = Blueprint('orders', __name__)

def require_auth():
    """Check if user is authenticated and return user_id"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.replace('Bearer ', '').strip()
    else:
        token = auth_header.strip()
    
    if not token:
        return None, jsonify({'error': 'No token provided'}), 401
    
    auth_token = AuthToken.query.filter_by(token=token, is_revoked=False).first()
    if not auth_token or not auth_token.is_valid():
        return None, jsonify({'error': 'Invalid or expired token'}), 401
    
    # Get user
    user = User.query.get(auth_token.user_id)
    if not user or not user.is_active:
        return None, jsonify({'error': 'User not found or inactive'}), 401
    
    return user.id, None, None

@orders_bp.route('/orders', methods=['GET'])
def get_user_orders():
    """Get all orders for the current authenticated user"""
    user_id, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        # Get query parameters
        status_filter = request.args.get('status', '').strip()  # 'pending', 'confirmed', 'completed', 'cancelled'
        payment_status_filter = request.args.get('payment_status', '').strip()  # 'pending', 'paid', 'failed', 'refunded'
        
        # Build query
        query = Order.query.filter_by(user_id=user_id)
        
        # Apply filters
        if status_filter:
            query = query.filter(Order.status == status_filter)
        
        if payment_status_filter:
            query = query.filter(Order.payment_status == payment_status_filter)
        
        # Order by creation date (newest first)
        query = query.order_by(Order.created_at.desc())
        
        orders = query.all()
        
        # Build response with order details
        orders_data = []
        for order in orders:
            order_dict = order.to_dict()
            
            # Get group deal info
            group_deal = GroupDeal.query.get(order.group_deal_id)
            if group_deal:
                order_dict['group_deal'] = {
                    'id': group_deal.id,
                    'title': group_deal.title,
                    'description': group_deal.description,
                    'pickup_date': group_deal.pickup_date.isoformat() if group_deal.pickup_date else None,
                    'order_start_date': group_deal.order_start_date.isoformat() if group_deal.order_start_date else None,
                    'order_end_date': group_deal.order_end_date.isoformat() if group_deal.order_end_date else None
                }
            
            # Get order items with product details
            items_data = []
            for item in order.items:
                item_dict = item.to_dict()
                product = Product.query.get(item.product_id)
                if product:
                    item_dict['product'] = {
                        'id': product.id,
                        'name': product.name,
                        'image': product.image,
                        'pricing_type': product.pricing_type
                    }
                items_data.append(item_dict)
            
            order_dict['items'] = items_data
            
            orders_data.append(order_dict)
        
        return jsonify({
            'orders': orders_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error fetching user orders: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to fetch orders',
            'message': str(e)
        }), 500

@orders_bp.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get a single order by ID (must belong to current user)"""
    user_id, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        order = Order.query.filter_by(id=order_id, user_id=user_id).first()
        
        if not order:
            return jsonify({
                'error': 'Order not found'
            }), 404
        
        order_dict = order.to_dict()
        
        # Get group deal info
        group_deal = GroupDeal.query.get(order.group_deal_id)
        if group_deal:
            order_dict['group_deal'] = {
                'id': group_deal.id,
                'title': group_deal.title,
                'description': group_deal.description,
                'pickup_date': group_deal.pickup_date.isoformat() if group_deal.pickup_date else None,
                'order_start_date': group_deal.order_start_date.isoformat() if group_deal.order_start_date else None,
                'order_end_date': group_deal.order_end_date.isoformat() if group_deal.order_end_date else None
            }
        
        # Get order items with product details
        items_data = []
        for item in order.items:
            item_dict = item.to_dict()
            product = Product.query.get(item.product_id)
            if product:
                item_dict['product'] = {
                    'id': product.id,
                    'name': product.name,
                    'image': product.image,
                    'pricing_type': product.pricing_type,
                    'description': product.description
                }
            items_data.append(item_dict)
        
        order_dict['items'] = items_data
        
        return jsonify({
            'order': order_dict
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error fetching order: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to fetch order',
            'message': str(e)
        }), 500

def generate_order_number():
    """Generate a unique order number"""
    timestamp = utc_now().strftime('%Y%m%d%H%M%S')
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f'GSF-{timestamp}-{random_suffix}'

@orders_bp.route('/orders', methods=['POST'])
def create_order():
    """Create a new order"""
    user_id, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        group_deal_id = data.get('group_deal_id')
        items = data.get('items', [])
        delivery_method = data.get('delivery_method', 'pickup')  # 'pickup' or 'delivery'
        address_id = data.get('address_id') if delivery_method == 'delivery' else None
        
        if not group_deal_id:
            return jsonify({'error': 'group_deal_id is required'}), 400
        
        if not items or len(items) == 0:
            return jsonify({'error': 'At least one item is required'}), 400
        
        # Validate group deal exists and is active
        group_deal = GroupDeal.query.get(group_deal_id)
        if not group_deal:
            return jsonify({'error': 'Group deal not found'}), 404
        
        # Check if group deal is still accepting orders
        now = utc_now()
        if group_deal.order_end_date and group_deal.order_end_date < now:
            return jsonify({'error': 'This group deal is no longer accepting orders'}), 400
        
        # Validate delivery address if delivery method is selected
        if delivery_method == 'delivery':
            if not address_id:
                return jsonify({'error': 'address_id is required for delivery'}), 400
            # Verify address belongs to user (would need Address model import)
            from models.address import Address
            address = Address.query.filter_by(id=address_id, user_id=user_id).first()
            if not address:
                return jsonify({'error': 'Address not found or does not belong to user'}), 404
        
        # Calculate order totals
        subtotal = 0
        order_items = []
        
        for item_data in items:
            product_id = item_data.get('product_id')
            quantity = item_data.get('quantity', 1)
            pricing_type = item_data.get('pricing_type', 'per_item')
            
            if not product_id:
                return jsonify({'error': 'product_id is required for each item'}), 400
            
            if quantity <= 0:
                return jsonify({'error': 'quantity must be greater than 0'}), 400
            
            # Get product
            product = Product.query.get(product_id)
            if not product:
                return jsonify({'error': f'Product {product_id} not found'}), 404
            
            # Calculate item price based on pricing type
            if pricing_type == 'per_item':
                unit_price = float(product.deal_price or product.display_price or product.sale_price or 0)
            elif pricing_type == 'weight_range':
                # Use medium weight price for estimation
                ranges = product.pricing_data.get('ranges', []) if product.pricing_data else []
                if ranges:
                    sorted_ranges = sorted(ranges, key=lambda x: x.get('min', 0))
                    middle_index = len(sorted_ranges) // 2
                    unit_price = float(sorted_ranges[middle_index].get('price', 0))
                else:
                    unit_price = 0
            elif pricing_type == 'unit_weight':
                # Use price per unit with estimated weight
                price_per_unit = float(product.pricing_data.get('price_per_unit', 0) if product.pricing_data else 0)
                estimated_weight = 1  # Default 1 unit for estimation
                unit_price = price_per_unit * estimated_weight
            else:
                unit_price = float(product.deal_price or product.display_price or product.sale_price or 0)
            
            total_price = unit_price * quantity
            subtotal += total_price
            
            order_items.append({
                'product_id': product_id,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': total_price
            })
        
        # Calculate tax (0% for now, can be configured later)
        tax = 0
        total = subtotal + tax
        
        # Calculate points (1 point per dollar)
        points_earned = int(total)
        
        # Generate unique order number
        order_number = generate_order_number()
        
        # Create order
        order = Order(
            user_id=user_id,
            group_deal_id=group_deal_id,
            address_id=address_id,
            order_number=order_number,
            subtotal=subtotal,
            tax=tax,
            total=total,
            points_earned=points_earned,
            payment_status='pending',
            pickup_status='pending',
            status='pending'
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items
        for item_data in order_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data['product_id'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                total_price=item_data['total_price']
            )
            db.session.add(order_item)
        
        # Commit transaction
        db.session.commit()
        
        # Update product sales stats
        try:
            from utils.sales_stats import update_product_sales_stats
            update_product_sales_stats(order)
        except Exception as e:
            current_app.logger.warning(f'Failed to update sales stats: {e}')
        
        # Return created order
        order_dict = order.to_dict()
        
        # Get group deal info
        order_dict['group_deal'] = {
            'id': group_deal.id,
            'title': group_deal.title,
            'description': group_deal.description,
            'pickup_date': group_deal.pickup_date.isoformat() if group_deal.pickup_date else None
        }
        
        # Get order items with product details
        items_data = []
        for item in order.items:
            item_dict = item.to_dict()
            product = Product.query.get(item.product_id)
            if product:
                item_dict['product'] = {
                    'id': product.id,
                    'name': product.name,
                    'image': product.image,
                    'pricing_type': product.pricing_type
                }
            items_data.append(item_dict)
        
        order_dict['items'] = items_data
        
        return jsonify({
            'order': order_dict,
            'message': 'Order created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating order: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to create order',
            'message': str(e)
        }), 500

