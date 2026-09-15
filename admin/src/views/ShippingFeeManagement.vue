<template>
  <div class="shipping-fee-page">
    <div class="page-header">
      <h1>运费管理</h1>
      <p class="page-description">配置订单运费规则。不计入免运的商品价格不会计入免运费门槛计算。</p>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="config-form-container">
      <form @submit.prevent="saveConfig" class="config-form">
        <div class="tiers-header">
          <h2>运费档次</h2>
          <button type="button" @click="addTier" class="add-tier-btn">
            + 添加档次
          </button>
        </div>

        <div class="tiers-list">
          <div v-for="(tier, index) in formData.tiers" :key="index" class="tier-item">
            <div class="tier-header">
              <h3>{{ getTierTitle(index) }}</h3>
              <button 
                v-if="canRemoveTier(index)" 
                type="button" 
                @click="removeTier(index)" 
                class="remove-tier-btn"
                title="删除此档次"
              >
                ✕
              </button>
            </div>
            
            <div class="tier-fields">
              <div class="form-group">
                <label>订单小计门槛</label>
                <div class="input-with-unit">
                  <input 
                    v-model.number="tier.threshold" 
                    type="number" 
                    step="0.01" 
                    min="0" 
                    required
                    :disabled="index === 0"
                    placeholder="0.00"
                  />
                  <span class="unit">$</span>
                </div>
                <small v-if="index === 0" class="form-hint">基础运费 (门槛固定为 $0)</small>
                <small v-else class="form-hint">订单小计达到此金额时使用此档次的运费</small>
              </div>
              
              <div class="form-group">
                <label>运费</label>
                <div class="input-with-unit">
                  <input 
                    v-model.number="tier.fee" 
                    type="number" 
                    step="0.01" 
                    min="0" 
                    required 
                    placeholder="0.00"
                  />
                  <span class="unit">$</span>
                </div>
                <small v-if="tier.fee === 0 && index > 0" class="form-hint">设为 $0 即免运费</small>
              </div>
            </div>
          </div>
        </div>

        <div class="distance-header">
          <h2>地区加价</h2>
          <button type="button" @click="addRegion" class="add-tier-btn">+ 添加地区</button>
        </div>
        <p class="distance-help">
          顾客运费 = 上面的档次运费 + 所在城市加价。未列出的城市不加价。司机配送费：Markham / Richmond Hill $6，其他城市 $7。
        </p>
        <div class="tiers-list">
          <div v-for="(group, index) in formData.region_surcharges" :key="index" class="tier-item">
            <div class="tier-header">
              <h3>{{ group.label || `地区 ${index + 1}` }}</h3>
              <button type="button" class="remove-tier-btn" @click="removeRegion(index)">✕</button>
            </div>
            <div class="tier-fields region-fields">
              <div class="form-group">
                <label>名称</label>
                <input v-model="group.label" type="text" class="plain-input" placeholder="如 Waterloo / Kitchener / Guelph" />
              </div>
              <div class="form-group">
                <label>加价</label>
                <div class="input-with-unit">
                  <input v-model.number="group.surcharge" type="number" step="0.01" min="0" required />
                  <span class="unit">$</span>
                </div>
              </div>
              <div class="form-group cities-field">
                <label>城市（逗号分隔）</label>
                <input v-model="group.citiesText" type="text" class="plain-input" placeholder="Waterloo, Kitchener, Guelph" />
              </div>
            </div>
          </div>
        </div>
        <button type="button" class="reset-btn default-regions-btn" @click="useDefaultRegions">填入默认地区</button>
        <div class="depot-fields">
          <div class="form-group">
            <label>查看团购配送地址</label>
            <select v-model="selectedDealId" class="plain-input deal-select" @change="loadDealOrders">
              <option value="">选择团购，加载配送地址</option>
              <option v-for="deal in deals" :key="deal.id" :value="String(deal.id)">
                {{ deal.title }}（{{ dealStatusLabel(deal.status) }}）
              </option>
            </select>
            <small v-if="ordersLoading" class="form-hint">正在加载配送订单…</small>
            <small v-else-if="locatingCount" class="form-hint">正在定位 {{ locatingCount }} 个地址…</small>
            <small v-else-if="selectedDealId" class="form-hint">{{ dealOrdersHint }}</small>
          </div>
        </div>
        <div v-if="regionCounts.length" class="ring-counts">
          <div v-for="row in regionCounts" :key="row.key" class="ring-count" :style="{ '--swatch': row.color }">
            <span class="ring-count-label">{{ row.label }}</span>
            <span class="ring-count-value">{{ row.count }} 单</span>
            <span class="ring-count-fee">+${{ formatPrice(row.surcharge) }}</span>
          </div>
        </div>
        <DeliveryZoneMap
          :depot="formData.depot"
          :pins="orderPins"
          hint="地图只用于看订单分布。点按颜色对应上面的地区加价。"
          @select-pin="onSelectOrderPin"
        />
        <p v-if="previewText" class="preview-distance">{{ previewText }}</p>

        <div class="form-actions">
          <button type="button" @click="resetForm" class="reset-btn">重置</button>
          <button type="submit" :disabled="saving" class="save-btn">
            {{ saving ? '保存中...' : '保存配置' }}
          </button>
        </div>
      </form>

      <div class="rules-preview">
        <h2>规则预览</h2>
        <div class="preview-content">
          <div v-for="(tier, index) in sortedTiers" :key="index" class="preview-item">
            <div class="preview-condition">
              <span v-if="index === 0">订单小计 &lt; {{ formatPrice(getNextThreshold(index)) }}</span>
              <span v-else-if="index === sortedTiers.length - 1">
                订单小计 ≥ {{ formatPrice(tier.threshold) }}
              </span>
              <span v-else>
                {{ formatPrice(tier.threshold) }} ≤ 订单小计 &lt; {{ formatPrice(getNextThreshold(index)) }}
              </span>
            </div>
            <div class="preview-fee">
              <span v-if="tier.fee === 0" class="free-fee">档次免运费</span>
              <span v-else>档次运费: ${{ formatPrice(tier.fee) }}</span>
            </div>
          </div>
          <div v-for="(group, index) in formData.region_surcharges" :key="'r' + index" class="preview-item">
            <div class="preview-condition">{{ group.label || `地区 ${index + 1}` }}：{{ group.citiesText }}</div>
            <div class="preview-fee">+${{ formatPrice(group.surcharge) }}</div>
          </div>
          <div class="preview-item">
            <div class="preview-condition">其他城市</div>
            <div class="preview-fee">+$0.00</div>
          </div>
          <div class="preview-item">
            <div class="preview-condition">司机：Markham / Richmond Hill</div>
            <div class="preview-fee">$6.00</div>
          </div>
          <div class="preview-item">
            <div class="preview-condition">司机：其他城市</div>
            <div class="preview-fee">$7.00</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '@/api/client'
