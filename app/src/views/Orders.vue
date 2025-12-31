<template>
  <div class="orders-page">
    <header class="page-header">
      <h1>我的订单</h1>
    </header>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="orders.length === 0" class="empty-state">
      <div class="empty-icon">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
        </svg>
      </div>
      <h2>暂无订单</h2>
      <p>您还没有任何订单，快去参与团购吧！</p>
    </div>
    <div v-else class="orders-list">
      <!-- Filter Tabs -->
      <div class="filter-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          @click="activeTab = tab.key; filterOrders()"
          :class="['tab', { active: activeTab === tab.key }]"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Orders List -->
      <div class="orders-container">
        <div 
          v-for="order in filteredOrders" 
          :key="order.id" 
          class="order-card"
          @click="viewOrderDetail(order)">
          <div class="order-header">
            <div class="order-info">
              <span class="order-number">订单号: {{ order.order_number }}</span>
              <span class="order-date">{{ formatDate(order.created_at) }}</span>
            </div>
            <span :class="['status-badge', getStatusClass(order.status)]">
              {{ getStatusLabel(order.status) }}
            </span>
          </div>

          <div v-if="order.group_deal" class="group-deal-info">
            <h3>{{ order.group_deal.title }}</h3>
            <div class="deal-dates">
              <span v-if="order.group_deal.pickup_date" class="date-item">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="date-icon">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
                取货日期: {{ formatDate(order.group_deal.pickup_date) }}
              </span>
            </div>
          </div>

          <div class="order-items">
            <div v-for="item in order.items" :key="item.id" class="order-item">
              <div v-if="item.product && item.product.image" class="item-image">
                <img :src="item.product.image" :alt="item.product.name" />
              </div>
              <div v-else class="item-image placeholder">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                </svg>
              </div>
              <div class="item-details">
                <h4>{{ item.product ? item.product.name : '商品已下架' }}</h4>
                <div class="item-meta">
                  <span>数量: {{ item.quantity }}</span>
                  <span class="item-price">${{ item.total_price.toFixed(2) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- QR Code Section for Ready for Pickup -->
          <div v-if="order.status === 'ready_for_pickup'" class="qr-code-section">
            <div class="qr-code-container">
              <h4 class="qr-code-title">取货码</h4>
              <div class="qr-code-wrapper">
                <canvas :ref="el => setQRRef(order.id, el)" class="qr-code-canvas"></canvas>
              </div>
              <div class="pickup-code-text">{{ getPickupCode(order.order_number) }}</div>
            </div>
          </div>

          <div class="order-footer">
            <div class="order-total">
              <span class="total-label">订单总额:</span>
              <span class="total-amount">${{ order.total.toFixed(2) }}</span>
            </div>
            <div class="footer-right">
              <div class="payment-status">
                <span :class="['payment-badge', getPaymentStatusClass(order.payment_status)]">
                  {{ getPaymentStatusLabel(order.payment_status) }}
                </span>
              </div>
              <div class="order-actions" @click.stop>
                <span v-if="!order.is_editable" class="deadline-badge">已截单</span>
                <template v-else-if="order.is_editable && order.status !== 'cancelled'">
                  <button @click.stop="confirmCancelOrder(order)" class="cancel-btn">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    取消订单
                  </button>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Cancel Order Confirmation Modal -->
    <div v-if="showCancelModal" class="modal-overlay" @click="closeCancelModal">
      <div class="modal-content cancel-modal" @click.stop>
        <div class="modal-header">
          <h2>取消订单</h2>
          <button @click="closeCancelModal" class="close-btn">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div class="modal-body">
          <div v-if="cancellingOrder" class="cancel-warning">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div class="warning-content">
              <h3>确认取消订单？</h3>
              <p>订单号: {{ cancellingOrder.order_number }}</p>
              <p class="warning-text">取消后将无法恢复此订单</p>
            </div>
          </div>

          <div v-if="cancelError" class="error-message">{{ cancelError }}</div>
        </div>

        <div class="modal-footer">
          <button @click="closeCancelModal" class="cancel-btn-secondary">返回</button>
          <button @click="cancelOrder" class="confirm-cancel-btn" :disabled="cancelling">
            {{ cancelling ? '取消中...' : '确认取消' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import apiClient from '../api/client'
import { useModal } from '../composables/useModal'
import QRCode from 'qrcode'
import { formatDateEST_CN } from '../utils/date'

export default {
  name: 'Orders',
  setup() {
    const { success, error } = useModal()
    return { success, error }
  },
  data() {
    return {
      loading: true,
      error: null,
      orders: [],
      activeTab: 'all',
      tabs: [
        { key: 'all', label: '全部' },
        { key: 'pending', label: '待处理' },
        { key: 'confirmed', label: '已确认' },
        { key: 'completed', label: '已完成' },
        { key: 'cancelled', label: '已取消' }
      ],
      showCancelModal: false,
      cancellingOrder: null,
      cancelling: false,
      cancelError: null,
      qrRefs: {}
    }
  },
  computed: {
    filteredOrders() {
      if (this.activeTab === 'all') {
        return this.orders
      }
      return this.orders.filter(order => order.status === this.activeTab)
    }
  },
  mounted() {
    this.loadOrders()
  },
  updated() {
    // Generate QR codes after orders are loaded/updated
    this.$nextTick(() => {
      this.generateQRCodes()
    })
  },
  methods: {
    async loadOrders() {
      this.loading = true
      this.error = null
      try {
        const response = await apiClient.get('/orders')
        this.orders = response.data.orders || []
        // Generate QR codes after loading
        this.$nextTick(() => {
          this.generateQRCodes()
        })
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || '加载订单失败'
        console.error('Failed to load orders:', error)
      } finally {
        this.loading = false
      }
    },
    filterOrders() {
      // Filtering is handled by computed property
    },
    formatDate(dateString) {
      return formatDateEST_CN(dateString)
    },
    getStatusLabel(status) {
      const labels = {
        'submitted': '已提交订单',
        'confirmed': '已确认订单',
        'preparing': '正在配货',
        'ready_for_pickup': '可以取货',
        'out_for_delivery': '正在配送',
        'delivering': '正在配送', // Legacy fallback
        'completed': '订单完成',
        'cancelled': '已取消',
        // Legacy/fallback
        'pending': '待处理',
        'processing': '处理中'
      }
      return labels[status] || status
    },
    getStatusClass(status) {
      const classes = {
        'submitted': 'pending',
        'confirmed': 'confirmed',
        'preparing': 'processing',
        'ready_for_pickup': 'processing',
        'out_for_delivery': 'processing',
        'delivering': 'processing', // Legacy fallback
        'completed': 'completed',
        'cancelled': 'cancelled',
        // Legacy/fallback
        'pending': 'pending',
        'processing': 'processing'
      }
      return classes[status] || 'pending'
    },
    getPaymentStatusLabel(status) {
      const labels = {
        'pending': '待支付',
        'unpaid': '未支付',
        'paid': '已支付',
        'failed': '支付失败',
        'refunded': '已退款'
      }
      return labels[status] || status
    },
    getPaymentStatusClass(status) {
      const classes = {
        'pending': 'pending',
        'unpaid': 'pending',
        'paid': 'paid',
        'failed': 'failed',
        'refunded': 'refunded'
      }
      return classes[status] || 'pending'
    },
    viewOrderDetail(order) {
      // Navigate to group deal detail page
      if (order.group_deal && order.group_deal.id) {
        this.$router.push(`/group-deals/${order.group_deal.id}`)
      }
    },
    confirmCancelOrder(order) {
      this.cancellingOrder = order
      this.showCancelModal = true
      this.cancelError = null
    },
    closeCancelModal() {
      this.showCancelModal = false
      this.cancellingOrder = null
      this.cancelError = null
    },
    async cancelOrder() {
      if (!this.cancellingOrder) return
      
      this.cancelling = true
      this.cancelError = null
      
      try {
        const response = await apiClient.post(`/orders/${this.cancellingOrder.id}/cancel`)
        
        // Update the order in the list
        const index = this.orders.findIndex(o => o.id === this.cancellingOrder.id)
        if (index !== -1) {
          this.orders[index] = response.data.order
        }
        
        // Close modal and show success
        this.closeCancelModal()
        
        // Show success message
        await this.success('订单已取消')
      } catch (error) {
        this.cancelError = error.response?.data?.message || error.response?.data?.error || '取消订单失败'
        console.error('Failed to cancel order:', error)
      } finally {
        this.cancelling = false
      }
    },
    setQRRef(orderId, el) {
      if (el) {
        this.qrRefs[orderId] = el
      }
    },
    async generateQRCodes() {
      // Generate QR codes for orders with ready_for_pickup status
      await this.$nextTick()
      for (const order of this.orders) {
        if (order.status === 'ready_for_pickup') {
          const canvas = this.qrRefs[order.id]
          if (canvas && !canvas.dataset?.qrGenerated) {
            try {
              // Use last part of order_number for QR code (e.g., "CGN7O7" from "GSF-20231225123456-CGN7O7")
              const pickupCode = this.getPickupCode(order.order_number)
              await QRCode.toCanvas(canvas, pickupCode, {
                width: 200,
                margin: 2,
                color: {
                  dark: '#000000',
                  light: '#FFFFFF'
                }
              })
              canvas.dataset.qrGenerated = 'true'
            } catch (error) {
              console.error('Failed to generate QR code:', error)
            }
          }
        }
      }
    },
    getPickupCode(orderNumber) {
      // Extract last part of order_number (after last dash)
      // e.g., "GSF-20231225123456-CGN7O7" -> "CGN7O7"
      if (!orderNumber) return ''
      const parts = orderNumber.split('-')
      return parts[parts.length - 1] || orderNumber
    }
  }
}
</script>

<style scoped>
.orders-page {
  min-height: 100vh;
  background: var(--md-background);
  padding-bottom: calc(80px + env(safe-area-inset-bottom)); /* Space for bottom nav */
}

.page-header {
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-2);
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--md-spacing-md);
  padding-top: calc(var(--md-spacing-lg) + env(safe-area-inset-top));
}

.header-logo {
  width: 40px;
  height: 40px;
  object-fit: contain;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.15));
}

