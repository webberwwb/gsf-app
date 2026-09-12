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

export function normalizeQuantityBreaks(breaks) {
  if (!Array.isArray(breaks)) return []
  const seen = new Set()
  const out = []
  for (const row of breaks) {
    if (!row || typeof row !== 'object') continue
    const minQty = parseInt(row.min_qty, 10)
    const price = parseFloat(row.price)
    if (!Number.isFinite(minQty) || minQty < 2) continue
    if (!Number.isFinite(price) || price < 0) continue
    if (seen.has(minQty)) continue
    seen.add(minQty)
    out.push({ min_qty: minQty, price })
  }
  out.sort((a, b) => a.min_qty - b.min_qty)
  return out
}

export function lookupBreakPrice(basePrice, breaks, productQty) {
  let unit = parseFloat(basePrice || 0)
  const qty = parseInt(productQty, 10) || 1
  for (const row of normalizeQuantityBreaks(breaks)) {
    if (qty >= row.min_qty) unit = row.price
  }
  return roundMoney(unit)
}

export function productSharesVariantPrice(product) {
  if (!product) return true
  return product.variants_share_price !== false
}

/** Deal product APIs set is_discount per deal; 推荐官 payloads also mark influencer_discount. */
export function productOnSale(product) {
  return !!(product?.is_discount || product?.influencer_discount)
}

function optionalNumber(value) {
  if (value == null || value === '') return null
  const n = parseFloat(value)
  return Number.isFinite(n) ? n : null
}

export function paidPricingData(product, pricingData = null) {
  const pd = { ...(pricingData || product?.pricing_data || {}) }
  if (!productOnSale(product)) return pd
  const pt = product?.pricing_type
  if (pt === 'per_item') {
    const sale = optionalNumber(pd.sale_price)
    if (sale != null) pd.price = sale
  } else if (pt === 'unit_weight' || pt === 'bundled_weight') {
    const sale = optionalNumber(pd.sale_price_per_unit)
    if (sale != null) pd.price_per_unit = sale
  }
  return pd
}

function floorMoney(value, amount) {
  return roundMoney(Math.max(0, (parseFloat(value) || 0) - (parseFloat(amount) || 0)))
}

/**
 * Overlay a 推荐官 rate on a deal/catalog product (same as Python
 * apply_influencer_discount_to_product_payload). Skips if already applied.
 * `rate` is { commission_type: 'per_item'|'per_weight', amount }.
 */
export function applyInfluencerDiscountToProduct(product, rate) {
  if (!product || !rate) return product
  if (product.influencer_discount) return product
  const commissionType = rate.commission_type
  const amount = parseFloat(rate.amount)
  if (!Number.isFinite(amount) || amount <= 0) return product

  const data = {
    ...product,
    pricing_data: { ...(product.pricing_data || {}) },
    variants: (product.variants || []).map((v) => ({ ...v }))
  }
  const pd = { ...data.pricing_data }
  if (Array.isArray(pd.ranges)) pd.ranges = pd.ranges.map((row) => ({ ...row }))
  if (Array.isArray(pd.quantity_breaks)) {
    pd.quantity_breaks = pd.quantity_breaks.map((row) => ({ ...row }))
  }
  const pt = data.pricing_type
  const onSale = !!data.is_discount

  if (pt === 'unit_weight' || pt === 'bundled_weight') {
    const listUnit = pd.price_per_unit
    const paidUnit = onSale && pd.sale_price_per_unit != null ? pd.sale_price_per_unit : listUnit
    if (commissionType === 'per_weight' && paidUnit != null) {
      pd.sale_price_per_unit = floorMoney(paidUnit, amount)
      data.sale_price = pd.sale_price_per_unit
      data.display_price = pd.sale_price_per_unit
      data.price = pd.sale_price_per_unit
      if (data.original_price == null) {
        data.original_price = listUnit != null ? parseFloat(listUnit) : null
      }
    }
  } else {
    const listPrice = pd.price
    const paid = onSale && pd.sale_price != null ? pd.sale_price : listPrice
    if (paid != null) {
      const discounted = floorMoney(paid, amount)
      pd.sale_price = discounted
      data.sale_price = discounted
      data.display_price = discounted
      data.price = discounted
      if (data.original_price == null) {
        data.original_price = listPrice != null ? parseFloat(listPrice) : null
      }
    }
    if (pd.ranges) {
      pd.ranges = pd.ranges.map((row) => ({ ...row, price: floorMoney(row.price, amount) }))
    }
    if (pd.quantity_breaks) {
      pd.quantity_breaks = pd.quantity_breaks.map((row) => ({
        ...row,
        price: floorMoney(row.price, amount)
      }))
    }
    if (commissionType !== 'per_weight') {
      for (const variant of data.variants) {
        const base = onSale && variant.sale_price != null ? variant.sale_price : variant.price
        if (base != null) variant.sale_price = floorMoney(base, amount)
      }
    }
  }

  data.pricing_data = pd
  data.influencer_discount = true
  data.influencer_commission_type = commissionType
  data.influencer_commission_amount = amount
  return data
}

