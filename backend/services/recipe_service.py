"""Recipe reads, writes, hearts, collects, and comments."""
from models import db
from models.base import est_now
from models.groupdeal import GroupDeal, GroupDealProduct
from models.product import Product
from models.product_category import ProductCategory
from models.recipe import Recipe, RecipeCollect, RecipeComment, RecipeHeart, RecipeProduct
from models.user import User
from constants.status_enums import GroupDealStatus

TITLE_MAX = 80
BODY_MAX = 4000
SIDES_MAX = 500
COMMENT_MAX = 500
DIFFICULTIES = ('easy', 'medium', 'hard')
COOK_TIMES = ('under_1h', '1_to_4h', 'over_4h')
DIFFICULTY_LABELS = {'easy': '新手友好', 'medium': '花点功夫', 'hard': '大制作'}
COOK_TIME_LABELS = {'under_1h': '1小时内', '1_to_4h': '1–4小时', 'over_4h': '4小时以上'}
IMAGE_MAX = 6
PAGE_SIZE = 20


class RecipeError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def _clean_text(value, limit):
    text = (value or '').strip()
    if len(text) > limit:
        text = text[:limit]
    return text


def _is_recipe_image(url):
    return (
        isinstance(url, str)
        and '/api/images/recipes/' in url
        and len(url) <= 512
        and ' ' not in url
    )


def _live_query():
    return Recipe.query.filter(Recipe.deleted_at.is_(None))


def author_dict(recipe):
    if recipe.source == 'official':
        return {'name': '谷语农庄', 'initial': '谷', 'official': True}
    user = recipe.author
    name = (user.nickname if user else None) or '用户'
    return {
        'name': name,
        'initial': name[:1] or '用',
        'official': False,
        'user_id': recipe.author_user_id,
    }


def _open_deal_ids(product_ids):
    if not product_ids:
        return {}
    rows = (
        db.session.query(GroupDealProduct.product_id, GroupDeal.id)
        .join(GroupDeal, GroupDeal.id == GroupDealProduct.group_deal_id)
        .filter(
            GroupDealProduct.product_id.in_(product_ids),
            GroupDeal.status == GroupDealStatus.ACTIVE.value,
            GroupDeal.deleted_at.is_(None),
        )
        .order_by(GroupDeal.order_start_date.desc())
        .all()
    )
    found = {}
    for product_id, deal_id in rows:
        found.setdefault(product_id, deal_id)
    return found


def product_dicts(recipe):
    links = list(recipe.product_links or [])
    ids = [link.product_id for link in links]
    deals = _open_deal_ids(ids)
    out = []
    for link in links:
        product = link.product
        if not product or product.deleted_at is not None:
            continue
        image = None
        if product.images and isinstance(product.images, list) and product.images:
            image = product.images[0]
        elif product.image:
            image = product.image
        out.append({
            'id': product.id,
            'name': product.name,
            'image': image,
            'open_deal_id': deals.get(product.id),
        })
    return out


def comment_tree(recipe):
    rows = (
        RecipeComment.query.filter_by(recipe_id=recipe.id)
        .filter(RecipeComment.deleted_at.is_(None))
        .order_by(RecipeComment.created_at.asc())
        .all()
    )
    replies = {}
    tops = []
    for row in rows:
        if row.parent_id:
            replies.setdefault(row.parent_id, []).append(row)
        else:
            tops.append(row)

    def one(row):
        user = row.author
        name = (user.nickname if user else None) or '用户'
        return {
            'id': row.id,
            'body': row.body,
            'created_at': row.created_at.isoformat() if row.created_at else None,
            'user_id': row.user_id,
            'author_name': name,
            'initial': name[:1] or '用',
            'replies': [one(child) for child in replies.get(row.id, [])],
        }

    return [one(row) for row in tops]


def viewer_flags(recipe_ids, user_id):
    if not user_id or not recipe_ids:
        return set(), set()
    hearts = {
        row.recipe_id
        for row in RecipeHeart.query.filter(
            RecipeHeart.user_id == user_id,
            RecipeHeart.recipe_id.in_(recipe_ids),
        ).all()
    }
    collects = {
        row.recipe_id
        for row in RecipeCollect.query.filter(
            RecipeCollect.user_id == user_id,
            RecipeCollect.recipe_id.in_(recipe_ids),
        ).all()
    }
    return hearts, collects


