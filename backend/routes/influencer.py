"""Customer-app APIs for 推荐官 (influencer role)."""
from flask import Blueprint, jsonify, request

from models.user import User, AuthToken
from services import influencer_service

influencer_bp = Blueprint('influencer', __name__)


def require_influencer_auth():
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
    user = User.query.get(auth_token.user_id)
    if not user or not user.is_active:
        return None, jsonify({'error': 'User not found or inactive'}), 401
    if not user.is_influencer:
        return None, jsonify({'error': '推荐官权限不足'}), 403
    return user, None, None


@influencer_bp.route('/me', methods=['GET'])
def influencer_me():
    user, err, code = require_influencer_auth()
    if err:
        return err, code
    data = influencer_service.dashboard_for(user.id)
    data['user'] = {
        'id': user.id,
        'nickname': user.nickname,
        'is_influencer': True,
        'referral_code': user.referral_code,
    }
    return jsonify(data), 200


@influencer_bp.route('/customers', methods=['GET'])
def influencer_customers():
    user, err, code = require_influencer_auth()
    if err:
        return err, code
    return jsonify({'customers': influencer_service.customers_for(user.id)}), 200


@influencer_bp.route('/customers/<int:customer_id>', methods=['GET'])
def influencer_customer_detail(customer_id):
    user, err, code = require_influencer_auth()
    if err:
        return err, code
    detail = influencer_service.customer_detail_for(user.id, customer_id)
    if not detail:
        return jsonify({'error': '客户不存在'}), 404
    return jsonify(detail), 200


@influencer_bp.route('/rates', methods=['GET'])
def influencer_rates():
    user, err, code = require_influencer_auth()
    if err:
        return err, code
    return jsonify({'rates': influencer_service.effective_rates_for_influencer(user.id)}), 200
