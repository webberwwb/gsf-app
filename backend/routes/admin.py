from flask import Blueprint, jsonify, request, current_app, Response
from models import db
from models.product import Product
from models.product_category import ProductCategory
from models.user import User, AuthToken, UserRole
from models.groupdeal import GroupDeal, GroupDealProduct
from models.otp_attempt import OTPAttempt
from models.supplier import Supplier
from models.order import Order, OrderItem
from models.address import Address
from models.product_sales_stats import ProductSalesStats
from models.delivery_fee_config import DeliveryFeeConfig
from models.sdr import SDR, CommissionRule, CommissionRecord, QuarterlyBonus
from models.customer_feedback import CustomerFeedback, FeedbackContext, FeedbackOutcome
from models.work_document import WorkDocument, ActionItem
from models.base import utc_now, est_now
from utils.sales_stats import update_product_sales_stats, get_product_sales_by_date_range, get_popular_products
from utils.product_repurchase import compute_product_repurchase_rates
from utils.date_helpers import normalize_date_start, normalize_date_end
from utils.commission import calculate_commission_for_group_deal, get_commission_summary_for_group_deal
from datetime import datetime, timedelta, timezone, date
from config import Config
from constants.status_enums import OrderStatus, PaymentStatus, GroupDealStatus, UserStatus, PaymentMethod, DeliveryMethod
from schemas.product import CreateProductSchema, UpdateProductSchema, BulkUpdateSortOrderSchema
from schemas.product_category import CreateProductCategorySchema, UpdateProductCategorySchema, BulkUpdateCategorySortOrderSchema
from schemas.groupdeal import CreateGroupDealSchema, UpdateGroupDealSchema, UpdateGroupDealStatusSchema
from schemas.admin import CreateSupplierSchema, UpdateSupplierSchema, AssignRoleSchema, UpdateOrderStatusSchema, UpdateOrderPaymentSchema, MergeOrdersSchema, UpdateDeliveryFeeConfigSchema, UpdateUserSchema
from schemas.work_document import CreateWorkDocumentSchema, UpdateWorkDocumentSchema, CreateActionItemSchema, UpdateActionItemSchema
from schemas.order import (
    UpdateOrderWeightsSchema,
    AdminUpdateOrderSchema,
    AdminOrderItemAvailabilitySchema,
    AdminOrderItemSubstituteSchema,
    AdminProductFulfillmentSchema,
)
from utils.order_item_pricing import (
    priced_items_from_request,
    create_order_item_rows,
    enrich_order_item_dict,
    combine_order_notes,
    order_item_fields_for_merge,
    recalculate_existing_item,
    bulk_set_product_fulfillment,
    apply_product_substitute_fields,
    sync_product_variants,
)
from utils.order_audit import (
    EVENT_ADMIN_ITEMS_REPLACE,
    EVENT_MERGE,
    active_items_for_order,
    apply_item_sources_from_request,
    build_order_audit_trail,
    item_snapshot,
    record_order_audit,
)
from utils.order_totals import sync_order_pricing
from utils.order_points import award_order_points, revoke_order_points
from schemas.utils import validate_request
from urllib.parse import quote
import os
import uuid
import secrets
from werkzeug.utils import secure_filename
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import joinedload, selectinload
from decimal import Decimal
from utils.shipping import calculate_shipping_fee
from utils.stock_management import restore_stock
import csv
import io
from models.credit_transaction import CreditTransaction
from models.referral_program import ReferralProgramConfig, ReferralRecord
from services import credit_service
from services import referral_service