/** per_item commission on $/lb lines reduces the line total only (mirrors Python). */
function applyInfluencerLineDiscount(product, unitPrice, totalPrice, quantity) {
  if (product?.influencer_commission_type !== 'per_item') {
    return { unitPrice, totalPrice }
  }
  const amount = parseFloat(product.influencer_commission_amount)
  if (!Number.isFinite(amount) || amount <= 0) return { unitPrice, totalPrice }
  const pt = product.pricing_type
  if (pt === 'unit_weight' || pt === 'bundled_weight') {
    const qty = Math.max(parseInt(quantity, 10) || 0, 0)
    return { unitPrice, totalPrice: floorMoney(totalPrice, amount * qty) }
  }
  return { unitPrice, totalPrice }
}

function paidPerItemBase(product, variant = null) {
  const pd = product?.pricing_data || {}
  const listPrice = parseFloat(pd.price ?? 0)
  const sale = optionalNumber(pd.sale_price)
  const productBase = productOnSale(product) && sale != null ? sale : listPrice
  const share = productSharesVariantPrice(product)

  if (variant && !share) {
    const variantList =
      variant.price != null ? parseFloat(variant.price) : listPrice + parseFloat(variant.price_delta || 0)
    const variantSale = optionalNumber(variant.sale_price)
    const base = productOnSale(product) && variantSale != null ? variantSale : variantList
    return { base, listPrice }
  }
  return { base: productBase, listPrice }
}

export function resolvePerItemUnit(product, variant, productQty = 1) {
  const pd = product?.pricing_data || {}
  const qty = parseInt(productQty, 10) || 1
  const share = productSharesVariantPrice(product)
  const { base: productBase, listPrice } = paidPerItemBase(product, null)

  if (variant && !share) {
    const { base } = paidPerItemBase(product, variant)
    const unit = lookupBreakPrice(base, variant.quantity_breaks, qty)
    return { unitPrice: roundMoney(unit), variantDelta: roundMoney(base - listPrice) }
  }

  const unit = lookupBreakPrice(productBase, pd.quantity_breaks, qty)
  const delta = variant ? parseFloat(variant.price_delta || 0) : 0
  return { unitPrice: roundMoney(unit + delta), variantDelta: roundMoney(delta) }
}

export function emptyProductSelection() {
  return {
    quantity: 0,
    variant_id: null,
    variant_quantities: {},
    accept_substitute: null,
    cutting_qty: 0,
    cutting_quantities: {}
  }
}

export function productOffersCutting(product) {
  return !!(product && product.cutting_enabled)
}

export function catalogCuttingFee(product) {
  if (!productOffersCutting(product)) return 0
  const n = parseFloat(product.cutting_fee)
  return Number.isFinite(n) && n > 0 ? n : 0
}