import { useModal } from '@/composables/useModal'
import { loadGoogleMaps } from '@shared/maps/loadGoogleMaps.js'
import { formatOrderMoney2 } from '../utils/orderPricing'
import {
  BASE_REGION_COLOR,
  coordsFromAddress,
  DEFAULT_DEPOT,
  DEFAULT_REGION_SURCHARGES,
  matchRegionSurcharge,
  regionPinColor,
  regionSurchargesFrom
} from '../utils/shipping'
import { addressQuery, geocodeAddress, persistAddressCoords } from '../utils/geocodeAddress'
import DeliveryZoneMap from '../components/DeliveryZoneMap.vue'

const SUGGESTED_DEPOT = { ...DEFAULT_DEPOT }
const OLD_DEPOTS = [
  [43.8647, -79.3593],
  [43.8561, -79.337]
]

function isPlaceholderDepot(depot) {
  if (!depot) return true
  const lat = Number(depot.lat)
  const lng = Number(depot.lng)
  return OLD_DEPOTS.some(
    ([oldLat, oldLng]) => Math.abs(lat - oldLat) < 0.0003 && Math.abs(lng - oldLng) < 0.0003
  )
}

function citiesText(cities) {
  return (cities || []).join(', ')
}

function parseCities(text) {
  return String(text || '')
    .split(/[,，]/)
    .map((city) => city.trim())
    .filter(Boolean)
}

