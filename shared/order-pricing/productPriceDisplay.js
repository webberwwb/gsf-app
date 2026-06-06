/**
 * Catalog / product list price labels (2-decimal money).
 */

import { roundMoney, formatMoney, formatMoneyDisplay } from './money.js'

export { formatMoney, formatMoneyDisplay, roundMoney } from './money.js'

/** Variant price delta, e.g. "+$1.50" or "-$0.25" */
export function formatVariantDelta(delta) {
  const d = roundMoney(delta)
  return `${d > 0 ? '+' : '-'}${formatMoneyDisplay(Math.abs(d))}`
}

/** e.g. "$10.00" or "$10.00 - $12.50" */
export function formatMoneyRangeDisplay(min, max) {
  const a = roundMoney(min)
  const b = roundMoney(max)
  if (a === b) return formatMoneyDisplay(a)
  return `${formatMoneyDisplay(a)} - ${formatMoneyDisplay(b)}`
}

/** e.g. "$3.99/lb" */
export function formatUnitPriceDisplay(pricePerUnit, unit = 'lb') {
  const p = roundMoney(pricePerUnit)
  if (!p) return '价格待定'
  return `${formatMoneyDisplay(p)}/${unit}`
}

/** Simple per-item price string for lists */
export function formatProductListPrice(product) {
  if (product?.display_price != null && product.display_price !== '') {
    return formatMoney(product.display_price)
  }
  if (product?.price != null && product.price !== '') {
    return formatMoney(product.price)
  }
  return '0.00'
}

/**
 * Human-readable price label for a product card (weight_range, unit_weight, bundled_weight).
 */
export function formatProductPriceRange(product) {
  if (!product) return '价格待定'
  const pt = product.pricing_type

  if (pt === 'weight_range') {
    const ranges = product.pricing_data?.ranges || []
    if (!ranges.length) return '价格待定'
    const sorted = [...ranges].sort((a, b) => (a.min || 0) - (b.min || 0))
    const prices = sorted.map((r) => parseFloat(r.price || 0)).filter((p) => p > 0)
    if (!prices.length) return '价格待定'
    return formatMoneyRangeDisplay(Math.min(...prices), Math.max(...prices))
  }

  if (pt === 'unit_weight') {
    const pricePerUnit = product.pricing_data?.price_per_unit || 0
    const unit = product.pricing_data?.unit || 'lb'
    return formatUnitPriceDisplay(pricePerUnit, unit)
  }

  if (pt === 'bundled_weight') {
    const pricePerUnit = product.pricing_data?.price_per_unit || 0
    const minWeight = product.pricing_data?.min_weight || 7
    const maxWeight = product.pricing_data?.max_weight || 15
    const unit = product.pricing_data?.unit || 'lb'
    if (!roundMoney(pricePerUnit)) return '价格待定'
    const minPrice = roundMoney(pricePerUnit * minWeight)
    const maxPrice = roundMoney(pricePerUnit * maxWeight)
    const unitPriceDisplay = formatUnitPriceDisplay(pricePerUnit, unit)
    if (minPrice === maxPrice) {
      return `${formatMoneyDisplay(minPrice)}/份 (${minWeight}-${maxWeight}${unit}/份) · ${unitPriceDisplay}`
    }
    return `${formatMoneyRangeDisplay(minPrice, maxPrice)}/份 (${minWeight}-${maxWeight}${unit}/份) · ${unitPriceDisplay}`
  }

  return '价格待定'
}

/** Template helper: $12.34 from number or string */
export function formatCatalogMoney(value) {
  return formatMoneyDisplay(value)
}
