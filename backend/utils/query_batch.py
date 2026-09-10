"""Shared IN() loaders so list/detail serializers avoid per-row query.get."""
from sqlalchemy.orm import joinedload, selectinload

from models.product import Product
from models.user import User
from utils.deal_products import product_eager_options


def unique_ids(values):
    seen = set()
    ids = []
    for value in values:
        if value is None:
            continue
        vid = int(value)
        if vid in seen:
            continue
        seen.add(vid)
        ids.append(vid)
    return ids


def rows_by_id(model, ids, *options):
    ids = unique_ids(ids)
    if not ids:
        return {}
    query = model.query
    if options:
        query = query.options(*options)
    return {row.id: row for row in query.filter(model.id.in_(ids)).all()}


def products_by_ids(ids):
    return rows_by_id(Product, ids, *product_eager_options())


def users_by_ids(ids):
    return rows_by_id(
        User,
        ids,
        selectinload(User.roles),
        selectinload(User.influencer_profile),
    )


def order_storefront_eager_options():
    from models.order import Order, OrderItem
    return (
        selectinload(Order.items).selectinload(OrderItem.product).selectinload(Product.variants),
        selectinload(Order.items).joinedload(OrderItem.source_order),
        selectinload(Order.address),
        joinedload(Order.group_deal),
    )


def order_admin_eager_options():
    from models.order import Order, OrderItem
    return (
        joinedload(Order.user).selectinload(User.roles),
        joinedload(Order.user).selectinload(User.influencer_profile),
        selectinload(Order.items).selectinload(OrderItem.product).selectinload(Product.variants),
        selectinload(Order.items).joinedload(OrderItem.source_order),
        selectinload(Order.address),
        joinedload(Order.group_deal),
    )
