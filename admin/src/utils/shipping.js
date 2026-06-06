import apiClient from '../api/client'

export {
  calculateShippingFee,
  freeShippingSubtotalFromItems,
  previewShippingFeeForOrder,
  getNextShippingTier,
  shippingTierBaseFromParts
} from '@shared/order-pricing/shipping.js'

let shippingConfigCache = null
let configFetchPromise = null

const DEFAULT_SHIPPING_CONFIG = {
  tiers: [
    { threshold: 0, fee: 7.99 },
    { threshold: 58, fee: 5.99 },
    { threshold: 128, fee: 3.99 },
    { threshold: 150, fee: 0 }
  ]
}

/** Fetch active delivery fee tiers (cached). */
export async function fetchShippingConfig() {
  if (shippingConfigCache) {
    return shippingConfigCache
  }
  if (configFetchPromise) {
    return configFetchPromise
  }
  configFetchPromise = apiClient
    .get('/constants/delivery-fee-config')
    .then((response) => {
      shippingConfigCache = response.data?.tiers?.length
        ? response.data
        : DEFAULT_SHIPPING_CONFIG
      configFetchPromise = null
      return shippingConfigCache
    })
    .catch((error) => {
      console.error('Error fetching shipping config:', error)
      configFetchPromise = null
      shippingConfigCache = DEFAULT_SHIPPING_CONFIG
      return shippingConfigCache
    })
  return configFetchPromise
}

export function clearShippingConfigCache() {
  shippingConfigCache = null
  configFetchPromise = null
}
