/**
 * Composable for Google Maps Places Autocomplete
 * Provides address autocomplete functionality with auto-fill for city, postal code, etc.
 */
export function useAddressAutocomplete(inputElement, options = {}) {
  let autocomplete = null
  let place = null
  
  const {
    onPlaceSelected = () => {},
    componentRestrictions = { country: 'ca' }, // Default to Canada
    types = ['address'],
    fields = ['address_components', 'formatted_address', 'geometry']
  } = options

  // Load Google Maps script if not already loaded
  const loadGoogleMapsScript = () => {
    return new Promise((resolve, reject) => {
      // Check if script is already loaded
      if (window.google && window.google.maps && window.google.maps.places) {
        resolve()
        return
      }

      // Check if script is already being loaded
      if (document.querySelector('script[src*="maps.googleapis.com"]')) {
        const checkInterval = setInterval(() => {
          if (window.google && window.google.maps && window.google.maps.places) {
            clearInterval(checkInterval)
            resolve()
          }
        }, 100)
        return
      }

      const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY
      if (!apiKey) {
        reject(new Error('Google Maps API key not found. Please set VITE_GOOGLE_MAPS_API_KEY in your .env file'))
        return
      }

      const script = document.createElement('script')
      script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places&language=zh-CN`
      script.async = true
      script.defer = true
      script.onload = () => {
        if (window.google && window.google.maps && window.google.maps.places) {
          resolve()
        } else {
          reject(new Error('Failed to load Google Maps Places API'))
        }
      }
      script.onerror = () => {
        reject(new Error('Failed to load Google Maps script'))
      }
      document.head.appendChild(script)
    })
  }

  // Parse address components from Google Places result
  const parseAddressComponents = (place) => {
    const components = place.address_components || []
    const result = {
      formatted_address: place.formatted_address || '',
      address_line1: '',
      address_line2: '',
      city: '',
      postal_code: '',
      province: '',
      country: 'Canada'
    }

    // Helper function to get component by type
    const getComponent = (type) => {
      const component = components.find(comp => comp.types.includes(type))
      return component ? component.long_name : ''
    }

    // Extract address components
    const streetNumber = getComponent('street_number')
    const route = getComponent('route')
    const subpremise = getComponent('subpremise') // Unit number, floor, etc.
    
    // Build address_line1
    const streetAddress = [streetNumber, route].filter(Boolean).join(' ')
    result.address_line1 = streetAddress || place.formatted_address.split(',')[0] || ''
    
    // Extract city (locality or administrative_area_level_2)
    result.city = getComponent('locality') || 
                  getComponent('administrative_area_level_2') || 
                  getComponent('sublocality') || 
                  ''
    
    // Extract postal code
    result.postal_code = getComponent('postal_code') || ''
    
    // Extract province/state
    result.province = getComponent('administrative_area_level_1') || ''
    
    // Extract country
    const country = getComponent('country')
    if (country) {
      result.country = country
    }

    // If subpremise exists, it could go to address_line2
    if (subpremise) {
      result.address_line2 = subpremise
    }

    return result
  }

  // Initialize autocomplete
  const initAutocomplete = async () => {
    if (!inputElement || !inputElement.value) {
      return { error: 'Input element not available' }
    }

    try {
      await loadGoogleMapsScript()

      if (!window.google || !window.google.maps || !window.google.maps.places) {
        throw new Error('Google Maps Places API not available')
      }

      // Destroy existing instance if any
      destroy()

      autocomplete = new window.google.maps.places.Autocomplete(
        inputElement.value,
        {
          componentRestrictions,
          types,
          fields
        }
      )

      // Listen for place selection
      autocomplete.addListener('place_changed', () => {
        const selectedPlace = autocomplete.getPlace()
        if (selectedPlace && selectedPlace.address_components) {
          place = selectedPlace
          const parsedAddress = parseAddressComponents(selectedPlace)
          onPlaceSelected(parsedAddress)
        }
      })

      return { success: true }
    } catch (err) {
      console.error('Error initializing autocomplete:', err)
      return { error: err.message }
    }
  }

  // Clean up autocomplete instance
  const destroy = () => {
    if (autocomplete) {
      window.google?.maps?.event?.clearInstanceListeners?.(autocomplete)
      autocomplete = null
    }
    place = null
  }

  return {
    initAutocomplete,
    destroy,
    parseAddressComponents
  }
}

