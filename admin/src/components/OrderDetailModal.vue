<template>
  <div v-if="show" class="modal-overlay" @click="$emit('close')">
    <div class="modal-content order-detail-modal" @click.stop>
      <div class="modal-header">
        <div class="header-content">
          <div class="header-icon">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div class="header-text">
            <h2>订单详情</h2>
            <p class="order-number">{{ order?.order_number }}</p>
          </div>
          <div v-if="order" class="header-status-badges">
            <span class="payment-status-badge-header" :class="`payment-${order.payment_status}`">
              {{ getPaymentStatusText(order.payment_status) }}
            </span>
          </div>
          <button @click="$emit('close')" class="close-btn">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
      <div class="modal-body">
        <div v-if="order" class="order-detail-content">
          <div class="order-info-section">
            <div class="section-header">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3>订单信息</h3>
            </div>
            <div class="info-row">
              <div class="info-item-user">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <span class="value">{{ order.user?.nickname || order.user?.phone || 'N/A' }}</span>
              </div>
              <div class="info-item-price">
                <span class="value price">${{ parseFloat(order.total || 0).toFixed(2) }}</span>
              </div>
            </div>
            <div class="info-row">
              <div class="info-item-order-status">
                <label class="order-status-label">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="width: 18px; height: 18px;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  订单状态:
                </label>
                <select v-model="localOrderStatus" class="order-status-select" @change="handleOrderStatusChange">
                  <option value="submitted">已提交订单</option>
                  <option value="confirmed">已确认订单</option>
                  <option value="preparing">正在配货</option>
                  <option value="ready_for_pickup">可以取货</option>
                  <option value="out_for_delivery">正在配送</option>
                  <option value="completed">订单完成</option>
                  <option value="cancelled">已取消</option>
                </select>
              </div>
            </div>
            <div class="info-row">
              <div class="info-item-payment-method">
                <label class="payment-method-label">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="width: 18px; height: 18px;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                  </svg>
                  支付方式:
                </label>
                <select v-model="localPaymentMethod" class="payment-method-select" @change="handlePaymentMethodChange">
                  <option value="">未选择</option>
                  <option value="cash">现金</option>
                  <option value="etransfer">电子转账</option>
                </select>
              </div>
            </div>
            <!-- Mark as Paid Button (for EMT orders) -->
            <div class="info-row" v-if="order && localPaymentMethod === 'etransfer' && order.payment_status === 'unpaid'">
              <button @click="$emit('mark-paid', order)" class="mark-paid-btn">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="width: 18px; height: 18px;">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                标记为已付款
              </button>
            </div>
          </div>

          <div class="order-items-section">
            <div class="section-header">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
              <h3>商品列表</h3>
              <button @click="showAddProductModal = true" class="add-item-btn">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="width: 18px; height: 18px;">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
                </svg>
                添加商品
              </button>
            </div>
            <div class="items-list">
              <div v-for="(item, index) in editableItems" :key="item.tempId || item.id" class="order-item-row">
                <div class="item-info">
                  <div class="item-name">{{ item.product?.name || 'N/A' }}</div>
                  <div class="item-meta">
                    <div class="quantity-controls">
                      <button @click="decreaseQuantity(index)" class="qty-btn" :disabled="item.quantity <= 1">-</button>
                      <input 
                        type="number" 
                        v-model.number="item.quantity" 
                        @input="recalculateItemPrice(index)"
                        min="1"
                        class="quantity-input" />
                      <button @click="increaseQuantity(index)" class="qty-btn">+</button>
                    </div>
                    <span class="item-price">${{ parseFloat(item.total_price || 0).toFixed(2) }}</span>
                  </div>
                  <div v-if="item.product?.pricing_type === 'weight_range' || item.product?.pricing_type === 'unit_weight'" class="weight-input-group">
                    <label>
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
                      </svg>
                      实际重量 (lb)
                    </label>
                    <input 
                      type="number" 
                      step="0.001"
                      v-model.number="item.final_weight"
                      @input="recalculateItemPrice(index)"
                      :placeholder="item.final_weight ? item.final_weight.toString() : '输入重量'"
                      class="weight-input" />
                  </div>
                </div>
                <button @click="removeItem(index)" class="remove-item-btn" title="删除商品">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
          
          <!-- Add Product Modal -->
          <div v-if="showAddProductModal" class="modal-overlay-inner" @click.stop>
            <div class="modal-content-inner" @click.stop>
              <div class="modal-header-inner">
                <h3>选择商品</h3>
                <button @click="showAddProductModal = false" class="close-btn-small">×</button>
              </div>
              <div class="modal-body-inner">
                <div v-if="availableProducts.length === 0" class="empty-products">暂无可用商品</div>
                <div v-else class="products-list">
                  <div 
                    v-for="product in availableProducts" 
                    :key="product.id"
                    @click="addProductToOrder(product)"
                    class="product-item">
                    <div class="product-name">{{ product.name }}</div>
                    <div class="product-price">${{ parseFloat(product.deal_price || product.price || 0).toFixed(2) }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="updateError" class="error-message">{{ updateError }}</div>
        </div>
      </div>
      <div class="modal-footer">
        <button 
          v-if="order && order.status !== 'completed'"
          @click="$emit('mark-complete', order)" 
          class="complete-order-btn"
          :disabled="updatingOrder || markingComplete">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="width: 18px; height: 18px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {{ markingComplete ? '处理中...' : '标记订单完成' }}
        </button>
        <button 
          @click="handleUpdateOrder" 
          class="update-order-btn"
          :disabled="updatingOrder || markingComplete">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="width: 18px; height: 18px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {{ updatingOrder ? '更新中...' : '更新订单' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'

export default {
  name: 'OrderDetailModal',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    order: {
      type: Object,
      default: null
    },
    availableProducts: {
      type: Array,
      default: () => []
    },
    updatingOrder: {
      type: Boolean,
      default: false
    },
    markingComplete: {
      type: Boolean,
      default: false
    },
    updateError: {
      type: String,
      default: null
    }
  },
  emits: ['close', 'update', 'mark-paid', 'mark-complete', 'status-change', 'payment-method-change', 'order-updated', 'update-error'],
  data() {
    return {
      localOrderStatus: '',
      localPaymentMethod: '',
      editableItems: [],
      showAddProductModal: false,
      tempIdCounter: 0,
      isInitializingOrder: false,
      lastOrderId: null // Track last initialized order ID to prevent duplicate initialization
    }
  },
  watch: {
    show(newVal) {
      if (newVal && this.order) {
        this.initializeOrder()
      } else if (!newVal) {
        this.resetModal()
      }
    },
    // Watch order.id instead of deep watching the entire object for better performance
    'order.id'(newId, oldId) {
      // Only reinitialize if order actually changed and modal is visible
      if (newId && newId !== oldId && this.show) {
        this.initializeOrder()
      }
    },
    localPaymentMethod(newVal, oldVal) {
      // Auto-mark as paid when cash is selected and order is unpaid
      // Don't trigger for cancelled orders or during initialization
      if (!this.isInitializingOrder && 
          newVal === 'cash' && 
          oldVal !== 'cash' && 
          this.order && 
          this.order.payment_status === 'unpaid' &&
          this.order.status !== 'cancelled') {
        this.$emit('payment-method-change', 'cash')
      }
    }
  },
  methods: {
    initializeOrder() {
      if (!this.order || !this.show) {
        return
      }
      
      // Prevent duplicate initialization for the same order
      if (this.order.id === this.lastOrderId) {
        return
      }
      
      this.isInitializingOrder = true
      
      // Initialize editable items
      this.editableItems = []
      if (this.order.items && Array.isArray(this.order.items)) {
        this.order.items.forEach(item => {
          this.editableItems.push({
            ...item,
            tempId: item.id,
            final_weight: item.final_weight ? parseFloat(item.final_weight) : null
          })
        })
      }
      
      // Initialize order status
      this.localOrderStatus = this.order.status || 'submitted'
      
      // Initialize payment method (watcher will check isInitializingOrder flag)
      this.localPaymentMethod = this.order.payment_method || ''
      
      // Track the order ID we just initialized
      this.lastOrderId = this.order.id
      
      // Reset initialization flag after watcher has had chance to see it
      // Use nextTick to ensure watcher checks complete before we clear the flag
      this.$nextTick(() => {
        this.isInitializingOrder = false
      })
    },
    resetModal() {
      this.localOrderStatus = ''
      this.localPaymentMethod = ''
      this.editableItems = []
      this.showAddProductModal = false
      this.tempIdCounter = 0
      this.isInitializingOrder = false
      this.lastOrderId = null
    },
    addProductToOrder(product) {
      // Check if product already exists in order
      const existingIndex = this.editableItems.findIndex(item => item.product_id === product.id)
      if (existingIndex >= 0) {
        // Increase quantity if already exists
        this.editableItems[existingIndex].quantity += 1
        this.recalculateItemPrice(existingIndex)
      } else {
        // Add new item
        let initialPrice = 0
        if (product.pricing_type === 'per_item') {
          initialPrice = parseFloat(product.deal_price || product.price || 0)
        }
        
        this.editableItems.push({
          tempId: `temp_${++this.tempIdCounter}`,
          product_id: product.id,
          product: product,
          quantity: 1,
          unit_price: initialPrice,
          total_price: initialPrice,
          final_weight: null
        })
      }
      this.showAddProductModal = false
    },
    removeItem(index) {
      this.editableItems.splice(index, 1)
    },
    increaseQuantity(index) {
      this.editableItems[index].quantity += 1
      this.recalculateItemPrice(index)
    },
    decreaseQuantity(index) {
      if (this.editableItems[index].quantity > 1) {
        this.editableItems[index].quantity -= 1
        this.recalculateItemPrice(index)
      }
    },
    recalculateItemPrice(index) {
      const item = this.editableItems[index]
      const product = item.product
      
      if (!product) return
      
      // If weight-based product
      if (product.pricing_type === 'weight_range' || product.pricing_type === 'unit_weight') {
        // Must have final_weight to calculate price
        if (!item.final_weight || item.final_weight <= 0) {
          item.unit_price = 0
          item.total_price = 0
          return
        }
        
        // For weight_range, find the matching range
        if (product.pricing_type === 'weight_range') {
          if (product.pricing_data && product.pricing_data.ranges && Array.isArray(product.pricing_data.ranges)) {
            const ranges = product.pricing_data.ranges
            let matchedPrice = 0
            for (const range of ranges) {
              const min = range.min || 0
              const max = range.max
              if (item.final_weight >= min && (max === null || max === undefined || item.final_weight < max)) {
                matchedPrice = parseFloat(range.price || 0)
                break
              }
            }
            item.unit_price = matchedPrice
            item.total_price = matchedPrice * item.quantity
          } else {
            const basePrice = parseFloat(product.deal_price || product.price || 0)
            item.unit_price = basePrice
            item.total_price = basePrice * item.quantity
          }
        } else if (product.pricing_type === 'unit_weight') {
          if (product.pricing_data && product.pricing_data.price_per_unit) {
            const pricePerUnit = parseFloat(product.pricing_data.price_per_unit || 0)
            item.unit_price = pricePerUnit * item.final_weight
            item.total_price = pricePerUnit * item.final_weight * item.quantity
          } else {
            const pricePerUnit = parseFloat(product.deal_price || product.price || 0)
            item.unit_price = pricePerUnit * item.final_weight
            item.total_price = pricePerUnit * item.final_weight * item.quantity
          }
        }
      } else {
        // Regular pricing (per_item)
        const unitPrice = parseFloat(product.deal_price || product.price || 0)
        item.unit_price = unitPrice
        item.total_price = unitPrice * item.quantity
      }
    },
    handleUpdateOrder() {
      if (!this.order || this.editableItems.length === 0) {
        this.$emit('update-error', '订单必须至少包含一个商品')
        return
      }
      
      const items = this.editableItems.map(item => ({
        product_id: item.product_id,
        quantity: item.quantity,
        final_weight: item.final_weight || null
      }))
      
      const updateData = {
        items: items
      }
      
      if (this.localPaymentMethod) {
        updateData.payment_method = this.localPaymentMethod
      }
      
      this.$emit('update', this.order.id, updateData)
    },
    handleOrderUpdated(order) {
      // Update local state when order is updated from parent
      if (order && order.id === this.order?.id) {
        // Reset lastOrderId to force re-initialization
        this.lastOrderId = null
        this.initializeOrder()
      }
    },
    handleOrderStatusChange() {
      if (!this.order || !this.localOrderStatus) {
        return
      }
      
      if (this.localOrderStatus === this.order.status) {
        return
      }
      
      this.$emit('status-change', this.order.id, this.localOrderStatus)
    },
    handlePaymentMethodChange() {
      if (this.localPaymentMethod === 'cash' && this.order && this.order.payment_status === 'unpaid') {
        this.$emit('payment-method-change', 'cash')
      }
    },
    getPaymentStatusText(paymentStatus) {
      const paymentMap = {
        'unpaid': '未付款',
        'paid': '已付款'
      }
      return paymentMap[paymentStatus] || paymentStatus
    }
  }
}
</script>

