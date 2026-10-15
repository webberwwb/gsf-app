"""Recipe feed, delete, comments, hearts, image resize, and voucher reward."""
import io
from datetime import timedelta

import pytest
from PIL import Image

from constants import feature_flags

from constants.status_enums import UserStatus
from models import db
from models.base import utc_now
from models.credit_transaction import CreditTransaction
from models.product import Product
from models.recipe import Recipe
from models.user import AuthToken, User, UserRole
from utils.recipe_images import resize_to_jpeg

IMAGE = 'https://backend.grainstoryfarm.ca/api/images/recipes/test-photo.jpg'


@pytest.fixture(autouse=True)
def recipes_open_to_everyone(monkeypatch):
    """Existing recipe tests assume customers can see the feed."""
    monkeypatch.setitem(feature_flags.FEATURE_FLAGS, 'recipes', 'all')


def _user(phone, nickname='用户'):
    user = User(phone=phone, nickname=nickname, status=UserStatus.ACTIVE.value)
    db.session.add(user)
    db.session.flush()
    return user


def _admin():
    user = _user('+15551110001', '管理员')
    db.session.add(UserRole(user_id=user.id, role='admin'))
    db.session.flush()
    return user


def _headers(user):
    existing = AuthToken.query.filter_by(user_id=user.id, is_revoked=False).first()
    if existing:
        return {'Authorization': f'Bearer {existing.token}'}
    token = AuthToken(
        user_id=user.id,
        token=f'tok-recipe-{user.id}',
        token_type='bearer',
        expires_at=utc_now() + timedelta(days=1),
    )
    db.session.add(token)
    db.session.flush()
    return {'Authorization': f'Bearer {token.token}'}


def _product(name='番茄'):
    product = Product(name=name, pricing_type='per_item', is_active=True)
    db.session.add(product)
    db.session.flush()
    return product


def _png(width, height, color=(20, 120, 40)):
    image = Image.new('RGB', (width, height), color)
    buf = io.BytesIO()
    image.save(buf, format='PNG')
    return buf.getvalue()


def _create(client, headers, product, title='红烧番茄'):
    return client.post('/api/recipes', json={
        'title': title,
        'body': '切片，下锅，收汁。',
        'sides': '葱、姜',
        'difficulty': 'easy',
        'cook_time': 'under_1h',
        'images': [IMAGE],
        'cover_image': IMAGE,
        'product_ids': [product.id],
    }, headers=headers)


def test_resize_keeps_aspect_and_does_not_crop():
    jpeg, size = resize_to_jpeg(_png(2000, 1000))
    assert size == (960, 480)
    assert jpeg[:2] == b'\xff\xd8'


def test_new_recipe_is_public_and_delete_hides_it(app, db_session):
    author = _user('+15551110002', '小厨')
    product = _product()
    db.session.commit()
    client = app.test_client()
    headers = _headers(author)

    created = _create(client, headers, product)
    assert created.status_code == 201, created.get_json()
    recipe_id = created.get_json()['recipe']['id']

    public = client.get('/api/recipes')
    assert public.status_code == 200
    assert [row['id'] for row in public.get_json()['recipes']] == [recipe_id]

    by_product = client.get(f'/api/products/{product.id}/recipes')
    assert by_product.get_json()['count'] == 1

    share = client.get(f'/share/recipes/{recipe_id}')
    assert share.status_code == 200
    assert '红烧番茄' in share.get_data(as_text=True)
    assert IMAGE in share.get_data(as_text=True)

    deleted = client.delete(f'/api/recipes/{recipe_id}', headers=headers)
    assert deleted.status_code == 200

    assert client.get('/api/recipes').get_json()['recipes'] == []
    assert client.get(f'/api/products/{product.id}/recipes').get_json()['count'] == 0
    gone = client.get(f'/share/recipes/{recipe_id}')
    assert gone.status_code == 404
    assert '不可用' in gone.get_data(as_text=True)


