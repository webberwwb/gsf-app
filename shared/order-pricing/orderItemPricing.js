/**
 * Client-side order line price estimation (mirrors backend order_item_pricing.py).
 */

import { roundMoney, formatMoney, formatMoneyDisplay } from './money.js'

export { roundMoney, formatMoney, formatMoneyDisplay } from './money.js'

function parseWeight(w) {
  if (w == null || w === '') return null
  const n = parseFloat(w)
  return n > 0 ? n : null
}

function lowestBandPrice(ranges) {
  if (!ranges?.length) return 0
  return Math.min(...ranges.map((r) => parseFloat(r.price || 0)))
}

export function computeBasePrice(product, quantity = 1, finalWeight = null) {
  const pricingType = product.pricing_type || 'per_item'
  const qty = parseInt(quantity, 10) || 1
  const pd = product.pricing_data || {}
  const fw = parseWeight(finalWeight)

  let unitPrice = 0
  let totalPrice = 0

  if (pricingType === 'per_item') {
    unitPrice = parseFloat(product.price ?? pd.price ?? 0)
    totalPrice = unitPrice * qty
  } else if (pricingType === 'weight_range') {
    const ranges = pd.ranges || []
    if (fw != null && ranges.length) {
      let matched = null
      for (const r of ranges) {
        const min = r.min ?? 0
        const max = r.max
        if (fw >= min && (max == null || fw < max)) {
          matched = parseFloat(r.price || 0)
          break
        }
      }
      unitPrice = matched != null ? matched : lowestBandPrice(ranges)
    } else {
      unitPrice = lowestBandPrice(ranges)
    }
    totalPrice = unitPrice * qty
  } else if (pricingType === 'unit_weight') {
    unitPrice = parseFloat(pd.price_per_unit || 0)
    const weight = fw ?? 1
    totalPrice = unitPrice * weight
  } else if (pricingType === 'bundled_weight') {
    const pricePerUnit = parseFloat(pd.price_per_unit || 0)
    const weight = fw ?? parseFloat(pd.min_weight || 7)
    totalPrice = pricePerUnit * weight
    unitPrice = qty > 1 ? totalPrice / qty : pricePerUnit
  } else {
    unitPrice = parseFloat(product.price || 0)
    totalPrice = unitPrice * qty
  }

  return { unitPrice: roundMoney(unitPrice), totalPrice: roundMoney(totalPrice) }
}

export function applyVariantDelta(unitPrice, totalPrice, delta, pricingType, quantity, finalWeight, product) {
  const d = parseFloat(delta || 0)
  if (!d) return { unitPrice, totalPrice }
  unitPrice += d
  const qty = parseInt(quantity, 10) || 1
  const fw = parseWeight(finalWeight)

  if (pricingType === 'per_item' || pricingType === 'weight_range') {
    totalPrice = unitPrice * qty
  } else if (pricingType === 'unit_weight') {
    totalPrice = unitPrice * (fw ?? 1)
  } else if (pricingType === 'bundled_weight') {
    const pd = product?.pricing_data || {}
    totalPrice = unitPrice * (fw ?? parseFloat(pd.min_weight || 7))
  }
  return { unitPrice: roundMoney(unitPrice), totalPrice: roundMoney(totalPrice) }
}

export function estimateLinePrice(product, selection = {}) {
  const { quantity = 1, final_weight: finalWeight = null, variant_id: variantId = null } = selection
  const variant = (product.variants || []).find(v => v.id === variantId)
  const delta = variant ? parseFloat(variant.price_delta || 0) : 0

  let { unitPrice, totalPrice } = computeBasePrice(product, quantity, finalWeight)
  ;({ unitPrice, totalPrice } = applyVariantDelta(
    unitPrice,
    totalPrice,
    delta,
    product.pricing_type,
    quantity,
    finalWeight,
    product
  ))
  return { unitPrice: roundMoney(unitPrice), totalPrice: roundMoney(totalPrice), variant }
}

export function getDisplayPriceFromConfig(pricingType, pricingData = {}) {
  const pd = pricingData || {}
  if (pricingType === 'per_item') {
    return pd.price != null ? parseFloat(pd.price) : null
  }
  if (pricingType === 'weight_range') {
    const ranges = pd.ranges || []
    return ranges.length ? lowestBandPrice(ranges) : null
  }
  if (pricingType === 'unit_weight') {
    return pd.price_per_unit != null ? parseFloat(pd.price_per_unit) : null
  }
  if (pricingType === 'bundled_weight') {
    const ppu = parseFloat(pd.price_per_unit || 0)
    const minW = parseFloat(pd.min_weight || 7)
    const maxW = parseFloat(pd.max_weight || 15)
    return ppu > 0 ? ppu * ((minW + maxW) / 2) : null
  }
  return null
}

