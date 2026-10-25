"""Ask which still-open orders keep their price when the catalog list price changes.

Sale fields are not part of this choice. 本团折扣 applies them when a line is
priced, separately from an original-price update.
"""
from types import SimpleNamespace

from models.groupdeal import GroupDeal
from models.order import Order, OrderItem
from models.user import User
from utils.money import round_money
from utils.order_item_pricing import (
    build_priced_order_item,
    recalculate_existing_item,
    resnapshot_item_from_catalog,
    synthetic_snapshot_from_stored,
)
from utils.order_lock import deal_accepts_price_choice, order_money_locked
from utils.order_totals import sync_order_pricing


class _ProposedVariant:
    def __init__(self, row, product_id):
        self.id = row.get('id')
        self.name = (row.get('name') or '').strip()
        self.price_delta = row.get('price_delta') or 0
        self.price = row.get('price')
        self.sale_price = row.get('sale_price')
        self.quantity_breaks = row.get('quantity_breaks')
        self.is_active = row.get('is_active', True)
        self.product_id = product_id


def _proposed_product(product, data):
    data = data or {}
    ghost = SimpleNamespace()
    ghost.id = product.id
    ghost.name = product.name
    ghost.pricing_type = data.get('pricing_type', product.pricing_type)
    ghost.pricing_data = data.get('pricing_data', product.pricing_data)
    ghost.variants_share_price = data.get('variants_share_price', product.variants_share_price)
    ghost.counts_toward_free_shipping = data.get(
        'counts_toward_free_shipping', product.counts_toward_free_shipping
    )
    ghost.substitute_enabled = data.get('substitute_enabled', product.substitute_enabled)
    ghost.substitute_name = data.get('substitute_name', product.substitute_name)
    ghost.substitute_description = data.get('substitute_description', product.substitute_description)
    ghost.substitute_images = data.get('substitute_images', product.substitute_images)
    ghost.substitute_pricing_type = data.get('substitute_pricing_type', product.substitute_pricing_type)
    ghost.substitute_pricing_data = data.get('substitute_pricing_data', product.substitute_pricing_data)
    ghost.substitute_price = data.get('substitute_price', product.substitute_price)
    ghost.cutting_enabled = data.get('cutting_enabled', product.cutting_enabled)
    ghost.cutting_fee = data.get('cutting_fee', product.cutting_fee)
    ghost._variant_rows = None
    if 'variants' in data and data.get('variants') is not None:
        ghost._variant_rows = [
            _ProposedVariant(row, product.id)
            for row in data['variants']
            if (row.get('name') or '').strip()
        ]
    ghost.get_active_variants = lambda: [
        v for v in (product.variants or []) if getattr(v, 'is_active', True)
    ]
    ghost.get_substitute_dict = lambda: {}
    return ghost


_SALE_KEYS = ('sale_price', 'sale_price_per_unit', 'sale_amount_off')


def _strip_sale(pricing_data):
    """Shallow copy with catalog sale fields removed. Nested rows are shared."""
    if not isinstance(pricing_data, dict):
        return pricing_data
    cleaned = dict(pricing_data)
    for key in _SALE_KEYS:
        cleaned.pop(key, None)
    return cleaned


def _list_ghost(product, data):
    """Proposed product quoted at list price, ignoring sale and 推荐官 rates."""
    ghost = _proposed_product(product, data)
    ghost.pricing_data = _strip_sale(ghost.pricing_data)
    ghost.substitute_pricing_data = _strip_sale(ghost.substitute_pricing_data)
    ghost.is_discount = False
    ghost._deal_is_discount = False
    if ghost._variant_rows is not None:
        for row in ghost._variant_rows:
            row.sale_price = None
    return ghost


def _quote_line(ghost, item):
    return build_priced_order_item(
        ghost,
        quantity=item.quantity,
        final_weight=item.final_weight,
        variant_id=item.variant_id,
        accept_substitute=item.accept_substitute,
        cutting=bool(item.cutting),
        is_unavailable=bool(item.is_unavailable),
        cannot_fulfill=bool(item.cannot_fulfill),
        require_variant=False,
        variant_rows=ghost._variant_rows,
    )


