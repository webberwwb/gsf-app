from flask import Blueprint, jsonify, request, current_app, Response
from models import db
from models.product import Product
from models.user import User, AuthToken, UserRole
from models.groupdeal import GroupDeal, GroupDealProduct
from models.otp_attempt import OTPAttempt
from models.supplier import Supplier
from models.order import Order, OrderItem
from models.product_sales_stats import ProductSalesStats
from utils.sales_stats import update_product_sales_stats, get_product_sales_by_date_range, get_popular_products
from datetime import datetime, timedelta, timezone, date
from models.base import utc_now
from config import Config
from constants.status_enums import OrderStatus, PaymentStatus, GroupDealStatus, UserStatus, PaymentMethod
from schemas.product import CreateProductSchema, UpdateProductSchema
from schemas.groupdeal import CreateGroupDealSchema, UpdateGroupDealSchema, UpdateGroupDealStatusSchema
from schemas.admin import CreateSupplierSchema, UpdateSupplierSchema, AssignRoleSchema, UpdateOrderStatusSchema, UpdateOrderPaymentSchema
from schemas.order import UpdateOrderWeightsSchema, AdminUpdateOrderSchema
from schemas.utils import validate_request
import os
import uuid
from werkzeug.utils import secure_filename
from sqlalchemy import func
from decimal import Decimal
import csv
import io

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
    
    # Refresh token expiration on each use (extend to 30 days from now)
    # This ensures if user uses app at least once a month, they never need to OTP again
    # Make sure expires_at is stored as naive datetime (MySQL doesn't support timezone-aware)
    new_expires_at = utc_now() + timedelta(days=30)
    auth_token.expires_at = new_expires_at  # Already naive UTC datetime
    db.session.commit()
    
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
    
    # Validate request data using schema
    validated_data, error_response, status_code = validate_request(CreateProductSchema)
    if error_response:
        return error_response, status_code
    
    try:
        # Handle images: prefer images array, fallback to single image for backward compatibility
        images = validated_data.get('images')
        if not images and validated_data.get('image'):
            images = [validated_data.get('image')]
        
        product = Product(
            name=validated_data['name'],
            image=validated_data.get('image'),  # Keep for backward compatibility
            images=images,  # New multiple images array
            pricing_type=validated_data['pricing_type'],
            pricing_data=validated_data['pricing_data'],
            description=validated_data.get('description', ''),
            stock_limit=validated_data.get('stock_limit'),
            is_active=validated_data.get('is_active', True),
            supplier_id=validated_data.get('supplier_id'),
            counts_toward_free_shipping=validated_data.get('counts_toward_free_shipping', True)
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
    
    # Get raw data first to check pricing_type
    raw_data = request.get_json()
    pricing_type = raw_data.get('pricing_type') if raw_data else product.pricing_type
    
    # Validate request data using schema
    validated_data, error_response, status_code = validate_request(
        UpdateProductSchema,
        context={'pricing_type': pricing_type}
    )
    if error_response:
        return error_response, status_code
    
    try:
        # Re-validate pricing_data if both pricing_type and pricing_data are being updated
        if 'pricing_type' in validated_data and 'pricing_data' in validated_data:
            validated_data, error_response, status_code = validate_request(
                UpdateProductSchema,
                data=validated_data,
                context={'pricing_type': validated_data['pricing_type']}
            )
            if error_response:
                return error_response, status_code
        
        # Update pricing_type if provided
        if 'pricing_type' in validated_data:
            product.pricing_type = validated_data['pricing_type']
        
        if 'name' in validated_data:
            product.name = validated_data['name']
        if 'images' in validated_data:
            product.images = validated_data['images']
            # Also update single image for backward compatibility (use first image)
            if validated_data['images'] and len(validated_data['images']) > 0:
                product.image = validated_data['images'][0]
        elif 'image' in validated_data:
            # Backward compatibility: convert single image to array
            product.image = validated_data['image']
            if validated_data['image']:
                product.images = [validated_data['image']]
            else:
                product.images = []
        if 'pricing_data' in validated_data:
            product.pricing_data = validated_data['pricing_data']
        if 'description' in validated_data:
            product.description = validated_data['description']
        if 'stock_limit' in validated_data:
            product.stock_limit = validated_data['stock_limit'] if validated_data['stock_limit'] else None
        if 'is_active' in validated_data:
            product.is_active = validated_data['is_active']
        if 'supplier_id' in validated_data:
            product.supplier_id = validated_data['supplier_id'] if validated_data['supplier_id'] else None
        if 'counts_toward_free_shipping' in validated_data:
            product.counts_toward_free_shipping = validated_data['counts_toward_free_shipping']
        
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
        user.status = UserStatus.ACTIVE.value
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
    
    # Validate request data using schema
    validated_data, error_response, status_code = validate_request(AssignRoleSchema)
    if error_response:
        return error_response, status_code
    
    role_name = validated_data['role'].lower()
    
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
        
        # Build query - filter out soft-deleted deals
        query = GroupDeal.query.filter(GroupDeal.deleted_at.is_(None))
        
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
    
    # Validate request data using schema
    validated_data, error_response, status_code = validate_request(CreateGroupDealSchema)
    if error_response:
        return error_response, status_code
    
    try:
        # Import date helpers
        from utils.date_helpers import normalize_date_start, normalize_date_end
        
        # Parse and normalize dates
        # order_start_date: 00:00:00 EST
        # order_end_date: 23:59:59 EST
        # pickup_date: 00:00:00 EST
        order_start_date = normalize_date_start(validated_data['order_start_date'])
        order_end_date = normalize_date_end(validated_data['order_end_date'])
        pickup_date = normalize_date_start(validated_data['pickup_date'])
        
        # Determine status based on dates
        # Use naive EST datetime for comparison
        now = utc_now()
        if order_start_date > now:
            status = GroupDealStatus.UPCOMING.value
        elif order_start_date <= now <= order_end_date:
            status = GroupDealStatus.ACTIVE.value
        else:
            status = GroupDealStatus.CLOSED.value
        
        group_deal = GroupDeal(
            title=validated_data['title'],
            description=validated_data.get('description', ''),
            order_start_date=order_start_date,
            order_end_date=order_end_date,
            pickup_date=pickup_date,
            status=validated_data.get('status', status)
        )
        
        db.session.add(group_deal)
        db.session.flush()
        
        # Add products to deal
        products = validated_data.get('products', [])
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
    
    deal = GroupDeal.query.filter(
        GroupDeal.id == deal_id,
        GroupDeal.deleted_at.is_(None)
    ).first_or_404()
    
    # Validate request data using schema
    validated_data, error_response, status_code = validate_request(UpdateGroupDealSchema)
    if error_response:
        return error_response, status_code
    
    try:
        # Import date helpers
        from utils.date_helpers import normalize_date_start, normalize_date_end
        from models.base import est_now
        
        dates_updated = False
        
        if 'title' in validated_data:
            deal.title = validated_data['title']
        if 'description' in validated_data:
            deal.description = validated_data['description']
        if 'order_start_date' in validated_data:
            # Normalize to 00:00:00 EST
            deal.order_start_date = normalize_date_start(validated_data['order_start_date'])
            dates_updated = True
        if 'order_end_date' in validated_data:
            # Normalize to 23:59:59 EST
            deal.order_end_date = normalize_date_end(validated_data['order_end_date'])
            dates_updated = True
        if 'pickup_date' in validated_data:
            # Normalize to 00:00:00 EST
            deal.pickup_date = normalize_date_start(validated_data['pickup_date'])
        
        # Store original status before any updates
        original_status = deal.status
        
        # Handle status update
        status_explicitly_provided = 'status' in validated_data
        new_status = None
        if status_explicitly_provided:
            new_status = validated_data['status']
            deal.status = new_status
        
        # Re-evaluate status based on dates if dates were updated
        # Priority: Manual status changes > Date-based auto-evaluation
        if dates_updated:
            # If status was explicitly changed to a manual status, respect it and don't re-evaluate
            if status_explicitly_provided and new_status in GroupDealStatus.get_manual_managed_statuses():
                # User explicitly set a manual status (preparing, ready_for_pickup, completed), respect it
                pass
            # Otherwise, re-evaluate based on dates (for auto-managed statuses or when status not provided)
            else:
                now = est_now()
                if deal.order_start_date > now:
                    deal.status = GroupDealStatus.UPCOMING.value
                elif deal.order_start_date <= now <= deal.order_end_date:
                    deal.status = GroupDealStatus.ACTIVE.value
                elif deal.order_end_date < now:
                    deal.status = GroupDealStatus.CLOSED.value
        
        # Determine final status after all updates
        final_status = deal.status
        
        # Cascade status changes to orders (same logic as update_group_deal_status endpoint)
        orders_updated = 0
        if final_status != original_status:
            if final_status == GroupDealStatus.PREPARING.value:
                # All submitted/confirmed orders become preparing
                orders = Order.query.filter(
                    Order.group_deal_id == deal_id,
                    Order.status.in_([OrderStatus.SUBMITTED.value, OrderStatus.CONFIRMED.value]),
                    Order.status != OrderStatus.CANCELLED.value
                ).all()
                for order in orders:
                    order.status = OrderStatus.PREPARING.value
                    orders_updated += 1
            
            elif final_status == GroupDealStatus.READY_FOR_PICKUP.value:
                # All submitted/confirmed/preparing orders become ready_for_pickup
                orders = Order.query.filter(
                    Order.group_deal_id == deal_id,
                    Order.status.in_([
                        OrderStatus.SUBMITTED.value,
                        OrderStatus.CONFIRMED.value,
                        OrderStatus.PREPARING.value
                    ]),
                    Order.status != OrderStatus.CANCELLED.value
                ).all()
                for order in orders:
                    order.status = OrderStatus.READY_FOR_PICKUP.value
                    orders_updated += 1
            
            elif final_status == GroupDealStatus.CLOSED.value:
                # All submitted orders become confirmed when group deal is closed
                orders = Order.query.filter(
                    Order.group_deal_id == deal_id,
                    Order.status == OrderStatus.SUBMITTED.value,
                    Order.status != OrderStatus.CANCELLED.value
                ).all()
                for order in orders:
                    order.status = OrderStatus.CONFIRMED.value
                    orders_updated += 1
            
            if orders_updated > 0:
                current_app.logger.info(f'Cascaded group deal status change from {original_status} to {final_status} to {orders_updated} orders')
        
        # Update products if provided
        if 'products' in validated_data:
            # Check if there are existing orders for this group deal
            existing_orders_count = Order.query.filter(
                Order.group_deal_id == deal.id,
                Order.deleted_at.is_(None)
            ).count()
            
            if existing_orders_count > 0:
                # If there are existing orders, check which products are in orders
                # Get product IDs that are in existing order items
                products_in_orders = db.session.query(OrderItem.product_id).join(
                    Order, OrderItem.order_id == Order.id
                ).filter(
                    Order.group_deal_id == deal.id,
                    Order.deleted_at.is_(None)
                ).distinct().all()
                products_in_orders_set = {pid[0] for pid in products_in_orders}
                
                # Get current products in the deal
                current_deal_products = GroupDealProduct.query.filter_by(group_deal_id=deal.id).all()
                current_product_ids = {dp.product_id for dp in current_deal_products}
                
                # Get new product IDs from request
                new_product_ids = {product_data.get('product_id') for product_data in validated_data['products'] if product_data.get('product_id')}
                
                # Check if any products in orders are being removed
                products_being_removed = current_product_ids - new_product_ids
                products_in_orders_being_removed = products_being_removed & products_in_orders_set
                
                if products_in_orders_being_removed:
                    product_names = db.session.query(Product.name).filter(
                        Product.id.in_(products_in_orders_being_removed)
                    ).all()
                    product_names_list = [name[0] for name in product_names]
                    return jsonify({
                        'error': 'Cannot remove products that are in existing orders',
                        'message': f'以下商品已在订单中，无法移除: {", ".join(product_names_list)}'
                    }), 400
            
            # Remove existing products (safe now - we've validated)
            GroupDealProduct.query.filter_by(group_deal_id=deal.id).delete()
            
            # Add new products
            for product_data in validated_data['products']:
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
    """Delete a group deal (soft delete) and all associated orders"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    deal = GroupDeal.query.filter(
        GroupDeal.id == deal_id,
        GroupDeal.deleted_at.is_(None)
    ).first_or_404()
    
    try:
        # Soft delete all associated orders that aren't already soft deleted
        now = utc_now()
        associated_orders = Order.query.filter(
            Order.group_deal_id == deal_id,
            Order.deleted_at.is_(None)
        ).all()
        
        orders_deleted = 0
        for order in associated_orders:
            order.deleted_at = now
            orders_deleted += 1
        
        # Soft delete the group deal
        deal.deleted_at = now
        db.session.commit()
        
        current_app.logger.info(f'Soft deleted group deal: {deal.id} - {deal.title} and {orders_deleted} associated orders')
        
        return jsonify({
            'message': 'Group deal deleted successfully',
            'orders_deleted': orders_deleted
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting group deal: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to delete group deal',
            'message': str(e)
        }), 500

@admin_bp.route('/products', methods=['GET'])
def get_admin_products():
    """Get all products with optional sales stats and sorting (admin only)"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        # Get query parameters
        sort_by = request.args.get('sort', 'created_at')  # 'created_at', 'popularity', 'name'
        days = request.args.get('days', 30, type=int)  # Days for popularity calculation
        
        # Base query
        query = Product.query
        
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
                db.desc(stats_subquery.c.total_sold),
                Product.created_at.desc()
            )
        elif sort_by == 'name':
            query = query.order_by(Product.name.asc())
        else:
            query = query.order_by(Product.created_at.desc())
        
        products = query.all()
        
        # Get sales stats for each product
        start_date = date.today() - timedelta(days=days)
        products_data = []
        for product in products:
            product_dict = product.to_dict()
            
            # Get sales stats for date range
            stats_query = db.session.query(
                func.sum(ProductSalesStats.quantity_sold).label('total_sold'),
                func.sum(ProductSalesStats.order_count).label('total_orders')
            ).filter(
                ProductSalesStats.product_id == product.id,
                ProductSalesStats.sale_date >= start_date
            ).first()
            
            product_dict['sales_stats'] = {
                'total_sold': int(stats_query.total_sold) if stats_query.total_sold else 0,
                'total_orders': int(stats_query.total_orders) if stats_query.total_orders else 0,
                'period_days': days
            }
            
            products_data.append(product_dict)
        
        return jsonify({
            'products': products_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error fetching products: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to fetch products',
            'message': str(e)
        }), 500

