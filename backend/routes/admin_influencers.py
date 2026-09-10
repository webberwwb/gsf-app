"""Admin APIs for 推荐官 program."""
from decimal import Decimal

from flask import Blueprint, jsonify, request, current_app

from models import db
from models.influencer import (
    COMMISSION_PER_ITEM,
    COMMISSION_PER_WEIGHT,
    PAYOUT_CASH,
    PAYOUT_CREDIT,
    InfluencerCommissionEntry,
    InfluencerProductRate,
    InfluencerProfile,
    InfluencerRateOverride,
)
from models.product import Product
from models.user import User, UserRole
from routes.admin import require_admin_auth
from services import influencer_service

admin_influencers_bp = Blueprint('admin_influencers', __name__)


def _profile_row(profile):
    dash = influencer_service.dashboard_for(profile.user_id)
    user = profile.user
    return {
        'id': profile.id,
        'user_id': profile.user_id,
        'payout_type': profile.payout_type,
        'is_active': profile.is_active,
        'nickname': user.nickname if user else None,
        'phone': user.phone if user else None,
        'referral_code': user.referral_code if user else None,
        'customer_count': dash['customer_count'],
        'credited': dash['credited'],
        'payable': dash['payable'],
        'paid_cash': dash['paid_cash'],
        'customer_spend': dash['customer_spend'],
    }


@admin_influencers_bp.route('/influencers', methods=['GET'])
def list_influencers():
    admin_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    profiles = InfluencerProfile.query.order_by(InfluencerProfile.id.desc()).all()
    return jsonify({'influencers': [_profile_row(p) for p in profiles]}), 200


@admin_influencers_bp.route('/influencers', methods=['POST'])
def assign_influencer():
    admin_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    existing_role = UserRole.query.filter_by(user_id=user.id, role='influencer').first()
    if not existing_role:
        db.session.add(UserRole(user_id=user.id, role='influencer'))
    profile = influencer_service.activate_profile_for_user(user.id)
    db.session.commit()
    return jsonify({'influencer': _profile_row(profile)}), 200


@admin_influencers_bp.route('/influencers/<int:user_id>', methods=['DELETE'])
def unassign_influencer(user_id):
    admin_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    profile = InfluencerProfile.query.filter_by(user_id=user_id).first()
    role = UserRole.query.filter_by(user_id=user_id, role='influencer').first()
    if not profile and not role:
        return jsonify({'error': '该用户不是推荐官'}), 404
    if role:
        db.session.delete(role)
    influencer_service.deactivate_profile_for_user(user_id)
    db.session.commit()
    return jsonify({'message': '已移除推荐官'}), 200


@admin_influencers_bp.route('/influencers/config', methods=['GET'])
def get_influencer_config():
    admin_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    return jsonify({'config': influencer_service.get_active_config().to_dict()}), 200


@admin_influencers_bp.route('/influencers/config', methods=['PUT'])
def update_influencer_config():
    admin_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    data = request.get_json() or {}
    cfg = influencer_service.get_active_config()
    if 'lead_bonus_amount' in data:
        amt = Decimal(str(data['lead_bonus_amount'] or 0))
        if amt < 0:
            amt = Decimal('0')
        cfg.lead_bonus_amount = amt
    if 'is_active' in data:
        cfg.is_active = bool(data['is_active'])
    db.session.commit()
    return jsonify({'config': cfg.to_dict()}), 200


@admin_influencers_bp.route('/influencers/rates', methods=['GET'])
def list_global_rates():
    admin_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    influencer_service.ensure_default_global_rates()
    db.session.commit()
    products = Product.query.order_by(Product.sort_order, Product.id).all()
    rates = {r.product_id: r for r in InfluencerProductRate.query.all()}
    rows = []
    for product in products:
        rate = rates.get(product.id)
        rows.append({
            'product_id': product.id,
            'product_name': product.name,
            'pricing_type': product.pricing_type,
            'is_active': product.is_active,
            'commission_type': rate.commission_type if rate else COMMISSION_PER_ITEM,
            'amount': float(rate.amount) if rate and rate.amount is not None else 0,
        })
    return jsonify({'rates': rows}), 200


@admin_influencers_bp.route('/influencers/rates', methods=['PUT'])
def upsert_global_rate():
    admin_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    data = request.get_json() or {}
    product_id = data.get('product_id')
    if not product_id:
        return jsonify({'error': 'product_id is required'}), 400
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    commission_type = data.get('commission_type') or COMMISSION_PER_ITEM
    if commission_type not in (COMMISSION_PER_ITEM, COMMISSION_PER_WEIGHT):
        return jsonify({'error': 'Invalid commission_type'}), 400
    amount = Decimal(str(data.get('amount') or 0))
    if amount < 0:
        amount = Decimal('0')
    rate = InfluencerProductRate.query.filter_by(product_id=product_id).first()
    if not rate:
        rate = InfluencerProductRate(product_id=product_id)
        db.session.add(rate)
    rate.commission_type = commission_type
    rate.amount = amount
    db.session.commit()
    return jsonify({'rate': rate.to_dict(include_product=True)}), 200


