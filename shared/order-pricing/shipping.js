/**
 * Delivery fee tier calculation (mirrors backend/utils/shipping.py tier logic).
 * See businessRules.js ORDER_PRICING_AND_POINTS_RULES.
 */

import { roundMoney } from './money.js'
import { lineProductAmount } from './orderItemPricing.js'

/** Public map label only — never put a street address here. */
export const DEFAULT_DEPOT = { lat: 43.8776838, lng: -79.3639328, label: 'Markham' }

/** Customer region add-on. Unlisted cities use the subtotal tier only (no extra). */
export const DEFAULT_REGION_SURCHARGES = [
  {
    label: 'Waterloo / Kitchener / Guelph',
    surcharge: 4,
    cities: ['Waterloo', 'Kitchener', 'Guelph', 'Kitchener-Waterloo']
  },
  {
    label: 'Whitby / Pickering / Ajax / Hamilton / Burlington',
    surcharge: 2,
    cities: ['Whitby', 'Pickering', 'Ajax', 'Hamilton', 'Burlington']
  }
]

export const REGION_PIN_COLORS = ['#FB8C00', '#1E88E5', '#8E24AA', '#00897B']
export const BASE_REGION_COLOR = '#43A047'
export const DEFAULT_REGION_LABEL = 'GTA默认区域'

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

export function shippingTierBaseFromParts(subtotal, credit = 0, adjustment = 0, cuttingFees = 0) {
  const disc = adjustmentDiscount(adjustment)
  const cut = Number(cuttingFees) || 0
  return roundMoney(Math.max(0, subtotal - cut - credit + disc))
}

function itemCountsTowardFreeShipping(item) {
  const product = item?.product
  if (!product) return true
  return product.counts_toward_free_shipping !== false
}

function productSubtotalFromItems(items = []) {
  return roundMoney(items.reduce((sum, item) => sum + lineProductAmount(item), 0))
}

/**
 * Allocate shipping_tier_base proportionally across lines that count toward free shipping.
 */
export function eligibleTierSubtotalFromItems(items = [], tierBase = null) {
  const gross = productSubtotalFromItems(items)
  if (gross <= 0) return 0
  const base = tierBase != null ? Number(tierBase) : gross
  return roundMoney(
    items.reduce((sum, item) => {
      if (!itemCountsTowardFreeShipping(item)) return sum
      const line = lineProductAmount(item)
      return sum + (line / gross) * base
    }, 0)
  )
}

/** @deprecated use eligibleTierSubtotalFromItems */
export function freeShippingSubtotalFromItems(items = []) {
  return eligibleTierSubtotalFromItems(items)
}

export function coordsFromAddress(address) {
  if (!address) return null
  const lat = Number(address.latitude ?? address.lat)
  const lng = Number(address.longitude ?? address.lng)
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null
  return { lat, lng }
}

function toRad(deg) {
  return (deg * Math.PI) / 180
}

export function distanceKm(a, b) {
  if (!a || !b) return null
  const lat1 = Number(a.lat)
  const lng1 = Number(a.lng)
  const lat2 = Number(b.lat)
  const lng2 = Number(b.lng)
  if (![lat1, lng1, lat2, lng2].every(Number.isFinite)) return null
  const dLat = toRad(lat2 - lat1)
  const dLng = toRad(lng2 - lng1)
  const x =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2
  return 6371 * 2 * Math.atan2(Math.sqrt(x), Math.sqrt(1 - x))
}

export function depotFromConfig(config) {
  const depotRaw = config?.depot
  if (
    depotRaw &&
    Number.isFinite(Number(depotRaw.lat)) &&
    Number.isFinite(Number(depotRaw.lng))
  ) {
    return {
      lat: Number(depotRaw.lat),
      lng: Number(depotRaw.lng),
      label: depotRaw.label || DEFAULT_DEPOT.label
    }
  }
  return { ...DEFAULT_DEPOT }
}

/** @deprecated depot lookup only — region fees no longer use km rings. */
export function distanceConfigFrom(config) {
  return {
    depot: depotFromConfig(config),
    rings: [],
    beyondSurcharge: 0,
    beyondLabel: '',
    enabled: false
  }
}

export function cityKey(city) {
  return String(city || '')
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '')
}

