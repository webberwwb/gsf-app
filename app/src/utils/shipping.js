import apiClient from '../api/client'

export {
  calculateShippingFee,
  getNextShippingTier,
  shippingTierBaseFromParts
} from '@shared/order-pricing/shipping.js'

let shippingConfigCache = null
let configFetchPromise = null

/**
 * Fetch delivery fee configuration from API
 */
export async function fetchShippingConfig() {
  if (shippingConfigCache) {
    return shippingConfigCache
  }

  if (configFetchPromise) {
    return configFetchPromise
  }

  configFetchPromise = apiClient.get('/constants/delivery-fee-config')
    .then(response => {
      shippingConfigCache = response.data
      configFetchPromise = null
      return shippingConfigCache
    })
    .catch(error => {
      console.error('Error fetching shipping config:', error)
      configFetchPromise = null
      return {
        tiers: [
          { threshold: 0, fee: 7.99 },
          { threshold: 150.00, fee: 0 }
        ]
      }
    })

  return configFetchPromise
}

export function clearShippingConfigCache() {
  shippingConfigCache = null
  configFetchPromise = null
}
