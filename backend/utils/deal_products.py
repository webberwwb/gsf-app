"""Batch-load group-deal products so storefront/admin deal payloads avoid N+1."""
from sqlalchemy.orm import joinedload, selectinload

from models.groupdeal import GroupDealProduct, deal_product_to_dict
from models.product import Product


def product_eager_options():
    """Eager-load relations Product.to_dict() always touches."""
    return (
        selectinload(Product.variants),
        joinedload(Product.category),
        joinedload(Product.supplier),
    )


def deal_product_eager_options():
    return (
        joinedload(GroupDealProduct.product).selectinload(Product.variants),
        joinedload(GroupDealProduct.product).joinedload(Product.category),
        joinedload(GroupDealProduct.product).joinedload(Product.supplier),
    )


def load_group_deal_products(deal_ids):
    """Load GroupDealProduct rows for one or more deals with product relations."""
    if deal_ids is None:
        return []
    if isinstance(deal_ids, int):
        ids = [deal_ids]
    else:
        ids = list(deal_ids)
    if not ids:
        return []
    return (
        GroupDealProduct.query.options(*deal_product_eager_options())
        .filter(GroupDealProduct.group_deal_id.in_(ids))
        .all()
    )


def group_deal_products_by_deal(deal_products):
    grouped = {}
    for dp in deal_products:
        grouped.setdefault(dp.group_deal_id, []).append(dp)
    return grouped


def serialize_loaded_deal_products(
    deal_products,
    buyer=None,
    include_all_variants=False,
    active_products_only=False,
):
    """Serialize already-loaded deal products. Buyer influencer rates are batched."""
    rows = []
    for dp in deal_products:
        product = dp.product
        if not product:
            continue
        if active_products_only and not product.is_active:
            continue
        rows.append(dp)

    rate_by_product = {}
    apply_inf = bool(buyer and getattr(buyer, 'is_influencer', False))
    if apply_inf and rows:
        from services import influencer_service
        from utils.influencer_pricing import apply_influencer_discount_to_product_payload
        rate_by_product = influencer_service.resolve_rates_for_products(
            buyer.id, [dp.product_id for dp in rows]
        )
    else:
        apply_influencer_discount_to_product_payload = None

    products_data = []
    for dp in rows:
        data = deal_product_to_dict(
            dp, include_all_variants=include_all_variants, product=dp.product
        )
        if data and apply_inf:
            data = apply_influencer_discount_to_product_payload(
                data, buyer.id, resolved=rate_by_product.get(dp.product_id)
            )
        if data:
            products_data.append(data)
    return products_data