export function getCuttingQuantity(selection = {}, variantId = null) {
  if (variantId != null) {
    const cq = selection.cutting_quantities
    if (cq && typeof cq === 'object') {
      return Math.max(0, parseInt(cq[variantId] ?? cq[String(variantId)], 10) || 0)
    }
    return 0
  }
  return Math.max(0, parseInt(selection.cutting_qty, 10) || 0)
}

export function setCuttingQuantity(selection = {}, qty, variantId = null) {
  const next = {
    ...emptyProductSelection(),
    ...selection,
    variant_quantities: { ...(selection.variant_quantities || {}) },
    cutting_quantities: { ...(selection.cutting_quantities || {}) }
  }
  const n = Math.max(0, parseInt(qty, 10) || 0)
  if (variantId != null) {
    const max = getVariantQuantity(next, variantId)
    const clamped = Math.min(n, max)
    if (clamped > 0) next.cutting_quantities[variantId] = clamped
    else delete next.cutting_quantities[variantId]
  } else {
    next.cutting_qty = Math.min(n, getSelectionQuantity(next))
  }
  return next
}

export function clampCuttingQuantities(selection = {}) {
  const next = {
    ...emptyProductSelection(),
    ...selection,
    variant_quantities: { ...(selection.variant_quantities || {}) },
    cutting_quantities: { ...(selection.cutting_quantities || {}) }
  }
  const vq = next.variant_quantities
  if (vq && Object.keys(vq).length) {
    for (const key of Object.keys(next.cutting_quantities)) {
      const max = getVariantQuantity(next, key)
      const cut = Math.min(getCuttingQuantity(next, key), max)
      if (cut > 0) next.cutting_quantities[key] = cut
      else delete next.cutting_quantities[key]
    }
  } else {
    next.cutting_qty = Math.min(getCuttingQuantity(next), getSelectionQuantity(next))
  }
  return next
}

export function splitSelectionIntoOrderLines(product, selection = {}) {
  const lines = []
  const variants = product?.variants || []
  const accept = selection.accept_substitute
  const offers = productOffersCutting(product)
  const push = (qty, variantId, cutting) => {
    if (qty <= 0) return
    lines.push({
      quantity: qty,
      variant_id: variantId || null,
      cutting: !!cutting,
      accept_substitute: accept
    })
  }
  if (variants.length) {
    for (const variant of variants) {
      const qty = getVariantQuantity(selection, variant.id)
      if (qty <= 0) continue
      const cut = offers ? Math.min(qty, getCuttingQuantity(selection, variant.id)) : 0
      push(qty - cut, variant.id, false)
      push(cut, variant.id, true)
    }
  } else {
    const qty = getSelectionQuantity(selection)
    const cut = offers ? Math.min(qty, getCuttingQuantity(selection, null)) : 0
    push(qty - cut, selection.variant_id, false)
    push(cut, selection.variant_id, true)
  }
  return lines
}

export function lineCuttingFeeTotal(item) {
  if (!item || !item.cutting) return 0
  const fee = parseFloat(item.cutting_fee)
  const qty = Math.max(0, parseInt(item.quantity, 10) || 0)
  if (!Number.isFinite(fee) || fee <= 0 || qty <= 0) return 0
  return roundMoney(fee * qty)
}

export function cuttingFeesTotal(items = []) {
  return roundMoney(items.reduce((sum, item) => sum + lineCuttingFeeTotal(item), 0))
}

export function lineProductAmount(item) {
  return roundMoney(Math.max(0, resolveOrderLineTotal(item) - lineCuttingFeeTotal(item)))
}

export function formatCuttingLabel(item) {
  if (!item || !item.cutting) return null
  return '切分'
}

export function getVariantQuantity(selection = {}, variantId) {
  if (!selection || variantId == null) return 0
  const vq = selection.variant_quantities
  if (vq && typeof vq === 'object') {
    const raw = vq[variantId] ?? vq[String(variantId)]
    return Math.max(0, parseInt(raw, 10) || 0)
  }
  if (selection.variant_id === variantId || String(selection.variant_id) === String(variantId)) {
    return Math.max(0, parseInt(selection.quantity, 10) || 0)
  }
  return 0
}

