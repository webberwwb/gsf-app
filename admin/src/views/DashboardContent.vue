<template>
  <div class="dashboard-content">
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📦</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.products || 0 }}</div>
          <div class="stat-label">商品总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🛒</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.orders || 0 }}</div>
          <div class="stat-label">订单总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">👥</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.users || 0 }}</div>
          <div class="stat-label">用户总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">💰</div>
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
          <div class="order-id">订单 #{{ order.id }}</div>
          <div class="order-amount">${{ order.total_amount || '0.00' }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DashboardContent',
  data() {
    return {
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
      // TODO: Load actual stats from API
      // For now, just show placeholder
      this.stats = {
        products: 0,
        orders: 0,
        users: 0,
        revenue: '0.00'
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
  font-size: 3rem;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 140, 0, 0.1);
  border-radius: var(--md-radius-lg);
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

.order-id {
  font-weight: 500;
  color: var(--md-on-surface);
}

.order-amount {
  font-weight: 600;
  color: var(--md-primary);
  font-size: 1.1rem;
}
</style>

