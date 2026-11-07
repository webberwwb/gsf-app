"""B端 delivery sheets keep prices even when the printed sheet hides them."""
from datetime import timedelta

from models import db
from models.base import utc_now
from models.product import Product
from models.user import AuthToken, User, UserRole
from constants.status_enums import UserStatus


def _admin():
    user = User(phone='+15550003001', nickname='Admin', status=UserStatus.ACTIVE.value)
    db.session.add(user)
    db.session.flush()
    db.session.add(UserRole(user_id=user.id, role='admin'))
    token = AuthToken(
        user_id=user.id,
        token='tok-b-delivery',
        token_type='bearer',
        expires_at=utc_now() + timedelta(days=1),
    )
    db.session.add(token)
    db.session.commit()
    return {'Authorization': f'Bearer {token.token}'}


def test_delivery_stores_prices_when_sheet_hides_them(app, db_session):
    headers = _admin()
    product = Product(name='Pegion / 乳鸽', pricing_type='per_item', pricing_data={'price': 17.5})
    db.session.add(product)
    db.session.commit()
    client = app.test_client()

    merchant = client.post('/api/admin/b-merchants', json={
        'name': '1001280318 Ontario Inc. (Fusion Foodmart)',
        'show_prices': False,
        'payment_due_days': 7,
    }, headers=headers)
    assert merchant.status_code == 201, merchant.get_json()
    merchant_id = merchant.get_json()['merchant']['id']
    assert merchant.get_json()['merchant']['show_prices'] is False

    created = client.post('/api/admin/b-deliveries', json={
        'merchant_id': merchant_id,
        'invoice_date': '2026-11-06',
        'due_date': '2026-11-13',
        'show_prices': False,
        'hst': 0,
        'discount': 5,
        'lines': [
            {'product_id': product.id, 'product_name': 'Pegion / 乳鸽', 'quantity': 10, 'unit': 'pc', 'unit_price': 17.5},
            {'product_name': 'Duck/水鸭', 'quantity': 15, 'unit': 'pc', 'unit_price': 22},
        ],
    }, headers=headers)
    assert created.status_code == 201, created.get_json()
    delivery = created.get_json()['delivery']
    assert delivery['show_prices'] is False
    assert delivery['subtotal'] == 505
    assert delivery['grand_total'] == 500
    assert delivery['lines'][0]['unit_price'] == 17.5
    assert delivery['lines'][0]['amount'] == 175
    assert delivery['lines'][1]['amount'] == 330
    assert delivery['lines'][0]['product_id'] == product.id

    listed = client.get(f'/api/admin/b-deliveries?merchant_id={merchant_id}', headers=headers)
    assert listed.status_code == 200
    body = listed.get_json()
    assert body['aggregates']['count'] == 1
    assert body['aggregates']['grand_total'] == 500
    assert body['aggregates']['unpaid_total'] == 500
    assert body['aggregates']['paid_total'] == 0

    paid = client.put(f"/api/admin/b-deliveries/{delivery['id']}", json={
        'merchant_id': merchant_id,
        'invoice_date': '2026-11-06',
        'due_date': '2026-11-13',
        'show_prices': True,
        'payment_status': 'paid',
        'hst': 0,
        'discount': 5,
        'lines': [
            {'product_name': 'Pegion / 乳鸽', 'quantity': 10, 'unit': 'pc', 'unit_price': 17.5},
            {'product_name': 'Duck/水鸭', 'quantity': 15, 'unit': 'pc', 'unit_price': 22},
        ],
    }, headers=headers)
    assert paid.status_code == 200, paid.get_json()
    assert paid.get_json()['delivery']['payment_status'] == 'paid'
    assert paid.get_json()['delivery']['show_prices'] is True
    assert paid.get_json()['delivery']['paid_at']