.page-header h1 {
  font-size: var(--md-headline-size);
  color: white;
  font-weight: 500;
  letter-spacing: -0.5px;
}

.loading, .error {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--md-spacing-xl);
  text-align: center;
  min-height: 50vh;
}

.empty-icon {
  width: 80px;
  height: 80px;
  color: var(--md-on-surface-variant);
  opacity: 0.5;
  margin-bottom: var(--md-spacing-md);
}

.empty-icon svg {
  width: 100%;
  height: 100%;
}

.empty-state h2 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-sm);
}

.empty-state p {
  font-size: var(--md-body-size);
  color: var(--md-on-surface-variant);
}

.filter-tabs {
  display: flex;
  gap: var(--md-spacing-xs);
  padding: var(--md-spacing-md);
  background: var(--md-surface);
  border-bottom: 1px solid var(--md-outline-variant);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.tab {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: none;
  background: transparent;
  color: var(--md-on-surface-variant);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  border-radius: var(--md-radius-md);
  white-space: nowrap;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.tab.active {
  background: var(--md-primary);
  color: white;
}

.orders-container {
  padding: var(--md-spacing-md);
  max-width: 600px;
  margin: 0 auto;
}

.order-card {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-md);
  margin-bottom: var(--md-spacing-md);
  box-shadow: var(--md-elevation-1);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.order-card:hover {
  box-shadow: var(--md-elevation-2);
  transform: translateY(-2px);
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--md-spacing-md);
  padding-bottom: var(--md-spacing-sm);
  border-bottom: 1px solid var(--md-outline-variant);
}

.order-info {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-xs);
}