<style scoped>
/* Modal Styles */
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
  z-index: 1000;
  padding: var(--md-spacing-md);
}

.modal-content {
  background: #FFFFFF;
  border-radius: 24px;
  max-width: 800px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0px 11px 15px -7px rgba(0, 0, 0, 0.2), 0px 24px 38px 3px rgba(0, 0, 0, 0.14), 0px 9px 46px 8px rgba(0, 0, 0, 0.12);
  overflow: hidden;
}

.order-detail-modal {
  max-width: 900px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  background: var(--gradient-primary);
  border-bottom: 1px solid rgba(255, 165, 0, 0.2);
  border-radius: 24px 24px 0 0;
}

.header-content {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
  width: 100%;
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
  width: 20px;
  height: 20px;
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.header-status-badges {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  margin-left: auto;
}

.payment-status-badge-header {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.payment-status-badge-header.payment-unpaid {
  background: #FFF3E0;
  color: #E65100;
}

.payment-status-badge-header.payment-paid {
  background: #E8F5E9;
  color: #1B5E20;
}

.modal-header h2 {
  font-size: 1.125rem;
  color: rgba(0, 0, 0, 0.9);
  font-weight: 600;
  margin: 0;
}

.order-number {
  font-size: 0.8125rem;
  color: rgba(0, 0, 0, 0.7);
  font-family: 'Courier New', monospace;
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
  padding: var(--md-spacing-md);
  background: #FAFAFA;
}

.modal-footer {
  display: flex;
  gap: var(--md-spacing-md);
  padding: var(--md-spacing-md);
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  background: #FFFFFF;
  border-radius: 0 0 24px 24px;
}

.update-order-btn {
  flex: 1;
  padding: 10px 24px;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.1px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(230, 81, 0, 0.2);
  background: #FFF3E0;
  color: #E65100;
  min-height: 40px;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  position: relative;
  overflow: hidden;
  outline: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.update-order-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(230, 81, 0, 0.1);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s, opacity 0.3s;
  opacity: 0;
}

.update-order-btn:hover:not(:disabled) {
  background: #FFE0B2;
  border-color: rgba(230, 81, 0, 0.4);
  box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.16), 0px 3px 6px rgba(0, 0, 0, 0.23);
  transform: translateY(-1px);
}

.update-order-btn:active:not(:disabled) {
  background: #FFCC80;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  transform: translateY(0);
}

.update-order-btn:active:not(:disabled)::before {
  width: 300px;
  height: 300px;
  opacity: 1;
  transition: width 0s, height 0s, opacity 0.3s;
}

.update-order-btn:disabled {
  opacity: 0.38;
  cursor: not-allowed;
  box-shadow: none;
}

/* Add Product Modal Styles */
.modal-overlay-inner {
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

.modal-content-inner {
  background: #FFFFFF;
  border-radius: 16px;
  max-width: 500px;
  width: 100%;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0px 11px 15px -7px rgba(0, 0, 0, 0.2), 0px 24px 38px 3px rgba(0, 0, 0, 0.14), 0px 9px 46px 8px rgba(0, 0, 0, 0.12);
  overflow: hidden;
}

.modal-header-inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.modal-header-inner h3 {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
}

.close-btn-small {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: rgba(0, 0, 0, 0.7);
  cursor: pointer;
  border-radius: 50%;
  font-size: 24px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn-small:hover {
  background: rgba(0, 0, 0, 0.05);
}

.modal-body-inner {
  flex: 1;
  overflow-y: auto;
  padding: var(--md-spacing-md);
}

.products-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
}

.product-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  background: #F5F5F5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.product-item:hover {
  background: #EEEEEE;
  transform: translateX(4px);
}

.product-name {
  font-weight: 500;
  color: rgba(0, 0, 0, 0.87);
}

.product-price {
  font-weight: 600;
  color: #E65100;
}

.empty-products {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.order-detail-content {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.order-info-section,
.order-items-section {
  background: #FFFFFF;
  border-radius: 12px;
  padding: var(--md-spacing-md);
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.08), 0px 1px 2px rgba(0, 0, 0, 0.06);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--md-spacing-xs);
  margin-bottom: var(--md-spacing-sm);
  padding-bottom: var(--md-spacing-xs);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.add-item-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #E8F5E9;
  color: #2E7D32;
  border: 1px solid rgba(46, 125, 50, 0.2);
  border-radius: 16px;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.add-item-btn:hover {
  background: #C8E6C9;
  border-color: rgba(46, 125, 50, 0.4);
}

.section-header svg {
  width: 20px;
  height: 20px;
  color: #E65100;
}

.order-info-section h3,
.order-items-section h3 {
  font-size: 1rem;
  color: rgba(0, 0, 0, 0.87);
  margin: 0;
  font-weight: 600;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--md-spacing-md);
  margin-top: var(--md-spacing-sm);
}

.info-row:first-of-type {
  margin-top: 0;
}

.info-item-user {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-item-user svg {
  width: 18px;
  height: 18px;
  color: rgba(0, 0, 0, 0.6);
}

.info-item-price {
  display: flex;
  align-items: center;
}

.info-item-price .value.price {
  color: var(--md-primary);
  font-weight: 600;
  font-size: 1.1rem;
}

.info-item-payment-method {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  width: 100%;
}

.payment-method-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.7);
  white-space: nowrap;
}