export function cityFromAddress(address) {
  if (!address) return ''
  if (typeof address === 'string') return address
  return address.city || address.locality || ''
}

function asRegionGroups(raw) {
  if (!Array.isArray(raw)) return []
  return raw
    .map((group) => ({
      label: group?.label || '',
      surcharge: Number(group?.surcharge) || 0,
      cities: (group?.cities || []).map((city) => String(city).trim()).filter(Boolean)
    }))
    .filter((group) => group.cities.length)
}

export function regionSurchargesFrom(config) {
  const fromNew = asRegionGroups(config?.region_surcharges)
  if (fromNew.length) return fromNew
  const fromLegacy = asRegionGroups(config?.distance_surcharges)
  if (fromLegacy.length) return fromLegacy
  return DEFAULT_REGION_SURCHARGES.map((group) => ({
    label: group.label,
    surcharge: group.surcharge,
    cities: [...group.cities]
  }))
}

export function matchRegionSurcharge(config, address) {
  const city = cityFromAddress(address)
  const key = cityKey(city)
  const groups = regionSurchargesFrom(config)
  if (!key) {
    return { surcharge: 0, label: DEFAULT_REGION_LABEL, city, region: null, matched: false }
  }
  const region = groups.find((group) => group.cities.some((item) => cityKey(item) === key))
  if (region) {
    return {
      surcharge: roundMoney(region.surcharge),
      label: region.label,
      city,
      region,
      matched: true
    }
  }
  return { surcharge: 0, label: DEFAULT_REGION_LABEL, city, region: null, matched: false }
}

export function regionPinColor(config, address) {
  const match = matchRegionSurcharge(config, address)
  if (!match.matched) return BASE_REGION_COLOR
  const groups = regionSurchargesFrom(config)
  const index = groups.findIndex(
    (group) => group.label === match.region.label && group.surcharge === match.region.surcharge
  )
  return REGION_PIN_COLORS[Math.max(0, index) % REGION_PIN_COLORS.length]
}

export function regionSurchargeForAddress(config, address) {
  return matchRegionSurcharge(config, address).surcharge
}

export function baseDeliveryFee(config) {
  const tiers = [...(config?.tiers || [])].sort((a, b) => (a.threshold || 0) - (b.threshold || 0))
  if (!tiers.length) return 7.99
  return roundMoney(tiers[0].fee)
}

/** Base-tier fee + region add-on, e.g. 7.99 or 9.99. */
export function regionListedFee(config, surcharge = 0) {
  return roundMoney(baseDeliveryFee(config) + (Number(surcharge) || 0))
}

/** Live shipping fee for admin/checkout/user previews. */
export function previewShippingFeeForOrder({
  items = [],
  deliveryMethod = 'pickup',
  shippingConfig = null,
  storeCredit = 0,
  adjustment = 0,
  address = null
} = {}) {
  if (deliveryMethod !== 'delivery') return 0
  const productGross = productSubtotalFromItems(items)
  const tierBase = shippingTierBaseFromParts(productGross, storeCredit, adjustment)
  const tierSubtotal = eligibleTierSubtotalFromItems(items, tierBase)
  const base = calculateShippingFee(tierSubtotal, shippingConfig)
  return roundMoney(base + regionSurchargeForAddress(shippingConfig, address))
}

export function previewShippingBreakdown({
  items = [],
  deliveryMethod = 'pickup',
  shippingConfig = null,
  storeCredit = 0,
  adjustment = 0,
  address = null
} = {}) {
  if (deliveryMethod !== 'delivery') {
    return {
      base: 0,
      surcharge: 0,
      total: 0,
      label: '',
      city: '',
      matched: false
    }
  }
  const productGross = productSubtotalFromItems(items)
  const tierBase = shippingTierBaseFromParts(productGross, storeCredit, adjustment)
  const tierSubtotal = eligibleTierSubtotalFromItems(items, tierBase)
  const base = calculateShippingFee(tierSubtotal, shippingConfig)
  const match = matchRegionSurcharge(shippingConfig, address)
  return {
    base,
    surcharge: roundMoney(match.surcharge),
    total: roundMoney(base + match.surcharge),
    label: match.label,
    city: match.city,
    matched: match.matched
  }
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
