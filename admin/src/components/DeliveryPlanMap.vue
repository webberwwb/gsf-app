<template>
  <div class="plan-map-wrap">
    <div class="plan-map-toolbar">
      <div class="pin-legend">
        <span><i class="swatch unassigned"></i>未分配</span>
        <span><i class="swatch self"></i>我来送</span>
        <span><i class="swatch third"></i>第三方</span>
      </div>
    </div>
    <div ref="mapEl" class="plan-map"></div>
    <p v-if="loadError" class="plan-map-error">{{ loadError }}</p>
    <p v-else-if="missingCount" class="plan-map-hint">正在定位 {{ missingCount }} 个地址…</p>
  </div>
</template>

<script>
import { loadGoogleMaps } from '@shared/maps/loadGoogleMaps.js'
import { DEFAULT_DEPOT, coordsFromAddress, distanceKm } from '../utils/shipping'
import { addressQuery, geocodeAddress, persistAddressCoords } from '../utils/geocodeAddress'
import { routeSeqLabel } from '../utils/deliveryRoute'

const LANE_PINS = {
  unassigned: 'https://maps.google.com/mapfiles/ms/icons/yellow-dot.png',
  self: 'https://maps.google.com/mapfiles/ms/icons/orange-dot.png',
  third_party: 'https://maps.google.com/mapfiles/ms/icons/blue-dot.png'
}

export default {
  name: 'DeliveryPlanMap',
  props: {
    unassigned: { type: Array, default: () => [] },
    self: { type: Array, default: () => [] },
    thirdParty: { type: Array, default: () => [] },
    selectedOrderId: { type: [Number, String], default: null },
    depot: { type: Object, default: null },
    rings: { type: Array, default: () => [] }
  },
  emits: ['select-order'],
  data() {
    return {
      loadError: null,
      missingCount: 0,
      extraCoords: {}
    }
  },
  watch: {
    unassigned: { deep: true, handler() { this.refresh() } },
    self: { deep: true, handler() { this.refresh() } },
    thirdParty: { deep: true, handler() { this.refresh() } },
    depot: { deep: true, handler() { this.draw() } },
    selectedOrderId() { this.draw() }
  },
  mounted() {
    this.init()
  },
  beforeUnmount() {
    this.clear()
    this.map = null
  },
  methods: {
    async init() {
      try {
        await loadGoogleMaps({ libraries: ['places'] })
        const center = this.depotCenter()
        this.geocoder = new window.google.maps.Geocoder()
        this.map = new window.google.maps.Map(this.$refs.mapEl, {
          center,
          zoom: 10,
          maxZoom: 11,
          minZoom: 8,
          mapTypeControl: false,
          streetViewControl: false,
          fullscreenControl: false,
          clickableIcons: false
        })
        await this.refresh()
      } catch (err) {
        this.loadError = err.message || '无法加载地图'
      }
    },
    depotCenter() {
      const raw = this.depot
      if (raw && Number.isFinite(Number(raw.lat)) && Number.isFinite(Number(raw.lng))) {
        return { lat: Number(raw.lat), lng: Number(raw.lng) }
      }
      return DEFAULT_DEPOT
    },
    allOrders() {
      const rows = []
      for (const [lane, orders] of [
        ['unassigned', this.unassigned],
        ['self', this.self],
        ['third_party', this.thirdParty]
      ]) {
        orders.forEach((order, index) => {
          rows.push({ order, lane, index })
        })
      }
      return rows
    },
    coordsFor(order) {
      const fromRow = coordsFromAddress(order.address)
      if (fromRow) return fromRow
      const id = order.address?.id
      return id != null ? this.extraCoords[id] : null
    },
    async refresh() {
      if (!this.map) return
      const missing = this.allOrders().filter((row) => {
        const address = row.order.address
        if (!address) return false
        if (this.coordsFor(row.order)) return false
        return Boolean(addressQuery(address))
      })
      this.missingCount = missing.length
      for (const row of missing) {
        const coords = await geocodeAddress(this.geocoder, row.order.address)
        if (coords) {
          this.extraCoords = { ...this.extraCoords, [row.order.address.id]: coords }
          if (row.order.address) {
            row.order.address.latitude = coords.lat
            row.order.address.longitude = coords.lng
          }
          persistAddressCoords(row.order.address.id, coords)
        }
        this.missingCount = Math.max(0, this.missingCount - 1)
      }
      this.draw()
    },
    clear() {
      for (const overlay of this.overlays || []) overlay.setMap(null)
      this.overlays = []
      for (const marker of this.markers || []) marker.setMap(null)
      this.markers = []
      if (this.depotMarker) {
        this.depotMarker.setMap(null)
        this.depotMarker = null
      }
    },
    applyView(center, stops) {
      this.map.setCenter(center)
      let zoom = 10
      for (const stop of stops) {
        const km = distanceKm(center, stop.coords)
        if (km > 55) zoom = Math.min(zoom, 8)
        else if (km > 28) zoom = Math.min(zoom, 9)
      }
      this.map.setZoom(zoom)
    },
    draw() {
      if (!this.map || !window.google?.maps) return
      this.clear()
      const center = this.depotCenter()
      this.depotMarker = new window.google.maps.Marker({
        map: this.map,
        position: center,
        title: '配送中心',
        zIndex: 5,
        icon: {
          path: window.google.maps.SymbolPath.CIRCLE,
          scale: 6,
          fillColor: '#333',
          fillOpacity: 1,
          strokeColor: '#fff',
          strokeWeight: 2
        }
      })
      const stops = this.allOrders()
        .map((row) => ({ ...row, coords: this.coordsFor(row.order) }))
        .filter((row) => row.coords)
      this.markers = stops.map(({ order, lane, coords, index }) => {
        const selected = String(this.selectedOrderId) === String(order.id)
        const marker = new window.google.maps.Marker({
          map: this.map,
          position: coords,
          title: [order.order_number, lane === 'self' ? `我来送 #${routeSeqLabel(order, index)}` : lane === 'third_party' ? '第三方' : '未分配']
            .filter(Boolean)
            .join(' · '),
          zIndex: selected ? 30 : 10,
          icon: {
            url: LANE_PINS[lane] || LANE_PINS.unassigned,
            scaledSize: new window.google.maps.Size(selected ? 40 : 32, selected ? 40 : 32)
          },
          label:
            lane === 'self'
              ? {
                  text: String(routeSeqLabel(order, index)),
                  color: '#fff',
                  fontSize: '11px',
                  fontWeight: '700'
                }
              : undefined
        })
        marker.addListener('click', () => this.$emit('select-order', order, lane))
        return marker
      })
      this.applyView(center, stops)
    }
  }
}
</script>

<style scoped>
.plan-map-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.pin-legend {
  display: flex;
  gap: 14px;
  font-size: 13px;
  color: #555;
}
.pin-legend span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.swatch {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}
.swatch.unassigned { background: #F9A825; }
.swatch.self { background: #FB8C00; }
.swatch.third { background: #1E88E5; }
.rings-toggle {
  font-size: 13px;
  color: #555;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.plan-map {
  width: 100%;
  height: 420px;
  border-radius: 12px;
  background: #f0f0f0;
}
.plan-map-error {
  margin: 8px 0 0;
  font-size: 13px;
  color: #c62828;
}
.plan-map-hint {
  margin: 8px 0 0;
  font-size: 13px;
  color: #666;
}
</style>