.order-number {
  font-size: var(--md-body-size);
  font-weight: 600;
  color: var(--md-on-surface);
}

.order-date {
  font-size: var(--md-label-size);
  font-weight: 400;
  color: var(--md-on-surface-variant);
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: var(--md-radius-xl);
  font-size: var(--md-label-size);
  font-weight: 500;
  white-space: nowrap;
}

.status-badge.pending {
  background: #FFF3E0;
  color: #E65100;
}

.status-badge.confirmed {
  background: #E3F2FD;
  color: #1565C0;
}

.status-badge.processing {
  background: #E8F5E9;
  color: #2E7D32;
}

.status-badge.completed {
  background: #E8F5E9;
  color: #2E7D32;
}

.status-badge.cancelled {
  background: #FFEBEE;
  color: #C62828;
}

.group-deal-info {
  margin-bottom: var(--md-spacing-md);
}

.group-deal-info h3 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-sm);
  font-weight: 500;
}

.deal-dates {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-xs);
}

.date-item {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-xs);
  font-size: var(--md-label-size);
  font-weight: 400;
  color: var(--md-on-surface-variant);
}

.date-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.order-items {
  margin-bottom: var(--md-spacing-md);
}

.order-item {
  display: flex;
  gap: var(--md-spacing-md);
  padding: var(--md-spacing-sm) 0;
  border-bottom: 1px solid var(--md-outline-variant);
}

