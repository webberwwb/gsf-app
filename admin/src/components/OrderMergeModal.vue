<template>
  <div v-if="show" class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <div class="header-content">
          <div class="header-icon">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
            </svg>
          </div>
          <h2>合并订单</h2>
        </div>
        <button @click="$emit('close')" class="close-btn">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="modal-body">
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="error" class="error-message">{{ error }}</div>
        <template v-else>
          <!-- Order Summary -->
          <div class="orders-summary">
            <h3>将合并以下订单:</h3>
            <div class="orders-list">
              <div v-for="(order, index) in orders" :key="order.id" class="order-item">
                <div class="order-badge">订单 {{ index + 1 }}</div>
                <div class="order-details">
                  <div class="order-number">{{ order.order_number }}</div>
                  <div class="order-info">
                    <span>商品: {{ order.items?.length || 0 }}件</span>
                    <span>总价: ${{ parseFloat(order.total || 0).toFixed(2) }}</span>
                  </div>
                  <div class="order-meta">
                    <span v-if="order.payment_method" class="meta-item">
                      支付: {{ getPaymentMethodText(order.payment_method) }}
                    </span>
                    <span v-if="order.delivery_method" class="meta-item">
                      {{ getDeliveryMethodText(order.delivery_method) }}
                    </span>
                    <span v-if="order.notes" class="meta-item">备注: {{ order.notes }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Conflict Resolution -->
          <div class="conflict-resolution">
            <h3>选择要保留的信息:</h3>
            
            <!-- Payment Method -->
            <div v-if="hasConflict('payment_method')" class="conflict-section">
              <label class="conflict-label">支付方式:</label>
              <div class="conflict-options">
                <label 
                  v-for="(order, index) in orders" 
                  :key="`payment-${order.id}`"
                  class="radio-option"
                  :class="{ 'selected': mergeData.keep_payment_method === order.payment_method }">
                  <input 
                    type="radio" 
                    :value="order.payment_method" 
                    v-model="mergeData.keep_payment_method" />
                  <span>订单 {{ index + 1 }}: {{ getPaymentMethodText(order.payment_method) }}</span>
                </label>
              </div>
            </div>

            <!-- Delivery Method -->
            <div v-if="hasConflict('delivery_method')" class="conflict-section">
              <label class="conflict-label">配送方式:</label>
              <div class="conflict-options">
                <label 
                  v-for="(order, index) in orders" 
                  :key="`delivery-${order.id}`"
                  class="radio-option"
                  :class="{ 'selected': mergeData.keep_delivery_method === order.delivery_method }">
                  <input 
                    type="radio" 
                    :value="order.delivery_method" 
                    v-model="mergeData.keep_delivery_method"
                    @change="handleDeliveryMethodChange" />
                  <span>订单 {{ index + 1 }}: {{ getDeliveryMethodText(order.delivery_method) }}</span>
                </label>
              </div>
            </div>

            <!-- Pickup Location (if pickup) -->
            <div v-if="mergeData.keep_delivery_method === 'pickup' && hasConflict('pickup_location')" class="conflict-section">
              <label class="conflict-label">自取点:</label>
              <div class="conflict-options">
                <label 
                  v-for="(order, index) in orders.filter(o => o.pickup_location)" 
                  :key="`pickup-${order.id}`"
                  class="radio-option"
                  :class="{ 'selected': mergeData.keep_pickup_location === order.pickup_location }">
                  <input 
                    type="radio" 
                    :value="order.pickup_location" 
                    v-model="mergeData.keep_pickup_location" />
                  <span>订单 {{ index + 1 }}: {{ getPickupLocationText(order.pickup_location) }}</span>
                </label>
              </div>
            </div>

            <!-- Address (if delivery) -->
            <div v-if="mergeData.keep_delivery_method === 'delivery' && hasConflict('address_id')" class="conflict-section">
              <label class="conflict-label">配送地址:</label>
              <div class="conflict-options">
                <label 
                  v-for="(order, index) in orders.filter(o => o.address)" 
                  :key="`address-${order.id}`"
                  class="radio-option"
                  :class="{ 'selected': mergeData.keep_address_id === order.address_id }">
                  <input 
                    type="radio" 
                    :value="order.address_id" 
                    v-model="mergeData.keep_address_id" />
                  <span>订单 {{ index + 1 }}: {{ formatAddress(order.address) }}</span>
                </label>
              </div>
            </div>

            <!-- Notes -->
            <div v-if="hasAnyNotes()" class="conflict-section">
              <label class="conflict-label">备注:</label>
              <div class="conflict-options">
                <label 
                  v-for="(order, index) in orders.filter(o => o.notes)" 
                  :key="`notes-${order.id}`"
                  class="radio-option"
                  :class="{ 'selected': mergeData.keep_notes === order.notes }">
                  <input 
                    type="radio" 
                    :value="order.notes" 
                    v-model="mergeData.keep_notes" />
                  <span>订单 {{ index + 1 }}: {{ order.notes }}</span>
                </label>
                <label 
                  class="radio-option"
                  :class="{ 'selected': mergeData.keep_notes === '' }">
                  <input 
                    type="radio" 
                    value="" 
                    v-model="mergeData.keep_notes" />
                  <span>清空备注</span>
                </label>
              </div>
            </div>
          </div>

          <!-- Merged Items Preview -->
          <div class="merged-preview">
            <h3>合并后的商品列表:</h3>
            <div class="items-list">
              <div v-for="item in mergedItems" :key="item.product_id" class="item-row">
                <div class="item-info">
                  <div class="item-name">{{ item.product_name }}</div>
                  <div class="item-quantity">数量: {{ item.total_quantity }}</div>
                </div>
                <div class="item-price">${{ item.total_price.toFixed(2) }}</div>
              </div>
            </div>
            <div class="total-row">
              <span>合并后总价:</span>
              <span class="total-price">${{ mergedTotal.toFixed(2) }}</span>
            </div>
          </div>
        </template>
      </div>

      <div class="modal-footer">
        <button @click="$emit('close')" class="cancel-btn" :disabled="merging">
          取消
        </button>
        <button @click="handleMerge" class="merge-btn" :disabled="merging || !canMerge">
          <span v-if="merging">合并中...</span>
          <span v-else>确认合并</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'

export default {
  name: 'OrderMergeModal',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    orders: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      loading: false,
      error: null,
      merging: false,
      mergeData: {
        keep_payment_method: null,
        keep_delivery_method: null,
        keep_address_id: null,
        keep_pickup_location: null,
        keep_notes: null
      }
    }
  },
  computed: {
    mergedItems() {
      const itemsMap = new Map()
      
      this.orders.forEach(order => {
        if (order.items) {
          order.items.forEach(item => {
            const productId = item.product_id
            if (itemsMap.has(productId)) {
              const existing = itemsMap.get(productId)
              existing.total_quantity += item.quantity
              existing.total_price += parseFloat(item.total_price || 0)
            } else {
              itemsMap.set(productId, {
                product_id: productId,
                product_name: item.product?.name || `商品 ${productId}`,
                total_quantity: item.quantity,
                total_price: parseFloat(item.total_price || 0)
              })
            }
          })
        }
      })
      
      return Array.from(itemsMap.values())
    },
    mergedTotal() {
      return this.mergedItems.reduce((sum, item) => sum + item.total_price, 0)
    },
    canMerge() {
      // Check if all conflicts are resolved
      if (this.hasConflict('payment_method') && !this.mergeData.keep_payment_method) {
        return false
      }
      if (this.hasConflict('delivery_method') && !this.mergeData.keep_delivery_method) {
        return false
      }
      if (this.mergeData.keep_delivery_method === 'pickup' && 
          this.hasConflict('pickup_location') && 
          !this.mergeData.keep_pickup_location) {
        return false
      }
      if (this.mergeData.keep_delivery_method === 'delivery' && 
          this.hasConflict('address_id') && 
          !this.mergeData.keep_address_id) {
        return false
      }
      return true
    }
  },
  watch: {
    show(newVal) {
      if (newVal) {
        this.initializeMergeData()
      }
    }
  },
  methods: {
    initializeMergeData() {
      // Initialize with values from first order
      if (this.orders.length > 0) {
        const firstOrder = this.orders[0]
        this.mergeData.keep_payment_method = firstOrder.payment_method
        this.mergeData.keep_delivery_method = firstOrder.delivery_method
        this.mergeData.keep_address_id = firstOrder.address_id
        this.mergeData.keep_pickup_location = firstOrder.pickup_location
        
        // For notes: find the first order with notes, or default to empty string
        const orderWithNotes = this.orders.find(o => o.notes)
        this.mergeData.keep_notes = orderWithNotes ? orderWithNotes.notes : ''
      }
    },
    hasConflict(field) {
      const values = new Set()
      this.orders.forEach(order => {
        const value = order[field]
        if (value !== null && value !== undefined && value !== '') {
          values.add(value)
        }
      })
      return values.size > 1
    },
    hasAnyNotes() {
      // Check if any order has notes
      return this.orders.some(order => order.notes && order.notes.trim() !== '')
    },
    handleDeliveryMethodChange() {
      // Clear related fields when delivery method changes
      if (this.mergeData.keep_delivery_method === 'pickup') {
        this.mergeData.keep_address_id = null
      } else if (this.mergeData.keep_delivery_method === 'delivery') {
        this.mergeData.keep_pickup_location = null
      }
    },
    async handleMerge() {
      if (!this.canMerge) {
        return
      }

      this.merging = true
      this.error = null

      try {
        const orderIds = this.orders.map(o => o.id)
        const response = await apiClient.post('/admin/orders/merge', {
          order_ids: orderIds,
          keep_payment_method: this.mergeData.keep_payment_method,
          keep_delivery_method: this.mergeData.keep_delivery_method,
          keep_address_id: this.mergeData.keep_address_id,
          keep_pickup_location: this.mergeData.keep_pickup_location,
          keep_notes: this.mergeData.keep_notes
        })

        this.$emit('merged', response.data.merged_order)
        this.$emit('close')
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || '合并失败'
        console.error('Failed to merge orders:', error)
      } finally {
        this.merging = false
      }
    },
    getPaymentMethodText(method) {
      const map = {
        'cash': '现金',
        'etransfer': '电子转账'
      }
      return map[method] || method
    },
    getDeliveryMethodText(method) {
      const map = {
        'pickup': '自取',
        'delivery': '配送'
      }
      return map[method] || method
    },
    getPickupLocationText(location) {
      return location === 'markham' ? 'Markham' : (location || 'N/A')
    },
    formatAddress(address) {
      if (!address) return ''
      const parts = []
      if (address.address_line1) parts.push(address.address_line1)
      if (address.address_line2) parts.push(address.address_line2)
      if (address.city) parts.push(address.city)
      if (address.postal_code) parts.push(address.postal_code)
      return parts.join(', ')
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: var(--md-spacing-md);
}

.modal-content {
  background: #FFFFFF;
  border-radius: 24px;
  max-width: 900px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0px 11px 15px -7px rgba(0, 0, 0, 0.2), 0px 24px 38px 3px rgba(0, 0, 0, 0.14), 0px 9px 46px 8px rgba(0, 0, 0, 0.12);
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  background: linear-gradient(135deg, #FF8C00 0%, #FFA500 100%);
  border-bottom: 1px solid rgba(255, 165, 0, 0.2);
  border-radius: 24px 24px 0 0;
}

.header-content {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
}

.header-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 10px;
  color: #FF8C00;
}

.header-icon svg {
  width: 24px;
  height: 24px;
}

.modal-header h2 {
  font-size: 1.25rem;
  color: rgba(0, 0, 0, 0.9);
  font-weight: 600;
  margin: 0;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: rgba(0, 0, 0, 0.7);
  cursor: pointer;
  border-radius: var(--md-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn svg {
  width: 20px;
  height: 20px;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  color: rgba(0, 0, 0, 0.9);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--md-spacing-lg);
  background: #FAFAFA;
}

.loading, .error-message {
  text-align: center;
  padding: var(--md-spacing-xl);
}

.error-message {
  color: #C62828;
  background: #FFEBEE;
  padding: var(--md-spacing-md);
  border-radius: var(--md-radius-md);
}

.orders-summary,
.conflict-resolution,
.merged-preview {
  background: #FFFFFF;
  border-radius: 12px;
  padding: var(--md-spacing-md);
  margin-bottom: var(--md-spacing-md);
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.08);
}

.orders-summary h3,
.conflict-resolution h3,
.merged-preview h3 {
  margin: 0 0 var(--md-spacing-md) 0;
  font-size: 1rem;
  color: rgba(0, 0, 0, 0.87);
  font-weight: 600;
  border-bottom: 2px solid #FF8C00;
  padding-bottom: var(--md-spacing-sm);
}

.orders-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
}