def recipe_dict(recipe, user_id=None, include_comments=False, hearted=None, collected=None):
    if hearted is None or collected is None:
        hearts, collects = viewer_flags([recipe.id], user_id)
        hearted = recipe.id in hearts
        collected = recipe.id in collects
    data = {
        'id': recipe.id,
        'title': recipe.title,
        'body': recipe.body,
        'sides': recipe.sides or '',
        'difficulty': recipe.difficulty,
        'difficulty_label': DIFFICULTY_LABELS.get(recipe.difficulty),
        'cook_time': recipe.cook_time,
        'cook_time_label': COOK_TIME_LABELS.get(recipe.cook_time),
        'images': list(recipe.images or []),
        'cover_image': recipe.cover_image,
        'source': recipe.source,
        'author': author_dict(recipe),
        'products': product_dicts(recipe),
        'heart_count': recipe.heart_count or 0,
        'collect_count': recipe.collect_count or 0,
        'comment_count': recipe.comment_count or 0,
        'hearted': bool(hearted),
        'collected': bool(collected),
        'is_owner': bool(user_id and recipe.author_user_id == user_id),
        'rewarded_at': recipe.rewarded_at.isoformat() if recipe.rewarded_at else None,
        'created_at': recipe.created_at.isoformat() if recipe.created_at else None,
    }
    if include_comments:
        data['comments'] = comment_tree(recipe)
    return data


def _replace_products(recipe, product_ids):
    if not product_ids:
        raise RecipeError('请选择一个商品')
    seen = []
    for raw in product_ids:
        try:
            pid = int(raw)
        except (TypeError, ValueError):
            raise RecipeError('商品无效')
        if pid not in seen:
            seen.append(pid)
    if len(seen) != 1:
        raise RecipeError('一份菜谱只关联一个商品')
    products = Product.query.filter(Product.id.in_(seen), Product.deleted_at.is_(None)).all()
    by_id = {product.id: product for product in products}
    missing = [pid for pid in seen if pid not in by_id]
    if missing:
        raise RecipeError('有商品不存在或已删除')
    RecipeProduct.query.filter_by(recipe_id=recipe.id).delete()
    for index, pid in enumerate(seen):
        db.session.add(RecipeProduct(recipe_id=recipe.id, product_id=pid, sort_order=index))


def _apply_fields(recipe, payload, partial=False):
    if not partial or 'title' in payload:
        title = _clean_text(payload.get('title'), TITLE_MAX)
        if not title:
            raise RecipeError('请填写标题')
        recipe.title = title
    if not partial or 'body' in payload:
        body = _clean_text(payload.get('body'), BODY_MAX)
        if not body:
            raise RecipeError('请写下做法')
        recipe.body = body
    if not partial or 'sides' in payload:
        recipe.sides = _clean_text(payload.get('sides'), SIDES_MAX)
    if not partial or 'difficulty' in payload:
        difficulty = payload.get('difficulty')
        if difficulty not in DIFFICULTIES:
            raise RecipeError('请选择难易程度')
        recipe.difficulty = difficulty
    if not partial or 'cook_time' in payload:
        cook_time = payload.get('cook_time')
        if cook_time not in COOK_TIMES:
            raise RecipeError('请选择烹饪时长')
        recipe.cook_time = cook_time
    if not partial or 'images' in payload or 'cover_image' in payload:
        images = payload.get('images', recipe.images)
        if not isinstance(images, list) or not images:
            raise RecipeError('请至少上传一张照片')
        if len(images) > IMAGE_MAX:
            raise RecipeError(f'最多 {IMAGE_MAX} 张照片')
        cleaned = []
        for url in images:
            if not _is_recipe_image(url):
                raise RecipeError('照片无效')
            if url not in cleaned:
                cleaned.append(url)
        cover = payload.get('cover_image') or (recipe.cover_image if partial else None)
        if not cover:
            cover = cleaned[0]
        if cover not in cleaned:
            raise RecipeError('封面必须是已上传的照片')
        recipe.images = cleaned
        recipe.cover_image = cover
    if not partial or 'product_ids' in payload:
        db.session.flush()
        _replace_products(recipe, payload.get('product_ids') or [])


def create_recipe(user, payload, source='user'):
    recipe = Recipe(
        author_user_id=user.id,
        source=source if source in ('user', 'official') else 'user',
        title=' ',
        body=' ',
        images=[],
        cover_image=' ',
    )
    db.session.add(recipe)
    db.session.flush()
    _apply_fields(recipe, payload, partial=False)
    return recipe


def update_recipe(recipe, payload):
    _apply_fields(recipe, payload, partial=True)
    return recipe


def soft_delete_recipe(recipe):
    recipe.deleted_at = est_now()


def _toggle(model, recipe, user, count_attr, adding):
    existing = model.query.filter_by(recipe_id=recipe.id, user_id=user.id).first()
    if adding:
        if existing:
            return
        db.session.add(model(recipe_id=recipe.id, user_id=user.id))
        setattr(recipe, count_attr, (getattr(recipe, count_attr) or 0) + 1)
        return
    if not existing:
        return
    db.session.delete(existing)
    setattr(recipe, count_attr, max(0, (getattr(recipe, count_attr) or 0) - 1))


def set_heart(recipe, user, hearted):
    _toggle(RecipeHeart, recipe, user, 'heart_count', hearted)


def set_collect(recipe, user, collected):
    _toggle(RecipeCollect, recipe, user, 'collect_count', collected)


