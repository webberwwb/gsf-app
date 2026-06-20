/**
 * Delivery fee tier calculation (mirrors backend/utils/shipping.py tier logic).
 * See businessRules.js ORDER_PRICING_AND_POINTS_RULES.
 */

import { roundMoney } from './money.js'
import { resolveOrderLineTotal } from './orderItemPricing.js'

export function calculateShippingFee(subtotal, config) {
  if (!config || !config.tiers || config.tiers.length === 0) {
    if (subtotal >= 150) return 0
    return roundMoney(7.99)
  }

  const tiers = [...config.tiers].sort((a, b) => a.threshold - b.threshold)
  let applicableFee = null
  for (const tier of tiers) {
    if (subtotal >= tier.threshold) {
      applicableFee = tier.fee
    } else {
      break
    }
  }
  const fee = applicableFee !== null ? applicableFee : tiers[0]?.fee || 7.99
  return roundMoney(fee)
}

/** Negative adjustment only (admin discount); penalties do not affect tier base. */
export function adjustmentDiscount(adjustment) {
  const adj = Number(adjustment) || 0
  return adj < 0 ? adj : 0
}

export function shippingTierBaseFromParts(subtotal, credit = 0, adjustment = 0) {
  const disc = adjustmentDiscount(adjustment)
  return roundMoney(Math.max(0, subtotal - credit + disc))
}

function itemCountsTowardFreeShipping(item) {
  const product = item?.product
  if (!product) return true
  return product.counts_toward_free_shipping !== false
}

function grossSubtotalFromItems(items = []) {
  return roundMoney(items.reduce((sum, item) => sum + resolveOrderLineTotal(item), 0))
}

/**
 * Allocate shipping_tier_base proportionally across lines that count toward free shipping.
 */
export function eligibleTierSubtotalFromItems(items = [], tierBase = null) {
  const gross = grossSubtotalFromItems(items)
  if (gross <= 0) return 0
  const base = tierBase != null ? Number(tierBase) : gross
  return roundMoney(
    items.reduce((sum, item) => {
      if (!itemCountsTowardFreeShipping(item)) return sum
      const line = resolveOrderLineTotal(item)
      return sum + (line / gross) * base
    }, 0)
  )
}

/** @deprecated use eligibleTierSubtotalFromItems */
export function freeShippingSubtotalFromItems(items = []) {
  return eligibleTierSubtotalFromItems(items)
}

/** Live shipping fee for admin/checkout/user previews. */
export function previewShippingFeeForOrder({
  items = [],
  deliveryMethod = 'pickup',
  shippingConfig = null,
  storeCredit = 0,
  adjustment = 0
} = {}) {
  if (deliveryMethod !== 'delivery') return 0
  const gross = grossSubtotalFromItems(items)
  const tierBase = shippingTierBaseFromParts(gross, storeCredit, adjustment)
  const tierSubtotal = eligibleTierSubtotalFromItems(items, tierBase)
  return calculateShippingFee(tierSubtotal, shippingConfig)
}

export function getNextShippingTier(subtotal, config) {
  if (!config?.tiers?.length) return null
  const currentFee = calculateShippingFee(subtotal, config)
  const tiers = [...config.tiers].sort((a, b) => a.threshold - b.threshold)
  for (const tier of tiers) {
    if (tier.threshold > subtotal && tier.fee < currentFee) {
      return {
        threshold: tier.threshold,
        fee: tier.fee,
        savings: currentFee - tier.fee,
        amountNeeded: tier.threshold - subtotal
      }
    }
  }
  return null
}