export function formatSubstitutePriceLabel(substitute) {
  if (!substitute) return null
  const pricingType = substitute.pricing_type || 'per_item'
  const pricingData = substitute.pricing_data || {}
  const display =
    getDisplayPriceFromConfig(pricingType, pricingData) ??
    (substitute.price != null ? parseFloat(substitute.price) : null)
  if (display == null || Number.isNaN(display)) return null

  if (pricingType === 'per_item') {
    return formatMoneyDisplay(display)
  }
  if (pricingType === 'unit_weight' || pricingType === 'bundled_weight') {
    const unit = pricingData.unit === 'kg' ? 'kg' : 'lb'
    const suffix = pricingType === 'bundled_weight' ? '（按实际重量）' : ''
    return `$${formatMoney(pricingData.price_per_unit || display)}/${unit}${suffix}`
  }
  if (pricingType === 'weight_range') {
    return `按重量区间计价（参考 ${formatMoneyDisplay(display)}）`
  }
  return formatMoneyDisplay(display)
}

export function productRequiresVariant(product) {
  return (product.variants || []).length > 0
}

export function productRequiresSubstituteChoice(product) {
  return !!(product.substitute_enabled || product.substitute?.enabled)
}

export function isSelectionComplete(product, selection = {}) {
  if (productRequiresVariant(product) && !selection.variant_id) return false
  if (productRequiresSubstituteChoice(product) && selection.accept_substitute == null) return false
  return true
}

export function getSubstitutePricing(product) {
  if (!product) return { pricingType: 'per_item', pricingData: {} }
  if (product.substitute_pricing_data) {
    return {
      pricingType: product.substitute_pricing_type || product.pricing_type,
      pricingData: product.substitute_pricing_data
    }
  }
  const sub = product.substitute
  if (sub?.pricing_data) {
    return {
      pricingType: sub.pricing_type || product.pricing_type,
      pricingData: sub.pricing_data
    }
  }
  if (product.substitute_price != null) {
    return { pricingType: 'per_item', pricingData: { price: product.substitute_price } }
  }
  if (sub?.price != null) {
    return { pricingType: 'per_item', pricingData: { price: sub.price } }
  }
  return { pricingType: product.pricing_type, pricingData: product.pricing_data || {} }
}

export function applyFulfillmentPrice(
  unitPrice,
  totalPrice,
  quantity,
  product,
  isUnavailable,
  acceptSubstitute,
  finalWeight,
  cannotFulfill = false
) {
  if (!isUnavailable) return { unitPrice, totalPrice }
  if (cannotFulfill) return { unitPrice: 0, totalPrice: 0 }
  if (!acceptSubstitute) return { unitPrice: roundMoney(unitPrice), totalPrice: roundMoney(totalPrice) }
  const { pricingType, pricingData } = getSubstitutePricing(product)
  const subProduct = { pricing_type: pricingType, pricing_data: pricingData, price: pricingData.price }
  return computeBasePrice(subProduct, quantity, finalWeight)
}

/** Estimate line unit/total for admin order modal (variant + fulfillment). */
export function estimateAdminLinePrice(product, opts = {}) {
  if (!product) return { unitPrice: 0, totalPrice: 0 }
  const quantity = Math.max(1, parseInt(opts.quantity, 10) || 1)
  const finalWeight = opts.final_weight
  const pricingType = product.pricing_type || 'per_item'
  let variantDelta = parseFloat(opts.variant_price_delta || 0)
  if (!variantDelta && opts.variant_id != null) {
    const v = (product.variants || []).find(
      (x) => x.id === opts.variant_id || String(x.id) === String(opts.variant_id)
    )
    variantDelta = parseFloat(v?.price_delta || 0)
  }

  let { unitPrice, totalPrice } = computeBasePrice(product, quantity, finalWeight)
  ;({ unitPrice, totalPrice } = applyVariantDelta(
    unitPrice,
    totalPrice,
    variantDelta,
    pricingType,
    quantity,
    finalWeight,
    product
  ))
  ;({ unitPrice, totalPrice } = applyFulfillmentPrice(
    unitPrice,
    totalPrice,
    quantity,
    product,
    !!opts.is_unavailable,
    opts.accept_substitute,
    finalWeight,
    !!opts.cannot_fulfill
  ))
  return { unitPrice: roundMoney(unitPrice), totalPrice: roundMoney(totalPrice) }
}

/** Format line total for UI (~ prefix when estimated). */
export function formatLinePrice(value, { estimated = false } = {}) {
  const prefix = estimated ? '~' : ''
  return `${prefix}$${formatMoney(value)}`
}

/** Reference weight for estimate when final_weight is missing (min weight / first band). */
export function getReferenceWeight(product) {
  if (!product) return null
  const pt = product.pricing_type
  const pd = product.pricing_data || {}
  if (pt === 'bundled_weight') {
    const w = parseFloat(pd.min_weight)
    return Number.isFinite(w) && w > 0 ? w : 7
  }
  if (pt === 'unit_weight') return 1
  if (pt === 'weight_range') {
    const ranges = pd.ranges || []
    if (!ranges.length) return null
    let minRef = null
    for (const r of ranges) {
      const m = parseFloat(r.min ?? 0)
      if (Number.isFinite(m) && (minRef == null || m < minRef)) minRef = m
    }
    return minRef
  }
  return null
}

