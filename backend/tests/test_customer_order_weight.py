from types import SimpleNamespace

from schemas.order import AdminOrderItemSchema, OrderItemSchema
from utils.order_item_pricing import restore_existing_line_weights


def test_customer_order_item_schema_drops_final_weight():
    data = OrderItemSchema().load({
        'product_id': 1,
        'quantity': 2,
        'final_weight': 9.5,
    })
    assert 'final_weight' not in data


def test_admin_order_item_schema_keeps_final_weight():
    data = AdminOrderItemSchema().load({
        'product_id': 1,
        'quantity': 1,
        'final_weight': 9.5,
    })
    assert data['final_weight'] == 9.5


def test_restore_keeps_staff_weight_on_unchanged_line():
    existing = [SimpleNamespace(id=11, product_id=5, quantity=1, variant_id=None, final_weight=8.25)]
    items = [{'id': 11, 'product_id': 5, 'quantity': 1, 'final_weight': 99}]
    restore_existing_line_weights(items, existing)
    assert items[0]['final_weight'] == 8.25


def test_restore_drops_client_weight_on_changed_line():
    existing = [SimpleNamespace(id=11, product_id=5, quantity=1, variant_id=None, final_weight=8.25)]
    items = [{'id': 11, 'product_id': 5, 'quantity': 2, 'final_weight': 99}]
    restore_existing_line_weights(items, existing)
    assert 'final_weight' not in items[0]


def test_restore_drops_client_weight_on_new_line():
    items = [{'product_id': 5, 'quantity': 1, 'final_weight': 99}]
    restore_existing_line_weights(items, [])
    assert 'final_weight' not in items[0]
