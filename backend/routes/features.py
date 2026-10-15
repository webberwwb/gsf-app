"""Evaluated feature flags for the current customer-app viewer."""
from flask import Blueprint, jsonify, request

from constants.feature_flags import enabled_map
from models.user import AuthToken, User

features_bp = Blueprint('features', __name__, url_prefix='/api')


def _optional_user():
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.replace('Bearer ', '', 1).strip() if auth_header.startswith('Bearer ') else auth_header.strip()
    if not token:
        return None
    auth_token = AuthToken.query.filter_by(token=token, is_revoked=False).first()
    if not auth_token or not auth_token.is_valid():
        return None
    user = User.query.get(auth_token.user_id)
    if not user or not user.is_active:
        return None
    return user


@features_bp.route('/features', methods=['GET'])
def get_features():
    return jsonify(enabled_map(_optional_user())), 200
