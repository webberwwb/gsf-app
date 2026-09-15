/**
 * Shared Google Maps JS loader + Places parse helpers.
 */
export function loadGoogleMaps({ libraries = ['places'] } = {}) {
  return new Promise((resolve, reject) => {
    if (window.google?.maps) {
      resolve(window.google.maps)
      return
    }

    const existing = document.querySelector('script[src*="maps.googleapis.com"]')
    if (existing) {
      const wait = setInterval(() => {
        if (window.google?.maps) {
          clearInterval(wait)
          resolve(window.google.maps)
        }
      }, 80)
      return
    }

    const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY
    if (!apiKey) {
      reject(new Error('Google Maps API key not found. Set VITE_GOOGLE_MAPS_API_KEY.'))
      return
    }

    const params = new URLSearchParams({
      key: apiKey,
      libraries: libraries.join(','),
      language: 'zh-CN'
    })
    const script = document.createElement('script')
    script.src = `https://maps.googleapis.com/maps/api/js?${params}`
    script.async = true
    script.defer = true
    script.onload = () => {
      if (window.google?.maps) resolve(window.google.maps)
      else reject(new Error('Failed to load Google Maps'))
    }
    script.onerror = () => reject(new Error('Failed to load Google Maps script'))
    document.head.appendChild(script)
  })
}

export function coordsFromPlace(place) {
  const loc = place?.geometry?.location
  if (!loc) return null
  const lat = typeof loc.lat === 'function' ? loc.lat() : loc.lat
  const lng = typeof loc.lng === 'function' ? loc.lng() : loc.lng
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null
  return { lat, lng }
}

export function parsePlaceAddress(place) {
  const components = place?.address_components || []
  const getComponent = (type) => {
    const component = components.find((comp) => comp.types.includes(type))
    return component ? component.long_name : ''
  }

  const streetNumber = getComponent('street_number')
  const route = getComponent('route')
  const subpremise = getComponent('subpremise')
  const streetAddress = [streetNumber, route].filter(Boolean).join(' ')
  const coords = coordsFromPlace(place)

  return {
    formatted_address: place?.formatted_address || '',
    address_line1: streetAddress || (place?.formatted_address || '').split(',')[0] || '',
    address_line2: subpremise || '',
    city:
      getComponent('locality') ||
      getComponent('administrative_area_level_2') ||
      getComponent('sublocality') ||
      '',
    postal_code: getComponent('postal_code') || '',
    province: getComponent('administrative_area_level_1') || '',
    country: getComponent('country') || 'Canada',
    latitude: coords?.lat ?? null,
    longitude: coords?.lng ?? null,
    place_id: place?.place_id || null
  }
}

export const RING_COLORS = ['#43A047', '#1E88E5', '#FB8C00', '#8E24AA', '#00897B', '#C62828']
