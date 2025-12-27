from flask import Blueprint, jsonify, request, current_app
from models import db
from models.address import Address
from models.user import User, AuthToken
from datetime import datetime, timezone
from models.base import utc_now
from schemas.address import CreateAddressSchema, UpdateAddressSchema
from schemas.utils import validate_request

addresses_bp = Blueprint('addresses', __name__)

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

@addresses_bp.route('/addresses', methods=['GET'])
def get_user_addresses():
    """Get all addresses for the current authenticated user"""
    user_id, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        addresses = Address.query.filter_by(user_id=user_id).order_by(
            Address.is_default.desc(),
            Address.created_at.desc()
        ).all()
        
        return jsonify({
            'addresses': [address.to_dict() for address in addresses]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error fetching user addresses: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to fetch addresses',
            'message': str(e)
        }), 500

@addresses_bp.route('/addresses/<int:address_id>', methods=['GET'])
def get_address(address_id):
    """Get a single address by ID (must belong to current user)"""
    user_id, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        address = Address.query.filter_by(id=address_id, user_id=user_id).first()
        
        if not address:
            return jsonify({
                'error': 'Address not found'
            }), 404
        
        return jsonify({
            'address': address.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error fetching address: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to fetch address',
            'message': str(e)
        }), 500

@addresses_bp.route('/addresses', methods=['POST'])
def create_address():
    """Create a new address for the current authenticated user"""
    user_id, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        # Validate request data using schema
        validated_data, error_response, status_code = validate_request(CreateAddressSchema)
        if error_response:
            return error_response, status_code
        
        # If this is set as default, unset other default addresses
        is_default = validated_data.get('is_default', False)
        if is_default:
            Address.query.filter_by(user_id=user_id, is_default=True).update({'is_default': False})
        
        address = Address(
            user_id=user_id,
            recipient_name=validated_data['recipient_name'],
            phone=validated_data['phone'],
            address_line1=validated_data['address_line1'],
            address_line2=validated_data.get('address_line2'),
            city=validated_data['city'],
            province='Ontario',  # Always Ontario for GTA area
            postal_code=validated_data['postal_code'],
            country='Canada',  # Always Canada
            delivery_instructions=validated_data.get('delivery_instructions'),
            is_default=is_default
        )
        
        db.session.add(address)
        db.session.commit()
        
        current_app.logger.info(f'Created address: {address.id} for user: {user_id}')
        
        return jsonify({
            'address': address.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating address: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to create address',
            'message': str(e)
        }), 500

@addresses_bp.route('/addresses/<int:address_id>', methods=['PUT'])
def update_address(address_id):
    """Update an existing address (must belong to current user)"""
    user_id, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        address = Address.query.filter_by(id=address_id, user_id=user_id).first()
        
        if not address:
            return jsonify({
                'error': 'Address not found'
            }), 404
        
        # Validate request data using schema
        validated_data, error_response, status_code = validate_request(UpdateAddressSchema)
        if error_response:
            return error_response, status_code
        
        # Update fields
        if 'recipient_name' in validated_data:
            address.recipient_name = validated_data['recipient_name']
        if 'phone' in validated_data:
            address.phone = validated_data['phone']
        if 'address_line1' in validated_data:
            address.address_line1 = validated_data['address_line1']
        if 'address_line2' in validated_data:
            address.address_line2 = validated_data.get('address_line2')
        if 'city' in validated_data:
            address.city = validated_data['city']
        if 'postal_code' in validated_data:
            address.postal_code = validated_data['postal_code']
        if 'delivery_instructions' in validated_data:
            address.delivery_instructions = validated_data.get('delivery_instructions')
        
        # Always set province and country (not editable)
        address.province = 'Ontario'
        address.country = 'Canada'
        
        # Handle default address
        if 'is_default' in validated_data:
            is_default = validated_data['is_default']
            if is_default and not address.is_default:
                # Unset other default addresses
                Address.query.filter_by(user_id=user_id, is_default=True).update({'is_default': False})
            address.is_default = is_default
        
        db.session.commit()
        
        current_app.logger.info(f'Updated address: {address.id} for user: {user_id}')
        
        return jsonify({
            'address': address.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating address: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to update address',
            'message': str(e)
        }), 500

@addresses_bp.route('/addresses/<int:address_id>', methods=['DELETE'])
def delete_address(address_id):
    """Delete an address (must belong to current user)"""
    user_id, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        address = Address.query.filter_by(id=address_id, user_id=user_id).first()
        
        if not address:
            return jsonify({
                'error': 'Address not found'
            }), 404
        
        db.session.delete(address)
        db.session.commit()
        
        current_app.logger.info(f'Deleted address: {address_id} for user: {user_id}')
        
        return jsonify({
            'message': 'Address deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting address: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to delete address',
            'message': str(e)
        }), 500

@addresses_bp.route('/addresses/<int:address_id>/set-default', methods=['POST'])
def set_default_address(address_id):
    """Set an address as default (must belong to current user)"""
    user_id, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        address = Address.query.filter_by(id=address_id, user_id=user_id).first()
        
        if not address:
            return jsonify({
                'error': 'Address not found'
            }), 404
        
        # Unset other default addresses
        Address.query.filter_by(user_id=user_id, is_default=True).update({'is_default': False})
        
        # Set this address as default
        address.is_default = True
        db.session.commit()
        
        current_app.logger.info(f'Set default address: {address_id} for user: {user_id}')
        
        return jsonify({
            'address': address.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error setting default address: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to set default address',
            'message': str(e)
        }), 500