function regionFormRows(config) {
  return regionSurchargesFrom(config).map((group) => ({
    label: group.label,
    surcharge: group.surcharge,
    citiesText: citiesText(group.cities)
  }))
}

function emptyForm() {
  return {
    tiers: [
      { threshold: 0, fee: 7.99 },
      { threshold: 58.00, fee: 5.99 },
      { threshold: 128.00, fee: 3.99 },
      { threshold: 150.00, fee: 0 }
    ],
    depot: { ...SUGGESTED_DEPOT },
    region_surcharges: regionFormRows()
  }
}

export default {
  name: 'ShippingFeeManagement',
  components: { DeliveryZoneMap },
  setup() {
    const { confirm, error: showError } = useModal()
    return { confirm, showError }
  },
  data() {
    return {
      loading: true,
      error: null,
      saving: false,
      previewPin: null,
      formData: emptyForm(),
      originalData: null,
      deals: [],
      selectedDealId: '',
      deliveryOrders: [],
      extraCoords: {},
      ordersLoading: false,
      locatingCount: 0
    }
  },
  computed: {
    regionConfig() {
      return {
        region_surcharges: this.formData.region_surcharges.map((group) => ({
          label: group.label,
          surcharge: parseFloat(group.surcharge) || 0,
          cities: parseCities(group.citiesText)
        }))
      }
    },
    previewText() {
      if (!this.previewPin?.label && !this.previewPin?.city) return ''
      const match = matchRegionSurcharge(this.regionConfig, { city: this.previewPin.city })
      const orderBit = this.previewPin?.label ? `${this.previewPin.label} · ` : ''
      const city = match.city || this.previewPin.city || ''
      const label = match.label || '其他城市'
      return `预览：${orderBit}${city} · ${label} · +$${this.formatPrice(match.surcharge)}`
    },
    orderPins() {
      return this.locatedOrders
        .filter((row) => row.coords)
        .map((row) => ({
          lat: row.coords.lat,
          lng: row.coords.lng,
          title: row.title,
          label: row.title,
          city: row.city,
          color: row.color,
          orderId: row.order.id
        }))
    },
    locatedOrders() {
      return this.deliveryOrders.map((order) => {
        const coords = this.coordsFor(order)
        const match = matchRegionSurcharge(this.regionConfig, order.address)
        return {
          order,
          coords,
          match,
          city: match.city || order.address?.city || '',
          title: this.orderPinTitle(order, match),
          color: coords ? regionPinColor(this.regionConfig, order.address) : '#9e9e9e'
        }
      })
    },
    regionCounts() {
      if (!this.deliveryOrders.length) return []
      const groups = this.regionConfig.region_surcharges
      const rows = groups.map((group, index) => ({
        key: `region-${index}`,
        label: group.label || `地区 ${index + 1}`,
        color: regionPinColor(this.regionConfig, { city: group.cities[0] }),
        surcharge: group.surcharge,
        count: 0
      }))
      const other = {
        key: 'other',
        label: '其他城市',
        color: BASE_REGION_COLOR,
        surcharge: 0,
        count: 0
      }
      for (const row of this.locatedOrders) {
        if (row.match?.matched) {
          const index = groups.findIndex(
            (group) => group.label === row.match.region.label && group.surcharge === row.match.region.surcharge
          )
          if (index >= 0) rows[index].count += 1
          else other.count += 1
        } else {
          other.count += 1
        }
      }
      return [...rows, other]
    },
    dealOrdersHint() {
      const total = this.deliveryOrders.length
      const located = this.locatedOrders.filter((row) => row.coords).length
      if (!total) return '该团购暂无配送订单'
      return `已标出 ${located}/${total} 个配送地址`
    },
    sortedTiers() {
      // Return a sorted copy of tiers for preview, ensuring values are valid numbers
      return [...this.formData.tiers].map(tier => ({
        threshold: parseFloat(tier.threshold) || 0,
        fee: parseFloat(tier.fee) || 0
      })).sort((a, b) => a.threshold - b.threshold)
    }
  },
  async mounted() {
    await Promise.all([this.fetchConfig(), this.loadDeals()])
  },
  methods: {
    getTierTitle(index) {
      if (index === 0) {
        return '基础运费'
      }
      return `运费档次 ${index}`
    },
    canRemoveTier(index) {
      // Can't remove the base tier (index 0), and need at least 1 tier
      return index > 0 && this.formData.tiers.length > 1
    },
    onSelectOrderPin(pin) {
      this.previewPin = {
        lat: pin.lat,
        lng: pin.lng,
        label: pin.label || '',
        city: pin.city || ''
      }
    },
    dealStatusLabel(status) {
      return {
        draft: '草稿',
        upcoming: '即将开始',
        active: '进行中',
        closed: '已截单',
        preparing: '正在配货',
        ready_for_pickup: '可以取货',
        completed: '已完成'
      }[status] || status
    },
    orderPinTitle(order, match) {
      const city = match?.city || order.address?.city || ''
      const extra = match?.matched ? `+$${this.formatPrice(match.surcharge)}` : '基础运费'
      return [order.order_number, city, extra].filter(Boolean).join(' · ')
    },
    coordsFor(order) {
      const fromRow = coordsFromAddress(order.address)
      if (fromRow) return fromRow
      const id = order.address?.id
      return id != null ? this.extraCoords[id] : null
    },
    flattenPlan(plan) {
      return [...(plan.unassigned || []), ...(plan.self || []), ...(plan.third_party || [])]
    },
    async loadDeals() {
      try {
        const res = await apiClient.get('/admin/group-deals', {
          params: { per_page: 50, include_products: 0 }
        })
        this.deals = res.data.group_deals || []
        const current = this.deals.find((deal) =>
          ['active', 'closed', 'preparing', 'ready_for_pickup'].includes(deal.status)
        )
        if (current) {
          this.selectedDealId = String(current.id)
          await this.loadDealOrders()
        }
      } catch (error) {
        console.error('Failed to load group deals:', error)
      }
    },
    async loadDealOrders() {
      if (!this.selectedDealId) {
        this.deliveryOrders = []
        this.locatingCount = 0
        return
      }
      this.ordersLoading = true
      try {
        const res = await apiClient.get(`/admin/fulfillment/deals/${this.selectedDealId}/delivery-plan`)
        this.deliveryOrders = this.flattenPlan(res.data)
        await this.locateMissingOrders()
      } catch (error) {
        console.error('Failed to load delivery orders:', error)
        this.deliveryOrders = []
        this.showError(error.response?.data?.error || '加载配送地址失败')
      } finally {
        this.ordersLoading = false
      }
    },
    async locateMissingOrders() {
      const missing = this.deliveryOrders.filter((order) => {
        if (this.coordsFor(order) || !order.address) return false
        return Boolean(addressQuery(order.address))
      })
      this.locatingCount = missing.length
      if (!missing.length) return
      try {
        await loadGoogleMaps({ libraries: ['places'] })
      } catch {
        this.locatingCount = 0
        return
      }
      const geocoder = new window.google.maps.Geocoder()
      for (const order of missing) {
        const coords = await geocodeAddress(geocoder, order.address)
        if (coords) {
          this.extraCoords = { ...this.extraCoords, [order.address.id]: coords }
          order.address.latitude = coords.lat
          order.address.longitude = coords.lng
          persistAddressCoords(order.address.id, coords)
        }
        this.locatingCount = Math.max(0, this.locatingCount - 1)
      }
    },
    addRegion() {
      this.formData.region_surcharges.push({
        label: '',
        surcharge: 0,
        citiesText: ''
      })
    },
    removeRegion(index) {
      this.formData.region_surcharges.splice(index, 1)
    },
    useDefaultRegions() {
      this.formData.region_surcharges = regionFormRows({
        region_surcharges: DEFAULT_REGION_SURCHARGES
      })
    },
    addTier() {
      // Add a new tier with threshold higher than the last one
      const lastTier = this.sortedTiers[this.sortedTiers.length - 1]
      const newThreshold = lastTier ? lastTier.threshold + 10 : 0
      
      this.formData.tiers.push({
        threshold: newThreshold,
        fee: 0
      })
    },
    removeTier(index) {
      if (this.canRemoveTier(index)) {
        this.formData.tiers.splice(index, 1)
      }
    },
    getNextThreshold(index) {
      if (index < this.sortedTiers.length - 1) {
        return this.sortedTiers[index + 1].threshold
      }
      return null
    },
    formatPrice(value) {
      if (value === null || value === undefined || value === '' || isNaN(value)) {
        return '0.00'
      }
      return formatOrderMoney2(value)
    },
    async fetchConfig() {
      this.loading = true
      this.error = null
      try {
        const response = await apiClient.get('/admin/delivery-fee-config')
        const config = response.data.config
        if (config?.tiers) {
          this.formData.tiers = config.tiers.map(tier => ({
            threshold: tier.threshold || 0,
            fee: tier.fee || 0
          }))
          this.formData.depot = isPlaceholderDepot(config.depot)
            ? { ...SUGGESTED_DEPOT, label: config.depot?.label || SUGGESTED_DEPOT.label }
            : { ...SUGGESTED_DEPOT, ...config.depot }
          this.formData.region_surcharges = regionFormRows(config)
          this.originalData = JSON.parse(JSON.stringify(this.formData))
        }
      } catch (error) {
        console.error('Error fetching delivery fee config:', error)
        this.error = error.response?.data?.error || '加载配置失败'
      } finally {
        this.loading = false
      }
    },
    async saveConfig() {
      // Sanitize tier values first - handle empty/NaN inputs
      this.formData.tiers = this.formData.tiers.map(tier => ({
        threshold: parseFloat(tier.threshold) || 0,
        fee: parseFloat(tier.fee) || 0
      }))
      
      // Validate tiers are in ascending order
      const sortedTiers = [...this.formData.tiers].sort((a, b) => a.threshold - b.threshold)
      
      // Check for duplicate thresholds
      const thresholds = sortedTiers.map(t => t.threshold)
      const uniqueThresholds = new Set(thresholds)
      if (thresholds.length !== uniqueThresholds.size) {
        this.showError('门槛金额不能重复')
        return
      }
      
      // Check if first tier has threshold 0
      if (sortedTiers[0].threshold !== 0) {
        this.showError('第一个档次必须是基础运费(门槛为 $0)')
        return
      }

      // Validate ascending order
      for (let i = 1; i < sortedTiers.length; i++) {
        if (sortedTiers[i].threshold <= sortedTiers[i-1].threshold) {
          this.showError('门槛金额必须按升序排列')
          return
        }
      }

      this.saving = true
      this.error = null
      try {
        const regions = this.regionConfig.region_surcharges.filter((group) => group.cities.length)
        if (!regions.length) {
          this.showError('请至少添加一个地区，或点「填入默认地区」')
          return
        }
        const response = await apiClient.put('/admin/delivery-fee-config', {
          tiers: sortedTiers,
          depot: this.formData.depot,
          region_surcharges: regions
        })
        
        this.formData.tiers = sortedTiers
        this.formData.region_surcharges = regionFormRows({ region_surcharges: regions })
        this.originalData = JSON.parse(JSON.stringify(this.formData))
        
        await this.confirm('运费配置已成功更新')
        // Optionally refresh the config
        await this.fetchConfig()
      } catch (error) {
        console.error('Error saving delivery fee config:', error)
        this.error = error.response?.data?.error || '保存配置失败'
        this.showError(this.error)
      } finally {
        this.saving = false
      }
    },
    resetForm() {
      if (this.originalData) {
        this.formData = JSON.parse(JSON.stringify(this.originalData))
      } else {
        this.formData = emptyForm()
      }
    }
  }
}
</script>