.order-item {
  display: flex;
  gap: var(--md-spacing-md);
  padding: var(--md-spacing-md);
  background: #F5F5F5;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.order-badge {
  background: #FF8C00;
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  height: fit-content;
}

.order-details {
  flex: 1;
}

.order-number {
  font-family: 'Courier New', monospace;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.87);
  margin-bottom: 4px;
}

.order-info {
  display: flex;
  gap: var(--md-spacing-md);
  font-size: 0.875rem;
  color: rgba(0, 0, 0, 0.6);
  margin-bottom: 4px;
}

.order-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--md-spacing-sm);
  font-size: 0.75rem;
}

.meta-item {
  background: rgba(255, 140, 0, 0.1);
  padding: 2px 8px;
  border-radius: 8px;
  color: #E65100;
}

.conflict-section {
  margin-bottom: var(--md-spacing-md);
}

.conflict-label {
  display: block;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.87);
  margin-bottom: var(--md-spacing-sm);
  font-size: 0.875rem;
}

.conflict-options {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-xs);
}

.radio-option {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  background: #F5F5F5;
  border-radius: 8px;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
}

.radio-option:hover {
  background: #EEEEEE;
}

.radio-option.selected {
  background: #FFF3E0;
  border-color: #FF8C00;
}

.radio-option input[type="radio"] {
  cursor: pointer;
}

