<template>
  <div class="zone-map-wrap">
    <div ref="mapEl" class="zone-map"></div>
    <p v-if="loadError" class="zone-map-error">{{ loadError }}</p>
    <p v-else-if="hint" class="zone-map-hint">{{ hint }}</p>
  </div>
</template>

<script>
import { loadGoogleMaps } from '@shared/maps/loadGoogleMaps.js'
import { depotFromConfig } from '../utils/shipping'

export default {
  name: 'DeliveryZoneMap',
  props: {
    depot: { type: Object, default: null },
    rings: { type: Array, default: () => [] },
    pin: { type: Object, default: null },
    pins: { type: Array, default: () => [] },
    highlightMaxKm: { type: Number, default: null },
    editable: { type: Boolean, default: false },
    hint: { type: String, default: '' }
  },
  emits: ['update:depot', 'map-click', 'select-pin'],
  data() {
    return { loadError: null }
  },
  watch: {
    depot: { deep: true, handler() { this.draw() } },
    rings: { deep: true, handler() { this.draw() } },
    pin: { deep: true, handler() { this.draw() } },
    pins: { deep: true, handler() { this.draw() } },
    highlightMaxKm() { this.draw() }
  },
  mounted() {
    this.init()
  },
  beforeUnmount() {
    this.teardown()
  },
  methods: {
    async init() {
      try {
        await loadGoogleMaps({ libraries: ['places'] })
        const center = this.depotCenter() || { lat: 43.8776838, lng: -79.3639328 }
        this.map = new window.google.maps.Map(this.$refs.mapEl, {
          center,
          zoom: 10,
          mapTypeControl: false,
          streetViewControl: false,
          fullscreenControl: false,
          clickableIcons: false
        })
        this.map.addListener('click', (event) => {
          const coords = { lat: event.latLng.lat(), lng: event.latLng.lng() }
          this.$emit('map-click', coords)
        })
        this.draw()
      } catch (err) {
        this.loadError = err.message || '无法加载地图'
      }
    },
    depotCenter() {
      return depotFromConfig({ depot: this.depot })
    },
    teardown() {
      this.clearOverlays()
      this.map = null
    },
    clearOverlays() {
      for (const overlay of this.overlays || []) overlay.setMap(null)
      this.overlays = []
      if (this.depotMarker) {
        this.depotMarker.setMap(null)
        this.depotMarker = null
      }
      if (this.pinMarker) {
        this.pinMarker.setMap(null)
        this.pinMarker = null
      }
      for (const marker of this.pinMarkers || []) marker.setMap(null)
      this.pinMarkers = []
    },
    draw() {
      if (!this.map || !window.google?.maps) return
      this.clearOverlays()
      const center = this.depotCenter()
      if (!center) return
      this.depotMarker = new window.google.maps.Marker({
        map: this.map,
        position: center,
        draggable: this.editable,
        title: '配送中心',
        zIndex: 10
      })
      if (this.editable) {
        this.depotMarker.addListener('dragend', () => {
          const pos = this.depotMarker.getPosition()
          this.$emit('update:depot', {
            lat: pos.lat(),
            lng: pos.lng(),
            label: this.depot?.label || ''
          })
        })
      }
      this.pinMarkers = (this.pins || [])
        .filter((item) => Number.isFinite(Number(item.lat)) && Number.isFinite(Number(item.lng)))
        .map((item) => {
          const position = { lat: Number(item.lat), lng: Number(item.lng) }
          const marker = new window.google.maps.Marker({
            map: this.map,
            position,
            title: item.title || item.label || '配送地址',
            zIndex: 15,
            icon: {
              path: window.google.maps.SymbolPath.CIRCLE,
              scale: 7,
              fillColor: item.color || '#FB8C00',
              fillOpacity: 0.92,
              strokeColor: '#fff',
              strokeWeight: 1.5
            }
          })
          marker.addListener('click', () => {
            this.$emit('select-pin', item)
            this.$emit('map-click', position)
          })
          return marker
        })
      if (this.pin && Number.isFinite(Number(this.pin.lat)) && Number.isFinite(Number(this.pin.lng))) {
        this.pinMarker = new window.google.maps.Marker({
          map: this.map,
          position: { lat: Number(this.pin.lat), lng: Number(this.pin.lng) },
          title: this.pin.label || '地址',
          zIndex: 20
        })
      }
    }
  }
}
</script>

<style scoped>
.zone-map-wrap {
  position: relative;
}
.zone-map {
  width: 100%;
  height: 400px;
  border-radius: 8px;
  background: #f0f0f0;
}
.zone-map-error,
.zone-map-hint {
  margin: 8px 0 0;
  font-size: 13px;
  color: #666;
}
.zone-map-error {
  color: #c62828;
}
</style>
