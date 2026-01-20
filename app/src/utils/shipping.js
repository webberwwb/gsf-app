import apiClient from '../api/client'

let shippingConfigCache = null
let configFetchPromise = null

/**
 * Fetch delivery fee configuration from API
 */
export async function fetchShippingConfig() {
  // Return cached config if available
  if (shippingConfigCache) {
    return shippingConfigCache
  }

  // If a fetch is already in progress, wait for it
  if (configFetchPromise) {
    return configFetchPromise
  }

  // Fetch config from API
  configFetchPromise = apiClient.get('/constants/delivery-fee-config')
    .then(response => {
      shippingConfigCache = response.data
      configFetchPromise = null
      return shippingConfigCache
    })
    .catch(error => {
      console.error('Error fetching shipping config:', error)
      configFetchPromise = null
      // Return default config on error
      return {
        base_fee: 7.99,
        threshold_1_amount: 58.00,
        threshold_1_fee: 5.99,
        threshold_2_amount: 128.00,
        threshold_2_fee: 3.99,
        threshold_3_amount: 150.00
      }
    })

  return configFetchPromise
}

/**
 * Calculate shipping fee based on subtotal and config
 * @param {number} subtotal - Order subtotal (excluding products that don't count toward free shipping)
 * @param {object} config - Shipping fee configuration
 * @returns {number} Shipping fee amount
 */
export function calculateShippingFee(subtotal, config) {
  if (!config) {
    // Fallback to default calculation
    if (subtotal >= 150) return 0
    if (subtotal >= 128) return 3.99
    if (subtotal >= 58) return 5.99
    return 7.99
  }

  const threshold3 = config.threshold_3_amount || 150
  const threshold2 = config.threshold_2_amount || 128
  const threshold1 = config.threshold_1_amount || 58
  const baseFee = config.base_fee || 7.99
  const fee1 = config.threshold_1_fee || 5.99
  const fee2 = config.threshold_2_fee || 3.99

  // Apply thresholds in descending order
  if (subtotal >= threshold3) {
    return 0 // Free delivery
  } else if (subtotal >= threshold2) {
    return fee2
  } else if (subtotal >= threshold1) {
    return fee1
  } else {
    return baseFee
  }
}

/**
 * Clear the shipping config cache (useful for testing or when config is updated)
 */
export function clearShippingConfigCache() {
  shippingConfigCache = null
  configFetchPromise = null
}