export function getSelectionQuantity(selection = {}) {
  const vq = selection.variant_quantities
  if (vq && typeof vq === 'object' && Object.keys(vq).length) {
    return Object.values(vq).reduce((sum, n) => sum + (parseInt(n, 10) || 0), 0)
  }
  return Math.max(0, parseInt(selection.quantity, 10) || 0)
}

/**
 * Rebuild product selections from saved order lines so edit screens
 * restore quantities (plain products and variant lines).
 */
export function selectionsFromOrderItems(items, existing = {}) {
  const next = { ...existing }
  const reset = new Set()
  for (const item of items || []) {
    if (item == null || item.product_id == null) continue
    const productId = Number(item.product_id)
    if (!Number.isFinite(productId)) continue

    const prev = next[productId] || emptyProductSelection()
    const sel = {
      ...prev,
      variant_quantities: { ...(prev.variant_quantities || {}) },
      item_ids: { ...(prev.item_ids || {}) }
    }

    if (!reset.has(productId)) {
      sel.variant_quantities = {}
      sel.item_ids = {}
      sel.cutting_quantities = {}
      sel.cutting_qty = 0
      sel.quantity = 0
      sel.variant_id = null
      reset.add(productId)
    }

    const qty = Math.max(0, parseInt(item.quantity, 10) || 0)
    if (item.variant_id != null) {
      const vid = item.variant_id
      sel.variant_quantities[vid] = (sel.variant_quantities[vid] || 0) + qty
      if (item.id != null) sel.item_ids[vid] = item.id
      sel.variant_id = vid
      if (item.cutting) {
        sel.cutting_quantities[vid] = (sel.cutting_quantities[vid] || 0) + qty
      }
    } else {
      sel.quantity = (sel.quantity || 0) + qty
      if (item.cutting) sel.cutting_qty = (sel.cutting_qty || 0) + qty
    }

    sel.quantity = getSelectionQuantity(sel)
    if (item.accept_substitute !== undefined) {
      sel.accept_substitute = item.accept_substitute
    }
    if (item.id != null) sel.item_id = item.id
    if (item.final_weight != null && Number(item.final_weight) > 0) {
      sel.weight = parseFloat(item.final_weight)
    }
    next[productId] = sel
  }
  return next
}

function lineIdentityKey(item) {
  const vid = item.variant_id == null ? '' : String(item.variant_id)
  const cut = item.cutting ? '1' : '0'
  return `${item.product_id}:${vid}:${cut}`
}

function sameSubstitute(a, b) {
  const left = a == null ? null : a
  const right = b == null ? null : b
  return left === right
}

export function summarizeOrderItemLines(items) {
  const map = {}
  for (const item of items || []) {
    if (item == null || item.product_id == null) continue
    const qty = Math.max(0, parseInt(item.quantity, 10) || 0)
    if (qty <= 0) continue
    const key = lineIdentityKey(item)
    if (!map[key]) {
      map[key] = { quantity: 0, accept_substitute: item.accept_substitute }
    }
    map[key].quantity += qty
    if (item.accept_substitute !== undefined) {
      map[key].accept_substitute = item.accept_substitute
    }
  }
  return map
}

export function orderItemSelectionChanged(currentItems, nextItems) {
  const current = summarizeOrderItemLines(currentItems)
  const next = summarizeOrderItemLines(nextItems)
  const keys = new Set([...Object.keys(current), ...Object.keys(next)])
  for (const key of keys) {
    if (!current[key] || !next[key]) return true
    if (current[key].quantity !== next[key].quantity) return true
    if (!sameSubstitute(current[key].accept_substitute, next[key].accept_substitute)) return true
  }
  return false
}

