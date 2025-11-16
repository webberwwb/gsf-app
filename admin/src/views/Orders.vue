<template>
  <div class="orders-page">
    <div class="page-header-actions">
      <div class="filter-group">
        <select v-model="statusFilter" class="filter-select">
          <option value="">全部状态</option>
          <option value="pending">待处理</option>
          <option value="confirmed">已确认</option>
          <option value="shipped">已发货</option>
          <option value="delivered">已送达</option>
          <option value="cancelled">已取消</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="orders.length === 0" class="empty-state">
      <p>暂无订单</p>
    </div>
    <div v-else class="orders-list">
      <div v-for="order in filteredOrders" :key="order.id" class="order-card">
        <div class="order-header">
          <div class="order-id">订单 #{{ order.id }}</div>
          <div class="order-status" :class="order.status">{{ getStatusText(order.status) }}</div>
        </div>
        <div class="order-info">
          <div class="info-item">
            <span class="label">用户:</span>
            <span class="value">{{ order.user?.nickname || order.user?.phone || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <span class="label">下单时间:</span>
            <span class="value">{{ formatDate(order.created_at) }}</span>
          </div>
          <div class="info-item">
            <span class="label">总金额:</span>
            <span class="value price">${{ order.total_amount || '0.00' }}</span>
          </div>
        </div>
        <div class="order-actions">
          <button @click="viewOrder(order)" class="view-btn">查看详情</button>
          <button v-if="order.status === 'pending'" @click="updateStatus(order.id, 'confirmed')" class="confirm-btn">
            确认订单
          </button>
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
      statusFilter: ''
    }
  },
  computed: {
    filteredOrders() {
      if (!this.statusFilter) {
        return this.orders
      }
      return this.orders.filter(order => order.status === this.statusFilter)
    }
  },
  mounted() {
    this.fetchOrders()
  },
  methods: {
    async fetchOrders() {
      try {
        this.loading = true
        // TODO: Replace with actual orders API endpoint
        // const response = await apiClient.get('/orders')
        // this.orders = response.data
        this.orders = []
      } catch (error) {
        this.error = error.message || 'Failed to load orders'
        console.error('Failed to fetch orders:', error)
      } finally {
        this.loading = false
      }
    },
    viewOrder(order) {
      // TODO: Implement order detail view
      alert(`View order: ${order.id}`)
    },
    async updateStatus(orderId, status) {
      // TODO: Implement status update API call
      alert(`Update order ${orderId} to ${status}`)
    },
    getStatusText(status) {
      const statusMap = {
        pending: '待处理',
        confirmed: '已确认',
        shipped: '已发货',
        delivered: '已送达',
        cancelled: '已取消'
      }
      return statusMap[status] || status
    },
    formatDate(dateString) {
      if (!dateString) return 'N/A'
      return new Date(dateString).toLocaleString('zh-CN')
    }
  }
}
</script>

<style scoped>
.orders-page {
  max-width: 1200px;
}

.page-header-actions {
  margin-bottom: var(--md-spacing-lg);
  display: flex;
  justify-content: flex-end;
}

.filter-group {
  display: flex;
  gap: var(--md-spacing-md);
}

.filter-select {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  background: var(--md-surface);
  color: var(--md-on-surface);
  cursor: pointer;
}

.loading, .error, .empty-state {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.orders-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.order-card {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.order-card:hover {
  box-shadow: var(--md-elevation-2);
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--md-spacing-md);
  padding-bottom: var(--md-spacing-md);
  border-bottom: 1px solid var(--md-surface-variant);
}

.order-id {
  font-size: var(--md-title-size);
  font-weight: 600;
  color: var(--md-on-surface);
}

.order-status {
  padding: var(--md-spacing-xs) var(--md-spacing-md);
  border-radius: var(--md-radius-xl);
  font-size: var(--md-label-size);
  font-weight: 500;
  text-transform: uppercase;
}

.order-status.pending {
  background: #FFF3E0;
  color: #E65100;
}

.order-status.confirmed {
  background: #E3F2FD;
  color: #1565C0;
}

.order-status.shipped {
  background: #E8F5E9;
  color: #2E7D32;
}

.order-status.delivered {
  background: #E8F5E9;
  color: #1B5E20;
}

.order-status.cancelled {
  background: #FFEBEE;
  color: #C62828;
}

.order-info {
  margin-bottom: var(--md-spacing-md);
}

.info-item {
  display: flex;
  gap: var(--md-spacing-md);
  margin-bottom: var(--md-spacing-sm);
}

.label {
  font-weight: 500;
  color: var(--md-on-surface-variant);
  min-width: 80px;
}

.value {
  color: var(--md-on-surface);
}

.value.price {
  color: var(--md-primary);
  font-weight: 600;
  font-size: 1.1rem;
}

.order-actions {
  display: flex;
  gap: var(--md-spacing-sm);
}

.view-btn, .confirm-btn {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-label-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.view-btn {
  background: var(--md-surface-variant);
  color: var(--md-on-surface);
}

.view-btn:hover {
  background: var(--md-outline);
  color: white;
}

.confirm-btn {
  background: var(--md-primary);
  color: white;
}

.confirm-btn:hover {
  background: #FF7F00;
}
</style>