# Optional imports for image upload
try:
    from google.cloud import storage
    from google.oauth2 import service_account
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    storage = None
    service_account = None

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

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
    
    # Refresh token expiration on each use (extend to 100 years from now)
    # Token effectively never expires
    # Make sure expires_at is stored as naive datetime (MySQL doesn't support timezone-aware)
    new_expires_at = utc_now() + timedelta(days=36500)  # 100 years
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
        
        # Handle stock_limit: explicitly preserve 0 value (0 means out of stock, None means unlimited)
        stock_limit_value = validated_data.get('stock_limit')
        if stock_limit_value is None or stock_limit_value == '':
            final_stock_limit = None
        else:
            final_stock_limit = int(stock_limit_value)  # Convert to int, preserving 0
        
        product = Product(
            name=validated_data['name'],
            image=validated_data.get('image'),  # Keep for backward compatibility
            images=images,  # New multiple images array
            pricing_type=validated_data['pricing_type'],
            pricing_data=validated_data['pricing_data'],
            description=validated_data.get('description', ''),
            stock_limit=final_stock_limit,
            is_active=validated_data.get('is_active', True),
            supplier_id=validated_data.get('supplier_id'),
            category_id=validated_data.get('category_id'),
            counts_toward_free_shipping=validated_data.get('counts_toward_free_shipping', True)
        )
        apply_product_substitute_fields(product, validated_data)
        
        db.session.add(product)
        db.session.flush()
        sync_product_variants(product, validated_data.get('variants'))
        db.session.commit()
        
        current_app.logger.info(f'Created product: {product.id} - {product.name}')
        
        return jsonify({
            'product': product.to_dict(include_all_variants=True)
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
            # Explicitly handle 0 as a valid value (out of stock)
            # None means unlimited stock, 0 means out of stock
            stock_limit_value = validated_data['stock_limit']
            if stock_limit_value is None or stock_limit_value == '':
                product.stock_limit = None
            else:
                product.stock_limit = int(stock_limit_value)  # Convert to int, preserving 0
        if 'is_active' in validated_data:
            product.is_active = validated_data['is_active']
        if 'supplier_id' in validated_data:
            product.supplier_id = validated_data['supplier_id'] if validated_data['supplier_id'] else None
        if 'category_id' in validated_data:
            product.category_id = validated_data['category_id'] if validated_data['category_id'] else None
        if 'counts_toward_free_shipping' in validated_data:
            product.counts_toward_free_shipping = validated_data['counts_toward_free_shipping']
        apply_product_substitute_fields(product, validated_data)
        if 'variants' in validated_data:
            sync_product_variants(product, validated_data.get('variants'))
        
        db.session.commit()
        
        current_app.logger.info(f'Updated product: {product.id} - {product.name}')
        
        return jsonify({
            'product': product.to_dict(include_all_variants=True)
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

@admin_bp.route('/products/sort-order', methods=['PUT'])
def update_product_sort_orders():
    """Update product sort orders in bulk"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        # Validate request data
        schema = BulkUpdateSortOrderSchema()
        data = schema.load(request.json)
        
        # Update each product's sort_order
        updated_count = 0
        for item in data['products']:
            product = Product.query.get(item['product_id'])
            if product:
                product.sort_order = item['sort_order']
                updated_count += 1
        
        db.session.commit()
        
        current_app.logger.info(f'Updated sort order for {updated_count} products')
        
        return jsonify({
            'message': f'Successfully updated sort order for {updated_count} products',
            'updated_count': updated_count
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'error': 'Invalid request data',
            'message': str(e.messages)
        }), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating product sort orders: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to update product sort orders',
            'message': str(e)
        }), 500

# ===== Product Category Routes =====

@admin_bp.route('/product-categories', methods=['GET'])
def get_product_categories():
    """Get all product categories"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        # Get query parameters
        sort = request.args.get('sort', 'custom')  # 'custom' or 'name'
        
        # Build query
        query = ProductCategory.query
        
        # Apply sorting
        if sort == 'name':
            query = query.order_by(ProductCategory.name.asc())
        else:  # default to custom sort order
            query = query.order_by(ProductCategory.sort_order.asc(), ProductCategory.created_at.asc())
        
        categories = query.all()
        
        return jsonify({
            'categories': [category.to_dict() for category in categories]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error getting product categories: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to get product categories',
            'message': str(e)
        }), 500

@admin_bp.route('/product-categories', methods=['POST'])
def create_product_category():
    """Create a new product category"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    # Validate request data using schema
    validated_data, error_response, status_code = validate_request(CreateProductCategorySchema)
    if error_response:
        return error_response, status_code
    
    try:
        category = ProductCategory(
            name=validated_data['name'],
            description=validated_data.get('description', ''),
            is_active=validated_data.get('is_active', True),
            sort_order=validated_data.get('sort_order', 0)
        )
        
        db.session.add(category)
        db.session.commit()
        
        current_app.logger.info(f'Created product category: {category.id} - {category.name}')
        
        return jsonify({
            'category': category.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating product category: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to create product category',
            'message': str(e)
        }), 500

@admin_bp.route('/product-categories/<int:category_id>', methods=['PUT'])
def update_product_category(category_id):
    """Update an existing product category"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    category = ProductCategory.query.get_or_404(category_id)
    
    # Validate request data using schema
    validated_data, error_response, status_code = validate_request(UpdateProductCategorySchema)
    if error_response:
        return error_response, status_code
    
    try:
        if 'name' in validated_data:
            category.name = validated_data['name']
        if 'description' in validated_data:
            category.description = validated_data['description']
        if 'is_active' in validated_data:
            category.is_active = validated_data['is_active']
        if 'sort_order' in validated_data:
            category.sort_order = validated_data['sort_order']
        
        db.session.commit()
        
        current_app.logger.info(f'Updated product category: {category.id} - {category.name}')
        
        return jsonify({
            'category': category.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating product category: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to update product category',
            'message': str(e)
        }), 500

@admin_bp.route('/product-categories/<int:category_id>', methods=['DELETE'])
def delete_product_category(category_id):
    """Delete a product category (soft delete by setting is_active=False)"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    category = ProductCategory.query.get_or_404(category_id)
    
    try:
        # Soft delete - set is_active to False
        category.is_active = False
        db.session.commit()
        
        current_app.logger.info(f'Deleted product category: {category.id} - {category.name}')
        
        return jsonify({
            'message': 'Product category deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting product category: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to delete product category',
            'message': str(e)
        }), 500

@admin_bp.route('/product-categories/sort-order', methods=['PUT'])
def update_category_sort_orders():
    """Update product category sort orders in bulk"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        # Validate request data
        schema = BulkUpdateCategorySortOrderSchema()
        data = schema.load(request.json)
        
        # Update each category's sort_order
        updated_count = 0
        for item in data['categories']:
            category = ProductCategory.query.get(item['category_id'])
            if category:
                category.sort_order = item['sort_order']
                updated_count += 1
        
        db.session.commit()
        
        current_app.logger.info(f'Updated sort order for {updated_count} product categories')
        
        return jsonify({
            'message': f'Successfully updated sort order for {updated_count} product categories',
            'updated_count': updated_count
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'error': 'Invalid request data',
            'message': str(e.messages)
        }), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating product category sort orders: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to update product category sort orders',
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
        role_filter = request.args.get('role', '').strip()
        
        # Build query
        query = User.query
        
        # Apply role filter (e.g., 'admin')
        if role_filter:
            from models.user import UserRole
            query = query.join(UserRole).filter(UserRole.role == role_filter)
        
        # Apply search filter
        if search:
            search_term = f'%{search}%'
            search_conds = [
                User.phone.like(search_term),
                User.nickname.like(search_term),
                User.email.like(search_term),
                User.wechat.like(search_term),
            ]
            if search.isdigit():
                try:
                    uid = int(search)
                    if uid > 0:
                        search_conds.append(User.id == uid)
                except ValueError:
                    pass
            query = query.filter(db.or_(*search_conds))
        
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

@admin_bp.route('/users/<int:user_id>', methods=['PATCH'])
def update_user(user_id):
    """Update user information (admin only)"""
    admin_user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        user = User.query.get_or_404(user_id)
        
        # Validate request data
        errors = validate_request(UpdateUserSchema, request.json)
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        data = request.json
        
        # Update fields if provided
        if 'phone' in data:
            # Check if phone is already taken by another user
            if data['phone'] and data['phone'] != user.phone:
                existing = User.query.filter_by(phone=data['phone']).first()
                if existing and existing.id != user_id:
                    return jsonify({'error': 'Phone number already in use'}), 400
            user.phone = data['phone']
        
        if 'nickname' in data:
            user.nickname = data['nickname']
        
        if 'email' in data:
            # Check if email is already taken by another user
            if data['email'] and data['email'] != user.email:
                existing = User.query.filter_by(email=data['email']).first()
                if existing and existing.id != user_id:
                    return jsonify({'error': 'Email already in use'}), 400
            user.email = data['email']
        
        if 'wechat' in data:
            user.wechat = data['wechat']
        
        if 'points' in data:
            user.points = data['points']
        
        if 'user_source' in data:
            user.user_source = data['user_source']
        
        if 'status' in data:
            user.status = data['status']
        
        db.session.commit()
        
        current_app.logger.info(f'Admin {admin_user_id} updated user {user_id}')
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating user: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to update user',
            'message': str(e)
        }), 500

@admin_bp.route('/users/<int:user_id>/impersonate', methods=['POST'])
def impersonate_user(user_id):
    """Generate a token for a user to allow admin to impersonate them"""
    admin_user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        target_user = User.query.get_or_404(user_id)
        
        # Check if user is active
        if not target_user.is_active:
            return jsonify({
                'error': 'Cannot impersonate inactive user'
            }), 400
        
        # Generate new auth token for the target user (100 years expiration - effectively never expires)
        expires_at = utc_now() + timedelta(days=36500)  # 100 years
        auth_token = AuthToken(
            user_id=target_user.id,
            token=secrets.token_urlsafe(32),
            token_type='bearer',
            expires_at=expires_at
        )
        db.session.add(auth_token)
        db.session.commit()
        
        # Get app frontend URL from config
        app_frontend_url = Config.APP_FRONTEND_URL
        
        # Handle local development
        is_production = os.environ.get('K_SERVICE') is not None
        if not is_production:
            # In local development, use localhost if APP_FRONTEND_URL is not set or is production URL
            if not app_frontend_url or 'grainstoryfarm.ca' in app_frontend_url:
                app_frontend_url = 'http://localhost:3000'  # App frontend dev server port
                current_app.logger.info(f'Using default localhost URL for local development: {app_frontend_url}')
        
        current_app.logger.info(f'Admin {admin_user_id} impersonating user {user_id}, token: {auth_token.token[:10]}...')
        
        # Return token and redirect URL
        return jsonify({
            'token': auth_token.token,
            'user': target_user.to_dict(),
            'redirect_url': f'{app_frontend_url}/login#token={auth_token.token}',
            'expires_at': auth_token.expires_at.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error impersonating user: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to impersonate user',
            'message': str(e)
        }), 500

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

@admin_bp.route('/users/bulk-assign-source', methods=['POST'])
def bulk_assign_user_source():
    """Bulk assign user source to multiple users (admin only)"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_ids = data.get('user_ids', [])
        user_source = data.get('user_source', '').strip()
        
        if not user_ids:
            return jsonify({'error': 'user_ids is required'}), 400
        
        if not user_source:
            return jsonify({'error': 'user_source is required'}), 400
        
        # Validate user_source (should be "花泽" or "default")
        if user_source not in ['花泽', 'default']:
            return jsonify({'error': f'Invalid user_source: {user_source}. Must be "花泽" or "default"'}), 400
        
        # Get users to update
        users = User.query.filter(User.id.in_(user_ids)).all()
        
        if not users:
            return jsonify({
                'message': 'No users found',
                'updated_count': 0
            }), 200
        
        # Update all users
        updated_count = 0
        for user in users:
            user.user_source = user_source
            user.updated_at = utc_now()
            updated_count += 1
            current_app.logger.info(f'Bulk updated user {user.id} source to {user_source}')
        
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully updated {updated_count} users source to {user_source}',
            'updated_count': updated_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error bulk updating user source: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to bulk update user source',
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

@admin_bp.route('/users/<int:user_id>/addresses', methods=['GET'])
def get_user_addresses(user_id):
    """Get user addresses"""
    admin_user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code

    try:
        user = User.query.get_or_404(user_id)
        # Address model doesn't have soft delete (is_deleted field), so just filter by user_id
        addresses = Address.query.filter_by(user_id=user.id).order_by(Address.created_at.desc()).all()
        
        return jsonify({
            'addresses': [address.to_dict() for address in addresses]
        }), 200
    except Exception as e:
        current_app.logger.error(f'Error fetching user addresses: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to fetch user addresses',
            'message': str(e)
        }), 500

@admin_bp.route('/users/<int:user_id>/addresses', methods=['POST'])
def create_user_address(user_id):
    """Create a new address for a user"""
    admin_user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code

    try:
        user = User.query.get_or_404(user_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['recipient_name', 'phone', 'address_line1', 'city', 'postal_code']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create new address
        address = Address(
            user_id=user.id,
            recipient_name=data['recipient_name'],
            phone=data['phone'],
            address_line1=data['address_line1'],
            address_line2=data.get('address_line2', ''),
            city=data['city'],
            postal_code=data['postal_code'],
            country=data.get('country', 'Canada'),
            delivery_instructions=data.get('delivery_instructions'),
            notification_email=data.get('notification_email'),
            is_default=data.get('is_default', False)
        )
        
        db.session.add(address)
        db.session.commit()
        
        current_app.logger.info(f'Admin {admin_user_id} created address {address.id} for user {user.id}')
        
        return jsonify({
            'message': 'Address created successfully',
            'address': address.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating user address: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to create address',
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
        
        # Get all deal IDs to fetch products in bulk
        deal_ids = [deal.id for deal in deals]
        
        # Fetch all GroupDealProducts for these deals in one query with eager loading
        from sqlalchemy.orm import joinedload
        deal_products_query = GroupDealProduct.query.options(
            joinedload(GroupDealProduct.product).joinedload(Product.category),
            joinedload(GroupDealProduct.product).joinedload(Product.supplier)
        ).filter(GroupDealProduct.group_deal_id.in_(deal_ids))
        
        deal_products_all = deal_products_query.all()
        
        # Group products by deal_id
        products_by_deal = {}
        for dp in deal_products_all:
            if dp.group_deal_id not in products_by_deal:
                products_by_deal[dp.group_deal_id] = []
            
            if dp.product:
                product_dict = dp.product.to_dict()
                product_dict['deal_stock_limit'] = dp.deal_stock_limit
                product_dict['group_deal_product_id'] = dp.id
                products_by_deal[dp.group_deal_id].append(product_dict)
        
        # Include products for each deal
        deals_data = []
        for deal in deals:
            deal_dict = deal.to_dict()
            deal_dict['products'] = products_by_deal.get(deal.id, [])
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
        
        # Products for this deal (single query + joinedload — avoid N+1 Product.query.get per row)
        deal_products = GroupDealProduct.query.options(
            joinedload(GroupDealProduct.product).joinedload(Product.category),
            joinedload(GroupDealProduct.product).joinedload(Product.supplier)
        ).filter(GroupDealProduct.group_deal_id == deal.id).all()
        products_data = []
        for dp in deal_products:
            if dp.product:
                product_dict = dp.product.to_dict()
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
            # Restore stock if order is not already cancelled (cancelled orders already had stock restored)
            if order.status != OrderStatus.CANCELLED.value:
                items_to_restore = [{'product_id': item.product_id, 'quantity': item.quantity} for item in order.items]
                try:
                    restore_stock(order.group_deal_id, items_to_restore)
                    current_app.logger.info(f'Restored stock for order {order.id} when deleting group deal {deal_id}')
                except Exception as e:
                    current_app.logger.error(f'Failed to restore stock for order {order.id} when deleting group deal {deal_id}: {e}')
                    # Continue with deletion even if stock restoration fails
            
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
        sort_by = request.args.get('sort', 'custom')  # 'custom', 'created_at', 'popularity', 'name'
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
        elif sort_by == 'custom':
            query = query.order_by(Product.sort_order.asc(), Product.created_at.desc())
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

def _build_admin_order_dict(order):
    """Full order payload for admin modal refresh after partial line updates."""
    order_dict = order.to_dict()
    user = User.query.get(order.user_id)
    if user:
        order_dict['user'] = user.to_dict()
    group_deal = GroupDeal.query.filter(
        GroupDeal.id == order.group_deal_id,
        GroupDeal.deleted_at.is_(None),
    ).first()
    if group_deal:
        order_dict['group_deal'] = group_deal.to_dict()
    if order.address_id:
        address = Address.query.get(order.address_id)
        if address:
            order_dict['address'] = address.to_dict()
    order_dict['items'] = [enrich_order_item_dict(i) for i in order.items]
    return order_dict


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
        user_source_filter = request.args.get('user_source', '').strip()
        search = request.args.get('search', '').strip()
        
        # Build query - join with User for phone search and eager load relationships
        # Filter out soft-deleted orders (deleted_at IS NULL)
        # Use eager loading to prevent N+1 queries
        query = Order.query.options(
            joinedload(Order.user),  # Eager load user (already joined)
            selectinload(Order.items).selectinload(OrderItem.product),  # Eager load items and their products
            selectinload(Order.address),  # Eager load address if exists
            joinedload(Order.group_deal)  # Eager load group deal (many-to-one via backref)
        ).join(User, Order.user_id == User.id).filter(Order.deleted_at.is_(None))
        
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
        
        if user_source_filter:
            query = query.filter(User.user_source == user_source_filter)
        
        # Order by creation date (newest first)
        query = query.order_by(Order.created_at.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        orders = pagination.items
        
        # Build response with order details (all relationships already loaded)
        orders_data = []
        for order in orders:
            order_dict = order.to_dict()
            
            # Get user info (already loaded via joinedload)
            if order.user:
                order_dict['user'] = {
                    'id': order.user.id,
                    'nickname': order.user.nickname,
                    'phone': order.user.phone,
                    'email': order.user.email,
                    'wechat': order.user.wechat,
                    'user_source': order.user.user_source or 'default'
                }
            
            # Get group deal info (already loaded via joinedload)
            if order.group_deal and order.group_deal.deleted_at is None:
                order_dict['group_deal'] = {
                    'id': order.group_deal.id,
                    'title': order.group_deal.title,
                    'pickup_date': order.group_deal.pickup_date.isoformat() if order.group_deal.pickup_date else None
                }
            
            # Get address info (already loaded via selectinload)
            if order.address:
                order_dict['address'] = order.address.to_dict()
            
            items_data = [
                enrich_order_item_dict(item, item.product) for item in order.items
            ]
            order_dict['items'] = items_data
            order_dict['items_count'] = len(items_data)
            
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
        
        order_dict['items'] = [enrich_order_item_dict(item) for item in order.items]
        
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
        old_payment_status = order.payment_status
        
        # If changing status to cancelled, restore stock
        if status == OrderStatus.CANCELLED.value and old_status != OrderStatus.CANCELLED.value:
            items_to_restore = [{'product_id': item.product_id, 'quantity': item.quantity} for item in order.items]
            try:
                restore_stock(order.group_deal_id, items_to_restore)
            except Exception as e:
                current_app.logger.error(f'Failed to restore stock when changing order status to cancelled: {e}')
                # Continue with status change even if stock restoration fails
        
        order.status = status
        
        # For pickup orders with cash payment: auto-mark as paid when completing
        if (status == OrderStatus.COMPLETED.value and 
            order.delivery_method == DeliveryMethod.PICKUP.value and 
            order.payment_method == PaymentMethod.CASH.value and
            old_payment_status == PaymentStatus.UNPAID.value):
            
            order.payment_status = PaymentStatus.PAID.value
            user = User.query.get(order.user_id)
            points_awarded = award_order_points(order, user)
            order.payment_date = utc_now()
            if user:
                current_app.logger.info(f'Awarded {points_awarded} points to user {user.id} for order {order_id}')

            current_app.logger.info(f'Auto-marked pickup cash order {order_id} as paid when completing')
        
        points_awarded = 0
        points_notice = None
        if (
            status == OrderStatus.COMPLETED.value
            and order.payment_status == PaymentStatus.UNPAID.value
            and old_status != OrderStatus.COMPLETED.value
        ):
            points_notice = (
                'Order completed but payment is still unpaid; loyalty points are awarded when marked paid.'
            )

        referral_service.on_order_first_completed(order, old_status)
        
        db.session.commit()
        
        current_app.logger.info(f'Updated order {order_id} status from {old_status} to {status}')
        
        # Build response with user info
        order_dict = order.to_dict()
        
        # Get user info
        user = User.query.get(order.user_id)
        if user:
            order_dict['user'] = {
                'id': user.id,
                'nickname': user.nickname,
                'phone': user.phone,
                'email': user.email,
                'wechat': user.wechat,
                'is_admin': user.is_admin
            }
        
        payload = {
            'message': 'Order status updated successfully',
            'order': order_dict,
            'points_awarded': points_awarded,
        }
        if points_notice:
            payload['points_notice'] = points_notice
        return jsonify(payload), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating order status: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to update order status',
            'message': str(e)
        }), 500

@admin_bp.route('/orders/bulk-update-status', methods=['POST'])
def bulk_update_order_status():
    """Bulk update order status for multiple orders (admin only)"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        new_status = data.get('status')
        group_deal_id = data.get('group_deal_id')
        delivery_method = data.get('delivery_method')
        current_status = data.get('current_status')
        
        if not new_status:
            return jsonify({'error': 'Status is required'}), 400
        
        # Validate status
        if new_status not in OrderStatus.get_all_values():
            return jsonify({'error': f'Invalid status: {new_status}'}), 400
        
        # Build query for orders to update
        query = Order.query.filter(Order.deleted_at.is_(None))
        
        # Apply filters
        if group_deal_id:
            query = query.filter(Order.group_deal_id == group_deal_id)
        
        if delivery_method:
            query = query.filter(Order.delivery_method == delivery_method)
        
        if current_status:
            query = query.filter(Order.status == current_status)
        else:
            # If no specific current status is provided, exclude orders that are already in final states
            # Don't update orders that are already out_for_delivery, completed, or cancelled
            query = query.filter(Order.status.notin_([
                OrderStatus.OUT_FOR_DELIVERY.value,
                OrderStatus.COMPLETED.value,
                OrderStatus.CANCELLED.value
            ]))
        
        # Get orders to update
        orders = query.all()
        
        if not orders:
            return jsonify({
                'message': 'No orders found matching the criteria',
                'updated_count': 0
            }), 200
        
        # Update all orders
        updated_count = 0
        for order in orders:
            old_status = order.status
            order.status = new_status
            order.updated_at = utc_now()
            referral_service.on_order_first_completed(order, old_status)
            updated_count += 1
            current_app.logger.info(f'Bulk updated order {order.id} status from {old_status} to {new_status}')
        
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully updated {updated_count} orders to {OrderStatus.get_label(new_status)}',
            'updated_count': updated_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error bulk updating order status: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to bulk update order status',
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
        
        # Restore stock for cancelled order
        items_to_restore = [{'product_id': item.product_id, 'quantity': item.quantity} for item in order.items]
        try:
            restore_stock(order.group_deal_id, items_to_restore)
        except Exception as e:
            current_app.logger.error(f'Failed to restore stock on admin cancellation: {e}')
            # Continue with cancellation even if stock restoration fails
        
        old_status = order.status
        user_row = User.query.get(order.user_id)
        if user_row:
            credit_service.refund_order_store_credit(order, user_row)
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
        
        old_order_status = order.status
        old_payment_status = order.payment_status
        order.payment_status = payment_status
        
        if payment_method:
            order.payment_method = payment_method
        
        points_awarded = 0
        # If changing from unpaid to paid, calculate points and complete order
        if old_payment_status == PaymentStatus.UNPAID.value and payment_status == PaymentStatus.PAID.value:
            user = User.query.get(order.user_id)
            points_awarded = award_order_points(order, user)
            order.payment_date = utc_now()
            if user:
                current_app.logger.info(f'Awarded {points_awarded} points to user {user.id} for order {order_id}')
            
            # Auto-complete the order for pickup cash orders
            if order.delivery_method == DeliveryMethod.PICKUP.value and order.payment_method == PaymentMethod.CASH.value:
                order.status = OrderStatus.COMPLETED.value
                current_app.logger.info(f'Pickup cash order {order_id} marked as paid and auto-completed. Points: {points_awarded}')
            else:
                # For other orders, also auto-complete (existing behavior)
                order.status = OrderStatus.COMPLETED.value
                current_app.logger.info(f'Order {order_id} marked as paid and completed. Points: {points_awarded}')
        elif old_payment_status == PaymentStatus.PAID.value and payment_status == PaymentStatus.UNPAID.value:
            user = User.query.get(order.user_id)
            revoked = revoke_order_points(order, user)
            if user and revoked:
                current_app.logger.info(f'Revoked {revoked} points from user {user.id} for order {order_id}')
        
        referral_service.on_order_first_completed(order, old_order_status)
        
        db.session.commit()
        
        # Build response with user info
        order_dict = order.to_dict()
        
        # Get user info
        user = User.query.get(order.user_id)
        if user:
            order_dict['user'] = {
                'id': user.id,
                'nickname': user.nickname,
                'phone': user.phone,
                'email': user.email,
                'wechat': user.wechat,
                'is_admin': user.is_admin
            }
        
        return jsonify({
            'message': 'Payment status updated successfully',
            'order': order_dict,
            'points_awarded': points_awarded if payment_status == PaymentStatus.PAID.value else 0
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating payment status: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to update payment status',
            'message': str(e)
        }), 500

@admin_bp.route('/orders/<int:order_id>/adjustment', methods=['PUT'])
def update_order_adjustment(order_id):
    """Update order adjustments (discount and manual adjustment)"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        order = Order.query.filter(Order.id == order_id, Order.deleted_at.is_(None)).first_or_404()
        
        data = request.get_json()
        
        # Update adjustment amount (can be positive or negative)
        if 'adjustment_amount' in data:
            # Convert to Decimal safely, handling None and empty strings
            adjustment_value = data['adjustment_amount']
            if adjustment_value is None or adjustment_value == '':
                order.adjustment_amount = Decimal('0')
            else:
                order.adjustment_amount = Decimal(str(adjustment_value))
        
        # Update adjustment notes
        if 'adjustment_notes' in data:
            order.adjustment_notes = data['adjustment_notes'] or None

        sync_order_pricing(order, reprice_lines=False)

        db.session.commit()

        current_app.logger.info(f'Updated adjustments for order {order_id}')
        
        return jsonify({
            'message': '订单调整更新成功',
            'order': order.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating order adjustment {order_id}: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to update order adjustment',
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
            
            order_item = OrderItem.get_active(item_id, order_id)
            if not order_item:
                continue
            
            product = Product.query.get(order_item.product_id)
            if not product:
                continue
            
            # Update final weight
            if final_weight is not None:
                order_item.final_weight = float(final_weight)

            recalculate_existing_item(order_item)

        sync_order_pricing(order, reprice_lines=False)

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

@admin_bp.route('/orders/<int:order_id>/audit-trail', methods=['GET'])
def get_order_audit_trail(order_id):
    """Merge history, item lineage, archived lines, and operation log for an order."""
    _, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code

    order = Order.query.filter(Order.id == order_id, Order.deleted_at.is_(None)).first()
    if not order:
        order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    trail = build_order_audit_trail(order_id)
    return jsonify(trail), 200


@admin_bp.route('/orders/<int:order_id>/update', methods=['PUT'])
def update_admin_order(order_id):
    """Update order items (add/remove items, update weights) - admin only"""
    admin_user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    # Validate request data using schema
    validated_data, error_response, status_code = validate_request(AdminUpdateOrderSchema)
    if error_response:
        return error_response, status_code
    
    items_data = validated_data['items']
    payment_method = validated_data.get('payment_method', '').strip() if validated_data.get('payment_method') else None
    delivery_method = validated_data.get('delivery_method')
    address_id = validated_data.get('address_id')
    pickup_location = validated_data.get('pickup_location')
    notes = validated_data.get('notes')
    
    try:
        order = Order.query.filter(Order.id == order_id, Order.deleted_at.is_(None)).first_or_404()
        
        # Get group deal for pricing (excluding soft-deleted)
        group_deal = GroupDeal.query.filter(
            GroupDeal.id == order.group_deal_id,
            GroupDeal.deleted_at.is_(None)
        ).first()
        if not group_deal:
            return jsonify({'error': 'Group deal not found'}), 404
        
        filtered_items = [
            i for i in items_data
            if i.get('product_id') and i.get('quantity', 1) > 0
        ]
        try:
            priced_items, subtotal = priced_items_from_request(
                filtered_items, require_variant=False
            )
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

        items_before = [
            item_snapshot(i, order.order_number) for i in active_items_for_order(order_id)
        ]
        apply_item_sources_from_request(priced_items, order_id, filtered_items)

        OrderItem.soft_delete_for_order(order_id, db.session)
        create_order_item_rows(order_id, priced_items, db.session)
        db.session.flush()

        items_after = [
            item_snapshot(i, order.order_number) for i in active_items_for_order(order_id)
        ]
        record_order_audit(
            order_id,
            EVENT_ADMIN_ITEMS_REPLACE,
            {
                'order_number': order.order_number,
                'items_before': items_before,
                'items_after': items_after,
                'request_item_count': len(filtered_items),
            },
            actor_user_id=admin_user_id,
        )

        # Update payment method if provided
        if payment_method:
            if payment_method in PaymentMethod.get_all_values():
                order.payment_method = payment_method
        
        # Update delivery method if provided
        if delivery_method:
            if delivery_method in DeliveryMethod.get_all_values():
                order.delivery_method = delivery_method
                # Clear pickup_location if switching to delivery
                if delivery_method == DeliveryMethod.DELIVERY.value:
                    order.pickup_location = None
                # Clear address_id if switching to pickup
                elif delivery_method == DeliveryMethod.PICKUP.value:
                    order.address_id = None
        
        # Determine the effective delivery method (use updated value if provided, otherwise current)
        effective_delivery_method = delivery_method if delivery_method else order.delivery_method
        
        # Update address_id if provided (only for delivery orders)
        if address_id is not None:
            if effective_delivery_method == DeliveryMethod.DELIVERY.value:
                order.address_id = address_id
        
        # Update pickup_location if provided (only for pickup orders)
        if pickup_location is not None:
            if effective_delivery_method == DeliveryMethod.PICKUP.value:
                order.pickup_location = pickup_location
        
        # Update notes if provided
        if notes is not None:
            order.notes = notes if notes else None
        
        sync_order_pricing(order)

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
        
        order_dict['items'] = [enrich_order_item_dict(item) for item in order.items]
        
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


@admin_bp.route('/orders/<int:order_id>/items/<int:item_id>/availability', methods=['PATCH'])
def update_order_item_availability(order_id, item_id):
    """Mark order line unavailable and recalculate order totals (admin only)."""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code

    validated_data, error_response, status_code = validate_request(AdminOrderItemAvailabilitySchema)
    if error_response:
        return error_response, status_code

    try:
        order = Order.query.filter(Order.id == order_id, Order.deleted_at.is_(None)).first_or_404()
        item = OrderItem.query.filter(
            OrderItem.id == item_id,
            OrderItem.order_id == order_id,
            OrderItem.active(),
        ).first_or_404()
        item.is_unavailable = bool(validated_data['is_unavailable'])
        if validated_data.get('cannot_fulfill') is not None:
            item.cannot_fulfill = bool(validated_data['cannot_fulfill'])
        recalculate_existing_item(item)
        sync_order_pricing(order, reprice_lines=False)
        db.session.commit()

        return jsonify({
            'message': 'Item availability updated',
            'order': _build_admin_order_dict(order),
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating item availability: {e}', exc_info=True)
        return jsonify({'error': 'Failed to update item availability', 'message': str(e)}), 500


@admin_bp.route('/orders/<int:order_id>/items/<int:item_id>/substitute-preference', methods=['PATCH'])
def update_order_item_substitute_preference(order_id, item_id):
    """Update accept/decline substitute on an order line and recalculate totals (admin only)."""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code

    validated_data, error_response, status_code = validate_request(AdminOrderItemSubstituteSchema)
    if error_response:
        return error_response, status_code

    try:
        order = Order.query.filter(Order.id == order_id, Order.deleted_at.is_(None)).first_or_404()
        item = OrderItem.query.filter(
            OrderItem.id == item_id,
            OrderItem.order_id == order_id,
            OrderItem.active(),
        ).first_or_404()
        product = Product.query.get(item.product_id)
        if not product or not product.substitute_enabled:
            return jsonify({'error': '此商品未配置备选'}), 400

        item.accept_substitute = bool(validated_data['accept_substitute'])
        recalculate_existing_item(item, product)
        sync_order_pricing(order, reprice_lines=False)
        db.session.commit()

        return jsonify({
            'message': 'Substitute preference updated',
            'order': _build_admin_order_dict(order),
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating substitute preference: {e}', exc_info=True)
        return jsonify({'error': 'Failed to update substitute preference', 'message': str(e)}), 500


@admin_bp.route('/group-deals/<int:deal_id>/products/<int:product_id>/fulfillment', methods=['PATCH'])
def bulk_update_product_fulfillment(deal_id, product_id):
    """Mark all order lines for a product in a group deal unavailable or restore availability."""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code

    validated_data, error_response, status_code = validate_request(AdminProductFulfillmentSchema)
    if error_response:
        return error_response, status_code

    try:
        GroupDeal.query.filter(
            GroupDeal.id == deal_id,
            GroupDeal.deleted_at.is_(None),
        ).first_or_404()

        stats = bulk_set_product_fulfillment(
            deal_id,
            product_id,
            bool(validated_data['is_unavailable']),
        )

        msg = '已恢复原商品' if not validated_data['is_unavailable'] else (
            f'已切换备选，处理 {stats["items_updated"]} 条商品行：'
            f'{stats["will_substitute"]} 条换备选，{stats["will_pending"]} 条待处理（不要备选，保留订单行）'
        )
        return jsonify({'message': msg, 'stats': stats}), 200
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error bulk product fulfillment: {e}', exc_info=True)
        return jsonify({'error': 'Failed to update product fulfillment', 'message': str(e)}), 500


@admin_bp.route('/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    """Soft delete an order (admin only)"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        order = Order.query.filter(Order.id == order_id, Order.deleted_at.is_(None)).first_or_404()
        
        # Restore stock if order is not already cancelled (cancelled orders already had stock restored)
        # Only restore stock for orders that were actually reserving stock
        if order.status != OrderStatus.CANCELLED.value:
            items_to_restore = [{'product_id': item.product_id, 'quantity': item.quantity} for item in order.items]
            try:
                restore_stock(order.group_deal_id, items_to_restore)
                current_app.logger.info(f'Restored stock for deleted order {order_id} (order_number: {order.order_number})')
            except Exception as e:
                current_app.logger.error(f'Failed to restore stock when deleting order {order_id}: {e}')
                # Continue with deletion even if stock restoration fails
        
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

@admin_bp.route('/orders/duplicates', methods=['GET'])
def find_duplicate_orders():
    """Find duplicate orders placed by same users in the same group deal (admin only)"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        group_deal_id = request.args.get('group_deal_id', type=int)
        
        # Build base query - find users with multiple orders in the same group deal
        query = db.session.query(
            Order.user_id,
            Order.group_deal_id,
            func.count(Order.id).label('order_count')
        ).filter(
            Order.deleted_at.is_(None),
            Order.status != OrderStatus.CANCELLED.value
        ).group_by(
            Order.user_id,
            Order.group_deal_id
        ).having(
            func.count(Order.id) > 1
        )
        
        # Filter by group deal if specified
        if group_deal_id:
            query = query.filter(Order.group_deal_id == group_deal_id)
        
        duplicates = query.all()
        
        # Get full order details for each duplicate set
        duplicate_sets = []
        for dup in duplicates:
            orders = Order.query.filter(
                Order.user_id == dup.user_id,
                Order.group_deal_id == dup.group_deal_id,
                Order.deleted_at.is_(None),
                Order.status != OrderStatus.CANCELLED.value
            ).order_by(Order.created_at.asc()).all()
            
            # Get user info
            user = User.query.get(dup.user_id)
            group_deal = GroupDeal.query.filter(
                GroupDeal.id == dup.group_deal_id,
                GroupDeal.deleted_at.is_(None)
            ).first()
            
            orders_data = []
            for order in orders:
                order_dict = order.to_dict()
                
                # Get items with product details
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
                            'pricing_data': product.pricing_data
                        }
                    items_data.append(item_dict)
                order_dict['items'] = items_data
                
                # Get address info if delivery order
                if order.address_id:
                    address = Address.query.get(order.address_id)
                    if address:
                        order_dict['address'] = address.to_dict()
                
                orders_data.append(order_dict)
            
            duplicate_sets.append({
                'user': user.to_dict() if user else None,
                'group_deal': group_deal.to_dict() if group_deal else None,
                'orders': orders_data,
                'order_count': dup.order_count
            })
        
        return jsonify({
            'duplicate_sets': duplicate_sets,
            'total_sets': len(duplicate_sets)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error finding duplicate orders: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to find duplicate orders',
            'message': str(e)
        }), 500

@admin_bp.route('/orders/merge', methods=['POST'])
def merge_orders():
    """Merge multiple orders into one (admin only)"""
    admin_user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    # Validate request data using schema
    validated_data, error_response, status_code = validate_request(MergeOrdersSchema)
    if error_response:
        return error_response, status_code
    
    order_ids = validated_data['order_ids']
    keep_payment_method = validated_data.get('keep_payment_method')
    keep_delivery_method = validated_data.get('keep_delivery_method')
    keep_address_id = validated_data.get('keep_address_id')
    keep_pickup_location = validated_data.get('keep_pickup_location')
    keep_notes = validated_data.get('keep_notes')
    notes_action = validated_data.get('notes_action', 'combine')
    
    try:
        # Fetch all orders
        orders = Order.query.filter(
            Order.id.in_(order_ids),
            Order.deleted_at.is_(None)
        ).all()
        
        if len(orders) < 2:
            return jsonify({'error': 'At least 2 orders are required to merge'}), 400
        
        if len(orders) != len(order_ids):
            return jsonify({'error': 'Some orders not found or already deleted'}), 404
        
        # Validate all orders belong to the same user
        user_ids = {order.user_id for order in orders}
        if len(user_ids) > 1:
            return jsonify({'error': 'Cannot merge orders from different users'}), 400
        
        # Validate all orders are from the same group deal
        group_deal_ids = {order.group_deal_id for order in orders}
        if len(group_deal_ids) > 1:
            return jsonify({'error': 'Cannot merge orders from different group deals'}), 400
        
        # Check if any order is cancelled or completed
        statuses = {order.status for order in orders}
        if OrderStatus.CANCELLED.value in statuses:
            return jsonify({'error': 'Cannot merge cancelled orders'}), 400
        
        # Sort orders by creation date (earliest first will be the main order)
        orders.sort(key=lambda x: x.created_at)
        main_order = orders[0]
        orders_to_merge = orders[1:]
        
        merge_time = utc_now()
        main_items_before = [
            item_snapshot(i, main_order.order_number)
            for i in active_items_for_order(main_order.id)
        ]
        lines_to_copy = []
        for order in orders:
            for item in OrderItem.query.filter(
                OrderItem.order_id == order.id,
                OrderItem.active(),
            ).all():
                lines_to_copy.append((order, item))

        OrderItem.soft_delete_for_order(main_order.id, db.session)
        line_copies = []
        new_items = []
        for source_order, source_item in lines_to_copy:
            new_item = OrderItem(
                order_id=main_order.id,
                **order_item_fields_for_merge(source_item),
            )
            db.session.add(new_item)
            new_items.append(new_item)
            line_copies.append({
                'source_order_id': source_order.id,
                'source_order_number': source_order.order_number,
                'source_item_id': source_item.id,
                'source_snapshot': item_snapshot(source_item, source_order.order_number),
            })
        db.session.flush()
        for entry, new_item in zip(line_copies, new_items):
            entry['new_item_id'] = new_item.id
            entry['new_snapshot'] = item_snapshot(new_item, main_order.order_number)
        
        # Update main order attributes based on admin's choices
        if keep_payment_method:
            main_order.payment_method = keep_payment_method
        
        if keep_delivery_method:
            main_order.delivery_method = keep_delivery_method
        
        if keep_address_id:
            main_order.address_id = keep_address_id
        elif keep_delivery_method == 'pickup':
            main_order.address_id = None
        
        if keep_pickup_location:
            main_order.pickup_location = keep_pickup_location
        elif keep_delivery_method == 'delivery':
            main_order.pickup_location = None
        
        if notes_action == 'clear':
            main_order.notes = None
        elif notes_action == 'replace' and keep_notes is not None and str(keep_notes).strip():
            main_order.notes = str(keep_notes).strip()
        else:
            main_order.notes = combine_order_notes(orders)

        db.session.flush()
        sync_order_pricing(main_order)
        main_order.updated_at = utc_now()

        # Soft delete source orders and link to survivor
        for order in orders_to_merge:
            order.deleted_at = merge_time
            order.merged_into_order_id = main_order.id
            order.merged_at = merge_time

        record_order_audit(
            main_order.id,
            EVENT_MERGE,
            {
                'main_order_id': main_order.id,
                'main_order_number': main_order.order_number,
                'source_order_ids': [o.id for o in orders],
                'merged_away_order_ids': [o.id for o in orders_to_merge],
                'notes_action': notes_action,
                'main_items_before': main_items_before,
                'line_copies': line_copies,
            },
            actor_user_id=admin_user_id,
        )

        db.session.commit()
        
        # Log the merge
        merged_order_ids = [order.id for order in orders_to_merge]
        current_app.logger.info(
            f'Admin merged orders {merged_order_ids} into order {main_order.id} '
            f'for user {main_order.user_id}'
        )
        
        # Return the merged order with full details
        order_dict = main_order.to_dict()
        
        # Get user info
        user = User.query.get(main_order.user_id)
        if user:
            order_dict['user'] = user.to_dict()
        
        # Get group deal info
        group_deal = GroupDeal.query.filter(
            GroupDeal.id == main_order.group_deal_id,
            GroupDeal.deleted_at.is_(None)
        ).first()
        if group_deal:
            order_dict['group_deal'] = group_deal.to_dict()
        
        order_dict['items'] = [
            enrich_order_item_dict(item) for item in main_order.items
        ]
        
        return jsonify({
            'message': 'Orders merged successfully',
            'merged_order': order_dict,
            'deleted_order_ids': merged_order_ids,
            'audit_trail': build_order_audit_trail(main_order.id),
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error merging orders: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to merge orders',
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

@admin_bp.route('/delivery-fee-config', methods=['GET'])
def get_delivery_fee_config():
    """Get the active delivery fee configuration"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        config = DeliveryFeeConfig.query.filter_by(is_active=True).first()
        
        if not config:
            # Return default values if no config exists
            return jsonify({
                'config': {
                    'id': None,
                    'tiers': [
                        {'threshold': 0, 'fee': 7.99},
                        {'threshold': 58.00, 'fee': 5.99},
                        {'threshold': 128.00, 'fee': 3.99},
                        {'threshold': 150.00, 'fee': 0}
                    ],
                    'is_active': True
                }
            }), 200
        
        return jsonify({
            'config': config.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error fetching delivery fee config: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to fetch delivery fee config',
            'message': str(e)
        }), 500

@admin_bp.route('/delivery-fee-config', methods=['PUT'])
def update_delivery_fee_config():
    """Update or create the active delivery fee configuration"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    # Validate request data using schema
    validated_data, error_response, status_code = validate_request(UpdateDeliveryFeeConfigSchema)
    if error_response:
        return error_response, status_code
    
    try:
        # Convert Decimal values to float for JSON storage
        tiers = []
        for tier in validated_data['tiers']:
            tiers.append({
                'threshold': float(tier['threshold']),
                'fee': float(tier['fee'])
            })
        
        # Get or create active config
        config = DeliveryFeeConfig.query.filter_by(is_active=True).first()
        
        if not config:
            # Create new config
            config = DeliveryFeeConfig(
                tiers=tiers,
                is_active=True
            )
            db.session.add(config)
        else:
            # Update existing config
            config.tiers = tiers
        
        db.session.commit()
        
        current_app.logger.info(f'Updated delivery fee config: {config.id}')
        
        return jsonify({
            'config': config.to_dict(),
            'message': '运费配置已更新'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating delivery fee config: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to update delivery fee config',
            'message': str(e)
        }), 500


# ============================================================================
# SDR Management Routes
# ============================================================================

@admin_bp.route('/sdrs', methods=['GET'])
def get_sdrs():
    """Get all SDRs"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        sdrs = SDR.query.order_by(SDR.name).all()
        return jsonify({
            'sdrs': [sdr.to_dict() for sdr in sdrs]
        }), 200
    except Exception as e:
        current_app.logger.error(f'Error fetching SDRs: {e}', exc_info=True)
        return jsonify({'error': 'Failed to fetch SDRs'}), 500


@admin_bp.route('/sdrs/<int:sdr_id>', methods=['GET'])
def get_sdr(sdr_id):
    """Get single SDR with commission rules"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        sdr = SDR.query.get(sdr_id)
        if not sdr:
            return jsonify({'error': 'SDR not found'}), 404
        
        sdr_data = sdr.to_dict()
        # Include commission rules
        rules = CommissionRule.query.filter_by(sdr_id=sdr_id, is_active=True).all()
        sdr_data['commission_rules'] = [rule.to_dict(include_product=True) for rule in rules]
        
        return jsonify({'sdr': sdr_data}), 200
    except Exception as e:
        current_app.logger.error(f'Error fetching SDR {sdr_id}: {e}', exc_info=True)
        return jsonify({'error': 'Failed to fetch SDR'}), 500


@admin_bp.route('/sdrs', methods=['POST'])
def create_sdr():
    """Create new SDR"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('source_identifier'):
            return jsonify({'error': 'Name and source identifier are required'}), 400
        
        # Check if source_identifier already exists
        existing = SDR.query.filter_by(source_identifier=data['source_identifier']).first()
        if existing:
            return jsonify({'error': 'Source identifier already exists'}), 400
        
        sdr = SDR(
            name=data['name'],
            source_identifier=data['source_identifier'],
            email=data.get('email'),
            phone=data.get('phone'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(sdr)
        db.session.commit()
        
        current_app.logger.info(f'Created SDR: {sdr.name} (ID: {sdr.id})')
        
        return jsonify({
            'sdr': sdr.to_dict(),
            'message': 'SDR创建成功'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating SDR: {e}', exc_info=True)
        return jsonify({'error': 'Failed to create SDR', 'message': str(e)}), 500


@admin_bp.route('/sdrs/<int:sdr_id>', methods=['PUT'])
def update_sdr(sdr_id):
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    """Update SDR"""
    try:
        sdr = SDR.query.get(sdr_id)
        if not sdr:
            return jsonify({'error': 'SDR not found'}), 404
        
        data = request.get_json()
        
        # Check if source_identifier is being changed and if it already exists
        if 'source_identifier' in data and data['source_identifier'] != sdr.source_identifier:
            existing = SDR.query.filter_by(source_identifier=data['source_identifier']).first()
            if existing:
                return jsonify({'error': 'Source identifier already exists'}), 400
        
        # Update fields
        if 'name' in data:
            sdr.name = data['name']
        if 'source_identifier' in data:
            sdr.source_identifier = data['source_identifier']
        if 'email' in data:
            sdr.email = data['email']
        if 'phone' in data:
            sdr.phone = data['phone']
        if 'is_active' in data:
            sdr.is_active = data['is_active']
        
        db.session.commit()
        
        current_app.logger.info(f'Updated SDR: {sdr.name} (ID: {sdr.id})')
        
        return jsonify({
            'sdr': sdr.to_dict(),
            'message': 'SDR更新成功'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating SDR {sdr_id}: {e}', exc_info=True)
        return jsonify({'error': 'Failed to update SDR', 'message': str(e)}), 500


@admin_bp.route('/sdrs/<int:sdr_id>', methods=['DELETE'])
def delete_sdr(sdr_id):
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    """Delete SDR"""
    try:
        sdr = SDR.query.get(sdr_id)
        if not sdr:
            return jsonify({'error': 'SDR not found'}), 404
        
        sdr_name = sdr.name
        db.session.delete(sdr)
        db.session.commit()
        
        current_app.logger.info(f'Deleted SDR: {sdr_name} (ID: {sdr_id})')
        
        return jsonify({'message': 'SDR删除成功'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting SDR {sdr_id}: {e}', exc_info=True)
        return jsonify({'error': 'Failed to delete SDR', 'message': str(e)}), 500


# ============================================================================
# Commission Rules Routes
# ============================================================================

@admin_bp.route('/sdrs/<int:sdr_id>/commission-rules', methods=['GET'])
def get_commission_rules(sdr_id):
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    """Get all commission rules for an SDR"""
    try:
        sdr = SDR.query.get(sdr_id)
        if not sdr:
            return jsonify({'error': 'SDR not found'}), 404
        
        rules = CommissionRule.query.filter_by(sdr_id=sdr_id, is_active=True).all()
        
        return jsonify({
            'rules': [rule.to_dict(include_product=True) for rule in rules]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error fetching commission rules for SDR {sdr_id}: {e}', exc_info=True)
        return jsonify({'error': 'Failed to fetch commission rules'}), 500


@admin_bp.route('/sdrs/<int:sdr_id>/commission-rules', methods=['POST'])
def create_or_update_commission_rule(sdr_id):
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    """Create or update commission rule for a product"""
    try:
        sdr = SDR.query.get(sdr_id)
        if not sdr:
            return jsonify({'error': 'SDR not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('product_id'):
            return jsonify({'error': 'Product ID is required'}), 400
        if 'own_customer_amount' not in data or 'general_customer_amount' not in data:
            return jsonify({'error': 'Commission amounts are required'}), 400
        
        product_id = data['product_id']
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Check if rule already exists
        existing_rule = CommissionRule.query.filter_by(
            sdr_id=sdr_id,
            product_id=product_id
        ).first()
        
        # Get commission_type (default to 'per_item' if not provided)
        commission_type = data.get('commission_type', 'per_item')
        if commission_type not in ['per_item', 'per_weight']:
            commission_type = 'per_item'
        
        if existing_rule:
            # Update existing rule
            existing_rule.commission_type = commission_type
            existing_rule.own_customer_amount = Decimal(str(data['own_customer_amount']))
            existing_rule.general_customer_amount = Decimal(str(data['general_customer_amount']))
            existing_rule.is_active = data.get('is_active', True)
            rule = existing_rule
            message = '提成规则更新成功'
        else:
            # Create new rule
            rule = CommissionRule(
                sdr_id=sdr_id,
                product_id=product_id,
                commission_type=commission_type,
                own_customer_amount=Decimal(str(data['own_customer_amount'])),
                general_customer_amount=Decimal(str(data['general_customer_amount'])),
                is_active=data.get('is_active', True)
            )
            db.session.add(rule)
            message = '提成规则创建成功'
        
        db.session.commit()
        
        current_app.logger.info(f'Created/updated commission rule for SDR {sdr_id}, Product {product_id}')
        
        return jsonify({
            'rule': rule.to_dict(include_product=True),
            'message': message
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating/updating commission rule: {e}', exc_info=True)
        return jsonify({'error': 'Failed to save commission rule', 'message': str(e)}), 500


@admin_bp.route('/sdrs/<int:sdr_id>/commission-rules/batch', methods=['POST'])
def batch_update_commission_rules(sdr_id):
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    """Batch update commission rules for multiple products"""
    try:
        sdr = SDR.query.get(sdr_id)
        if not sdr:
            return jsonify({'error': 'SDR not found'}), 404
        
        data = request.get_json()
        rules_data = data.get('rules', [])
        
        if not rules_data:
            return jsonify({'error': 'No rules provided'}), 400
        
        updated_rules = []
        
        for rule_data in rules_data:
            product_id = rule_data.get('product_id')
            if not product_id:
                continue
            
            product = Product.query.get(product_id)
            if not product:
                continue
            
            # Check if rule exists
            existing_rule = CommissionRule.query.filter_by(
                sdr_id=sdr_id,
                product_id=product_id
            ).first()
            
            # Get commission_type (default to 'per_item' if not provided)
            commission_type = rule_data.get('commission_type', 'per_item')
            if commission_type not in ['per_item', 'per_weight']:
                commission_type = 'per_item'
            
            if existing_rule:
                # Update existing
                existing_rule.commission_type = commission_type
                existing_rule.own_customer_amount = Decimal(str(rule_data['own_customer_amount']))
                existing_rule.general_customer_amount = Decimal(str(rule_data['general_customer_amount']))
                existing_rule.is_active = rule_data.get('is_active', True)
                updated_rules.append(existing_rule)
            else:
                # Create new
                rule = CommissionRule(
                    sdr_id=sdr_id,
                    product_id=product_id,
                    commission_type=commission_type,
                    own_customer_amount=Decimal(str(rule_data['own_customer_amount'])),
                    general_customer_amount=Decimal(str(rule_data['general_customer_amount'])),
                    is_active=rule_data.get('is_active', True)
                )
                db.session.add(rule)
                updated_rules.append(rule)
        
        db.session.commit()
        
        current_app.logger.info(f'Batch updated {len(updated_rules)} commission rules for SDR {sdr_id}')
        
        return jsonify({
            'rules': [rule.to_dict(include_product=True) for rule in updated_rules],
            'message': f'成功更新{len(updated_rules)}条提成规则'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error batch updating commission rules: {e}', exc_info=True)
        return jsonify({'error': 'Failed to batch update commission rules', 'message': str(e)}), 500


@admin_bp.route('/commission-rules/<int:rule_id>', methods=['DELETE'])
def delete_commission_rule(rule_id):
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    """Delete commission rule"""
    try:
        rule = CommissionRule.query.get(rule_id)
        if not rule:
            return jsonify({'error': 'Commission rule not found'}), 404
        
        db.session.delete(rule)
        db.session.commit()
        
        current_app.logger.info(f'Deleted commission rule ID: {rule_id}')
        
        return jsonify({'message': '提成规则删除成功'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting commission rule {rule_id}: {e}', exc_info=True)
        return jsonify({'error': 'Failed to delete commission rule', 'message': str(e)}), 500


# ============================================================================
# Commission Calculation & Records Routes
# ============================================================================

@admin_bp.route('/group-deals/<int:deal_id>/commission/calculate', methods=['POST'])
def calculate_group_deal_commission(deal_id):
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    """Calculate commission for a group deal"""
    try:
        data = request.get_json() or {}
        recalculate = data.get('recalculate', False)
        
        result = calculate_commission_for_group_deal(deal_id, recalculate=recalculate)
        
        if not result['success']:
            return jsonify({'error': result.get('error', 'Failed to calculate commission')}), 400
        
        return jsonify({
            'message': '提成计算成功',
            'records': result['records'],
            'total_commission': result['total_commission']
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error calculating commission for group deal {deal_id}: {e}', exc_info=True)
        return jsonify({'error': 'Failed to calculate commission', 'message': str(e)}), 500


@admin_bp.route('/group-deals/<int:deal_id>/commission', methods=['GET'])
def get_group_deal_commission(deal_id):
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    """Get commission breakdown for a group deal"""
    try:
        summary = get_commission_summary_for_group_deal(deal_id)
        
        if not summary:
            return jsonify({
                'message': '暂无提成记录',
                'records': [],
                'total_commission': 0
            }), 200
        
        return jsonify(summary), 200
        
    except Exception as e:
        current_app.logger.error(f'Error fetching commission for group deal {deal_id}: {e}', exc_info=True)
        return jsonify({'error': 'Failed to fetch commission', 'message': str(e)}), 500


@admin_bp.route('/commission-records', methods=['GET'])
def get_commission_records():
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    """Get all commission records with optional filters"""
    try:
        # Get query parameters
        sdr_id = request.args.get('sdr_id', type=int)
        payment_status = request.args.get('payment_status')
        group_deal_id = request.args.get('group_deal_id', type=int)
        
        # Build query
        query = CommissionRecord.query
        
        if sdr_id:
            query = query.filter_by(sdr_id=sdr_id)
        if payment_status:
            query = query.filter_by(payment_status=payment_status)
        if group_deal_id:
            query = query.filter_by(group_deal_id=group_deal_id)
        
        records = query.order_by(CommissionRecord.created_at.desc()).all()
        
        return jsonify({
            'records': [record.to_dict(include_relations=True) for record in records],
            'total_commission': sum(float(record.total_commission) for record in records)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error fetching commission records: {e}', exc_info=True)
        return jsonify({'error': 'Failed to fetch commission records'}), 500


@admin_bp.route('/commission-records/<int:record_id>/payment', methods=['PUT'])
def update_commission_payment(record_id):
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    """Update payment status of commission record"""
    try:
        record = CommissionRecord.query.get(record_id)
        if not record:
            return jsonify({'error': 'Commission record not found'}), 404
        
        data = request.get_json()
        
        if 'payment_status' in data:
            record.payment_status = data['payment_status']
        
        if data.get('payment_status') == 'paid' and not record.payment_date:
            record.payment_date = utc_now()
        
        if 'payment_notes' in data:
            record.payment_notes = data['payment_notes']
        
        db.session.commit()
        
        current_app.logger.info(f'Updated payment status for commission record {record_id}')
        
        return jsonify({
            'record': record.to_dict(include_relations=True),
            'message': '付款状态更新成功'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating commission payment {record_id}: {e}', exc_info=True)
        return jsonify({'error': 'Failed to update payment status', 'message': str(e)}), 500


@admin_bp.route('/commission-records/<int:record_id>/adjustment', methods=['PUT'])
def update_commission_adjustment(record_id):
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    """Update manual adjustment for commission record"""
    try:
        record = CommissionRecord.query.get(record_id)
        if not record:
            return jsonify({'error': 'Commission record not found'}), 404
        
        data = request.get_json()
        
        if 'manual_adjustment' in data:
            # Can be positive (bonus) or negative (deduction)
            # Handle None and empty strings safely
            adjustment_value = data['manual_adjustment']
            if adjustment_value is None or adjustment_value == '':
                record.manual_adjustment = Decimal('0')
            else:
                record.manual_adjustment = Decimal(str(adjustment_value))
        
        if 'adjustment_notes' in data:
            record.adjustment_notes = data['adjustment_notes']
        
        db.session.commit()
        
        current_app.logger.info(f'Updated manual adjustment for commission record {record_id}: {record.manual_adjustment}')
        
        return jsonify({
            'record': record.to_dict(include_relations=True),
            'message': '手动调整保存成功'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating commission adjustment {record_id}: {e}', exc_info=True)
        return jsonify({'error': 'Failed to update adjustment', 'message': str(e)}), 500


@admin_bp.route('/sdrs/<int:sdr_id>/quarterly-bonus/calculate', methods=['POST'])
def calculate_quarterly_bonus(sdr_id):
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    """Calculate quarterly bonus for an SDR based on commission records"""
    try:
        # Get SDR
        sdr = SDR.query.get(sdr_id)
        if not sdr:
            return jsonify({'error': 'SDR not found'}), 404
        
        data = request.get_json()
        year = data.get('year')
        quarter = data.get('quarter')
        
        if not year or not quarter:
            return jsonify({'error': 'Year and quarter are required'}), 400
        
        if quarter not in [1, 2, 3, 4]:
            return jsonify({'error': 'Quarter must be 1, 2, 3, or 4'}), 400
        
        # Calculate quarter date range
        quarter_start_month = (quarter - 1) * 3 + 1
        if quarter == 4:
            quarter_end_month = 12
            quarter_end_day = 31
        else:
            quarter_end_month = quarter_start_month + 2
            # Get last day of the quarter end month
            if quarter_end_month in [1, 3, 5, 7, 8, 10, 12]:
                quarter_end_day = 31
            elif quarter_end_month in [4, 6, 9, 11]:
                quarter_end_day = 30
            else:
                quarter_end_day = 28
        
        quarter_start = datetime(year, quarter_start_month, 1)
        quarter_end = datetime(year, quarter_end_month, quarter_end_day, 23, 59, 59)
        
        # Get all commission records for this SDR within the quarter
        commission_records = CommissionRecord.query.join(
            GroupDeal, CommissionRecord.group_deal_id == GroupDeal.id
        ).filter(
            CommissionRecord.sdr_id == sdr_id,
            GroupDeal.created_at >= quarter_start,
            GroupDeal.created_at <= quarter_end
        ).all()
        
        if not commission_records:
            return jsonify({
                'success': True,
                'commission_records': [],
                'total_commission': 0,
                'message': 'No commission records found for this quarter'
            }), 200
        
        # Build commission records data
        commission_records_data = []
        total_commission = Decimal('0')
        
        for record in commission_records:
            # For quarterly bonus, only count the base commission (exclude manual adjustments)
            base_commission = record.total_commission
            total_commission += base_commission
            
            commission_records_data.append({
                'commission_record_id': record.id,
                'group_deal_id': record.group_deal_id,
                'group_deal_title': record.group_deal.title if record.group_deal else f"团购 #{record.group_deal_id}",
                'total_commission': float(record.total_commission),
                'manual_adjustment': float(record.manual_adjustment or 0),
                'final_total': float(base_commission)
            })
        
        return jsonify({
            'success': True,
            'commission_records': commission_records_data,
            'total_commission': float(total_commission),
            'year': year,
            'quarter': quarter
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error calculating quarterly bonus for SDR {sdr_id}: {e}', exc_info=True)
        return jsonify({'error': 'Failed to calculate quarterly bonus', 'message': str(e)}), 500


@admin_bp.route('/sdrs/<int:sdr_id>/quarterly-bonus', methods=['POST'])
def create_quarterly_bonus(sdr_id):
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    """Create or update quarterly bonus for an SDR"""
    try:
        # Get SDR
        sdr = SDR.query.get(sdr_id)
        if not sdr:
            return jsonify({'error': 'SDR not found'}), 404
        
        data = request.get_json()
        year = data.get('year')
        quarter = data.get('quarter')
        bonus_percentage = data.get('bonus_percentage')
        commission_records_data = data.get('commission_records', [])
        
        if not year or not quarter or bonus_percentage is None:
            return jsonify({'error': 'Year, quarter, and bonus_percentage are required'}), 400
        
        if quarter not in [1, 2, 3, 4]:
            return jsonify({'error': 'Quarter must be 1, 2, 3, or 4'}), 400
        
        # Calculate totals
        total_commission = Decimal('0')
        for record_data in commission_records_data:
            total_commission += Decimal(str(record_data.get('final_total', 0)))
        
        bonus_percentage_decimal = Decimal(str(bonus_percentage))
        bonus_amount = total_commission * (bonus_percentage_decimal / Decimal('100'))
        
        # Check if bonus already exists
        existing_bonus = QuarterlyBonus.query.filter_by(
            sdr_id=sdr_id,
            year=year,
            quarter=quarter
        ).first()
        
        if existing_bonus:
            # Update existing bonus
            existing_bonus.commission_records_data = commission_records_data
            existing_bonus.total_commission = total_commission
            existing_bonus.bonus_percentage = bonus_percentage_decimal
            existing_bonus.bonus_amount = bonus_amount
            bonus = existing_bonus
        else:
            # Create new bonus
            bonus = QuarterlyBonus(
                sdr_id=sdr_id,
                year=year,
                quarter=quarter,
                commission_records_data=commission_records_data,
                total_commission=total_commission,
                bonus_percentage=bonus_percentage_decimal,
                bonus_amount=bonus_amount,
                payment_status='pending'
            )
            db.session.add(bonus)
        
        db.session.commit()
        
        current_app.logger.info(f'Created/updated quarterly bonus for SDR {sdr_id}, Q{quarter} {year}')
        
        return jsonify({
            'bonus': bonus.to_dict(include_relations=True),
            'message': '季度分红保存成功'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating quarterly bonus for SDR {sdr_id}: {e}', exc_info=True)
        return jsonify({'error': 'Failed to create quarterly bonus', 'message': str(e)}), 500


@admin_bp.route('/sdrs/<int:sdr_id>/quarterly-bonuses', methods=['GET'])
def get_quarterly_bonuses(sdr_id):
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    """Get all quarterly bonuses for an SDR"""
    try:
        # Get SDR
        sdr = SDR.query.get(sdr_id)
        if not sdr:
            return jsonify({'error': 'SDR not found'}), 404
        
        bonuses = QuarterlyBonus.query.filter_by(sdr_id=sdr_id).order_by(
            QuarterlyBonus.year.desc(),
            QuarterlyBonus.quarter.desc()
        ).all()
        
        return jsonify({
            'bonuses': [bonus.to_dict(include_relations=True) for bonus in bonuses]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error fetching quarterly bonuses for SDR {sdr_id}: {e}', exc_info=True)
        return jsonify({'error': 'Failed to fetch quarterly bonuses'}), 500


@admin_bp.route('/quarterly-bonuses/<int:bonus_id>/payment', methods=['PUT'])
def update_quarterly_bonus_payment(bonus_id):
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    """Update payment status of quarterly bonus"""
    try:
        bonus = QuarterlyBonus.query.get(bonus_id)
        if not bonus:
            return jsonify({'error': 'Quarterly bonus not found'}), 404
        
        data = request.get_json()
        
        if 'payment_status' in data:
            bonus.payment_status = data['payment_status']
        
        if data.get('payment_status') == 'paid' and not bonus.payment_date:
            bonus.payment_date = utc_now()
        
        if 'payment_notes' in data:
            bonus.payment_notes = data['payment_notes']
        
        db.session.commit()
        
        current_app.logger.info(f'Updated payment status for quarterly bonus {bonus_id}')
        
        return jsonify({
            'bonus': bonus.to_dict(include_relations=True),
            'message': '付款状态更新成功'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating quarterly bonus payment {bonus_id}: {e}', exc_info=True)
        return jsonify({'error': 'Failed to update payment status', 'message': str(e)}), 500


@admin_bp.route('/quarterly-bonuses/<int:bonus_id>', methods=['DELETE'])
def delete_quarterly_bonus(bonus_id):
    """Delete a quarterly bonus record"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        bonus = QuarterlyBonus.query.get(bonus_id)
        if not bonus:
            return jsonify({'error': 'Quarterly bonus not found'}), 404
        
        db.session.delete(bonus)
        db.session.commit()
        
        current_app.logger.info(f'Deleted quarterly bonus {bonus_id}')
        
        return jsonify({'message': '季度分红记录已删除'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting quarterly bonus {bonus_id}: {e}', exc_info=True)
        return jsonify({'error': 'Failed to delete quarterly bonus', 'message': str(e)}), 500


def _admin_user_ids():
    return [r[0] for r in db.session.query(UserRole.user_id).filter(UserRole.role == 'admin').all()]


def _customer_feedback_summary_for_users(user_ids, context):
    """Returns (counts_by_user_id, records_list_by_user_id) for customer_feedback."""
    from collections import defaultdict

    if not user_ids:
        return {}, {}

    count_rows = db.session.query(
        CustomerFeedback.user_id,
        func.count(CustomerFeedback.id),
    ).filter(
        CustomerFeedback.user_id.in_(user_ids),
        CustomerFeedback.context == context,
    ).group_by(CustomerFeedback.user_id).all()
    counts = {uid: c for uid, c in count_rows}

    all_recs = CustomerFeedback.query.options(
        joinedload(CustomerFeedback.created_by)
    ).filter(
        CustomerFeedback.user_id.in_(user_ids),
        CustomerFeedback.context == context,
    ).all()
    by_uid = defaultdict(list)
    for r in all_recs:
        by_uid[r.user_id].append(r)
    records_out = {}
    for uid in user_ids:
        rows = sorted(by_uid[uid], key=lambda x: x.created_at, reverse=True)[:25]
        records_out[uid] = [x.to_dict(include_created_by=True) for x in rows]

    return counts, records_out


def _user_deal_order_pairs(user_ids, deal_ids):
    """Set of (user_id, group_deal_id) where the user has a non-cancelled order in that deal."""
    if not user_ids or not deal_ids:
        return set()
    rows = db.session.query(Order.user_id, Order.group_deal_id).filter(
        Order.user_id.in_(user_ids),
        Order.group_deal_id.in_(deal_ids),
        Order.deleted_at.is_(None),
        Order.status != OrderStatus.CANCELLED.value,
    ).distinct().all()
    return set(rows)


def _deal_chips_for_user(user_id, deals_ordered, pair_set):
    return [
        {
            'id': d.id,
            'title': d.title,
            'has_order': (user_id, d.id) in pair_set,
        }
        for d in deals_ordered
    ]


def _merge_chip_deals_first_time(target_deal, recent_two):
    """Unique deals: selected target + recent two, sorted by order_end_date desc (newest first)."""
    seen = {}
    for d in [target_deal] + list(recent_two or []):
        if d and d.id not in seen:
            seen[d.id] = d
    out = list(seen.values())
    out.sort(
        key=lambda d: d.order_end_date.timestamp() if d.order_end_date else 0.0,
        reverse=True,
    )
    return out


def _after_sales_first_time_buyers_payload(target_deal, admin_ids, search, chip_deals):
    """Build items for users whose only non-cancelled order is in target_deal."""
    q = db.session.query(Order.user_id).filter(
        Order.deleted_at.is_(None),
        Order.status != OrderStatus.CANCELLED.value,
    )
    if admin_ids:
        q = q.filter(~Order.user_id.in_(admin_ids))
    single_order_user_ids = [
        r[0] for r in q.group_by(Order.user_id).having(func.count(Order.id) == 1).all()
    ]

    if not single_order_user_ids:
        return []

    orders_query = Order.query.options(
        joinedload(Order.user),
        joinedload(Order.group_deal),
    ).join(User, Order.user_id == User.id).filter(
        Order.user_id.in_(single_order_user_ids),
        Order.group_deal_id == target_deal.id,
        Order.deleted_at.is_(None),
        Order.status != OrderStatus.CANCELLED.value,
    )
    if search:
        term = f'%{search}%'
        orders_query = orders_query.filter(
            or_(
                User.nickname.like(term),
                User.phone.like(term),
                User.wechat.like(term),
            )
        )
    orders = orders_query.order_by(Order.created_at.desc()).all()

    user_ids = list({o.user_id for o in orders})
    fu_counts, fu_records = _customer_feedback_summary_for_users(
        user_ids, FeedbackContext.AFTER_SALES_FIRST_ORDER
    )

    deal_ids = [d.id for d in chip_deals] if chip_deals else []
    pair_set = _user_deal_order_pairs(user_ids, deal_ids)

    items = []
    for order in orders:
        u = order.user
        if not u:
            continue
        uid = order.user_id
        base_total = float(order.total) if order.total is not None else 0.0
        adj = float(order.adjustment_amount) if order.adjustment_amount is not None else 0.0
        final_total = round(base_total + adj, 2)
        items.append({
            'user': {
                'id': u.id,
                'nickname': u.nickname,
                'phone': u.phone,
                'wechat': u.wechat,
                'user_source': u.user_source or 'default',
            },
            'order': {
                'id': order.id,
                'order_number': order.order_number,
                'created_at': order.created_at.isoformat() if order.created_at else None,
                'status': order.status,
                'final_total': final_total,
            },
            'group_deal': {
                'id': order.group_deal.id,
                'title': order.group_deal.title,
                'order_end_date': order.group_deal.order_end_date.isoformat() if order.group_deal and order.group_deal.order_end_date else None,
                'pickup_date': order.group_deal.pickup_date.isoformat() if order.group_deal and order.group_deal.pickup_date else None,
            } if order.group_deal else None,
            'deal_chips': _deal_chips_for_user(uid, chip_deals, pair_set),
            'feedback': {
                'count': fu_counts.get(uid, 0),
                'records': fu_records.get(uid, []),
            },
        })
    return items


@admin_bp.route('/after-sales/first-time-buyers', methods=['GET'])
def get_after_sales_first_time_buyers():
    """First-time buyers in a chosen group deal (default: latest by order_end_date)."""
    _admin_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code

    try:
        group_deal_options = GroupDeal.query.filter(
            GroupDeal.deleted_at.is_(None)
        ).order_by(GroupDeal.order_end_date.desc()).all()
        options_payload = [d.to_dict() for d in group_deal_options]

        admin_ids = _admin_user_ids()
        search = request.args.get('search', '').strip()

        if not group_deal_options:
            return jsonify({
                'recent_group_deals': [],
                'group_deal_options': [],
                'selected_group_deal_id': None,
                'items': [],
                'feedback_outcome_options': FeedbackOutcome.all_values(),
            }), 200

        requested_id = request.args.get('group_deal_id', type=int)
        if requested_id is not None:
            target_deal = GroupDeal.query.filter(
                GroupDeal.id == requested_id,
                GroupDeal.deleted_at.is_(None),
            ).first()
            if not target_deal:
                return jsonify({
                    'error': 'Invalid group_deal_id',
                    'message': '团购不存在或已删除',
                }), 400
        else:
            target_deal = group_deal_options[0]

        recent_two = GroupDeal.query.filter(
            GroupDeal.deleted_at.is_(None)
        ).order_by(GroupDeal.order_end_date.desc()).limit(2).all()
        chip_deals = _merge_chip_deals_first_time(target_deal, recent_two)

        items = _after_sales_first_time_buyers_payload(target_deal, admin_ids, search, chip_deals)

        return jsonify({
            'recent_group_deals': [target_deal.to_dict()],
            'group_deal_options': options_payload,
            'selected_group_deal_id': target_deal.id,
            'items': items,
            'feedback_outcome_options': FeedbackOutcome.all_values(),
        }), 200

    except Exception as e:
        current_app.logger.error(f'Error listing first-time buyers: {e}', exc_info=True)
        return jsonify({'error': 'Failed to list first-time buyers', 'message': str(e)}), 500


@admin_bp.route('/after-sales/customer-feedback', methods=['POST'])
def create_after_sales_customer_feedback():
    """Append one customer feedback row (multiple per user; join user to count)."""
    admin_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code

    try:
        data = request.get_json() or {}
        target_user_id = data.get('user_id')
        if not target_user_id:
            return jsonify({'error': 'user_id is required'}), 400

        context = (data.get('context') or '').strip()
        if context not in FeedbackContext.all_values():
            return jsonify({'error': 'Invalid context'}), 400

        outcome = (data.get('outcome') or '').strip()
        if outcome not in FeedbackOutcome.all_values():
            return jsonify({'error': 'Invalid outcome'}), 400

        user = User.query.get(int(target_user_id))
        if not user:
            return jsonify({'error': 'User not found'}), 404

        raw_order_id = data.get('order_id')
        order_id = None
        if raw_order_id is not None and raw_order_id != '':
            order_id = int(raw_order_id)
            order = Order.query.filter(
                Order.id == order_id,
                Order.user_id == user.id,
                Order.deleted_at.is_(None),
            ).first()
            if not order:
                return jsonify({'error': 'Order not found for this user'}), 404

        notes = data.get('notes')
        if notes is not None:
            notes = (notes or '').strip() or None

        row = CustomerFeedback(
            user_id=user.id,
            order_id=order_id,
            context=context,
            outcome=outcome,
            notes=notes,
            created_by_user_id=admin_id,
        )
        db.session.add(row)
        db.session.commit()

        saved = CustomerFeedback.query.options(
            joinedload(CustomerFeedback.created_by)
        ).get(row.id)

        return jsonify({
            'record': saved.to_dict(include_created_by=True) if saved else row.to_dict(),
            'message': '已保存',
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating customer feedback: {e}', exc_info=True)
        return jsonify({'error': 'Failed to save feedback', 'message': str(e)}), 500


@admin_bp.route('/after-sales/customer-feedback/<int:record_id>', methods=['PATCH'])
def update_after_sales_customer_feedback(record_id):
    """Update outcome/notes on an existing after-sales feedback row."""
    _admin_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code

    try:
        row = CustomerFeedback.query.get(record_id)
        if not row:
            return jsonify({'error': 'Not found', 'message': '记录不存在'}), 404
        if row.context not in FeedbackContext.all_values():
            return jsonify({'error': 'Forbidden', 'message': '无法编辑此记录'}), 403

        data = request.get_json() or {}
        outcome = (data.get('outcome') or '').strip()
        if outcome not in FeedbackOutcome.all_values():
            return jsonify({'error': 'Invalid outcome'}), 400

        notes = data.get('notes')
        if notes is not None:
            notes = (notes or '').strip() or None

        row.outcome = outcome
        row.notes = notes
        db.session.commit()

        saved = CustomerFeedback.query.options(
            joinedload(CustomerFeedback.created_by)
        ).get(row.id)

        return jsonify({
            'record': saved.to_dict(include_created_by=True) if saved else row.to_dict(),
            'message': '已更新',
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating customer feedback: {e}', exc_info=True)
        return jsonify({'error': 'Failed to update feedback', 'message': str(e)}), 500


@admin_bp.route('/after-sales/customer-feedback/<int:record_id>', methods=['DELETE'])
def delete_after_sales_customer_feedback(record_id):
    """Delete one after-sales feedback row."""
    _admin_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code

    try:
        row = CustomerFeedback.query.get(record_id)
        if not row:
            return jsonify({'error': 'Not found', 'message': '记录不存在'}), 404
        if row.context not in FeedbackContext.all_values():
            return jsonify({'error': 'Forbidden', 'message': '无法删除此记录'}), 403

        db.session.delete(row)
        db.session.commit()

        return jsonify({'message': '已删除'}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting customer feedback: {e}', exc_info=True)
        return jsonify({'error': 'Failed to delete feedback', 'message': str(e)}), 500


@admin_bp.route('/after-sales/churned-buyers', methods=['GET'])
def get_after_sales_churned_buyers():
    """Users who have purchased before but have no non-cancelled order in the last two group deals (by order_end_date)."""
    _admin_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code

    try:
        recent_deals = GroupDeal.query.filter(
            GroupDeal.deleted_at.is_(None)
        ).order_by(GroupDeal.order_end_date.desc()).limit(2).all()
        recent_ids = [d.id for d in recent_deals]

        admin_ids = _admin_user_ids()

        if not recent_ids:
            return jsonify({
                'recent_group_deals': [],
                'items': [],
                'feedback_outcome_options': FeedbackOutcome.all_values(),
            }), 200

        q_all = db.session.query(Order.user_id).filter(
            Order.deleted_at.is_(None),
            Order.status != OrderStatus.CANCELLED.value,
        )
        if admin_ids:
            q_all = q_all.filter(~Order.user_id.in_(admin_ids))
        all_buyer_ids = set(r[0] for r in q_all.distinct().all())

        q_recent = db.session.query(Order.user_id).filter(
            Order.deleted_at.is_(None),
            Order.status != OrderStatus.CANCELLED.value,
            Order.group_deal_id.in_(recent_ids),
        )
        if admin_ids:
            q_recent = q_recent.filter(~Order.user_id.in_(admin_ids))
        recent_buyer_ids = set(r[0] for r in q_recent.distinct().all())

        churned_ids = list(all_buyer_ids - recent_buyer_ids)
        if not churned_ids:
            return jsonify({
                'recent_group_deals': [d.to_dict() for d in recent_deals],
                'items': [],
                'feedback_outcome_options': FeedbackOutcome.all_values(),
            }), 200

        subq = db.session.query(
            Order.user_id.label('uid'),
            func.max(Order.id).label('mid'),
        ).filter(
            Order.deleted_at.is_(None),
            Order.status != OrderStatus.CANCELLED.value,
            Order.user_id.in_(churned_ids),
        ).group_by(Order.user_id).subquery()

        last_orders_query = Order.query.options(
            joinedload(Order.user),
            joinedload(Order.group_deal),
        ).join(
            subq,
            and_(Order.user_id == subq.c.uid, Order.id == subq.c.mid),
        ).join(User, Order.user_id == User.id)

        search = request.args.get('search', '').strip()
        if search:
            term = f'%{search}%'
            last_orders_query = last_orders_query.filter(
                or_(
                    User.nickname.like(term),
                    User.phone.like(term),
                    User.wechat.like(term),
                )
            )

        last_orders = last_orders_query.all()
        filtered_churned_ids = [o.user_id for o in last_orders]

        if not filtered_churned_ids:
            return jsonify({
                'recent_group_deals': [d.to_dict() for d in recent_deals],
                'items': [],
                'feedback_outcome_options': FeedbackOutcome.all_values(),
            }), 200

        order_count_rows = db.session.query(
            Order.user_id,
            func.count(Order.id),
        ).filter(
            Order.deleted_at.is_(None),
            Order.status != OrderStatus.CANCELLED.value,
            Order.user_id.in_(filtered_churned_ids),
        ).group_by(Order.user_id).all()
        counts = {uid: c for uid, c in order_count_rows}

        fu_counts, fu_records = _customer_feedback_summary_for_users(
            filtered_churned_ids, FeedbackContext.AFTER_SALES_CHURNED
        )

        pair_set = _user_deal_order_pairs(filtered_churned_ids, recent_ids)

        items = []
        for order in last_orders:
            u = order.user
            if not u:
                continue
            gd = order.group_deal
            uid = u.id
            base_total = float(order.total) if order.total is not None else 0.0
            adj = float(order.adjustment_amount) if order.adjustment_amount is not None else 0.0
            final_total = round(base_total + adj, 2)
            items.append({
                'user': {
                    'id': u.id,
                    'nickname': u.nickname,
                    'phone': u.phone,
                    'wechat': u.wechat,
                    'user_source': u.user_source or 'default',
                },
                'total_non_cancelled_orders': counts.get(u.id, 0),
                'last_order': {
                    'id': order.id,
                    'order_number': order.order_number,
                    'created_at': order.created_at.isoformat() if order.created_at else None,
                    'status': order.status,
                    'final_total': final_total,
                },
                'last_group_deal': {
                    'id': gd.id,
                    'title': gd.title,
                    'order_end_date': gd.order_end_date.isoformat() if gd and gd.order_end_date else None,
                    'pickup_date': gd.pickup_date.isoformat() if gd and gd.pickup_date else None,
                } if gd else None,
                'deal_chips': _deal_chips_for_user(uid, recent_deals, pair_set),
                'feedback': {
                    'count': fu_counts.get(uid, 0),
                    'records': fu_records.get(uid, []),
                },
            })

        items.sort(key=lambda x: (x['last_order']['created_at'] or ''), reverse=True)

        return jsonify({
            'recent_group_deals': [d.to_dict() for d in recent_deals],
            'items': items,
            'feedback_outcome_options': FeedbackOutcome.all_values(),
        }), 200

    except Exception as e:
        current_app.logger.error(f'Error listing churned buyers: {e}', exc_info=True)
        return jsonify({'error': 'Failed to list churned buyers', 'message': str(e)}), 500


@admin_bp.route('/after-sales/product-repurchase-rates', methods=['GET'])
def get_after_sales_product_repurchase_rates():
    """Per-product repurchase rate from live orders (有效订单, excluding admins)."""
    _admin_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code

    try:
        admin_ids = _admin_user_ids()
        rows = compute_product_repurchase_rates(admin_user_ids=admin_ids)
        for r in rows:
            rr = r.get('repurchase_rate')
            if rr is not None:
                r['repurchase_rate'] = round(float(rr), 6)
        return jsonify({'items': rows}), 200
    except Exception as e:
        current_app.logger.error(f'Error computing product repurchase rates: {e}', exc_info=True)
        return jsonify({'error': 'Failed to compute repurchase rates', 'message': str(e)}), 500


# ============================================
# Work Document Routes
# ============================================

@admin_bp.route('/work-documents', methods=['GET'])
def list_work_documents():
    """Get all work documents"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        documents = WorkDocument.query.options(
            joinedload(WorkDocument.created_by),
            joinedload(WorkDocument.updated_by)
        ).order_by(WorkDocument.updated_at.desc()).all()
        
        return jsonify({
            'documents': [doc.to_dict() for doc in documents]
        }), 200
    except Exception as e:
        current_app.logger.error(f'Error listing work documents: {e}', exc_info=True)
        return jsonify({'error': 'Failed to list work documents', 'message': str(e)}), 500


@admin_bp.route('/work-documents/<int:document_id>', methods=['GET'])
def get_work_document(document_id):
    """Get a specific work document with action items"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        document = WorkDocument.query.options(
            joinedload(WorkDocument.created_by),
            joinedload(WorkDocument.updated_by),
            joinedload(WorkDocument.action_items).joinedload(ActionItem.assigned_to),
            joinedload(WorkDocument.action_items).joinedload(ActionItem.created_by)
        ).get(document_id)
        
        if not document:
            return jsonify({'error': 'Work document not found'}), 404
        
        doc_data = document.to_dict()
        doc_data['action_items'] = [item.to_dict() for item in document.action_items]
        
        return jsonify(doc_data), 200
    except Exception as e:
        current_app.logger.error(f'Error getting work document: {e}', exc_info=True)
        return jsonify({'error': 'Failed to get work document', 'message': str(e)}), 500


@admin_bp.route('/work-documents', methods=['POST'])
def create_work_document():
    """Create a new work document"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    validated_data, error_response, status_code = validate_request(CreateWorkDocumentSchema)
    if error_response:
        return error_response, status_code
    
    try:
        document = WorkDocument(
            title=validated_data['title'],
            content=validated_data['content'],
            created_by_id=user_id,
            updated_by_id=user_id
        )
        
        db.session.add(document)
        db.session.commit()
        
        return jsonify(document.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating work document: {e}', exc_info=True)
        return jsonify({'error': 'Failed to create work document', 'message': str(e)}), 500


@admin_bp.route('/work-documents/<int:document_id>', methods=['PUT', 'PATCH'])
def update_work_document(document_id):
    """Update a work document"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    validated_data, error_response, status_code = validate_request(UpdateWorkDocumentSchema)
    if error_response:
        return error_response, status_code
    
    try:
        document = WorkDocument.query.get(document_id)
        if not document:
            return jsonify({'error': 'Work document not found'}), 404
        
        if 'title' in validated_data and validated_data['title']:
            document.title = validated_data['title']
        if 'content' in validated_data and validated_data['content'] is not None:
            document.content = validated_data['content']
        
        document.updated_by_id = user_id
        document.updated_at = utc_now()
        
        db.session.commit()
        
        # Broadcast update to all connected clients
        try:
            import app
            if app.socketio is not None and hasattr(app.socketio, 'emit'):
                user = User.query.get(user_id)
                app.socketio.emit('document_changed', {
                    'document_id': document_id,
                    'updated_by': user.nickname or user.phone if user else 'Unknown',
                    'updated_at': document.updated_at.isoformat() if document.updated_at else None
                }, room=f'doc_{document_id}')
        except Exception as ws_error:
            current_app.logger.debug(f'Failed to broadcast document update: {ws_error}')
        
        return jsonify(document.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating work document: {e}', exc_info=True)
        return jsonify({'error': 'Failed to update work document', 'message': str(e)}), 500


@admin_bp.route('/work-documents/<int:document_id>', methods=['DELETE'])
def delete_work_document(document_id):
    """Delete a work document"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        document = WorkDocument.query.get(document_id)
        if not document:
            return jsonify({'error': 'Work document not found'}), 404
        
        db.session.delete(document)
        db.session.commit()
        
        return jsonify({'message': 'Work document deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting work document: {e}', exc_info=True)
        return jsonify({'error': 'Failed to delete work document', 'message': str(e)}), 500


# ============================================
# Action Item Routes
# ============================================

@admin_bp.route('/action-items', methods=['GET'])
def list_action_items():
    """Get all action items, optionally filtered by status or assigned user"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        query = ActionItem.query.options(
            joinedload(ActionItem.assigned_to),
            joinedload(ActionItem.created_by),
            joinedload(ActionItem.document)
        )
        
        status = request.args.get('status')
        if status:
            query = query.filter_by(status=status)
        
        assigned_to_id = request.args.get('assigned_to_id')
        if assigned_to_id:
            query = query.filter_by(assigned_to_id=int(assigned_to_id))
        
        document_id = request.args.get('document_id')
        if document_id:
            query = query.filter_by(document_id=int(document_id))
        
        action_items = query.order_by(ActionItem.created_at.desc()).all()
        
        return jsonify({
            'action_items': [item.to_dict() for item in action_items]
        }), 200
    except Exception as e:
        current_app.logger.error(f'Error listing action items: {e}', exc_info=True)
        return jsonify({'error': 'Failed to list action items', 'message': str(e)}), 500


@admin_bp.route('/action-items', methods=['POST'])
def create_action_item():
    """Create a new action item"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    validated_data, error_response, status_code = validate_request(CreateActionItemSchema)
    if error_response:
        return error_response, status_code
    
    try:
        document = WorkDocument.query.get(validated_data['document_id'])
        if not document:
            return jsonify({'error': 'Work document not found'}), 404
        
        if validated_data.get('assigned_to_id'):
            assigned_user = User.query.get(validated_data['assigned_to_id'])
            if not assigned_user:
                return jsonify({'error': 'Assigned user not found'}), 404
        
        action_item = ActionItem(
            document_id=validated_data['document_id'],
            title=validated_data['title'],
            description=validated_data.get('description'),
            assigned_to_id=validated_data.get('assigned_to_id'),
            status=validated_data.get('status', 'pending'),
            due_date=validated_data.get('due_date'),
            created_by_id=user_id
        )
        
        db.session.add(action_item)
        db.session.commit()
        
        return jsonify(action_item.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating action item: {e}', exc_info=True)
        return jsonify({'error': 'Failed to create action item', 'message': str(e)}), 500


@admin_bp.route('/action-items/<int:item_id>', methods=['PUT', 'PATCH'])
def update_action_item(item_id):
    """Update an action item"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    validated_data, error_response, status_code = validate_request(UpdateActionItemSchema)
    if error_response:
        return error_response, status_code
    
    try:
        action_item = ActionItem.query.get(item_id)
        if not action_item:
            return jsonify({'error': 'Action item not found'}), 404
        
        if 'title' in validated_data and validated_data['title']:
            action_item.title = validated_data['title']
        if 'description' in validated_data:
            action_item.description = validated_data['description']
        if 'assigned_to_id' in validated_data:
            if validated_data['assigned_to_id']:
                assigned_user = User.query.get(validated_data['assigned_to_id'])
                if not assigned_user:
                    return jsonify({'error': 'Assigned user not found'}), 404
            action_item.assigned_to_id = validated_data['assigned_to_id']
        if 'status' in validated_data and validated_data['status']:
            old_status = action_item.status
            action_item.status = validated_data['status']
            if validated_data['status'] == 'completed' and old_status != 'completed':
                action_item.completed_at = utc_now()
            elif validated_data['status'] != 'completed':
                action_item.completed_at = None
        if 'due_date' in validated_data:
            action_item.due_date = validated_data['due_date']
        if 'completed_at' in validated_data:
            action_item.completed_at = validated_data['completed_at']
        
        action_item.updated_at = utc_now()
        
        db.session.commit()
        
        return jsonify(action_item.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating action item: {e}', exc_info=True)
        return jsonify({'error': 'Failed to update action item', 'message': str(e)}), 500


@admin_bp.route('/action-items/<int:item_id>', methods=['DELETE'])
def delete_action_item(item_id):
    """Delete an action item"""
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        action_item = ActionItem.query.get(item_id)
        if not action_item:
            return jsonify({'error': 'Action item not found'}), 404
        
        db.session.delete(action_item)
        db.session.commit()
        
        return jsonify({'message': 'Action item deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting action item: {e}', exc_info=True)
        return jsonify({'error': 'Failed to delete action item', 'message': str(e)}), 500


# --- Store credit & referrals (admin) ---

@admin_bp.route('/referral-program-config', methods=['GET'])
def admin_get_referral_program_config():
    _, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    cfg = referral_service.get_active_referral_config()
    return jsonify({'config': cfg.to_dict()}), 200


@admin_bp.route('/referral-program-config', methods=['PUT'])
def admin_put_referral_program_config():
    _, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    data = request.get_json() or {}
    cfg = ReferralProgramConfig.query.filter_by(is_active=True).order_by(
        ReferralProgramConfig.id.desc()
    ).first()
    if not cfg:
        cfg = ReferralProgramConfig(
            invitee_bonus_amount=Decimal('5'),
            inviter_reward_amount=Decimal('5'),
            is_active=True,
        )
        db.session.add(cfg)
    if 'invitee_bonus_amount' in data:
        cfg.invitee_bonus_amount = Decimal(str(data['invitee_bonus_amount']))
    if 'inviter_reward_amount' in data:
        cfg.inviter_reward_amount = Decimal(str(data['inviter_reward_amount']))
    if 'is_active' in data:
        cfg.is_active = bool(data['is_active'])
    db.session.commit()
    return jsonify({'config': cfg.to_dict()}), 200


@admin_bp.route('/credit-transactions', methods=['GET'])
def admin_list_credit_transactions():
    _, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    uid = request.args.get('user_id', type=int)
    limit = min(request.args.get('limit', default=50, type=int), 200)
    offset = request.args.get('offset', default=0, type=int)
    q = CreditTransaction.query.options(joinedload(CreditTransaction.user)).order_by(CreditTransaction.created_at.desc())
    if uid:
        q = q.filter(CreditTransaction.user_id == uid)
    total = q.count()
    rows = q.offset(offset).limit(limit).all()
    return jsonify({
        'transactions': [t.to_dict(include_user=True) for t in rows],
        'total': total,
        'limit': limit,
        'offset': offset,
    }), 200


@admin_bp.route('/users/<int:target_user_id>/credit', methods=['POST'])
def admin_grant_user_credit(target_user_id):
    admin_uid, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    data = request.get_json() or {}
    if 'amount' not in data:
        return jsonify({'error': 'amount is required'}), 400
    reason = (data.get('reason') or '').strip()
    if not reason:
        return jsonify({'error': 'reason is required'}), 400
    amount = Decimal(str(data['amount']))
    if amount == 0:
        return jsonify({'error': 'amount cannot be zero'}), 400
    user = User.query.get(target_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    try:
        credit_service.apply_credit_change(
            user,
            amount,
            credit_service.TX_ADMIN_GRANT,
            reason=reason,
            created_by_admin_user_id=admin_uid,
        )
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    db.session.refresh(user)
    return jsonify({'user': user.to_dict()}), 200


def _referral_record_user_summary(user):
    """Admin list: human-facing fields only (ids stay on the record for support)."""
    if not user:
        return None
    return {
        'id': user.id,
        'nickname': user.nickname or None,
        'wechat': user.wechat or None,
        'phone': user.phone or None,
    }


_REFERRAL_RECORD_STATUS_LABEL_ZH = {
    ReferralRecord.STATUS_PENDING_ORDER: '已绑定，未下单',
    ReferralRecord.STATUS_REWARDED: '已发放奖励',
}


def _referral_record_status_label_zh(status):
    if not status:
        return '—'
    return _REFERRAL_RECORD_STATUS_LABEL_ZH.get(status, f'未知（{status}）')


@admin_bp.route('/referrals', methods=['GET'])
def admin_list_referral_records():
    _, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    limit = min(request.args.get('limit', default=100, type=int), 500)
    offset = request.args.get('offset', default=0, type=int)
    q = ReferralRecord.query.order_by(ReferralRecord.created_at.desc())
    inviter_q = request.args.get('inviter_user_id', type=int)
    if inviter_q:
        q = q.filter(ReferralRecord.inviter_user_id == inviter_q)
    total = q.count()
    rows = q.offset(offset).limit(limit).all()
    payload = []
    for r in rows:
        inviter = User.query.get(r.inviter_user_id)
        invitee = User.query.get(r.invitee_user_id)
        completed = bool(r.first_completed_order_id)
        payload.append({
            **r.to_dict(),
            'status_label': _referral_record_status_label_zh(r.status),
            'inviter': _referral_record_user_summary(inviter),
            'invitee': _referral_record_user_summary(invitee),
            'invitee_has_completed_order': completed or (
                referral_service.user_has_completed_order(r.invitee_user_id) if not completed else True
            ),
        })
    return jsonify({'referrals': payload, 'total': total, 'limit': limit, 'offset': offset}), 200