<style scoped>
.shipping-fee-page {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 8px;
}

.page-description {
  color: #666;
  font-size: 14px;
}

.loading, .error {
  text-align: center;
  padding: 40px;
  font-size: 16px;
}

.error {
  color: #d32f2f;
}

.config-form-container {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 32px;
}

.config-form {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.distance-header,
.tiers-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.distance-header {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e0e0e0;
}
.distance-help {
  margin: -12px 0 16px;
  font-size: 13px;
  color: #666;
}
.default-regions-btn {
  margin-bottom: 16px;
}
.depot-fields {
  margin: 8px 0 16px;
}
.region-fields {
  grid-template-columns: 1fr 140px;
}
.cities-field {
  grid-column: 1 / -1;
}
.deal-select {
  height: 40px;
}
.ring-counts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0 0 12px;
}
.ring-count {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  background: #f5f5f5;
  font-size: 13px;
}
.ring-count::before {
  content: '';
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--swatch);
  flex-shrink: 0;
}
.ring-count-label {
  color: #555;
}
.ring-count-value {
  font-weight: 600;
  color: #222;
}
.ring-count-fee {
  color: #f57c00;
  font-weight: 600;
}
.depot-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.depot-row .plain-input {
  flex: 1;
  min-width: 0;
}
.depot-row .reset-btn {
  flex-shrink: 0;
  height: 40px;
}
.plain-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}
.preview-distance {
  margin: 10px 0 16px;
  font-size: 14px;
  color: #f57c00;
  font-weight: 600;
}

