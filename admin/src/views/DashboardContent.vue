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
  background: #FFFFFF;
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
  transition: var(--transition-normal);
  border: none;
  position: relative;
  overflow: hidden;
}

.stat-card:hover {
  background: #FFFFFF;
  box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.16), 0px 2px 4px rgba(0, 0, 0, 0.23);
  transform: translateY(-2px);
}

.stat-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.04);
  border-radius: var(--md-radius-lg);
  color: var(--md-primary);
  transition: var(--transition-normal);
  position: relative;
  z-index: 1;
}

.stat-card:hover .stat-icon {
  transform: scale(1.05);
  background: rgba(0, 0, 0, 0.06);
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
  background: #FFFFFF;
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  border: none;
  animation: fadeIn 0.6s ease-out;
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
  background: #FFFFFF;
  border-radius: var(--md-radius-md);
  border: 1px solid rgba(0, 0, 0, 0.08);
  transition: var(--transition-fast);
}

.order-item:hover {
  background: #FFFFFF;
  transform: translateX(4px);
  box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.16);
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

/* Mobile Responsive Styles */
@media (max-width: 767px) {
  .stats-grid {
    grid-template-columns: 1fr;
    gap: var(--md-spacing-md);
  }

  .stat-card {
    padding: var(--md-spacing-md);
  }

  .stat-icon {
    width: 60px;
    height: 60px;
  }

  .stat-icon svg {
    width: 24px;
    height: 24px;
  }

  .stat-value {
    font-size: 1.5rem;
  }

  .recent-section {
    padding: var(--md-spacing-md);
  }

  .order-item {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--md-spacing-sm);
  }

  .order-amount {
    align-self: flex-end;
    font-size: var(--md-body-size);
  }
}

@media (max-width: 480px) {
  .stat-card {
    flex-direction: column;
    text-align: center;
  }

  .stat-icon {
    width: 50px;
    height: 50px;
  }

  .stat-value {
    font-size: 1.25rem;
  }
}
</style>