@admin_bp.route('/products/<int:product_id>/sales-stats', methods=['GET'])
def get_product_sales_stats(product_id):
    """Get product sales statistics by date range"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        product = Product.query.get_or_404(product_id)
        
        # Get date range from query params (default: last 30 days)
        days = request.args.get('days', 30, type=int)
        start_date = date.today() - timedelta(days=days)
        end_date = date.today()
        
        # Get sales stats
        stats = get_product_sales_by_date_range(product_id, start_date, end_date)
        
        return jsonify({
            'product_id': product_id,
            'product_name': product.name,
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'stats': stats
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error fetching product sales stats: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to fetch sales statistics',
            'message': str(e)
        }), 500

@admin_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        # Count products
        products_count = Product.query.filter_by(is_active=True).count()
        
        # Count users
        users_count = User.query.filter_by(status=UserStatus.ACTIVE.value).count()
        
        # Count orders (excluding soft-deleted)
        orders_count = Order.query.filter(Order.deleted_at.is_(None)).count()
        
        # Calculate total revenue (sum of all paid orders, excluding soft-deleted)
        revenue_result = db.session.query(func.sum(Order.total)).filter(
            Order.payment_status == PaymentStatus.PAID.value,
            Order.deleted_at.is_(None)
        ).scalar()
        total_revenue = float(revenue_result) if revenue_result else 0.0
        
        # Get recent orders (last 10, excluding soft-deleted)
        recent_orders = Order.query.filter(Order.deleted_at.is_(None)).order_by(Order.created_at.desc()).limit(10).all()
        recent_orders_data = []
        for order in recent_orders:
            user = User.query.get(order.user_id)
            recent_orders_data.append({
                'id': order.id,
                'order_number': order.order_number,
                'user_name': user.nickname if user else user.phone if user else 'N/A',
                'total_amount': float(order.total) if order.total else 0.0,
                'payment_status': order.payment_status,
                'status': order.status,
                'created_at': order.created_at.isoformat() if order.created_at else None
            })
        
        return jsonify({
            'stats': {
                'products': products_count,
                'orders': orders_count,
                'users': users_count,
                'revenue': round(total_revenue, 2)
            },
            'recent_orders': recent_orders_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error fetching dashboard stats: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to fetch dashboard statistics',
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
        start_date = utc_now() - timedelta(days=days)
        
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

# Orders Management
@admin_bp.route('/orders', methods=['GET'])
def get_admin_orders():
    """Get all orders (admin only)"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        # Get query parameters for pagination and filtering
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        status_filter = request.args.get('status', '').strip()
        payment_filter = request.args.get('payment_status', '').strip()
        payment_method_filter = request.args.get('payment_method', '').strip()
        delivery_method_filter = request.args.get('delivery_method', '').strip()
        group_deal_id = request.args.get('group_deal_id')
        search = request.args.get('search', '').strip()
        
        # Build query - join with User for phone search
        # Filter out soft-deleted orders (deleted_at IS NULL)
        query = Order.query.join(User, Order.user_id == User.id).filter(Order.deleted_at.is_(None))
        
        # Apply search filter (order number or phone)
        if search:
            search_term = f'%{search}%'
            query = query.filter(
                db.or_(
                    Order.order_number.like(search_term),
                    User.phone.like(search_term)
                )
            )
        
        # Apply filters
        if status_filter:
            query = query.filter(Order.status == status_filter)
        
        if payment_filter:
            query = query.filter(Order.payment_status == payment_filter)
        
        if payment_method_filter:
            query = query.filter(Order.payment_method == payment_method_filter)
        
        if delivery_method_filter:
            query = query.filter(Order.delivery_method == delivery_method_filter)
        
        if group_deal_id:
            query = query.filter(Order.group_deal_id == int(group_deal_id))
        
        # Order by creation date (newest first)
        query = query.order_by(Order.created_at.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        orders = pagination.items
        
        # Build response with order details
        orders_data = []
        for order in orders:
            order_dict = order.to_dict()
            
            # Get user info
            user = User.query.get(order.user_id)
            if user:
                order_dict['user'] = {
                    'id': user.id,
                    'nickname': user.nickname,
                    'phone': user.phone,
                    'email': user.email,
                    'wechat': user.wechat
                }
            
            # Get group deal info (excluding soft-deleted)
            group_deal = GroupDeal.query.filter(
                GroupDeal.id == order.group_deal_id,
                GroupDeal.deleted_at.is_(None)
            ).first()
            if group_deal:
                order_dict['group_deal'] = {
                    'id': group_deal.id,
                    'title': group_deal.title,
                    'pickup_date': group_deal.pickup_date.isoformat() if group_deal.pickup_date else None
                }
            
            # Get address info if delivery order
            if order.address_id:
                from models.address import Address
                address = Address.query.get(order.address_id)
                if address:
                    order_dict['address'] = address.to_dict()
            
            # Get order items count
            order_dict['items_count'] = len(order.items)
            
            orders_data.append(order_dict)
        
        return jsonify({
            'orders': orders_data,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error fetching orders: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to fetch orders',
            'message': str(e)
        }), 500

@admin_bp.route('/orders/<int:order_id>', methods=['GET'])
def get_admin_order(order_id):
    """Get a single order by ID (admin only)"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        order = Order.query.filter(Order.id == order_id, Order.deleted_at.is_(None)).first_or_404()
        order_dict = order.to_dict()
        
        # Get user info
        user = User.query.get(order.user_id)
        if user:
            order_dict['user'] = user.to_dict()
        
        # Get group deal info (excluding soft-deleted)
        group_deal = GroupDeal.query.filter(
            GroupDeal.id == order.group_deal_id,
            GroupDeal.deleted_at.is_(None)
        ).first()
        if group_deal:
            order_dict['group_deal'] = group_deal.to_dict()
        
        # Get address info if delivery order
        if order.address_id:
            from models.address import Address
            address = Address.query.get(order.address_id)
            if address:
                order_dict['address'] = address.to_dict()
        
        # Get order items with product details
        items_data = []
        for item in order.items:
            item_dict = item.to_dict()
            product = Product.query.get(item.product_id)
            if product:
                item_dict['product'] = product.to_dict()
            items_data.append(item_dict)
        
        order_dict['items'] = items_data
        
        return jsonify({
            'order': order_dict
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error fetching order: {e}', exc_info=True)
        return jsonify({
            'error': 'Order not found',
            'message': str(e)
        }), 404

@admin_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Update order status (admin only)"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    # Validate request data using schema
    validated_data, error_response, status_code = validate_request(UpdateOrderStatusSchema)
    if error_response:
        return error_response, status_code
    
    status = validated_data['status']
    
    try:
        order = Order.query.filter(Order.id == order_id, Order.deleted_at.is_(None)).first_or_404()
        old_status = order.status
        order.status = status
        db.session.commit()
        
        current_app.logger.info(f'Updated order {order_id} status from {old_status} to {status}')
        
        return jsonify({
            'message': 'Order status updated successfully',
            'order': order.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating order status: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to update order status',
            'message': str(e)
        }), 500

@admin_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
def admin_cancel_order(order_id):
    """Cancel an order (admin only - can cancel at any stage)"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        order = Order.query.filter(Order.id == order_id, Order.deleted_at.is_(None)).first_or_404()
        
        # Check if already cancelled or completed
        if order.status == OrderStatus.CANCELLED.value:
            return jsonify({'error': 'Order is already cancelled'}), 400
        
        if order.status == OrderStatus.COMPLETED.value:
            return jsonify({'error': 'Cannot cancel a completed order. Please refund instead.'}), 400
        
        old_status = order.status
        order.status = OrderStatus.CANCELLED.value
        db.session.commit()
        
        current_app.logger.info(f'Admin cancelled order {order_id} (was {old_status})')
        
        return jsonify({
            'message': 'Order cancelled successfully',
            'order': order.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error cancelling order: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to cancel order',
            'message': str(e)
        }), 500

@admin_bp.route('/orders/<int:order_id>/payment', methods=['PUT'])
def update_order_payment(order_id):
    """Update order payment status (admin only) - triggers points and completion"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    # Validate request data using schema
    validated_data, error_response, status_code = validate_request(UpdateOrderPaymentSchema)
    if error_response:
        return error_response, status_code
    
    payment_status = validated_data['payment_status']
    payment_method = validated_data.get('payment_method', '').strip() if validated_data.get('payment_method') else None
    
    try:
        order = Order.query.filter(Order.id == order_id, Order.deleted_at.is_(None)).first_or_404()
        
        # Check if order is cancelled
        if order.status == OrderStatus.CANCELLED.value:
            return jsonify({'error': 'Cannot update payment for cancelled order'}), 400
        
        old_payment_status = order.payment_status
        order.payment_status = payment_status
        
        if payment_method:
            order.payment_method = payment_method
        
        # If changing from unpaid to paid, calculate points and complete order
        if old_payment_status == PaymentStatus.UNPAID.value and payment_status == PaymentStatus.PAID.value:
            # Calculate points: 1 point per cent ($0.01)
            total_cents = int(float(order.total) * 100)
            order.points_earned = total_cents
            order.payment_date = utc_now()
            
            # Update user's points balance
            user = User.query.get(order.user_id)
            if user:
                user.points = (user.points or 0) + total_cents
                current_app.logger.info(f'Awarded {total_cents} points to user {user.id} for order {order_id}')
            
            # Auto-complete the order
            order.status = OrderStatus.COMPLETED.value
            
            current_app.logger.info(f'Order {order_id} marked as paid and completed. Points: {total_cents}')
        
        db.session.commit()
        
        return jsonify({
            'message': 'Payment status updated successfully',
            'order': order.to_dict(),
            'points_awarded': order.points_earned if payment_status == PaymentStatus.PAID.value else 0
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating payment status: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to update payment status',
            'message': str(e)
        }), 500

@admin_bp.route('/orders/by-pickup-code/<pickup_code>', methods=['GET'])
def get_order_by_pickup_code(pickup_code):
    """Get order by pickup code (for QR scanning) - pickup_code is the last part of order_number"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        # pickup_code is the last part of order_number (e.g., "CGN7O7" from "GSF-20231225123456-CGN7O7")
        # Search for orders where order_number ends with the pickup code
        # Format: GSF-{timestamp}-{pickup_code}
        order = Order.query.filter(
            Order.order_number.like(f'%-{pickup_code}'),
            Order.deleted_at.is_(None)
        ).first()
        
        if not order:
            return jsonify({
                'error': 'Order not found',
                'message': 'Invalid pickup code'
            }), 404
        
        order_dict = order.to_dict()
        
        # Get user info
        user = User.query.get(order.user_id)
        if user:
            order_dict['user'] = user.to_dict()
        
        # Get group deal info (excluding soft-deleted)
        group_deal = GroupDeal.query.filter(
            GroupDeal.id == order.group_deal_id,
            GroupDeal.deleted_at.is_(None)
        ).first()
        if group_deal:
            order_dict['group_deal'] = group_deal.to_dict()
        
        # Get order items with product details
        items_data = []
        for item in order.items:
            item_dict = item.to_dict()
            product = Product.query.get(item.product_id)
            if product:
                item_dict['product'] = product.to_dict()
            items_data.append(item_dict)
        
        order_dict['items'] = items_data
        
        return jsonify({
            'order': order_dict
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error fetching order by pickup code: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to fetch order',
            'message': str(e)
        }), 500

@admin_bp.route('/orders/<int:order_id>/update-weights', methods=['PUT'])
def update_order_weights(order_id):
    """Update order items with final weights and recalculate prices (admin only)"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    # Validate request data using schema
    validated_data, error_response, status_code = validate_request(UpdateOrderWeightsSchema)
    if error_response:
        return error_response, status_code
    
    items_data = validated_data['items']
    
    try:
        order = Order.query.filter(Order.id == order_id, Order.deleted_at.is_(None)).first_or_404()
        
        # Check if order is ready for pickup
        if order.status != OrderStatus.READY_FOR_PICKUP.value:
            return jsonify({'error': 'Order must be in ready_for_pickup status to update weights'}), 400
        
        # Create a map of item_id to final_weight for quick lookup
        weight_updates = {item.get('item_id'): item.get('final_weight') for item in items_data if item.get('item_id')}
        
        # Update items with final weights and recalculate prices
        for item_update in items_data:
            item_id = item_update.get('item_id')
            final_weight = item_update.get('final_weight')
            
            if not item_id:
                continue
            
            order_item = OrderItem.query.filter_by(id=item_id, order_id=order_id).first()
            if not order_item:
                continue
            
            product = Product.query.get(order_item.product_id)
            if not product:
                continue
            
            # Update final weight
            if final_weight is not None:
                order_item.final_weight = float(final_weight)
            
            # Recalculate price if product is weight-based
            if product.pricing_type in ['weight_range', 'unit_weight'] and final_weight is not None:
                # Calculate new price based on final weight
                new_price = product.calculate_price(quantity=order_item.quantity, weight=float(final_weight))
                if new_price is not None:
                    order_item.unit_price = new_price / order_item.quantity
                    order_item.total_price = new_price
        
        # Recalculate subtotal from ALL items in the order (not just updated ones)
        subtotal = 0
        for order_item in order.items:
            subtotal += float(order_item.total_price)
        
        # Recalculate order totals
        tax = 0
        total = subtotal + tax
        points_earned = int(total * 100)  # 1 point per cent
        
        order.subtotal = subtotal
        order.tax = tax
        order.total = total
        order.points_earned = points_earned
        
        db.session.commit()
        
        current_app.logger.info(f'Updated weights and prices for order {order_id}')
        
        # Return updated order
        order_dict = order.to_dict()
        
        # Get user info
        user = User.query.get(order.user_id)
        if user:
            order_dict['user'] = user.to_dict()
        
        # Get group deal info (excluding soft-deleted)
        group_deal = GroupDeal.query.filter(
            GroupDeal.id == order.group_deal_id,
            GroupDeal.deleted_at.is_(None)
        ).first()
        if group_deal:
            order_dict['group_deal'] = group_deal.to_dict()
        
        # Get order items with product details
        items_data_response = []
        for item in order.items:
            item_dict = item.to_dict()
            product = Product.query.get(item.product_id)
            if product:
                item_dict['product'] = product.to_dict()
            items_data_response.append(item_dict)
        
        order_dict['items'] = items_data_response
        
        return jsonify({
            'message': 'Order weights and prices updated successfully',
            'order': order_dict
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating order weights: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to update order weights',
            'message': str(e)
        }), 500

@admin_bp.route('/orders/<int:order_id>/update', methods=['PUT'])
def update_admin_order(order_id):
    """Update order items (add/remove items, update weights) - admin only"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    # Validate request data using schema
    validated_data, error_response, status_code = validate_request(AdminUpdateOrderSchema)
    if error_response:
        return error_response, status_code
    
    items_data = validated_data['items']
    payment_method = validated_data.get('payment_method', '').strip() if validated_data.get('payment_method') else None
    
    try:
        order = Order.query.filter(Order.id == order_id, Order.deleted_at.is_(None)).first_or_404()
        
        # Get group deal for pricing (excluding soft-deleted)
        group_deal = GroupDeal.query.filter(
            GroupDeal.id == order.group_deal_id,
            GroupDeal.deleted_at.is_(None)
        ).first()
        if not group_deal:
            return jsonify({'error': 'Group deal not found'}), 404
        
        # Delete all existing order items
        OrderItem.query.filter_by(order_id=order_id).delete()
        
        # Calculate new order totals
        subtotal = 0
        new_order_items = []
        
        for item_data in items_data:
            product_id = item_data.get('product_id')
            quantity = item_data.get('quantity', 1)
            final_weight = item_data.get('final_weight')
            
            if not product_id:
                continue
            
            if quantity <= 0:
                continue
            
            # Get product
            product = Product.query.get(product_id)
            if not product:
                continue
            
            # Get group deal specific price (if set for this deal)
            deal_product = GroupDealProduct.query.filter_by(
                group_deal_id=order.group_deal_id,
                product_id=product_id
            ).first()
            
            # Calculate item price
            if final_weight is not None and product.pricing_type in ['weight_range', 'unit_weight']:
                # Use final weight for price calculation
                item_price = product.calculate_price(quantity=quantity, weight=float(final_weight))
            else:
                # Use deal price if available, otherwise use product price
                if deal_product and deal_product.deal_price:
                    unit_price = float(deal_product.deal_price)
                else:
                    unit_price = float(product.price) if product.price else 0
                item_price = unit_price * quantity
            
            if item_price is None:
                item_price = 0
            
            # Create order item
            order_item = OrderItem(
                order_id=order_id,
                product_id=product_id,
                quantity=quantity,
                unit_price=item_price / quantity if quantity > 0 else 0,
                total_price=item_price,
                final_weight=float(final_weight) if final_weight is not None else None
            )
            db.session.add(order_item)
            new_order_items.append(order_item)
            subtotal += item_price
        
        # Recalculate order totals
        tax = 0
        total = subtotal + tax
        points_earned = int(total * 100)  # 1 point per cent
        
        order.subtotal = subtotal
        order.tax = tax
        order.total = total
        order.points_earned = points_earned
        
        # Update payment method if provided
        if payment_method:
            if payment_method in PaymentMethod.get_all_values():
                order.payment_method = payment_method
        
        db.session.commit()
        
        current_app.logger.info(f'Admin updated order {order_id} items')
        
        # Return updated order
        order_dict = order.to_dict()
        
        # Get user info
        user = User.query.get(order.user_id)
        if user:
            order_dict['user'] = user.to_dict()
        
        # Get group deal info
        order_dict['group_deal'] = group_deal.to_dict()
        
        # Get address info if delivery order
        if order.address_id:
            from models.address import Address
            address = Address.query.get(order.address_id)
            if address:
                order_dict['address'] = address.to_dict()
        
        # Get order items with product details
        items_data_response = []
        for item in order.items:
            item_dict = item.to_dict()
            product = Product.query.get(item.product_id)
            if product:
                item_dict['product'] = product.to_dict()
            items_data_response.append(item_dict)
        
        order_dict['items'] = items_data_response
        
        return jsonify({
            'message': 'Order updated successfully',
            'order': order_dict
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating order: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to update order',
            'message': str(e)
        }), 500

@admin_bp.route('/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    """Soft delete an order (admin only)"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        order = Order.query.filter(Order.id == order_id, Order.deleted_at.is_(None)).first_or_404()
        
        # Soft delete: set deleted_at timestamp
        order.deleted_at = utc_now()
        db.session.commit()
        
        current_app.logger.info(f'Admin soft-deleted order {order_id} (order_number: {order.order_number})')
        
        return jsonify({
            'message': 'Order deleted successfully',
            'order_id': order_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting order: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to delete order',
            'message': str(e)
        }), 500

@admin_bp.route('/group-deals/<int:deal_id>/status', methods=['PUT'])
def update_group_deal_status(deal_id):
    """Update group deal status - cascades to all orders (admin only)"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    # Validate request data using schema
    validated_data, error_response, status_code = validate_request(UpdateGroupDealStatusSchema)
    if error_response:
        return error_response, status_code
    
    new_status = validated_data['status']
    
    try:
        deal = GroupDeal.query.filter(
            GroupDeal.id == deal_id,
            GroupDeal.deleted_at.is_(None)
        ).first_or_404()
        old_status = deal.status
        deal.status = new_status
        
        # Cascade status to orders
        orders_updated = 0
        if new_status == GroupDealStatus.PREPARING.value:
            # All submitted/confirmed orders become preparing
            orders = Order.query.filter(
                Order.group_deal_id == deal_id,
                Order.status.in_([OrderStatus.SUBMITTED.value, OrderStatus.CONFIRMED.value]),
                Order.status != OrderStatus.CANCELLED.value
            ).all()
            for order in orders:
                order.status = OrderStatus.PREPARING.value
                orders_updated += 1
        
        elif new_status == GroupDealStatus.READY_FOR_PICKUP.value:
            # All submitted/confirmed/preparing orders become ready_for_pickup
            orders = Order.query.filter(
                Order.group_deal_id == deal_id,
                Order.status.in_([
                    OrderStatus.SUBMITTED.value,
                    OrderStatus.CONFIRMED.value,
                    OrderStatus.PREPARING.value
                ]),
                Order.status != OrderStatus.CANCELLED.value
            ).all()
            for order in orders:
                order.status = OrderStatus.READY_FOR_PICKUP.value
                orders_updated += 1
        
        elif new_status == GroupDealStatus.CLOSED.value:
            # All submitted orders become confirmed when group deal is closed
            # Orders that are already confirmed or beyond should not be changed
            orders = Order.query.filter(
                Order.group_deal_id == deal_id,
                Order.status == OrderStatus.SUBMITTED.value,
                Order.status != OrderStatus.CANCELLED.value
            ).all()
            for order in orders:
                order.status = OrderStatus.CONFIRMED.value
                orders_updated += 1
        
        db.session.commit()
        
        current_app.logger.info(f'Updated group deal {deal_id} status from {old_status} to {new_status}. Cascaded to {orders_updated} orders.')
        
        return jsonify({
            'message': 'Group deal status updated successfully',
            'group_deal': deal.to_dict(),
            'orders_updated': orders_updated
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating group deal status: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to update group deal status',
            'message': str(e)
        }), 500

# Supplier Management
@admin_bp.route('/suppliers', methods=['GET'])
def get_suppliers():
    """Get all suppliers"""
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
        query = Supplier.query
        
        # Apply search filter
        if search:
            search_term = f'%{search}%'
            query = query.filter(
                db.or_(
                    Supplier.name.like(search_term),
                    Supplier.contact_person.like(search_term),
                    Supplier.phone.like(search_term),
                    Supplier.email.like(search_term)
                )
            )
        
        # Apply status filter
        if status_filter == 'active':
            query = query.filter(Supplier.is_active == True)
        elif status_filter == 'inactive':
            query = query.filter(Supplier.is_active == False)
        
        # Order by creation date (newest first)
        query = query.order_by(Supplier.created_at.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        suppliers = pagination.items
        
        return jsonify({
            'suppliers': [supplier.to_dict() for supplier in suppliers],
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error fetching suppliers: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to fetch suppliers',
            'message': str(e)
        }), 500

@admin_bp.route('/suppliers/<int:supplier_id>', methods=['GET'])
def get_supplier(supplier_id):
    """Get a single supplier by ID"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        return jsonify({
            'supplier': supplier.to_dict()
        }), 200
    except Exception as e:
        current_app.logger.error(f'Error fetching supplier: {e}', exc_info=True)
        return jsonify({
            'error': 'Supplier not found',
            'message': str(e)
        }), 404