.tiers-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

.add-tier-btn {
  padding: 8px 16px;
  background: #ff9800;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.2s;
}

.add-tier-btn:hover {
  background: #f57c00;
}

.tiers-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 24px;
}

.tier-item {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  background: #fafafa;
}

.tier-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.tier-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.remove-tier-btn {
  padding: 4px 8px;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  transition: background 0.2s;
}

.remove-tier-btn:hover {
  background: #d32f2f;
}

.tier-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.input-with-unit {
  position: relative;
  display: flex;
  align-items: center;
}

.input-with-unit input {
  flex: 1;
  padding: 10px 32px 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.input-with-unit input:focus {
  outline: none;
  border-color: #ff9800;
}

.input-with-unit input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.input-with-unit .unit {
  position: absolute;
  right: 12px;
  color: #666;
  font-size: 14px;
  pointer-events: none;
}

.form-hint {
  margin-top: 4px;
  font-size: 12px;
  color: #666;
  font-style: italic;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.reset-btn, .save-btn {
  padding: 10px 24px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.reset-btn {
  background: white;
  color: #666;
  border: 1px solid #ddd;
}

.reset-btn:hover {
  background: #f5f5f5;
}

.save-btn {
  background: #ff9800;
  color: white;
}

.save-btn:hover {
  background: #f57c00;
}

.save-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.rules-preview {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  height: fit-content;
  position: sticky;
  top: 24px;
}

.rules-preview h2 {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 16px;
}

.preview-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.preview-item {
  padding: 12px;
  background: #f5f5f5;
  border-radius: 6px;
  border-left: 4px solid #ff9800;
}

.preview-condition {
  font-size: 14px;
  color: #333;
  margin-bottom: 4px;
  font-weight: 500;
}

.preview-fee {
  font-size: 16px;
  color: #f57c00;
  font-weight: 600;
}

.free-fee {
  color: #ff9800;
}

@media (max-width: 1366px) {
  .shipping-fee-page {
    padding: var(--md-spacing-md);
  }
  
  .add-tier-btn,
  .save-config-btn {
    padding: 8px 16px;
    font-size: 0.875rem;
  }
  
  .config-form-container {
    gap: var(--md-spacing-md);
  }
  
  .tier-fields {
    gap: var(--md-spacing-sm);
  }
}

@media (max-width: 968px) {
  .config-form-container {
    grid-template-columns: 1fr;
  }
  
  .rules-preview {
    position: static;
  }
  
  .tier-fields,
  .region-fields,
  .depot-fields {
    grid-template-columns: 1fr;
  }
}
</style>