.order-item:last-child {
  border-bottom: none;
}

.item-image {
  width: 60px;
  height: 60px;
  border-radius: var(--md-radius-md);
  overflow: hidden;
  flex-shrink: 0;
  background: var(--md-surface-variant);
}

.item-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.item-image.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--md-on-surface-variant);
  opacity: 0.5;
}

.item-image.placeholder svg {
  width: 32px;
  height: 32px;
}

.item-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.item-details h4 {
  font-size: var(--md-body-size);
  color: var(--md-on-surface);
  font-weight: 500;
  margin-bottom: var(--md-spacing-xs);
}

.item-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--md-label-size);
  font-weight: 400;
  color: var(--md-on-surface-variant);
}

.item-price {
  font-size: var(--md-label-size);
  font-weight: 600;
  color: var(--md-primary);
}

.order-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--md-spacing-sm);
  border-top: 1px solid var(--md-outline-variant);
  gap: var(--md-spacing-md);
  flex-wrap: wrap;
}

.footer-right {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
  flex-wrap: wrap;
}

.payment-status {
  display: flex;
  align-items: center;
  height: 100%;
}

.order-actions {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  height: 100%;
}

.cancel-btn {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-xs);
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: none;
  background: #FFEBEE;
  color: #C62828;
  border-radius: var(--md-radius-md);
  font-size: var(--md-label-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  line-height: 1.5;
  height: 36px;
}

.cancel-btn svg {
  width: 16px;
  height: 16px;
}

.cancel-btn:hover {
  background: #C62828;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(198, 40, 40, 0.3);
}

.cancel-btn:active {
  transform: translateY(0);
}

.deadline-badge {
  padding: 0.25rem 0.75rem;
  border-radius: var(--md-radius-xl);
  font-size: var(--md-label-size);
  font-weight: 500;
  background: #F5F5F5;
  color: #757575;
  white-space: nowrap;
  line-height: 1.5;
  display: inline-flex;
  align-items: center;
  height: 36px;
}

.order-total {
  display: flex;
  align-items: baseline;
  gap: var(--md-spacing-xs);
}