.payment-method-select {
  flex: 1;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  background: var(--md-surface);
  color: var(--md-on-surface);
  cursor: pointer;
  max-width: 200px;
}

.payment-method-select:focus {
  outline: none;
  border-color: var(--md-primary);
  border-width: 2px;
}

.info-item-order-status {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  width: 100%;
}

.order-status-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.7);
  white-space: nowrap;
}

.order-status-select {
  flex: 1;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  background: var(--md-surface);
  color: var(--md-on-surface);
  cursor: pointer;
  max-width: 200px;
}

.order-status-select:focus {
  outline: none;
  border-color: var(--md-primary);
  border-width: 2px;
}

.mark-paid-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 24px;
  border: 1px solid rgba(46, 125, 50, 0.2);
  border-radius: 24px;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.1px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  background: #E8F5E9;
  color: #2E7D32;
  min-height: 40px;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  position: relative;
  overflow: hidden;
  outline: none;
  width: 100%;
  justify-content: center;
}

.mark-paid-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(46, 125, 50, 0.1);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s, opacity 0.3s;
  opacity: 0;
}

.mark-paid-btn:hover {
  background: #C8E6C9;
  border-color: rgba(46, 125, 50, 0.4);
  box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.16), 0px 3px 6px rgba(0, 0, 0, 0.23);
  transform: translateY(-1px);
}

