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
        <div v-for="order in filteredOrders" :key="order.id" class="order-card">
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

          <div class="order-footer">
            <div class="order-total">
              <span class="total-label">订单总额:</span>
              <span class="total-amount">${{ order.total.toFixed(2) }}</span>
            </div>
            <div class="payment-status">
              <span :class="['payment-badge', getPaymentStatusClass(order.payment_status)]">
                {{ getPaymentStatusLabel(order.payment_status) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'

export default {
  name: 'Orders',
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
      ]
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
  methods: {
    async loadOrders() {
      this.loading = true
      this.error = null
      try {
        const response = await apiClient.get('/orders')
        this.orders = response.data.orders || []
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
      if (!dateString) return ''
      const date = new Date(dateString)
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    },
    getStatusLabel(status) {
      const labels = {
        'pending': '待处理',
        'confirmed': '已确认',
        'processing': '处理中',
        'completed': '已完成',
        'cancelled': '已取消'
      }
      return labels[status] || status
    },
    getStatusClass(status) {
      const classes = {
        'pending': 'pending',
        'confirmed': 'confirmed',
        'processing': 'processing',
        'completed': 'completed',
        'cancelled': 'cancelled'
      }
      return classes[status] || 'pending'
    },
    getPaymentStatusLabel(status) {
      const labels = {
        'pending': '待支付',
        'paid': '已支付',
        'failed': '支付失败',
        'refunded': '已退款'
      }
      return labels[status] || status
    },
    getPaymentStatusClass(status) {
      const classes = {
        'pending': 'pending',
        'paid': 'paid',
        'failed': 'failed',
        'refunded': 'refunded'
      }
      return classes[status] || 'pending'
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
  padding-top: calc(var(--md-spacing-lg) + env(safe-area-inset-top));
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
}

.order-card:hover {
  box-shadow: var(--md-elevation-2);
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
  color: var(--md-on-surface-variant);
}

.item-price {
  font-weight: 600;
  color: var(--md-primary);
}

.order-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--md-spacing-sm);
  border-top: 1px solid var(--md-outline-variant);
}

.order-total {
  display: flex;
  align-items: baseline;
  gap: var(--md-spacing-xs);
}

.total-label {
  font-size: var(--md-body-size);
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
</style>

