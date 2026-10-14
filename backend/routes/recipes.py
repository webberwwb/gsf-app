"""Public and customer recipe APIs."""
from flask import Blueprint, jsonify, request

from models import db
from models.user import AuthToken, User
from services import recipe_service
from services.recipe_service import RecipeError
from utils.recipe_images import GCS_AVAILABLE, PIL_AVAILABLE, resize_to_jpeg, store_recipe_jpeg

recipes_bp = Blueprint('recipes', __name__)


def _require_user():
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.replace('Bearer ', '', 1).strip() if auth_header.startswith('Bearer ') else auth_header.strip()
    if not token:
        return None, (jsonify({'error': '请先登录'}), 401)
    auth_token = AuthToken.query.filter_by(token=token, is_revoked=False).first()
    if not auth_token or not auth_token.is_valid():
        return None, (jsonify({'error': '请先登录'}), 401)
    user = User.query.get(auth_token.user_id)
    if not user or not user.is_active:
        return None, (jsonify({'error': '请先登录'}), 401)
    return user, None


def _optional_user():
    user, _err = _require_user()
    return user


def _payload():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return {}
    return data


def _error(exc):
    status = getattr(exc, 'status', 400)
    return jsonify({'error': str(exc)}), status


@recipes_bp.route('/recipes/counts', methods=['GET'])
def recipe_counts():
    return jsonify({'counts': recipe_service.product_counts()}), 200


@recipes_bp.route('/recipes/categories', methods=['GET'])
def recipe_categories():
    return jsonify({'categories': recipe_service.recipe_categories()}), 200


@recipes_bp.route('/recipes/images', methods=['POST'])
def upload_recipe_image():
    user, err = _require_user()
    if err:
        return err
    if not PIL_AVAILABLE or not GCS_AVAILABLE:
        return jsonify({'error': '图片上传暂不可用'}), 503
    file = request.files.get('image')
    if not file or not file.filename:
        return jsonify({'error': '请选择照片'}), 400
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in {'png', 'jpg', 'jpeg', 'gif', 'webp'}:
        return jsonify({'error': '请上传 jpg、png 或 webp 照片'}), 400
    try:
        jpeg, _size = resize_to_jpeg(file.read())
        url = store_recipe_jpeg(jpeg)
    except Exception:
        return jsonify({'error': '照片上传失败'}), 500
    return jsonify({'url': url}), 200


@recipes_bp.route('/recipes', methods=['GET'])
def list_recipes():
    user = _optional_user()
    mine = request.args.get('mine') == '1'
    liked = request.args.get('liked') == '1'
    collected = request.args.get('collected') == '1'
    if (mine or liked or collected) and not user:
        return jsonify({'error': '请先登录'}), 401
    product_raw = request.args.get('product_id')
    product_id = None
    if product_raw:
        try:
            product_id = int(product_raw)
        except ValueError:
            return jsonify({'error': '商品无效'}), 400
    category_raw = (request.args.get('category_id') or '').strip()
    category_id = None
    if category_raw:
        if category_raw == 'none':
            category_id = 'none'
        else:
            try:
                category_id = int(category_raw)
            except ValueError:
                return jsonify({'error': '分类无效'}), 400
    try:
        page = int(request.args.get('page') or 1)
    except ValueError:
        page = 1
    sort = request.args.get('sort') or 'latest'
    if sort not in ('latest', 'hearts'):
        sort = 'latest'
    data = recipe_service.list_recipes(
        user_id=user.id if user else None,
        product_id=product_id,
        category_id=category_id,
        sort=sort,
        page=page,
        mine=mine,
        liked=liked,
        collected=collected,
        per_page=request.args.get('per_page'),
    )
    return jsonify(data), 200


@recipes_bp.route('/products/<int:product_id>/recipes', methods=['GET'])
def product_recipes(product_id):
    user = _optional_user()
    data = recipe_service.list_recipes(
        user_id=user.id if user else None,
        product_id=product_id,
        sort='latest',
        page=1,
    )
    return jsonify({'count': data['total'], 'recipes': data['recipes']}), 200