.radio-option span {
  font-size: 0.875rem;
  color: rgba(0, 0, 0, 0.87);
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
  margin-bottom: var(--md-spacing-md);
}

.item-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-sm);
  background: #F5F5F5;
  border-radius: 8px;
}

.item-info {
  flex: 1;
}

.item-name {
  font-weight: 500;
  color: rgba(0, 0, 0, 0.87);
  margin-bottom: 2px;
}

.item-quantity {
  font-size: 0.875rem;
  color: rgba(0, 0, 0, 0.6);
}

.item-price {
  font-weight: 600;
  color: #FF8C00;
  font-size: 1rem;
}

.total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-md);
  background: #FFF3E0;
  border-radius: 8px;
  border: 2px solid #FF8C00;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.87);
}

.total-price {
  font-size: 1.25rem;
  color: #FF8C00;
}

.modal-footer {
  display: flex;
  gap: var(--md-spacing-md);
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  background: #FFFFFF;
}

.cancel-btn,
.merge-btn {
  flex: 1;
  padding: 12px 24px;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  min-height: 44px;
}

.cancel-btn {
  background: rgba(0, 0, 0, 0.05);
  color: rgba(0, 0, 0, 0.87);
}

.cancel-btn:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.08);
}

.merge-btn {
  background: #FF8C00;
  color: white;
  box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.2);
}

.merge-btn:hover:not(:disabled) {
  background: #FFA500;
  box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.3);
}

.merge-btn:disabled,
.cancel-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 767px) {
  .modal-content {
    max-height: 95vh;
  }

  .modal-body {
    padding: var(--md-spacing-md);
  }

  .order-item {
    flex-direction: column;
  }

  .order-info {
    flex-direction: column;
    gap: 4px;
  }

  .modal-footer {
    flex-direction: column;
  }

  .cancel-btn,
  .merge-btn {
    width: 100%;
  }
}
</style>
