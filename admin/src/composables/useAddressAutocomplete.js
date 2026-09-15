/**
 * Composable for Google Maps Places Autocomplete
 */
import { loadGoogleMaps, parsePlaceAddress } from '@shared/maps/loadGoogleMaps.js'

export function useAddressAutocomplete(inputElement, options = {}) {
  let autocomplete = null

  const {
    onPlaceSelected = () => {},
    componentRestrictions = { country: 'ca' },
    types = ['address'],
    fields = ['address_components', 'formatted_address', 'geometry', 'place_id']
  } = options

  const initAutocomplete = async () => {
    if (!inputElement || !inputElement.value) {
      return { error: 'Input element not available' }
    }

    try {
      await loadGoogleMaps({ libraries: ['places'] })
      if (!window.google?.maps?.places) {
        throw new Error('Google Maps Places API not available')
      }

      destroy()
      autocomplete = new window.google.maps.places.Autocomplete(
        inputElement.value,
        { componentRestrictions, types, fields }
      )
      autocomplete.addListener('place_changed', () => {
        const selectedPlace = autocomplete.getPlace()
        if (selectedPlace?.address_components) {
          onPlaceSelected(parsePlaceAddress(selectedPlace))
        }
      })
      return { success: true }
    } catch (err) {
      console.error('Error initializing autocomplete:', err)
      return { error: err.message }
    }
  }

  const destroy = () => {
    if (autocomplete) {
      window.google?.maps?.event?.clearInstanceListeners?.(autocomplete)
      autocomplete = null
    }
  }

  return { initAutocomplete, destroy, parseAddressComponents: parsePlaceAddress }
}