.mark-paid-btn:active {
  background: #A5D6A7;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  transform: translateY(0);
}

.mark-paid-btn:active::before {
  width: 300px;
  height: 300px;
  opacity: 1;
  transition: width 0s, height 0s, opacity 0.3s;
}

.complete-order-btn {
  padding: 10px 24px;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.1px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(46, 125, 50, 0.2);
  background: #E8F5E9;
  color: #2E7D32;
  min-height: 40px;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  position: relative;
  overflow: hidden;
  outline: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.complete-order-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(46, 125, 50, 0.1);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s, opacity 0.3s;
  opacity: 0;
}

.complete-order-btn:hover:not(:disabled) {
  background: #C8E6C9;
  border-color: rgba(46, 125, 50, 0.4);
  box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.16), 0px 3px 6px rgba(0, 0, 0, 0.23);
  transform: translateY(-1px);
}

.complete-order-btn:active:not(:disabled) {
  background: #A5D6A7;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  transform: translateY(0);
}

.complete-order-btn:active:not(:disabled)::before {
  width: 300px;
  height: 300px;
  opacity: 1;
  transition: width 0s, height 0s, opacity 0.3s;
}

.complete-order-btn:disabled {
  opacity: 0.38;
  cursor: not-allowed;
  box-shadow: none;
}