@admin_bp.route('/suppliers', methods=['POST'])
def create_supplier():
    """Create a new supplier"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    # Validate request data using schema
    validated_data, error_response, status_code = validate_request(CreateSupplierSchema)
    if error_response:
        return error_response, status_code
    
    try:
        supplier = Supplier(
            name=validated_data['name'],
            contact_person=validated_data.get('contact_person'),
            phone=validated_data.get('phone'),
            email=validated_data.get('email'),
            address=validated_data.get('address'),
            notes=validated_data.get('notes'),
            is_active=validated_data.get('is_active', True)
        )
        
        db.session.add(supplier)
        db.session.commit()
        
        current_app.logger.info(f'Created supplier: {supplier.id} - {supplier.name}')
        
        return jsonify({
            'supplier': supplier.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating supplier: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to create supplier',
            'message': str(e)
        }), 500

@admin_bp.route('/suppliers/<int:supplier_id>', methods=['PUT'])
def update_supplier(supplier_id):
    """Update an existing supplier"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    supplier = Supplier.query.get_or_404(supplier_id)
    
    # Validate request data using schema
    validated_data, error_response, status_code = validate_request(UpdateSupplierSchema)
    if error_response:
        return error_response, status_code
    
    try:
        if 'name' in validated_data:
            supplier.name = validated_data['name']
        if 'contact_person' in validated_data:
            supplier.contact_person = validated_data['contact_person']
        if 'phone' in validated_data:
            supplier.phone = validated_data['phone']
        if 'email' in validated_data:
            supplier.email = validated_data['email']
        if 'address' in validated_data:
            supplier.address = validated_data['address']
        if 'notes' in validated_data:
            supplier.notes = validated_data['notes']
        if 'is_active' in validated_data:
            supplier.is_active = validated_data['is_active']
        
        db.session.commit()
        
        current_app.logger.info(f'Updated supplier: {supplier.id} - {supplier.name}')
        
        return jsonify({
            'supplier': supplier.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating supplier: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to update supplier',
            'message': str(e)
        }), 500