function variantQuantitiesTotal(variantQuantities = {}) {
  return Object.values(variantQuantities).reduce((sum, n) => sum + (parseInt(n, 10) || 0), 0)
}

export function setVariantQuantity(selection = {}, variantId, qty) {
  const next = {
    ...emptyProductSelection(),
    ...selection,
    variant_quantities: { ...(selection.variant_quantities || {}) }
  }
  const n = Math.max(0, parseInt(qty, 10) || 0)
  if (n > 0) next.variant_quantities[variantId] = n
  else delete next.variant_quantities[variantId]
  next.quantity = variantQuantitiesTotal(next.variant_quantities)
  if (next.quantity === 0) next.variant_id = null
  else if (n > 0) next.variant_id = variantId
  else if (next.variant_id == null || next.variant_quantities[next.variant_id] == null) {
    const first = Object.keys(next.variant_quantities)[0]
    next.variant_id = first != null ? Number(first) || first : null
  }
  return clampCuttingQuantities(next)
}

export function computeBasePrice(product, quantity = 1, finalWeight = null) {
  const pricingType = product.pricing_type || 'per_item'
  const qty = parseInt(quantity, 10) || 1
  const pd = paidPricingData(product)
  const fw = parseWeight(finalWeight)

  let unitPrice = 0
  let totalPrice = 0

  if (pricingType === 'per_item') {
    unitPrice = parseFloat(pd.price ?? product.price ?? 0)
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

function applyCuttingToEstimate(product, unitPrice, totalPrice, quantity, cutting) {
  if (!cutting) return { unitPrice, totalPrice, cuttingFee: 0 }
  const fee = catalogCuttingFee(product)
  const qty = parseInt(quantity, 10) || 1
  const extra = roundMoney(fee * qty)
  const pt = product.pricing_type || 'per_item'
  if (pt === 'per_item') {
    return {
      unitPrice: roundMoney(unitPrice + fee),
      totalPrice: roundMoney(totalPrice + extra),
      cuttingFee: fee
    }
  }
  return { unitPrice, totalPrice: roundMoney(totalPrice + extra), cuttingFee: fee }
}

export function estimateLinePrice(product, selection = {}) {
  const {
    quantity = 1,
    final_weight: finalWeight = null,
    variant_id: variantId = null,
    product_qty: productQty = null,
    cutting = false
  } = selection
  const variant = (product.variants || []).find(
    (v) => v.id === variantId || String(v.id) === String(variantId)
  )
  const pooled = productQty != null ? productQty : quantity
  const pt = product.pricing_type || 'per_item'

  let unitPrice
  let totalPrice
  if (pt === 'per_item') {
    ;({ unitPrice } = resolvePerItemUnit(product, variant, pooled))
    totalPrice = roundMoney(unitPrice * (parseInt(quantity, 10) || 1))
  } else {
    const delta = variant ? parseFloat(variant.price_delta || 0) : 0
    ;({ unitPrice, totalPrice } = computeBasePrice(product, quantity, finalWeight))
    ;({ unitPrice, totalPrice } = applyVariantDelta(
      unitPrice,
      totalPrice,
      delta,
      pt,
      quantity,
      finalWeight,
      product
    ))
  }
  ;({ unitPrice, totalPrice } = applyInfluencerLineDiscount(
    product,
    unitPrice,
    totalPrice,
    quantity
  ))
  const cut = applyCuttingToEstimate(product, unitPrice, totalPrice, quantity, cutting)
  return {
    unitPrice: roundMoney(cut.unitPrice),
    totalPrice: roundMoney(cut.totalPrice),
    variant,
    cuttingFee: cut.cuttingFee
  }
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
  const qty = getSelectionQuantity(selection)
  if (qty <= 0) return true
  if (productRequiresVariant(product)) {
    const hasVariantQty = (product.variants || []).some((v) => getVariantQuantity(selection, v.id) > 0)
    if (!hasVariantQty && !selection.variant_id) return false
  }
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
  const variant = (product.variants || []).find(
    (x) => x.id === opts.variant_id || String(x.id) === String(opts.variant_id)
  )
  const pooled = opts.product_qty != null ? opts.product_qty : quantity

  let unitPrice
  let totalPrice
  if (pricingType === 'per_item') {
    ;({ unitPrice } = resolvePerItemUnit(product, variant, pooled))
    totalPrice = roundMoney(unitPrice * quantity)
  } else {
    let variantDelta = parseFloat(opts.variant_price_delta || 0)
    if (!variantDelta && variant) variantDelta = parseFloat(variant.price_delta || 0)
    ;({ unitPrice, totalPrice } = computeBasePrice(product, quantity, finalWeight))
    ;({ unitPrice, totalPrice } = applyVariantDelta(
      unitPrice,
      totalPrice,
      variantDelta,
      pricingType,
      quantity,
      finalWeight,
      product
    ))
  }
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
  ;({ unitPrice, totalPrice } = applyInfluencerLineDiscount(
    product,
    unitPrice,
    totalPrice,
    quantity
  ))
  if (!opts.cannot_fulfill) {
    const cut = applyCuttingToEstimate(product, unitPrice, totalPrice, quantity, !!opts.cutting)
    unitPrice = cut.unitPrice
    totalPrice = cut.totalPrice
  }
  return { unitPrice: roundMoney(unitPrice), totalPrice: roundMoney(totalPrice) }
}

const WEIGHT_TYPES = ['weight_range', 'unit_weight', 'bundled_weight']

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
    cannot_fulfill: item.cannot_fulfill,
    cutting: !!item.cutting
  })
  return roundMoney(totalPrice)
}