def test_heart_is_idempotent(app, db_session):
    author = _user('+15551110003', '作者')
    fan = _user('+15551110004', '粉丝')
    product = _product()
    db.session.commit()
    client = app.test_client()
    recipe_id = _create(client, _headers(author), product).get_json()['recipe']['id']
    fan_headers = _headers(fan)

    first = client.post(f'/api/recipes/{recipe_id}/heart', headers=fan_headers)
    second = client.post(f'/api/recipes/{recipe_id}/heart', headers=fan_headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.get_json()['recipe']['heart_count'] == 1
    assert second.get_json()['recipe']['hearted'] is True

    db.session.expire_all()
    assert db.session.get(Recipe, recipe_id).heart_count == 1


def test_only_author_can_delete_comments(app, db_session):
    author = _user('+15551110005', '作者')
    other = _user('+15551110006', '路人')
    product = _product()
    db.session.commit()
    client = app.test_client()
    recipe_id = _create(client, _headers(author), product).get_json()['recipe']['id']

    commented = client.post(
        f'/api/recipes/{recipe_id}/comments',
        json={'body': '看起来很好吃'},
        headers=_headers(other),
    )
    assert commented.status_code == 201, commented.get_json()
    comment_id = commented.get_json()['recipe']['comments'][0]['id']

    denied = client.delete(
        f'/api/recipes/{recipe_id}/comments/{comment_id}',
        headers=_headers(other),
    )
    assert denied.status_code == 403

    removed = client.delete(
        f'/api/recipes/{recipe_id}/comments/{comment_id}',
        headers=_headers(author),
    )
    assert removed.status_code == 200
    assert removed.get_json()['recipe']['comments'] == []
    assert removed.get_json()['recipe']['comment_count'] == 0


def test_reply_is_one_level(app, db_session):
    author = _user('+15551110007', '作者')
    product = _product()
    db.session.commit()
    client = app.test_client()
    headers = _headers(author)
    recipe_id = _create(client, headers, product).get_json()['recipe']['id']
    parent = client.post(
        f'/api/recipes/{recipe_id}/comments',
        json={'body': '主楼'},
        headers=headers,
    ).get_json()['recipe']['comments'][0]
    reply = client.post(
        f'/api/recipes/{recipe_id}/comments',
        json={'body': '回复', 'parent_id': parent['id']},
        headers=headers,
    )
    assert reply.status_code == 201
    nested = reply.get_json()['recipe']['comments'][0]['replies'][0]['id']
    deeper = client.post(
        f'/api/recipes/{recipe_id}/comments',
        json={'body': '再回复', 'parent_id': nested},
        headers=headers,
    )
    assert deeper.status_code == 400


def test_upload_returns_public_recipe_url(app, db_session, monkeypatch):
    author = _user('+15551110008')
    db.session.commit()
    client = app.test_client()
    monkeypatch.setattr('routes.recipes.GCS_AVAILABLE', True)
    monkeypatch.setattr('routes.recipes.PIL_AVAILABLE', True)
    monkeypatch.setattr(
        'routes.recipes.store_recipe_jpeg',
        lambda jpeg: 'https://backend.grainstoryfarm.ca/api/images/recipes/abc.jpg',
    )
    response = client.post(
        '/api/recipes/images',
        data={'image': (io.BytesIO(_png(1200, 800)), 'plate.png')},
        content_type='multipart/form-data',
        headers=_headers(author),
    )
    assert response.status_code == 200, response.get_json()
    assert response.get_json()['url'].endswith('/api/images/recipes/abc.jpg')
    assert 'X-Goog-Signature' not in response.get_json()['url']


def test_filter_recipes_by_product_category(app, db_session):
    from models.product_category import ProductCategory

    veg = ProductCategory(name='蔬菜', is_active=True, sort_order=1)
    meat = ProductCategory(name='肉类', is_active=True, sort_order=2)
    db.session.add_all([veg, meat])
    db.session.flush()
    tomato = _product('番茄')
    tomato.category_id = veg.id
    pork = _product('猪肉')
    pork.category_id = meat.id
    loose = _product('散装')
    author = _user('+15551110010', '分类厨')
    db.session.commit()
    client = app.test_client()
    headers = _headers(author)
    veg_id = _create(client, headers, tomato, title='番茄炒蛋').get_json()['recipe']['id']
    meat_id = _create(client, headers, pork, title='红烧肉').get_json()['recipe']['id']
    loose_id = _create(client, headers, loose, title='家常菜').get_json()['recipe']['id']

    categories = client.get('/api/recipes/categories')
    assert categories.status_code == 200
    assert [(row['id'], row['name']) for row in categories.get_json()['categories']] == [
        (veg.id, '蔬菜'),
        (meat.id, '肉类'),
        ('none', '其他'),
    ]

    listed = client.get(f'/api/recipes?category_id={veg.id}')
    assert [row['id'] for row in listed.get_json()['recipes']] == [veg_id]
    meat_list = client.get(f'/api/recipes?category_id={meat.id}')
    assert [row['id'] for row in meat_list.get_json()['recipes']] == [meat_id]
    other = client.get('/api/recipes?category_id=none')
    assert [row['id'] for row in other.get_json()['recipes']] == [loose_id]
    assert client.get('/api/recipes?category_id=nope').status_code == 400


def test_admin_list_filters_by_product(app, db_session):
    admin = _admin()
    author = _user('+15551110011', '厨')
    tomato = _product('番茄')
    pork = _product('猪肉')
    db.session.commit()
    client = app.test_client()
    headers = _headers(author)
    tomato_id = _create(client, headers, tomato, title='番茄炒蛋').get_json()['recipe']['id']
    _create(client, headers, pork, title='红烧肉')

    listed = client.get(
        f'/api/admin/recipes?product_id={tomato.id}&sort=latest',
        headers=_headers(admin),
    )
    assert listed.status_code == 200, listed.get_json()
    body = listed.get_json()
    assert [row['id'] for row in body['recipes']] == [tomato_id]
    assert body['total'] == 1
    assert client.get('/api/admin/recipes?product_id=nope', headers=_headers(admin)).status_code == 400


def test_admin_reward_tags_recipe(app, db_session):
    admin = _admin()
    author = _user('+15551110009', '作者')
    product = _product()
    db.session.commit()
    client = app.test_client()
    recipe_id = _create(client, _headers(author), product, title='清炒时蔬').get_json()['recipe']['id']

    rewarded = client.post(
        f'/api/admin/recipes/{recipe_id}/reward',
        json={'amount': '5.00', 'reason': '菜谱奖励：清炒时蔬'},
        headers=_headers(admin),
    )
    assert rewarded.status_code == 200, rewarded.get_json()
    tx = CreditTransaction.query.filter_by(user_id=author.id).one()
    assert float(tx.delta) == 5
    assert tx.metadata_json['recipe_id'] == recipe_id
    assert tx.tx_type == 'admin_grant'

    again = client.post(
        f'/api/admin/recipes/{recipe_id}/reward',
        json={'amount': '1', 'reason': '再来一次'},
        headers=_headers(admin),
    )
    assert again.status_code == 400


def test_recipes_stay_hidden_until_opened_to_everyone(app, db_session, monkeypatch):
    monkeypatch.setitem(feature_flags.FEATURE_FLAGS, 'recipes', 'admins')
    admin = _admin()
    customer = _user('+15551110020', '顾客')
    product = _product()
    db.session.commit()
    client = app.test_client()
    created = _create(client, _headers(admin), product)
    assert created.status_code == 201, created.get_json()
    recipe_id = created.get_json()['recipe']['id']

    assert client.get('/api/features').get_json()['recipes'] is False
    assert client.get('/api/recipes').status_code == 404
    assert client.get('/api/recipes', headers=_headers(customer)).status_code == 404
    assert client.get('/api/recipes/counts').status_code == 404
    listed = client.get('/api/recipes', headers=_headers(admin))
    assert listed.status_code == 200
    assert listed.get_json()['recipes'][0]['id'] == recipe_id
    assert client.get('/api/features', headers=_headers(admin)).get_json()['recipes'] is True

    share = client.get(f'/share/recipes/{recipe_id}')
    assert share.status_code == 404
    assert '不可用' in share.get_data(as_text=True)

    monkeypatch.setitem(feature_flags.FEATURE_FLAGS, 'recipes', 'all')
    assert client.get('/api/features').get_json()['recipes'] is True
    opened = client.get(f'/share/recipes/{recipe_id}')
    assert opened.status_code == 200
    assert '红烧番茄' in opened.get_data(as_text=True)


def test_dev_customer_login_is_a_normal_user(app, db_session, monkeypatch):
    client = app.test_client()
    first = client.post('/api/auth/dev-customer-login')
    assert first.status_code == 200, first.get_json()
    body = first.get_json()
    assert body['token']
    assert body['user']['phone'] == '+15555550100'
    assert body['user']['nickname'] == '测试顾客'
    assert body['user']['is_admin'] is False
    assert 'admin' not in (body['user'].get('roles') or [])

    second = client.post('/api/auth/dev-customer-login')
    assert second.status_code == 200
    assert second.get_json()['user']['id'] == body['user']['id']

    monkeypatch.setenv('K_SERVICE', 'gsf-backend')
    denied = client.post('/api/auth/dev-customer-login')
    assert denied.status_code == 403


def test_dev_customer_login_refuses_privileged_phone(app, db_session):
    user = _user('+15555550100', '不该是管理员')
    db.session.add(UserRole(user_id=user.id, role='admin'))
    db.session.commit()
    client = app.test_client()
    denied = client.post('/api/auth/dev-customer-login')
    assert denied.status_code == 403
    assert denied.get_json().get('token') is None