@admin_bp.route('/suppliers/<int:supplier_id>', methods=['DELETE'])
def delete_supplier(supplier_id):
    """Delete a supplier (soft delete by setting is_active=False)"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    supplier = Supplier.query.get_or_404(supplier_id)
    
    try:
        # Soft delete - set is_active to False
        supplier.is_active = False
        db.session.commit()
        
        current_app.logger.info(f'Deleted supplier: {supplier.id} - {supplier.name}')
        
        return jsonify({
            'message': 'Supplier deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting supplier: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to delete supplier',
            'message': str(e)
        }), 500

@admin_bp.route('/group-deals/<int:deal_id>/export-orders-csv', methods=['GET'])
def export_group_deal_orders_csv(deal_id):
    """Export order products for a group deal as CSV, grouped by supplier with aggregated quantities"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        # Get group deal (excluding soft-deleted)
        group_deal = GroupDeal.query.filter(
            GroupDeal.id == deal_id,
            GroupDeal.deleted_at.is_(None)
        ).first_or_404()
        
        # Get all orders for this group deal (excluding soft-deleted and cancelled)
        orders = Order.query.filter(
            Order.group_deal_id == deal_id,
            Order.deleted_at.is_(None),
            Order.status != OrderStatus.CANCELLED.value
        ).all()
        
        # Aggregate quantities by supplier and product
        # Structure: {supplier_name: {product_name: total_quantity}}
        aggregated_data = {}
        
        for order in orders:
            for item in order.items:
                product = Product.query.get(item.product_id)
                if not product:
                    continue
                
                # Get supplier (or use "No Supplier" if none)
                supplier = product.supplier
                supplier_name = supplier.name if supplier else "No Supplier"
                product_name = product.name
                
                # Initialize nested dicts if needed
                if supplier_name not in aggregated_data:
                    aggregated_data[supplier_name] = {}
                
                if product_name not in aggregated_data[supplier_name]:
                    aggregated_data[supplier_name][product_name] = 0
                
                # Aggregate quantity
                aggregated_data[supplier_name][product_name] += item.quantity
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Supplier',
            'Product Name',
            'Total Quantity'
        ])
        
        # Sort suppliers alphabetically
        sorted_suppliers = sorted(aggregated_data.keys())
        
        # Write data grouped by supplier
        for supplier_name in sorted_suppliers:
            products = aggregated_data[supplier_name]
            # Sort products alphabetically
            sorted_products = sorted(products.items())
            
            for product_name, total_quantity in sorted_products:
                writer.writerow([
                    supplier_name,
                    product_name,
                    total_quantity
                ])
        
        # Get CSV content
        csv_content = output.getvalue()
        output.close()
        
        # Create response with CSV
        response = Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=group_deal_{deal_id}_orders_by_supplier.csv'
            }
        )
        
        current_app.logger.info(f'Exported CSV for group deal {deal_id} with {len(orders)} orders')
        
        return response, 200
        
    except Exception as e:
        current_app.logger.error(f'Error exporting CSV: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to export CSV',
            'message': str(e)
        }), 500

