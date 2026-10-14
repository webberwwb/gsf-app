"""Admin recipe list, official posts, delete, and voucher rewards."""
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request

from models import db
from models.base import est_now
from models.recipe import RecipeComment
from models.user import User
from routes.admin import require_admin_auth
from services import recipe_service
from services.credit_service import TX_ADMIN_GRANT, apply_credit_change
from services.recipe_service import RecipeError

admin_recipes_bp = Blueprint('admin_recipes', __name__)


def _payload():
    data = request.get_json(silent=True) or {}
    return data if isinstance(data, dict) else {}


@admin_recipes_bp.route('/recipes', methods=['GET'])
def admin_list_recipes():
    admin_id, err, status = require_admin_auth()
    if err:
        return err, status
    try:
        page = int(request.args.get('page') or 1)
    except ValueError:
        page = 1
    data = recipe_service.list_recipes(user_id=admin_id, sort='latest', page=page)
    return jsonify(data), 200


@admin_recipes_bp.route('/recipes', methods=['POST'])
def admin_create_recipe():
    admin_id, err, status = require_admin_auth()
    if err:
        return err, status
    user = User.query.get(admin_id)
    try:
        recipe = recipe_service.create_recipe(user, _payload(), source='official')
        db.session.commit()
    except RecipeError as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), exc.status
    return jsonify({'recipe': recipe_service.recipe_dict(recipe, admin_id, include_comments=True)}), 201


@admin_recipes_bp.route('/recipes/<int:recipe_id>', methods=['PUT'])
def admin_update_recipe(recipe_id):
    admin_id, err, status = require_admin_auth()
    if err:
        return err, status
    recipe = recipe_service.get_live_recipe(recipe_id)
    if not recipe:
        return jsonify({'error': '菜谱不存在'}), 404
    try:
        recipe_service.update_recipe(recipe, _payload())
        db.session.commit()
    except RecipeError as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), exc.status
    return jsonify({'recipe': recipe_service.recipe_dict(recipe, admin_id, include_comments=True)}), 200


@admin_recipes_bp.route('/recipes/<int:recipe_id>', methods=['DELETE'])
def admin_delete_recipe(recipe_id):
    _admin_id, err, status = require_admin_auth()
    if err:
        return err, status
    recipe = recipe_service.get_live_recipe(recipe_id)
    if not recipe:
        return jsonify({'error': '菜谱不存在'}), 404
    recipe_service.soft_delete_recipe(recipe)
    db.session.commit()
    return jsonify({'ok': True}), 200


@admin_recipes_bp.route('/recipes/<int:recipe_id>/comments/<int:comment_id>', methods=['DELETE'])
def admin_delete_comment(recipe_id, comment_id):
    admin_id, err, status = require_admin_auth()
    if err:
        return err, status
    recipe = recipe_service.get_live_recipe(recipe_id)
    if not recipe:
        return jsonify({'error': '菜谱不存在'}), 404
    comment = RecipeComment.query.filter_by(id=comment_id, recipe_id=recipe.id).first()
    if not comment or comment.deleted_at is not None:
        return jsonify({'error': '评论不存在'}), 404
    recipe_service.delete_comment(recipe, comment)
    db.session.commit()
    return jsonify({'recipe': recipe_service.recipe_dict(recipe, admin_id, include_comments=True)}), 200


@admin_recipes_bp.route('/recipes/<int:recipe_id>/reward', methods=['POST'])
def admin_reward_recipe(recipe_id):
    admin_id, err, status = require_admin_auth()
    if err:
        return err, status
    recipe = recipe_service.get_live_recipe(recipe_id)
    if not recipe:
        return jsonify({'error': '菜谱不存在'}), 404
    if recipe.rewarded_at is not None:
        return jsonify({'error': '这份菜谱已经发过代金券'}), 400
    payload = _payload()
    try:
        amount = Decimal(str(payload.get('amount')))
    except (InvalidOperation, TypeError):
        return jsonify({'error': '请填写金额'}), 400
    if amount <= 0:
        return jsonify({'error': '金额需要大于 0'}), 400
    reason = (payload.get('reason') or f'菜谱奖励：{recipe.title}').strip()
    if not reason:
        return jsonify({'error': '请填写原因'}), 400
    author = User.query.get(recipe.author_user_id)
    if not author:
        return jsonify({'error': '作者不存在'}), 404
    try:
        tx = apply_credit_change(
            author,
            amount,
            TX_ADMIN_GRANT,
            reason=reason,
            created_by_admin_user_id=admin_id,
            metadata={'recipe_id': recipe.id},
        )
        recipe.rewarded_at = est_now()
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 400
    return jsonify({
        'recipe': recipe_service.recipe_dict(recipe, admin_id),
        'transaction': tx.to_dict(),
    }), 200