.total-label {
  font-size: var(--md-body-size);
  font-weight: 400;
  color: var(--md-on-surface-variant);
}

.total-amount {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--md-primary);
}

.payment-badge {
  padding: 0.25rem 0.75rem;
  border-radius: var(--md-radius-xl);
  font-size: var(--md-label-size);
  font-weight: 500;
  line-height: 1.5;
  display: inline-flex;
  align-items: center;
  height: 36px;
}

.payment-badge.pending {
  background: #FFF3E0;
  color: #E65100;
}

.payment-badge.paid {
  background: #E8F5E9;
  color: #2E7D32;
}

.payment-badge.failed {
  background: #FFEBEE;
  color: #C62828;
}

.payment-badge.refunded {
  background: #F3E5F5;
  color: #7B1FA2;
}

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
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-content {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-lg);
  border-bottom: 1px solid var(--md-outline-variant);
}

.modal-header h2 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  font-weight: 500;
  margin: 0;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: var(--md-on-surface-variant);
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
  background: var(--md-surface-variant);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--md-spacing-lg);
}

.error-message {
  padding: var(--md-spacing-md);
  background: #FFEBEE;
  color: #C62828;
  border-radius: var(--md-radius-md);
  font-size: var(--md-label-size);
  margin-top: var(--md-spacing-md);
}

.modal-footer {
  display: flex;
  gap: var(--md-spacing-md);
  padding: var(--md-spacing-lg);
  border-top: 1px solid var(--md-outline-variant);
}


/* Cancel Modal Styles */
.cancel-modal {
  max-width: 450px;
}

.cancel-warning {
  display: flex;
  gap: var(--md-spacing-md);
  padding: var(--md-spacing-lg);
  background: #FFF3E0;
  border-radius: var(--md-radius-md);
  border-left: 4px solid #FF6F00;
}

.cancel-warning svg {
  width: 48px;
  height: 48px;
  color: #FF6F00;
  flex-shrink: 0;
}

.warning-content h3 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-sm);
  font-weight: 600;
}

.warning-content p {
  font-size: var(--md-body-size);
  color: var(--md-on-surface-variant);
  margin-bottom: var(--md-spacing-xs);
}

.warning-text {
  color: #E65100 !important;
  font-weight: 500;
}

.cancel-btn-secondary {
  flex: 1;
  padding: var(--md-spacing-md);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid var(--md-outline);
  background: transparent;
  color: var(--md-on-surface);
}

.cancel-btn-secondary:hover {
  background: var(--md-surface-variant);
}

.confirm-cancel-btn {
  flex: 1;
  padding: var(--md-spacing-md);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  background: #C62828;
  color: white;
}

.confirm-cancel-btn:hover:not(:disabled) {
  background: #B71C1C;
  box-shadow: 0 2px 8px rgba(198, 40, 40, 0.3);
}

.confirm-cancel-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* QR Code Styles */
.qr-code-section {
  margin: var(--md-spacing-md) 0;
  padding: var(--md-spacing-md);
  background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
  border-radius: var(--md-radius-lg);
  border: 2px solid #4CAF50;
}

.qr-code-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--md-spacing-sm);
}

.qr-code-title {
  font-size: var(--md-title-size);
  color: #2E7D32;
  font-weight: 600;
  margin: 0;
  text-align: center;
}

.qr-code-wrapper {
  background: white;
  padding: var(--md-spacing-md);
  border-radius: var(--md-radius-md);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.qr-code-canvas {
  display: block;
  max-width: 100%;
  height: auto;
}

.pickup-code-text {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1B5E20;
  letter-spacing: 0.2em;
  font-family: 'Courier New', monospace;
  margin-top: var(--md-spacing-xs);
}

@media (max-width: 480px) {
  .modal-content {
    max-height: 95vh;
  }

  .order-actions {
    flex-wrap: wrap;
  }
  
  .cancel-modal {
    max-width: 95vw;
  }
}
</style>

