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

export function formatQuantityBreakHint(product, variant = null) {
  const pd = product?.pricing_data || {}
  const share = product?.variants_share_price !== false
  const breaks = normalizeBreaks(
    !share && variant?.quantity_breaks ? variant.quantity_breaks : pd.quantity_breaks
  )
  if (!breaks.length) return ''
  return breaks.map((b) => `${b.min_qty}件起 ${formatMoneyDisplay(b.price)}/件`).join(' · ')
}

function normalizeBreaks(breaks) {
  if (!Array.isArray(breaks)) return []
  return [...breaks]
    .map((b) => ({ min_qty: parseInt(b.min_qty, 10), price: parseFloat(b.price) }))
    .filter((b) => Number.isFinite(b.min_qty) && b.min_qty >= 2 && Number.isFinite(b.price) && b.price >= 0)
    .sort((a, b) => a.min_qty - b.min_qty)
}

/** Chip label for a variant: absolute $ when different prices, else +/- delta. */
export function formatVariantPriceLabel(product, variant) {
  if (!variant) return ''
  if (product && product.variants_share_price === false) {
    const list = variant.price != null
      ? parseFloat(variant.price)
      : parseFloat(product.pricing_data?.price || product.price || 0) + parseFloat(variant.price_delta || 0)
    const sale = variant.sale_price != null ? parseFloat(variant.sale_price) : null
    const paid = product.is_discount && sale != null ? sale : list
    if (!Number.isFinite(paid)) return ''
    return formatMoneyDisplay(paid)
  }
  const d = parseFloat(variant.price_delta || 0)
  if (!d) return ''
  return formatVariantDelta(d)
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

/** Dollars off every weight band. Applies only when the deal marks 本团折扣. */
export function weightRangeSaleOff(product) {
  if (!product?.is_discount) return 0
  const off = parseFloat(product?.pricing_data?.sale_amount_off)
  return Number.isFinite(off) && off > 0 ? off : 0
}

/** Paid price for one weight band. List price when the deal is not on sale. */
export function weightRangePaidPrice(product, range) {
  const list = parseFloat(range?.price || 0)
  const off = weightRangeSaleOff(product)
  if (!off) return Number.isFinite(list) ? list : 0
  return roundMoney(Math.max(0, (Number.isFinite(list) ? list : 0) - off))
}

export function isProductOnSale(product) {
  if (!product?.is_discount && !product?.influencer_discount) return false
  const original = getProductOriginalAmount(product)
  const paid = getProductPaidAmount(product)
  return original != null && paid != null && roundMoney(original) > roundMoney(paid)
}

function weightRangePrices(product, paid) {
  const ranges = product?.pricing_data?.ranges || []
  return ranges
    .map((range) => (paid ? weightRangePaidPrice(product, range) : parseFloat(range?.price || 0)))
    .filter((price) => Number.isFinite(price) && price > 0)
}

export function getProductOriginalAmount(product) {
  if (!product) return null
  const pd = product.pricing_data || {}
  const pt = product.pricing_type
  if (pt === 'weight_range') {
    const prices = weightRangePrices(product, false)
    return prices.length ? Math.min(...prices) : null
  }
  if (pt === 'unit_weight' || pt === 'bundled_weight') {
    const n = parseFloat(pd.price_per_unit)
    return Number.isFinite(n) ? n : null
  }
  if (pd.price != null && pd.price !== '') {
    const n = parseFloat(pd.price)
    return Number.isFinite(n) ? n : null
  }
  if (product.original_price != null && product.original_price !== '') {
    const n = parseFloat(product.original_price)
    return Number.isFinite(n) ? n : null
  }
  return null
}

export function getProductPaidAmount(product) {
  if (!product) return null
  const pd = product.pricing_data || {}
  const pt = product.pricing_type
  if (pt === 'weight_range') {
    const prices = weightRangePrices(product, true)
    return prices.length ? Math.min(...prices) : null
  }
  if (pt === 'unit_weight' || pt === 'bundled_weight') {
    if ((product.is_discount || product.influencer_discount) && pd.sale_price_per_unit != null && pd.sale_price_per_unit !== '') {
      const sale = parseFloat(pd.sale_price_per_unit)
      if (Number.isFinite(sale)) return sale
    }
    const n = parseFloat(pd.price_per_unit)
    return Number.isFinite(n) ? n : null
  }
  if ((product.is_discount || product.influencer_discount) && pd.sale_price != null && pd.sale_price !== '') {
    const sale = parseFloat(pd.sale_price)
    if (Number.isFinite(sale)) return sale
  }
  if (product.display_price != null && product.display_price !== '') {
    const n = parseFloat(product.display_price)
    return Number.isFinite(n) ? n : null
  }
  if (product.price != null && product.price !== '') {
    const n = parseFloat(product.price)
    return Number.isFinite(n) ? n : null
  }
  const n = parseFloat(pd.price)
  return Number.isFinite(n) ? n : null
}

export function formatProductCompareAt(product) {
  if (!isProductOnSale(product)) return ''
  const pt = product.pricing_type
  if (pt === 'weight_range') {
    const prices = weightRangePrices(product, false)
    if (!prices.length) return ''
    return formatMoneyRangeDisplay(Math.min(...prices), Math.max(...prices))
  }
  const original = getProductOriginalAmount(product)
  if (original == null) return ''
  if (pt === 'unit_weight' || pt === 'bundled_weight') {
    return formatUnitPriceDisplay(original, product.pricing_data?.unit || 'lb')
  }
  return formatMoneyDisplay(original)
}

/** Simple per-item price string for lists (paid / sale price when on sale) */
export function formatProductListPrice(product) {
  const paid = getProductPaidAmount(product)
  if (paid != null) return formatMoney(paid)
  return '0.00'
}

/**
 * Human-readable price label for a product card (weight_range, unit_weight, bundled_weight).
 */
export function formatProductPriceRange(product) {
  if (!product) return '价格待定'
  const pt = product.pricing_type

  if (pt === 'weight_range') {
    const prices = weightRangePrices(product, true)
    if (!prices.length) return '价格待定'
    return formatMoneyRangeDisplay(Math.min(...prices), Math.max(...prices))
  }

  if (pt === 'unit_weight') {
    const pricePerUnit = getProductPaidAmount(product) || 0
    const unit = product.pricing_data?.unit || 'lb'
    return formatUnitPriceDisplay(pricePerUnit, unit)
  }

  if (pt === 'bundled_weight') {
    const pricePerUnit = getProductPaidAmount(product) || 0
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
