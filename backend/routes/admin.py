from flask import Blueprint, jsonify, request, current_app, Response
from models import db
from models.product import Product
from models.user import User, AuthToken, UserRole
from models.groupdeal import GroupDeal, GroupDealProduct
from models.otp_attempt import OTPAttempt
from datetime import datetime, timedelta
from config import Config
import os
import uuid
from werkzeug.utils import secure_filename
from sqlalchemy import func
from decimal import Decimal

# Optional imports for image upload
try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    storage = None

try:
    from PIL import Image
    import io
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    io = None

admin_bp = Blueprint('admin', __name__)

def require_admin_auth():
    """Check if user is authenticated and has admin role"""
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
    
    # Get user and check admin role
    user = User.query.get(auth_token.user_id)
    if not user:
        return None, jsonify({'error': 'User not found'}), 401
    
    if not user.is_active:
        return None, jsonify({'error': 'User account is inactive'}), 403
    
    if not user.is_admin:
        return None, jsonify({'error': 'Admin access required'}), 403
    
    return auth_token.user_id, None, None

def get_gcs_client():
    """Get Google Cloud Storage client"""
    if not GCS_AVAILABLE:
        current_app.logger.error('google-cloud-storage is not installed')
        return None
    try:
        # Use service account credentials if available
        creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if creds_path and os.path.exists(creds_path):
            from google.oauth2 import service_account
            credentials = service_account.Credentials.from_service_account_file(creds_path)
            return storage.Client(credentials=credentials, project=Config.GCS_PROJECT_ID)
        else:
            # Use default credentials
            return storage.Client(project=Config.GCS_PROJECT_ID)
    except Exception as e:
        current_app.logger.error(f'Failed to initialize GCS client: {e}')
        return None