@admin_bp.route('/group-deals/<int:deal_id>/export-delivery-csv', methods=['GET'])
def export_group_deal_delivery_csv(deal_id):
    """Export delivery orders for a group deal as CSV with delivery info and contact"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        # Get group deal (excluding soft-deleted)
        group_deal = GroupDeal.query.filter(
            GroupDeal.id == deal_id,
            GroupDeal.deleted_at.is_(None)
        ).first_or_404()
        
        # Get all delivery orders for this group deal (excluding soft-deleted and cancelled)
        orders = Order.query.filter(
            Order.group_deal_id == deal_id,
            Order.delivery_method == 'delivery',
            Order.deleted_at.is_(None),
            Order.status != OrderStatus.CANCELLED.value
        ).all()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Order Number',
            'Recipient Name',
            'Phone',
            'Email',
            'Address Line 1',
            'Address Line 2',
            'City',
            'Postal Code',
            'Country',
            'Delivery Instructions',
            'Total Amount',
            'Payment Status',
            'Order Status',
            'Items Count'
        ])
        
        # Write order data
        for order in orders:
            # Get user info
            user = User.query.get(order.user_id)
            
            # Get address info
            address = None
            if order.address_id:
                from models.address import Address
                address = Address.query.get(order.address_id)
            
            # Build address fields
            recipient_name = address.recipient_name if address else (user.nickname if user else 'N/A')
            phone = address.phone if address else (user.phone if user else '')
            email = address.notification_email if address and address.notification_email else (user.email if user else '')
            address_line1 = address.address_line1 if address else ''
            address_line2 = address.address_line2 if address else ''
            city = address.city if address else ''
            postal_code = address.postal_code if address else ''
            country = address.country if address else 'Canada'
            delivery_instructions = address.delivery_instructions if address else ''
            
            writer.writerow([
                order.order_number,
                recipient_name,
                phone,
                email,
                address_line1,
                address_line2,
                city,
                postal_code,
                country,
                delivery_instructions,
                f"{float(order.total) if order.total else 0:.2f}",
                order.payment_status,
                order.status,
                len(order.items)
            ])
        
        # Get CSV content
        csv_content = output.getvalue()
        output.close()
        
        # Create response with CSV
        response = Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=group_deal_{deal_id}_delivery_orders.csv'
            }
        )
        
        current_app.logger.info(f'Exported delivery CSV for group deal {deal_id} with {len(orders)} delivery orders')
        
        return response, 200
        
    except Exception as e:
        current_app.logger.error(f'Error exporting delivery CSV: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to export delivery CSV',
            'message': str(e)
        }), 500

