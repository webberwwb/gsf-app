<template>
  <div class="zone-map-wrap">
    <div ref="mapEl" class="zone-map"></div>
    <p v-if="loadError" class="zone-map-error">{{ loadError }}</p>
  </div>
</template>

<script>
import { loadGoogleMaps, RING_COLORS } from '@shared/maps/loadGoogleMaps.js'
import { distanceConfigFrom } from '../utils/shipping'

export default {
  name: 'DeliveryZoneMap',
  props: {
    depot: { type: Object, default: null },
    rings: { type: Array, default: () => [] },
    pin: { type: Object, default: null },
    highlightMaxKm: { type: Number, default: null }
  },
  data() {
    return { loadError: null }
  },
  watch: {
    depot: { deep: true, handler() { this.draw() } },
    rings: { deep: true, handler() { this.draw() } },
    pin: { deep: true, handler() { this.draw() } },
    highlightMaxKm() { this.draw() }
  },
  mounted() {
    this.init()
  },
  beforeUnmount() {
    this.clearOverlays()
    this.map = null
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
        this.draw()
      } catch (err) {
        this.loadError = err.message || '无法加载地图'
      }
    },
    depotCenter() {
      return distanceConfigFrom({ depot: this.depot, distance_surcharges: this.rings }).depot
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
    },
    draw() {
      if (!this.map || !window.google?.maps) return
      this.clearOverlays()
      const center = this.depotCenter()
      if (!center) return
      this.depotMarker = new window.google.maps.Marker({
        map: this.map,
        position: center,
        title: '配送中心',
        clickable: false
      })
      const sorted = [...(this.rings || [])]
        .map((ring) => ({ ...ring, max_km: Number(ring.max_km) }))
        .filter((ring) => ring.max_km > 0)
        .sort((a, b) => a.max_km - b.max_km)
      this.overlays = sorted.map((ring, index) => {
        const highlight = this.highlightMaxKm != null && Number(this.highlightMaxKm) === ring.max_km
        return new window.google.maps.Circle({
          map: this.map,
          center,
          radius: ring.max_km * 1000,
          strokeColor: RING_COLORS[index % RING_COLORS.length],
          strokeOpacity: highlight ? 1 : 0.7,
          strokeWeight: highlight ? 3 : 1.5,
          fillColor: RING_COLORS[index % RING_COLORS.length],
          fillOpacity: highlight ? 0.18 : 0.08,
          clickable: false
        })
      })
      if (this.pin && Number.isFinite(Number(this.pin.lat)) && Number.isFinite(Number(this.pin.lng))) {
        this.pinMarker = new window.google.maps.Marker({
          map: this.map,
          position: { lat: Number(this.pin.lat), lng: Number(this.pin.lng) },
          title: '配送地址'
        })
      }
    }
  }
}
</script>

<style scoped>
.zone-map {
  width: 100%;
  height: 220px;
  border-radius: 12px;
  background: var(--md-surface-variant, #f0f0f0);
}
.zone-map-error {
  margin: 8px 0 0;
  font-size: 13px;
  color: #c62828;
}
</style>