export function isOrderLinePriceEstimated(item) {
  const p = item?.product
  if (!p || !WEIGHT_TYPES.includes(p.pricing_type)) return false
  return parseWeight(item?.final_weight) == null
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

/** Sum estimate for user selection; weight types use one line per physical item. */
export function estimateSelectionTotal(product, quantity, selection = {}) {
  const qty = Math.max(0, parseInt(quantity, 10) || 0)
  if (!product || qty === 0) return 0
  const pooled = selection.product_qty != null ? selection.product_qty : qty
  const pt = product.pricing_type || 'per_item'
  if (WEIGHT_TYPES.includes(pt)) {
    let sum = 0
    for (let i = 0; i < qty; i++) {
      const refWeight = pt === 'unit_weight' ? 1 : getReferenceWeight(product)
      const { totalPrice } = estimateLinePrice(product, {
        quantity: 1,
        final_weight: selection.final_weight ?? refWeight,
        variant_id: selection.variant_id,
        product_qty: pooled,
        cutting: selection.cutting
      })
      sum += totalPrice
    }
    return roundMoney(sum)
  }
  const { totalPrice } = estimateLinePrice(product, {
    quantity: qty,
    final_weight: selection.final_weight ?? null,
    variant_id: selection.variant_id,
    product_qty: pooled,
    cutting: selection.cutting
  })
  return roundMoney(totalPrice)
}

/** Build pseudo order lines for live preview from user product selections. */
export function buildPreviewLinesFromSelection(products = [], selectedItems = {}) {
  const lines = []
  for (const product of products) {
    const selection = selectedItems[product.id]
    if (!selection) continue
    const pooled = getSelectionQuantity(selection)
    if (pooled <= 0) continue
    const variants = product.variants || []
    for (const part of splitSelectionIntoOrderLines(product, selection)) {
      const totalPrice = estimateSelectionTotal(product, part.quantity, {
        variant_id: part.variant_id,
        final_weight: selection.weight,
        product_qty: pooled,
        cutting: part.cutting
      })
      lines.push({
        product,
        product_id: product.id,
        quantity: part.quantity,
        variant_id: part.variant_id,
        cutting: part.cutting,
        cutting_fee: part.cutting ? catalogCuttingFee(product) : 0,
        total_price: totalPrice
      })
    }
  }
  return lines
}
