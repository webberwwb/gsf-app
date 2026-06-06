export * from '@shared/order-pricing/orderItemPricing.js'

import { productRequiresVariant, productRequiresSubstituteChoice } from '@shared/order-pricing/orderItemPricing.js'

/** Build display fields for checkout / summary line items. */
export function toCheckoutLineDisplay(item, product) {
  const variant = (product?.variants || []).find((v) => v.id === item.variant_id)
  const variantName = item.variant_name || variant?.name || null
  let priceDisplay = null
  if (item.pricing_type === 'bundled_weight' && item.price_range) {
    priceDisplay = item.price_range
  }
  return {
    product_id: item.product_id,
    quantity: item.quantity,
    total_price: item.estimated_price,
    estimated_price: item.estimated_price,
    display_name: product?.name || '商品',
    variant_name: variantName,
    variant: variantName ? { name: variantName } : null,
    accept_substitute: item.accept_substitute,
    show_substitute_preference: productRequiresSubstituteChoice(product || {}),
    substitute_name: product?.substitute?.name,
    price_display: priceDisplay,
    is_substituted: false,
    is_struck_out: false
  }
}

/** Normalize API order item for OrderLineDisplay (app variant). */
export function toOrderLineDisplay(item) {
  if (!item) return item
  const product = item.product || {}
  const variantName = item.variant?.name || item.variant_name
  return {
    ...item,
    display_name: item.display_name || product.name || '商品',
    variant_name: variantName,
    show_substitute_preference: product.substitute_enabled || !!product.substitute?.enabled,
    substitute_name: product.substitute?.name
  }
}

export function getSelectionIncompleteMessage(product, selection = {}) {
  const name = product?.name || '该商品'
  if (productRequiresVariant(product) && !selection.variant_id) {
    return `请完成「${name}」的产品细节`
  }
  if (productRequiresSubstituteChoice(product) && selection.accept_substitute == null) {
    return `请确认「${name}」的备选产品`
  }
  return null
}