@admin_bp.route('/upload-image', methods=['POST'])
def upload_image():
    """Upload product image to Google Cloud Storage"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    if not GCS_AVAILABLE or not PIL_AVAILABLE:
        return jsonify({
            'error': 'Image upload not available',
            'message': 'google-cloud-storage and Pillow packages are required'
        }), 503
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if file_ext not in allowed_extensions:
        return jsonify({'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'}), 400
    
    try:
        # Read and validate image
        image_data = file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary (for JPEG compatibility)
        if image.mode in ('RGBA', 'LA', 'P'):
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            rgb_image.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = rgb_image
        
        # Resize if too large (max 2000x2000)
        max_size = 2000
        if image.width > max_size or image.height > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Convert to bytes
        output = io.BytesIO()
        format = 'JPEG' if file_ext in ('jpg', 'jpeg') else 'PNG'
        image.save(output, format=format, quality=85, optimize=True)
        image_data = output.getvalue()
        
        # Generate unique filename
        filename = f"products/{uuid.uuid4()}.{format.lower()}"
        
        # Upload to GCS
        gcs_client = get_gcs_client()
        if not gcs_client:
            return jsonify({'error': 'GCS client not available'}), 500
        
        bucket_name = Config.GCS_BUCKET_NAME
        bucket = gcs_client.bucket(bucket_name)
        blob = bucket.blob(filename)
        
        # Set content type
        content_type = f'image/{format.lower()}'
        blob.upload_from_string(image_data, content_type=content_type)
        
        # Return URL pointing to backend image serving endpoint
        # Backend will proxy the image from GCS (bucket stays private)
        # Use /api/images/ endpoint (public, no auth required for images)
        base_url = request.host_url.rstrip('/')
        if 'localhost' in base_url or '127.0.0.1' in base_url:
            # Local dev
            public_url = f"{base_url}/api/images/{filename}"
        else:
            # Production - use backend domain
            public_url = f"https://backend.grainstoryfarm.ca/api/images/{filename}"
        
        current_app.logger.info(f'Uploaded image to GCS: {filename}, serving via: {public_url}')
        
        return jsonify({
            'url': public_url,
            'filename': filename
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error uploading image: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to upload image',
            'message': str(e)
        }), 500

@admin_bp.route('/products', methods=['POST'])
def create_product():
    """Create a new product"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'sale_price']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'{field} is required'}), 400
    
    try:
        product = Product(
            name=data['name'],
            image=data.get('image'),
            original_price=data.get('original_price', data['sale_price']),
            sale_price=data['sale_price'],
            description=data.get('description', ''),
            stock_limit=data.get('stock_limit'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(product)
        db.session.commit()
        
        current_app.logger.info(f'Created product: {product.id} - {product.name}')
        
        return jsonify({
            'product': product.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating product: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to create product',
            'message': str(e)
        }), 500

@admin_bp.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update an existing product"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    try:
        if 'name' in data:
            product.name = data['name']
        if 'image' in data:
            product.image = data['image']
        if 'original_price' in data:
            product.original_price = data['original_price']
        if 'sale_price' in data:
            product.sale_price = data['sale_price']
        if 'description' in data:
            product.description = data['description']
        if 'stock_limit' in data:
            product.stock_limit = data['stock_limit'] if data['stock_limit'] else None
        if 'is_active' in data:
            product.is_active = data['is_active']
        
        db.session.commit()
        
        current_app.logger.info(f'Updated product: {product.id} - {product.name}')
        
        return jsonify({
            'product': product.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating product: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to update product',
            'message': str(e)
        }), 500

@admin_bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product (soft delete by setting is_active=False)"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    product = Product.query.get_or_404(product_id)
    
    try:
        # Soft delete - set is_active to False
        product.is_active = False
        db.session.commit()
        
        current_app.logger.info(f'Deleted product: {product.id} - {product.name}')
        
        return jsonify({
            'message': 'Product deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting product: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to delete product',
            'message': str(e)
        }), 500

@admin_bp.route('/users', methods=['GET'])
def get_users():
    """Get all users"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        # Get query parameters for pagination and filtering
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '').strip()
        
        # Build query
        query = User.query
        
        # Apply search filter
        if search:
            search_term = f'%{search}%'
            query = query.filter(
                db.or_(
                    User.phone.like(search_term),
                    User.nickname.like(search_term),
                    User.email.like(search_term)
                )
            )
        
        # Apply status filter
        if status_filter:
            query = query.filter(User.status == status_filter)
        
        # Order by creation date (newest first)
        query = query.order_by(User.created_at.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        users = pagination.items
        
        return jsonify({
            'users': [user.to_dict(include_order_count=True) for user in users],
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error fetching users: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to fetch users',
            'message': str(e)
        }), 500

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get a single user by ID"""
    admin_user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        user = User.query.get_or_404(user_id)
        return jsonify({
            'user': user.to_dict()
        }), 200
    except Exception as e:
        current_app.logger.error(f'Error fetching user: {e}', exc_info=True)
        return jsonify({
            'error': 'User not found',
            'message': str(e)
        }), 404

@admin_bp.route('/users/<int:user_id>/ban', methods=['POST'])
def ban_user(user_id):
    """Ban a user"""
    admin_user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        user = User.query.get_or_404(user_id)
        user.status = 'banned'
        db.session.commit()
        
        current_app.logger.info(f'Banned user: {user.id} - {user.phone or user.email}')
        
        return jsonify({
            'message': 'User banned successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error banning user: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to ban user',
            'message': str(e)
        }), 500

@admin_bp.route('/users/<int:user_id>/unban', methods=['POST'])
def unban_user(user_id):
    """Unban a user"""
    admin_user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        user = User.query.get_or_404(user_id)
        user.status = 'active'
        db.session.commit()
        
        current_app.logger.info(f'Unbanned user: {user.id} - {user.phone or user.email}')
        
        return jsonify({
            'message': 'User unbanned successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error unbanning user: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to unban user',
            'message': str(e)
        }), 500

@admin_bp.route('/users/<int:user_id>/roles', methods=['GET'])
def get_user_roles(user_id):
    """Get user roles"""
    admin_user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        user = User.query.get_or_404(user_id)
        roles = [role.to_dict() for role in user.roles]
        return jsonify({
            'roles': roles,
            'is_admin': user.is_admin
        }), 200
    except Exception as e:
        current_app.logger.error(f'Error fetching user roles: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to fetch user roles',
            'message': str(e)
        }), 500

@admin_bp.route('/users/<int:user_id>/roles', methods=['POST'])
def assign_user_role(user_id):
    """Assign a role to a user"""
    admin_user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    data = request.get_json()
    role_name = data.get('role', '').strip().lower()
    
    if not role_name:
        return jsonify({'error': 'Role is required'}), 400
    
    # Validate role name
    valid_roles = ['admin', 'moderator', 'user']
    if role_name not in valid_roles:
        return jsonify({'error': f'Invalid role. Valid roles: {", ".join(valid_roles)}'}), 400
    
    try:
        user = User.query.get_or_404(user_id)
        
        # Check if role already exists
        existing_role = UserRole.query.filter_by(user_id=user.id, role=role_name).first()
        if existing_role:
            return jsonify({
                'message': 'Role already assigned',
                'role': existing_role.to_dict()
            }), 200
        
        # Create new role
        user_role = UserRole(user_id=user.id, role=role_name)
        db.session.add(user_role)
        db.session.commit()
        
        current_app.logger.info(f'Assigned role {role_name} to user {user.id}')
        
        return jsonify({
            'message': 'Role assigned successfully',
            'role': user_role.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error assigning role: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to assign role',
            'message': str(e)
        }), 500

@admin_bp.route('/users/<int:user_id>/roles/<role_name>', methods=['DELETE'])
def remove_user_role(user_id, role_name):
    """Remove a role from a user"""
    admin_user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    role_name = role_name.lower()
    
    # Prevent removing admin role from yourself
    if role_name == 'admin' and user_id == admin_user_id:
        return jsonify({'error': 'Cannot remove admin role from yourself'}), 400
    
    try:
        user = User.query.get_or_404(user_id)
        user_role = UserRole.query.filter_by(user_id=user.id, role=role_name).first()
        
        if not user_role:
            return jsonify({'error': 'Role not found'}), 404
        
        db.session.delete(user_role)
        db.session.commit()
        
        current_app.logger.info(f'Removed role {role_name} from user {user.id}')
        
        return jsonify({
            'message': 'Role removed successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error removing role: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to remove role',
            'message': str(e)
        }), 500

# Group Deal Management
@admin_bp.route('/group-deals', methods=['GET'])
def get_group_deals():
    """Get all group deals"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        status_filter = request.args.get('status', '').strip()
        
        # Build query
        query = GroupDeal.query
        
        # Apply status filter
        if status_filter:
            query = query.filter(GroupDeal.status == status_filter)
        
        # Order by order start date (newest first)
        query = query.order_by(GroupDeal.order_start_date.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        deals = pagination.items
        
        # Include products for each deal
        deals_data = []
        for deal in deals:
            deal_dict = deal.to_dict()
            # Get products for this deal
            deal_products = GroupDealProduct.query.filter_by(group_deal_id=deal.id).all()
            products_data = []
            for dp in deal_products:
                product = Product.query.get(dp.product_id)
                if product:
                    product_dict = product.to_dict()
                    product_dict['deal_price'] = float(dp.deal_price) if dp.deal_price else None
                    product_dict['deal_stock_limit'] = dp.deal_stock_limit
                    product_dict['group_deal_product_id'] = dp.id
                    products_data.append(product_dict)
            deal_dict['products'] = products_data
            deals_data.append(deal_dict)
        
        return jsonify({
            'group_deals': deals_data,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error fetching group deals: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to fetch group deals',
            'message': str(e)
        }), 500

@admin_bp.route('/group-deals/<int:deal_id>', methods=['GET'])
def get_group_deal(deal_id):
    """Get a single group deal by ID"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
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
                product_dict['deal_price'] = float(dp.deal_price) if dp.deal_price else None
                product_dict['deal_stock_limit'] = dp.deal_stock_limit
                product_dict['group_deal_product_id'] = dp.id
                products_data.append(product_dict)
        deal_dict['products'] = products_data
        
        return jsonify({
            'group_deal': deal_dict
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error fetching group deal: {e}', exc_info=True)
        return jsonify({
            'error': 'Group deal not found',
            'message': str(e)
        }), 404

@admin_bp.route('/group-deals', methods=['POST'])
def create_group_deal():
    """Create a new group deal"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['title', 'order_start_date', 'order_end_date', 'pickup_date']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'{field} is required'}), 400
    
    try:
        # Parse dates
        order_start_date = datetime.fromisoformat(data['order_start_date'].replace('Z', '+00:00'))
        order_end_date = datetime.fromisoformat(data['order_end_date'].replace('Z', '+00:00'))
        pickup_date = datetime.fromisoformat(data['pickup_date'].replace('Z', '+00:00'))
        
        # Determine status based on dates
        now = datetime.utcnow()
        if order_start_date > now:
            status = 'upcoming'
        elif order_start_date <= now <= order_end_date:
            status = 'active'
        else:
            status = 'closed'
        
        group_deal = GroupDeal(
            title=data['title'],
            description=data.get('description', ''),
            order_start_date=order_start_date,
            order_end_date=order_end_date,
            pickup_date=pickup_date,
            status=data.get('status', status)
        )
        
        db.session.add(group_deal)
        db.session.flush()
        
        # Add products to deal
        products = data.get('products', [])
        for product_data in products:
            product_id = product_data.get('product_id')
            if not product_id:
                continue
            
            deal_product = GroupDealProduct(
                group_deal_id=group_deal.id,
                product_id=product_id,
                deal_price=product_data.get('deal_price'),
                deal_stock_limit=product_data.get('deal_stock_limit')
            )
            db.session.add(deal_product)
        
        db.session.commit()
        
        current_app.logger.info(f'Created group deal: {group_deal.id} - {group_deal.title}')
        
        # Return full deal with products
        deal_dict = group_deal.to_dict()
        deal_products = GroupDealProduct.query.filter_by(group_deal_id=group_deal.id).all()
        products_data = []
        for dp in deal_products:
            product = Product.query.get(dp.product_id)
            if product:
                product_dict = product.to_dict()
                product_dict['deal_price'] = float(dp.deal_price) if dp.deal_price else None
                product_dict['deal_stock_limit'] = dp.deal_stock_limit
                products_data.append(product_dict)
        deal_dict['products'] = products_data
        
        return jsonify({
            'group_deal': deal_dict
        }), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'error': 'Invalid date format',
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating group deal: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to create group deal',
            'message': str(e)
        }), 500

@admin_bp.route('/group-deals/<int:deal_id>', methods=['PUT'])
def update_group_deal(deal_id):
    """Update an existing group deal"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    deal = GroupDeal.query.get_or_404(deal_id)
    data = request.get_json()
    
    try:
        if 'title' in data:
            deal.title = data['title']
        if 'description' in data:
            deal.description = data['description']
        if 'order_start_date' in data:
            deal.order_start_date = datetime.fromisoformat(data['order_start_date'].replace('Z', '+00:00'))
        if 'order_end_date' in data:
            deal.order_end_date = datetime.fromisoformat(data['order_end_date'].replace('Z', '+00:00'))
        if 'pickup_date' in data:
            deal.pickup_date = datetime.fromisoformat(data['pickup_date'].replace('Z', '+00:00'))
        if 'status' in data:
            deal.status = data['status']
        
        # Update products if provided
        if 'products' in data:
            # Remove existing products
            GroupDealProduct.query.filter_by(group_deal_id=deal.id).delete()
            
            # Add new products
            for product_data in data['products']:
                product_id = product_data.get('product_id')
                if not product_id:
                    continue
                
                deal_product = GroupDealProduct(
                    group_deal_id=deal.id,
                    product_id=product_id,
                    deal_price=product_data.get('deal_price'),
                    deal_stock_limit=product_data.get('deal_stock_limit')
                )
                db.session.add(deal_product)
        
        db.session.commit()
        
        current_app.logger.info(f'Updated group deal: {deal.id} - {deal.title}')
        
        # Return full deal with products
        deal_dict = deal.to_dict()
        deal_products = GroupDealProduct.query.filter_by(group_deal_id=deal.id).all()
        products_data = []
        for dp in deal_products:
            product = Product.query.get(dp.product_id)
            if product:
                product_dict = product.to_dict()
                product_dict['deal_price'] = float(dp.deal_price) if dp.deal_price else None
                product_dict['deal_stock_limit'] = dp.deal_stock_limit
                products_data.append(product_dict)
        deal_dict['products'] = products_data
        
        return jsonify({
            'group_deal': deal_dict
        }), 200
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'error': 'Invalid date format',
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating group deal: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to update group deal',
            'message': str(e)
        }), 500

@admin_bp.route('/group-deals/<int:deal_id>', methods=['DELETE'])
def delete_group_deal(deal_id):
    """Delete a group deal"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    deal = GroupDeal.query.get_or_404(deal_id)
    
    try:
        # Cascade delete will handle GroupDealProduct records
        db.session.delete(deal)
        db.session.commit()
        
        current_app.logger.info(f'Deleted group deal: {deal.id} - {deal.title}')
        
        return jsonify({
            'message': 'Group deal deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting group deal: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to delete group deal',
            'message': str(e)
        }), 500

@admin_bp.route('/otp-stats', methods=['GET'])
def get_otp_stats():
    """Get OTP usage statistics for Twilio cost tracking"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        # Get date range from query params (default: last 30 days)
        days = int(request.args.get('days', 30))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all attempts in date range
        attempts = OTPAttempt.query.filter(
            OTPAttempt.created_at >= start_date
        ).order_by(OTPAttempt.created_at.desc()).all()
        
        # Calculate statistics
        total_attempts = len(attempts)
        successful_sends = len([a for a in attempts if a.action_type == 'send' and a.status == 'success'])
        failed_sends = len([a for a in attempts if a.action_type == 'send' and a.status == 'failed'])
        successful_verifications = len([a for a in attempts if a.action_type == 'verify' and a.status == 'success'])
        failed_verifications = len([a for a in attempts if a.action_type == 'verify' and a.status == 'failed'])
        
        # Calculate total cost (only successful sends cost money)
        total_cost = sum(
            float(a.estimated_cost) if a.estimated_cost else 0 
            for a in attempts 
            if a.action_type == 'send' and a.status == 'success'
        )
        
        # Group by date for chart data
        daily_stats = {}
        for attempt in attempts:
            date_key = attempt.created_at.date().isoformat()
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    'date': date_key,
                    'sends': 0,
                    'verifications': 0,
                    'cost': 0.0
                }
            if attempt.action_type == 'send' and attempt.status == 'success':
                daily_stats[date_key]['sends'] += 1
                daily_stats[date_key]['cost'] += float(attempt.estimated_cost) if attempt.estimated_cost else 0
            elif attempt.action_type == 'verify':
                daily_stats[date_key]['verifications'] += 1
        
        daily_chart_data = sorted(daily_stats.values(), key=lambda x: x['date'])
        
        # Get recent attempts (last 50)
        recent_attempts = attempts[:50]
        
        return jsonify({
            'summary': {
                'total_attempts': total_attempts,
                'successful_sends': successful_sends,
                'failed_sends': failed_sends,
                'successful_verifications': successful_verifications,
                'failed_verifications': failed_verifications,
                'total_cost_usd': round(total_cost, 4),
                'estimated_monthly_cost': round(total_cost * (30 / days), 4) if days > 0 else 0,
                'period_days': days
            },
            'daily_chart': daily_chart_data,
            'recent_attempts': [a.to_dict() for a in recent_attempts]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error getting OTP stats: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to get OTP statistics',
            'message': str(e)
        }), 500