def open_order_price_impact(product, validated_data):
    """Orders in a not-yet-closed deal whose charged total for the current line would change.

    Compares the current catalog list schedule with the proposed one: per-item
    price, price per unit, weight-range bands, bundle rate, variant price and
    price delta, and quantity breaks. Sale fields and the deal's 本团折扣 flag
    are ignored, so filling in a discount does not ask for a choice.

    Also fills a missing snapshot from the price stored today, while the product
    row still has its current schedule. Caller rolls back when the save is rejected.
    """
    from utils.influencer_pricing import attach_influencer_buyer_discount

    lines = OrderItem.query.filter(
        OrderItem.product_id == product.id,
        OrderItem.active(),
    ).all()
    if not lines:
        return {'orders': [], 'by_order': {}}

    order_ids = {line.order_id for line in lines}
    orders = {
        order.id: order
        for order in Order.query.filter(
            Order.id.in_(order_ids),
            Order.deleted_at.is_(None),
        ).all()
    }
    deal_ids = {order.group_deal_id for order in orders.values() if order.group_deal_id}
    deals = {
        deal.id: deal
        for deal in GroupDeal.query.filter(GroupDeal.id.in_(deal_ids)).all()
    } if deal_ids else {}
    user_ids = {order.user_id for order in orders.values()}
    users = {
        user.id: user
        for user in User.query.filter(User.id.in_(user_ids)).all()
    } if user_ids else {}

    current = _list_ghost(product, None)
    proposed = _list_ghost(product, validated_data)
    grouped = {}
    for line in lines:
        grouped.setdefault(line.order_id, []).append(line)

    api_orders = []
    by_order = {}
    for order_id, items in grouped.items():
        order = orders.get(order_id)
        if not order or order_money_locked(order):
            continue
        deal = deals.get(order.group_deal_id)
        if not deal_accepts_price_choice(deal):
            continue
        for item in items:
            if not item.pricing_snapshot:
                item.pricing_snapshot = synthetic_snapshot_from_stored(item, product)
        if hasattr(current, '_influencer_discount'):
            del current._influencer_discount
        if hasattr(proposed, '_influencer_discount'):
            del proposed._influencer_discount
        current_list = 0.0
        proposed_list = 0.0
        quoted_ok = True
        for item in items:
            try:
                current_list += float(_quote_line(current, item)['total_price'])
                proposed_list += float(_quote_line(proposed, item)['total_price'])
            except ValueError:
                quoted_ok = False
                break
        if not quoted_ok or round_money(current_list) == round_money(proposed_list):
            continue
        attach_influencer_buyer_discount(proposed, order.user_id)
        old_total = 0.0
        new_total = 0.0
        for item in items:
            old_total += float(item.total_price or 0)
            try:
                quoted = _quote_line(proposed, item)
            except ValueError:
                quoted_ok = False
                break
            new_total += float(quoted['total_price'])
        if not quoted_ok or round_money(old_total) == round_money(new_total):
            continue
        user = users.get(order.user_id)
        customer = ''
        if user:
            customer = user.nickname or user.phone or ''
        api_orders.append({
            'order_id': order.id,
            'order_number': order.order_number,
            'customer_name': customer,
            'group_deal_title': deal.title if deal else '',
            'old_total': float(round_money(old_total)),
            'new_total': float(round_money(new_total)),
        })
        by_order[order.id] = {'order': order, 'items': items}

    api_orders.sort(key=lambda row: row['order_number'] or '')
    return {'orders': api_orders, 'by_order': by_order}


def price_choice_rejection(impact, choices):
    """None when every affected order has an explicit old/new choice."""
    orders = impact.get('orders') or []
    if not orders:
        return None
    parsed = {}
    for row in choices or []:
        if not isinstance(row, dict) or row.get('order_id') is None:
            continue
        try:
            order_id = int(row['order_id'])
        except (TypeError, ValueError):
            continue
        choice = row.get('choice')
        if choice in ('old', 'new'):
            parsed[order_id] = choice
    needed = {row['order_id'] for row in orders}
    if set(parsed) != needed:
        return {
            'error': '请为每个未截单订单选择原价或新价',
            'code': 'price_choice_required',
            'orders': orders,
        }
    return None


def apply_order_price_choices(product, impact, choices):
    """Record locked_old, or reprice from the product as it stands now."""
    parsed = {}
    for row in choices or []:
        parsed[int(row['order_id'])] = row['choice']
    for order_id, bucket in (impact.get('by_order') or {}).items():
        choice = parsed.get(order_id)
        if choice not in ('old', 'new'):
            continue
        order = bucket['order']
        items = bucket['items']
        if choice == 'old':
            for item in items:
                if not item.pricing_snapshot:
                    item.pricing_snapshot = synthetic_snapshot_from_stored(item, product)
                item.price_choice = 'locked_old'
            continue
        for item in items:
            resnapshot_item_from_catalog(item, product, order, list_price_only=True)
            recalculate_existing_item(item, product)
            item.price_choice = 'applied_new'
        sync_order_pricing(order)


def apply_deal_sale_to_open_orders(deal, product_ids):
    """Reprice this deal's open orders after 本团折扣 is toggled. No per-order choice.

    The new GroupDealProduct rows must already be flushed so the sale flag is visible.
    Paid, completed, cancelled, and already-截单 orders are left as stored.
    Other group deals are not touched.
    """
    from models.product import Product

    if not product_ids or not deal_accepts_price_choice(deal):
        return
    product_ids = list({int(pid) for pid in product_ids})
    lines = OrderItem.query.filter(
        OrderItem.product_id.in_(product_ids),
        OrderItem.active(),
    ).all()
    if not lines:
        return
    order_ids = {line.order_id for line in lines}
    orders = {
        order.id: order
        for order in Order.query.filter(
            Order.id.in_(order_ids),
            Order.group_deal_id == deal.id,
            Order.deleted_at.is_(None),
        ).all()
    }
    products = {
        product.id: product
        for product in Product.query.filter(Product.id.in_(product_ids)).all()
    }
    touched = {}
    for line in lines:
        order = orders.get(line.order_id)
        if not order or order_money_locked(order):
            continue
        product = products.get(line.product_id)
        if not product:
            continue
        resnapshot_item_from_catalog(line, product, order)
        line.price_choice = None
        touched[order.id] = order
    for order in touched.values():
        sync_order_pricing(order)
