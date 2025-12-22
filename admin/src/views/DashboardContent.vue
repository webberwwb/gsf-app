<template>
  <div class="dashboard-content">
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
          </svg>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.products || 0 }}</div>
          <div class="stat-label">商品总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.orders || 0 }}</div>
          <div class="stat-label">订单总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.users || 0 }}</div>
          <div class="stat-label">用户总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div class="stat-info">
          <div class="stat-value">${{ stats.revenue || '0.00' }}</div>
          <div class="stat-label">总收入</div>
        </div>
      </div>
    </div>

    <div class="recent-section">
      <h2>最近订单</h2>
      <div v-if="recentOrders.length === 0" class="empty-state">
        <p>暂无最近订单</p>
      </div>
      <div v-else class="recent-orders">
        <div v-for="order in recentOrders" :key="order.id" class="order-item">
          <div class="order-info">
            <div class="order-id">订单 #{{ order.order_number || order.id }}</div>
            <div class="order-user">{{ order.user_name }}</div>
            <div class="order-status">{{ order.payment_status === 'paid' ? '已支付' : '待支付' }}</div>
          </div>
          <div class="order-amount">${{ order.total_amount || '0.00' }}</div>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'

export default {
  name: 'DashboardContent',
  data() {
    return {
      loading: true,
      error: null,
      stats: {
        products: 0,
        orders: 0,
        users: 0,
        revenue: '0.00'
      },
      recentOrders: []
    }
  },
  mounted() {
    this.loadStats()
  },
  methods: {
    async loadStats() {
      this.loading = true
      this.error = null
      try {
        const response = await apiClient.get('/admin/stats')
        this.stats = response.data.stats || {
          products: 0,
          orders: 0,
          users: 0,
          revenue: '0.00'
        }
        this.recentOrders = response.data.recent_orders || []
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || 'Failed to load dashboard statistics'
        console.error('Failed to load dashboard stats:', error)
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.dashboard-content {
  max-width: 1200px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--md-spacing-lg);
  margin-bottom: var(--md-spacing-xl);
}

.stat-card {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.stat-card:hover {
  box-shadow: var(--md-elevation-2);
  transform: translateY(-2px);
}

.stat-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 140, 0, 0.1);
  border-radius: var(--md-radius-lg);
  color: var(--md-primary);
}

.stat-icon svg {
  width: 32px;
  height: 32px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 2rem;
  font-weight: 600;
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-xs);
}

.stat-label {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.recent-section {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
}

.recent-section h2 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-lg);
  font-weight: 500;
}

.empty-state {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.recent-orders {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.order-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-md);
  background: var(--md-surface-variant);
  border-radius: var(--md-radius-md);
}

.order-info {
  flex: 1;
}

.order-id {
  font-weight: 500;
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-xs);
}

.order-user {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin-bottom: var(--md-spacing-xs);
}

.order-status {
  font-size: var(--md-label-size);
  color: var(--md-primary);
  font-weight: 500;
}

.order-amount {
  font-weight: 600;
  color: var(--md-primary);
  font-size: 1.1rem;
}
</style>