def add_comment(recipe, user, body, parent_id=None):
    text = _clean_text(body, COMMENT_MAX)
    if not text:
        raise RecipeError('请填写评论')
    parent = None
    if parent_id:
        parent = RecipeComment.query.filter_by(id=parent_id, recipe_id=recipe.id).first()
        if not parent or parent.deleted_at is not None:
            raise RecipeError('回复的评论不存在')
        if parent.parent_id is not None:
            raise RecipeError('只能回复一层')
    comment = RecipeComment(
        recipe_id=recipe.id,
        user_id=user.id,
        parent_id=parent.id if parent else None,
        body=text,
    )
    db.session.add(comment)
    recipe.comment_count = (recipe.comment_count or 0) + 1
    return comment


def delete_comment(recipe, comment):
    if comment.deleted_at is not None:
        return
    now = est_now()
    removed = 1
    comment.deleted_at = now
    if comment.parent_id is None:
        children = RecipeComment.query.filter_by(
            recipe_id=recipe.id, parent_id=comment.id
        ).filter(RecipeComment.deleted_at.is_(None)).all()
        for child in children:
            child.deleted_at = now
            removed += 1
    recipe.comment_count = max(0, (recipe.comment_count or 0) - removed)


def get_live_recipe(recipe_id):
    recipe = db.session.get(Recipe, recipe_id)
    if not recipe or recipe.deleted_at is not None:
        return None
    return recipe


def _recipes_in_category(category_id):
    query = (
        db.session.query(RecipeProduct.recipe_id)
        .join(Product, Product.id == RecipeProduct.product_id)
        .filter(Product.deleted_at.is_(None))
    )
    if category_id == 'none':
        query = query.filter(Product.category_id.is_(None))
    else:
        query = query.filter(Product.category_id == category_id)
    return query


def recipe_categories():
    """Categories that have at least one live recipe, in catalog order."""
    rows = (
        db.session.query(ProductCategory)
        .join(Product, Product.category_id == ProductCategory.id)
        .join(RecipeProduct, RecipeProduct.product_id == Product.id)
        .join(Recipe, Recipe.id == RecipeProduct.recipe_id)
        .filter(
            Recipe.deleted_at.is_(None),
            Product.deleted_at.is_(None),
            ProductCategory.is_active.is_(True),
        )
        .order_by(ProductCategory.sort_order.asc(), ProductCategory.id.asc())
        .distinct()
        .all()
    )
    categories = [{'id': row.id, 'name': row.name} for row in rows]
    has_other = (
        db.session.query(Recipe.id)
        .join(RecipeProduct, RecipeProduct.recipe_id == Recipe.id)
        .join(Product, Product.id == RecipeProduct.product_id)
        .filter(
            Recipe.deleted_at.is_(None),
            Product.deleted_at.is_(None),
            Product.category_id.is_(None),
        )
        .limit(1)
        .first()
    )
    if has_other:
        categories.append({'id': 'none', 'name': '其他'})
    return categories


def list_recipes(user_id=None, product_id=None, category_id=None, sort='latest', page=1, mine=False, liked=False, collected=False, per_page=None):
    query = _live_query()
    if product_id:
        query = query.join(RecipeProduct).filter(RecipeProduct.product_id == product_id)
    if category_id is not None:
        query = query.filter(Recipe.id.in_(_recipes_in_category(category_id)))
    if mine:
        query = query.filter(Recipe.author_user_id == user_id)
    if liked:
        query = query.join(RecipeHeart, RecipeHeart.recipe_id == Recipe.id).filter(RecipeHeart.user_id == user_id)
    if collected:
        query = query.join(RecipeCollect, RecipeCollect.recipe_id == Recipe.id).filter(
            RecipeCollect.user_id == user_id
        )
    if sort == 'hearts':
        query = query.order_by(Recipe.heart_count.desc(), Recipe.created_at.desc())
    else:
        query = query.order_by(Recipe.created_at.desc())
    page = max(1, page)
    try:
        size = int(per_page) if per_page else PAGE_SIZE
    except (TypeError, ValueError):
        size = PAGE_SIZE
    size = min(max(size, 1), PAGE_SIZE)
    total = query.count()
    rows = query.offset((page - 1) * size).limit(size).all()
    hearts, collects = viewer_flags([row.id for row in rows], user_id)
    return {
        'recipes': [
            recipe_dict(row, user_id, hearted=row.id in hearts, collected=row.id in collects)
            for row in rows
        ],
        'page': page,
        'per_page': size,
        'total': total,
    }


def product_counts():
    rows = (
        db.session.query(RecipeProduct.product_id, db.func.count(Recipe.id))
        .join(Recipe, Recipe.id == RecipeProduct.recipe_id)
        .filter(Recipe.deleted_at.is_(None))
        .group_by(RecipeProduct.product_id)
        .all()
    )
    return {str(product_id): count for product_id, count in rows}


def load_user(user_id):
    return db.session.get(User, user_id)