@admin_influencers_bp.route('/influencers/<int:user_id>', methods=['GET'])
def get_influencer(user_id):
    admin_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    profile = InfluencerProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        return jsonify({'error': '推荐官不存在'}), 404
    data = _profile_row(profile)
    data['customers'] = influencer_service.customers_for(user_id, for_admin=True)
    data['overrides'] = [
        row.to_dict(include_product=True)
        for row in InfluencerRateOverride.query.filter_by(influencer_user_id=user_id).all()
    ]
    data['rates'] = influencer_service.effective_rates_for_influencer(user_id)
    data['payable_entries'] = [
        e.to_dict()
        for e in InfluencerCommissionEntry.query.filter_by(
            influencer_user_id=user_id,
            status='payable',
        ).order_by(InfluencerCommissionEntry.id.desc()).all()
    ]
    return jsonify({'influencer': data}), 200


@admin_influencers_bp.route('/influencers/<int:user_id>', methods=['PATCH'])
def update_influencer(user_id):
    admin_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    profile = InfluencerProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        return jsonify({'error': '推荐官不存在'}), 404
    data = request.get_json() or {}
    if 'payout_type' in data:
        if data['payout_type'] not in (PAYOUT_CREDIT, PAYOUT_CASH):
            return jsonify({'error': 'payout_type must be credit or cash'}), 400
        profile.payout_type = data['payout_type']
    if 'is_active' in data:
        profile.is_active = bool(data['is_active'])
    db.session.commit()
    return jsonify({'influencer': _profile_row(profile)}), 200


@admin_influencers_bp.route('/influencers/<int:user_id>/customers', methods=['POST'])
def assign_influencer_customer(user_id):
    admin_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    data = request.get_json() or {}
    customer_id = data.get('customer_user_id') or data.get('user_id')
    if not customer_id:
        return jsonify({'error': 'customer_user_id is required'}), 400
    try:
        customer, previous_id = influencer_service.bind_customer_to_influencer(user_id, int(customer_id))
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e, exc_info=True)
        return jsonify({'error': '绑定客户失败', 'message': str(e)}), 500
    return jsonify({
        'customer_user_id': customer.id,
        'influencer_user_id': user_id,
        'previous_referrer_user_id': previous_id,
        'customers': influencer_service.customers_for(user_id, for_admin=True),
    }), 200


@admin_influencers_bp.route('/influencers/<int:user_id>/customers/<int:customer_id>', methods=['DELETE'])
def unassign_influencer_customer(user_id, customer_id):
    admin_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    try:
        influencer_service.unbind_customer_from_influencer(user_id, customer_id)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e, exc_info=True)
        return jsonify({'error': '移除客户失败', 'message': str(e)}), 500
    return jsonify({
        'message': '已移除客户',
        'customers': influencer_service.customers_for(user_id, for_admin=True),
    }), 200


@admin_influencers_bp.route('/influencers/<int:user_id>/overrides', methods=['PUT'])
def upsert_override(user_id):
    admin_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    profile = InfluencerProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        return jsonify({'error': '推荐官不存在'}), 404
    data = request.get_json() or {}
    product_id = data.get('product_id')
    if not product_id:
        return jsonify({'error': 'product_id is required'}), 400
    if not Product.query.get(product_id):
        return jsonify({'error': 'Product not found'}), 404
    commission_type = data.get('commission_type') or COMMISSION_PER_ITEM
    if commission_type not in (COMMISSION_PER_ITEM, COMMISSION_PER_WEIGHT):
        return jsonify({'error': 'Invalid commission_type'}), 400
    amount = Decimal(str(data.get('amount') or 0))
    if amount < 0:
        amount = Decimal('0')
    row = InfluencerRateOverride.query.filter_by(
        influencer_user_id=user_id,
        product_id=product_id,
    ).first()
    if not row:
        row = InfluencerRateOverride(influencer_user_id=user_id, product_id=product_id)
        db.session.add(row)
    row.commission_type = commission_type
    row.amount = amount
    db.session.commit()
    return jsonify({'override': row.to_dict(include_product=True)}), 200


@admin_influencers_bp.route('/influencers/<int:user_id>/overrides/<int:product_id>', methods=['DELETE'])
def delete_override(user_id, product_id):
    admin_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    row = InfluencerRateOverride.query.filter_by(
        influencer_user_id=user_id,
        product_id=product_id,
    ).first()
    if not row:
        return jsonify({'error': 'Override not found'}), 404
    db.session.delete(row)
    db.session.commit()
    return jsonify({'message': 'Override removed'}), 200


@admin_influencers_bp.route('/influencers/cash-payouts', methods=['POST'])
def mark_cash_payouts():
    admin_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    data = request.get_json() or {}
    entry_ids = data.get('entry_ids') or []
    if not isinstance(entry_ids, list) or not entry_ids:
        return jsonify({'error': 'entry_ids is required'}), 400
    try:
        updated = influencer_service.mark_cash_paid([int(i) for i in entry_ids], admin_id)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e, exc_info=True)
        return jsonify({'error': 'Failed to mark paid', 'message': str(e)}), 500
    return jsonify({
        'updated': [e.to_dict() for e in updated],
        'count': len(updated),
    }), 200
