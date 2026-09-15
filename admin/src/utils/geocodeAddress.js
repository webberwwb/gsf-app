import apiClient from '../api/client'

export function addressQuery(address) {
  if (!address) return ''
  return [
    address.address_line1,
    address.address_line2,
    address.city,
    address.postal_code,
    'ON',
    'Canada'
  ]
    .filter((part) => part && String(part).trim())
    .join(', ')
}

export function geocodeAddress(geocoder, address) {
  const query = addressQuery(address)
  if (!query || !geocoder) return Promise.resolve(null)
  return new Promise((resolve) => {
    geocoder.geocode(
      { address: query, region: 'ca', componentRestrictions: { country: 'CA' } },
      (results, status) => {
        if (status === 'OK' && results?.[0]?.geometry?.location) {
          const loc = results[0].geometry.location
          resolve({
            lat: loc.lat(),
            lng: loc.lng(),
            place_id: results[0].place_id || null
          })
        } else {
          resolve(null)
        }
      }
    )
  })
}

export function persistAddressCoords(addressId, coords) {
  if (!addressId || !coords) return
  apiClient
    .put(`/admin/fulfillment/addresses/${addressId}/coords`, {
      latitude: coords.lat,
      longitude: coords.lng,
      place_id: coords.place_id
    })
    .catch(() => {})
}
