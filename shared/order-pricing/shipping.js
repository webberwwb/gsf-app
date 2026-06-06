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

export function shippingTierBaseFromParts(subtotal, credit = 0, adjustment = 0) {
  return roundMoney(Math.max(0, subtotal - credit - adjustment))
}

function itemCountsTowardFreeShipping(item) {
  const product = item?.product
  if (!product) return true
  return product.counts_toward_free_shipping !== false
}

/** Sum line totals for items that count toward free-shipping tiers (mirrors backend calculate_shipping_fee). */
export function freeShippingSubtotalFromItems(items = []) {
  return roundMoney(
    items.reduce((sum, item) => {
      if (!itemCountsTowardFreeShipping(item)) return sum
      return sum + resolveOrderLineTotal(item)
    }, 0)
  )
}

/** Live shipping fee for admin/checkout previews. */
export function previewShippingFeeForOrder({
  items = [],
  deliveryMethod = 'pickup',
  shippingConfig = null
} = {}) {
  if (deliveryMethod !== 'delivery') return 0
  const tierSubtotal = freeShippingSubtotalFromItems(items)
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