.info-item .value {
  color: rgba(0, 0, 0, 0.87);
  font-size: 0.875rem;
  line-height: 1.2;
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.order-item-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--md-spacing-sm);
  background: #F5F5F5;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  transition: all 0.2s;
  gap: var(--md-spacing-sm);
}

.order-item-row:hover {
  background: #EEEEEE;
  border-color: rgba(0, 0, 0, 0.1);
}

.item-info {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
}

.item-name {
  font-size: var(--md-body-size);
  font-weight: 500;
  color: var(--md-on-surface);
}

.item-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin-top: var(--md-spacing-xs);
  gap: var(--md-spacing-md);
}

.quantity-controls {
  display: flex;
  align-items: center;
  gap: 4px;
}

.qty-btn {
  width: 28px;
  height: 28px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 4px;
  background: #FFFFFF;
  color: rgba(0, 0, 0, 0.87);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 500;
  transition: all 0.2s;
}

.qty-btn:hover:not(:disabled) {
  background: #F5F5F5;
  border-color: rgba(0, 0, 0, 0.2);
}

.qty-btn:disabled {
  opacity: 0.38;
  cursor: not-allowed;
}

.quantity-input {
  width: 50px;
  padding: 4px 8px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 4px;
  text-align: center;
  font-size: 0.875rem;
}

.remove-item-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid rgba(244, 67, 54, 0.3);
  border-radius: 50%;
  color: #F44336;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.remove-item-btn:hover {
  background: rgba(244, 67, 54, 0.2);
  border-color: rgba(244, 67, 54, 0.5);
}

.remove-item-btn svg {
  width: 18px;
  height: 18px;
}

.item-price {
  font-weight: 600;
  color: var(--md-primary);
}

.weight-input-group {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  margin-top: var(--md-spacing-sm);
  padding-top: var(--md-spacing-sm);
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.weight-input-group label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--md-label-size);
  color: rgba(0, 0, 0, 0.7);
  font-weight: 500;
  min-width: 120px;
}

.weight-input-group label svg {
  color: #E65100;
}

.weight-input {
  flex: 1;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  background: var(--md-surface);
  color: var(--md-on-surface);
  max-width: 200px;
}

.weight-input:focus {
  outline: none;
  border-color: var(--md-primary);
  border-width: 2px;
}

.error-message {
  padding: var(--md-spacing-md);
  background: #FFEBEE;
  color: #C62828;
  border-radius: var(--md-radius-md);
  font-size: var(--md-label-size);
  margin-top: var(--md-spacing-md);
}
</style>