/** User declined substitute while product is unavailable — keep line, $0 until admin resolves. */
export function isDeclinedSubstituteLine(item) {
  if (!item) return false
  if (item.is_declined_substitute != null) return !!item.is_declined_substitute
  return !!item.is_unavailable && item.accept_substitute === false
}

/** Unavailable but user has not chosen substitute preference yet. */
export function isPendingSubstituteLine(item) {
  if (!item) return false
  if (item.is_pending_substitute != null) return !!item.is_pending_substitute
  return !!item.is_unavailable && item.accept_substitute == null
}

/** Line total for display: stored price, or estimate using min weight / lowest band. */
export function resolveOrderLineTotal(item) {
  if (!item) return 0
  if (item.cannot_fulfill) return 0

  const stored = parseFloat(item.total_price)
  if (Number.isFinite(stored)) return roundMoney(stored)

  const product = item.product
  if (!product) return 0

  const fw = parseWeight(item.final_weight)
  const pricingWeight = fw ?? getReferenceWeight(product)

  const { totalPrice } = estimateAdminLinePrice(product, {
    quantity: item.quantity,
    final_weight: pricingWeight,
    variant_id: item.variant_id,
    variant_price_delta: item.variant_price_delta,
    accept_substitute: item.accept_substitute,
    is_unavailable: item.is_unavailable,
    cannot_fulfill: item.cannot_fulfill
  })
  return roundMoney(totalPrice)
}

export function isOrderLinePriceEstimated(item) {
  const stored = parseFloat(item.total_price)
  if (Number.isFinite(stored) && stored > 0) return false
  const p = item?.product
  if (!p) return false
  if (!['weight_range', 'unit_weight', 'bundled_weight'].includes(p.pricing_type)) return false
  return !parseWeight(item?.final_weight)
}

export function getOrderLineWeightLabel(item) {
  const p = item.product
  if (!p) return null
  const pt = p.pricing_type
  if (!['weight_range', 'unit_weight', 'bundled_weight'].includes(pt)) return null
  const fw = parseWeight(item.final_weight)
  if (fw != null) return `重量 ${fw.toFixed(3)} lb`
  const ref = getReferenceWeight(p)
  if (ref != null) return `约 ${ref} lb（待称重）`
  return '重量待确认'
}

export function formatSubstitutePreferenceLabel(acceptSubstitute) {
  if (acceptSubstitute === true) return '接受备选'
  if (acceptSubstitute === false) return '不要备选'
  return null
}

export function toOrderLineDisplay(item) {
  if (!item) return item
  const product = item.product || {}
  const variantName = item.variant?.name || item.variant_name
  return {
    ...item,
    display_name: item.display_name || product.name || '商品',
    variant_name: variantName,
    show_substitute_preference:
      item.show_substitute_preference ??
      !!(product.substitute_enabled || product.substitute?.enabled),
    substitute_name: product.substitute?.name
  }
}

const WEIGHT_TYPES = ['weight_range', 'unit_weight', 'bundled_weight']

/** Sum estimate for user selection; weight types use one line per physical item. */
export function estimateSelectionTotal(product, quantity, selection = {}) {
  const qty = Math.max(0, parseInt(quantity, 10) || 0)
  if (!product || qty === 0) return 0
  const pt = product.pricing_type || 'per_item'
  if (WEIGHT_TYPES.includes(pt)) {
    let sum = 0
    for (let i = 0; i < qty; i++) {
      const refWeight = pt === 'unit_weight' ? 1 : getReferenceWeight(product)
      const { totalPrice } = estimateLinePrice(product, {
        quantity: 1,
        final_weight: selection.final_weight ?? refWeight,
        variant_id: selection.variant_id
      })
      sum += totalPrice
    }
    return roundMoney(sum)
  }
  const { totalPrice } = estimateLinePrice(product, {
    quantity: qty,
    final_weight: selection.final_weight ?? null,
    variant_id: selection.variant_id
  })
  return roundMoney(totalPrice)
}

/** Build pseudo order lines for live preview from user product selections. */
export function buildPreviewLinesFromSelection(products = [], selectedItems = {}) {
  const lines = []
  for (const product of products) {
    const selection = selectedItems[product.id]
    if (!selection || selection.quantity <= 0) continue
    const totalPrice = estimateSelectionTotal(product, selection.quantity, {
      variant_id: selection.variant_id,
      final_weight: selection.weight
    })
    lines.push({
      product,
      product_id: product.id,
      quantity: selection.quantity,
      variant_id: selection.variant_id,
      total_price: totalPrice
    })
  }
  return lines
}