@recipes_bp.route('/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    recipe = recipe_service.get_live_recipe(recipe_id)
    if not recipe:
        return jsonify({'error': '菜谱不存在'}), 404
    user = _optional_user()
    return jsonify({
        'recipe': recipe_service.recipe_dict(
            recipe, user.id if user else None, include_comments=True
        )
    }), 200


@recipes_bp.route('/recipes', methods=['POST'])
def create_recipe():
    user, err = _require_user()
    if err:
        return err
    try:
        recipe = recipe_service.create_recipe(user, _payload(), source='user')
        db.session.commit()
    except RecipeError as exc:
        db.session.rollback()
        return _error(exc)
    return jsonify({'recipe': recipe_service.recipe_dict(recipe, user.id, include_comments=True)}), 201


@recipes_bp.route('/recipes/<int:recipe_id>', methods=['PUT'])
def update_recipe(recipe_id):
    user, err = _require_user()
    if err:
        return err
    recipe = recipe_service.get_live_recipe(recipe_id)
    if not recipe:
        return jsonify({'error': '菜谱不存在'}), 404
    if recipe.author_user_id != user.id:
        return jsonify({'error': '只能修改自己的菜谱'}), 403
    try:
        recipe_service.update_recipe(recipe, _payload())
        db.session.commit()
    except RecipeError as exc:
        db.session.rollback()
        return _error(exc)
    return jsonify({'recipe': recipe_service.recipe_dict(recipe, user.id, include_comments=True)}), 200


@recipes_bp.route('/recipes/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    user, err = _require_user()
    if err:
        return err
    recipe = recipe_service.get_live_recipe(recipe_id)
    if not recipe:
        return jsonify({'error': '菜谱不存在'}), 404
    if recipe.author_user_id != user.id:
        return jsonify({'error': '只能删除自己的菜谱'}), 403
    recipe_service.soft_delete_recipe(recipe)
    db.session.commit()
    return jsonify({'ok': True}), 200


def _engagement(recipe_id, kind):
    user, err = _require_user()
    if err:
        return err
    recipe = recipe_service.get_live_recipe(recipe_id)
    if not recipe:
        return jsonify({'error': '菜谱不存在'}), 404
    adding = request.method == 'POST'
    if kind == 'heart':
        recipe_service.set_heart(recipe, user, adding)
    else:
        recipe_service.set_collect(recipe, user, adding)
    db.session.commit()
    return jsonify({'recipe': recipe_service.recipe_dict(recipe, user.id)}), 200


@recipes_bp.route('/recipes/<int:recipe_id>/heart', methods=['POST', 'DELETE'])
def recipe_heart(recipe_id):
    return _engagement(recipe_id, 'heart')


@recipes_bp.route('/recipes/<int:recipe_id>/collect', methods=['POST', 'DELETE'])
def recipe_collect(recipe_id):
    return _engagement(recipe_id, 'collect')


@recipes_bp.route('/recipes/<int:recipe_id>/comments', methods=['POST'])
def create_comment(recipe_id):
    user, err = _require_user()
    if err:
        return err
    recipe = recipe_service.get_live_recipe(recipe_id)
    if not recipe:
        return jsonify({'error': '菜谱不存在'}), 404
    payload = _payload()
    parent_id = payload.get('parent_id')
    if parent_id in ('', None):
        parent_id = None
    try:
        recipe_service.add_comment(recipe, user, payload.get('body'), parent_id)
        db.session.commit()
    except RecipeError as exc:
        db.session.rollback()
        return _error(exc)
    return jsonify({
        'recipe': recipe_service.recipe_dict(recipe, user.id, include_comments=True)
    }), 201


@recipes_bp.route('/recipes/<int:recipe_id>/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(recipe_id, comment_id):
    user, err = _require_user()
    if err:
        return err
    recipe = recipe_service.get_live_recipe(recipe_id)
    if not recipe:
        return jsonify({'error': '菜谱不存在'}), 404
    if recipe.author_user_id != user.id:
        return jsonify({'error': '只有作者可以删除评论'}), 403
    from models.recipe import RecipeComment
    comment = RecipeComment.query.filter_by(id=comment_id, recipe_id=recipe.id).first()
    if not comment or comment.deleted_at is not None:
        return jsonify({'error': '评论不存在'}), 404
    recipe_service.delete_comment(recipe, comment)
    db.session.commit()
    return jsonify({
        'recipe': recipe_service.recipe_dict(recipe, user.id, include_comments=True)
    }), 200
