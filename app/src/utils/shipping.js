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
        tiers: [
          { threshold: 0, fee: 7.99 },
          { threshold: 58.00, fee: 5.99 },
          { threshold: 128.00, fee: 3.99 },
          { threshold: 150.00, fee: 0 }
        ]
      }
    })

  return configFetchPromise
}

/**
 * Calculate shipping fee based on subtotal and config
 * @param {number} subtotal - Order subtotal (excluding products that don't count toward free shipping)
 * @param {object} config - Shipping fee configuration with tiers array
 * @returns {number} Shipping fee amount
 */
export function calculateShippingFee(subtotal, config) {
  if (!config || !config.tiers || config.tiers.length === 0) {
    // Fallback to default calculation
    if (subtotal >= 150) return 0
    if (subtotal >= 128) return 3.99
    if (subtotal >= 58) return 5.99
    return 7.99
  }

  // Get tiers sorted by threshold (should already be sorted)
  const tiers = [...config.tiers].sort((a, b) => a.threshold - b.threshold)
  
  // Find the appropriate tier (highest threshold that's <= subtotal)
  let applicableFee = null
  for (const tier of tiers) {
    if (subtotal >= tier.threshold) {
      applicableFee = tier.fee
    } else {
      // Since tiers are sorted, we can break early
      break
    }
  }
  
  // If we found a tier, use it; otherwise use the first tier (base fee)
  if (applicableFee !== null) {
    return applicableFee
  } else {
    return tiers[0]?.fee || 7.99
  }
}

/**
 * Get the next shipping tier threshold that would give a better rate
 * @param {number} subtotal - Current order subtotal
 * @param {object} config - Shipping fee configuration with tiers array
 * @returns {object|null} Next tier info with {threshold, fee, savings} or null if at best tier
 */
export function getNextShippingTier(subtotal, config) {
  if (!config || !config.tiers || config.tiers.length === 0) {
    return null
  }

  const currentFee = calculateShippingFee(subtotal, config)
  const tiers = [...config.tiers].sort((a, b) => a.threshold - b.threshold)
  
  // Find the next tier with a lower fee
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

/**
 * Clear the shipping config cache (useful for testing or when config is updated)
 */
export function clearShippingConfigCache() {
  shippingConfigCache = null
  configFetchPromise = null
}
