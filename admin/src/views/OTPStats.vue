<template>
  <div class="otp-stats-page">
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Summary Cards -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">📊</div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_attempts }}</div>
            <div class="stat-label">总尝试次数</div>
          </div>
        </div>
        <div class="stat-card success">
          <div class="stat-icon">✅</div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.successful_sends }}</div>
            <div class="stat-label">成功发送</div>
          </div>
        </div>
        <div class="stat-card error">
          <div class="stat-icon">❌</div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.failed_sends }}</div>
            <div class="stat-label">发送失败</div>
          </div>
        </div>
        <div class="stat-card primary">
          <div class="stat-icon">💰</div>
          <div class="stat-info">
            <div class="stat-value">${{ stats.total_cost_usd.toFixed(4) }}</div>
            <div class="stat-label">总成本 ({{ stats.period_days }}天)</div>
            <div class="stat-sublabel">预计月成本: ${{ stats.estimated_monthly_cost.toFixed(4) }}</div>
          </div>
        </div>
      </div>

      <!-- Verification Stats -->
      <div class="stats-section">
        <h2>验证统计</h2>
        <div class="verification-stats">
          <div class="verification-item">
            <span class="label">成功验证:</span>
            <span class="value success">{{ stats.successful_verifications }}</span>
          </div>
          <div class="verification-item">
            <span class="label">验证失败:</span>
            <span class="value error">{{ stats.failed_verifications }}</span>
          </div>
        </div>
      </div>

      <!-- Daily Chart -->
      <div class="stats-section">
        <h2>每日使用情况</h2>
        <div class="chart-container">
          <div v-for="day in dailyChart" :key="day.date" class="chart-bar">
            <div class="chart-bar-fill" :style="{ height: `${(day.sends / maxSends) * 100}%` }"></div>
            <div class="chart-label">{{ formatDateShort(day.date) }}</div>
            <div class="chart-value">{{ day.sends }}</div>
          </div>
        </div>
      </div>

      <!-- Recent Attempts -->
      <div class="stats-section">
        <h2>最近尝试记录</h2>
        <div class="attempts-table">
          <table>
            <thead>
              <tr>
                <th>时间</th>
                <th>手机号</th>
                <th>操作</th>
                <th>状态</th>
                <th>成本</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="attempt in recentAttempts" :key="attempt.id" :class="attempt.status">
                <td>{{ formatDateTime(attempt.created_at) }}</td>
                <td>{{ attempt.phone }}</td>
                <td>
                  <span class="badge" :class="attempt.action_type">
                    {{ attempt.action_type === 'send' ? '发送' : '验证' }}
                  </span>
                </td>
                <td>
                  <span class="status-badge" :class="attempt.status">
                    {{ attempt.status === 'success' ? '成功' : '失败' }}
                  </span>
                </td>
                <td>${{ attempt.estimated_cost ? parseFloat(attempt.estimated_cost).toFixed(4) : '0.0000' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'

export default {
  name: 'OTPStats',
  data() {
    return {
      loading: true,
      error: null,
      stats: {
        total_attempts: 0,
        successful_sends: 0,
        failed_sends: 0,
        successful_verifications: 0,
        failed_verifications: 0,
        total_cost_usd: 0,
        estimated_monthly_cost: 0,
        period_days: 30
      },
      dailyChart: [],
      recentAttempts: []
    }
  },
  computed: {
    maxSends() {
      if (this.dailyChart.length === 0) return 1
      return Math.max(...this.dailyChart.map(d => d.sends), 1)
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
        const response = await apiClient.get('/admin/otp-stats', {
          params: { days: 30 }
        })
        this.stats = response.data.summary
        this.dailyChart = response.data.daily_chart || []
        this.recentAttempts = response.data.recent_attempts || []
      } catch (error) {
        this.error = error.response?.data?.message || error.message || '加载统计数据失败'
        console.error('Failed to load OTP stats:', error)
      } finally {
        this.loading = false
      }
    },
    formatDateShort(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      return `${date.getMonth() + 1}/${date.getDate()}`
    },
    formatDateTime(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
  }
}
</script>

<style scoped>
.otp-stats-page {
  padding: var(--md-spacing-lg);
}

.loading,
.error {
  text-align: center;
  padding: var(--md-spacing-xl);
  font-size: var(--md-body-size);
}

.error {
  color: #ff4444;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--md-spacing-md);
  margin-bottom: var(--md-spacing-xl);
}

.stat-card {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-2);
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
}

.stat-card.success {
  border-left: 4px solid #4CAF50;
}

.stat-card.error {
  border-left: 4px solid #ff4444;
}

.stat-card.primary {
  border-left: 4px solid var(--md-primary);
}

.stat-icon {
  font-size: 2.5rem;
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: var(--md-headline-size);
  font-weight: 600;
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-xs);
}

.stat-label {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.stat-sublabel {
  font-size: 0.75rem;
  color: var(--md-on-surface-variant);
  margin-top: var(--md-spacing-xs);
}

.stats-section {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-2);
  margin-bottom: var(--md-spacing-lg);
}

.stats-section h2 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-md);
  font-weight: 500;
}

.verification-stats {
  display: flex;
  gap: var(--md-spacing-xl);
}

.verification-item {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
}

.verification-item .label {
  font-size: var(--md-body-size);
  color: var(--md-on-surface-variant);
}

.verification-item .value {
  font-size: var(--md-headline-size);
  font-weight: 600;
}

.verification-item .value.success {
  color: #4CAF50;
}

.verification-item .value.error {
  color: #ff4444;
}

.chart-container {
  display: flex;
  align-items: flex-end;
  gap: var(--md-spacing-sm);
  height: 200px;
  padding: var(--md-spacing-md) 0;
}

.chart-bar {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--md-spacing-xs);
  position: relative;
}

.chart-bar-fill {
  width: 100%;
  background: var(--md-primary);
  border-radius: var(--md-radius-sm) var(--md-radius-sm) 0 0;
  min-height: 4px;
  transition: height 0.3s ease;
}

.chart-label {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  writing-mode: horizontal-tb;
  text-align: center;
}

.chart-value {
  font-size: var(--md-label-size);
  font-weight: 500;
  color: var(--md-on-surface);
}

.attempts-table {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--md-surface-variant);
}

th {
  padding: var(--md-spacing-md);
  text-align: left;
  font-size: var(--md-label-size);
  font-weight: 500;
  color: var(--md-on-surface);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

td {
  padding: var(--md-spacing-md);
  border-bottom: 1px solid var(--md-surface-variant);
  font-size: var(--md-body-size);
  color: var(--md-on-surface);
}

tbody tr:hover {
  background: var(--md-surface-variant);
}

.badge {
  display: inline-block;
  padding: var(--md-spacing-xs) var(--md-spacing-sm);
  border-radius: var(--md-radius-sm);
  font-size: var(--md-label-size);
  font-weight: 500;
}

.badge.send {
  background: rgba(33, 150, 243, 0.1);
  color: #2196F3;
}

.badge.verify {
  background: rgba(76, 175, 80, 0.1);
  color: #4CAF50;
}

.status-badge {
  display: inline-block;
  padding: var(--md-spacing-xs) var(--md-spacing-sm);
  border-radius: var(--md-radius-sm);
  font-size: var(--md-label-size);
  font-weight: 500;
}

.status-badge.success {
  background: rgba(76, 175, 80, 0.1);
  color: #4CAF50;
}

.status-badge.failed {
  background: rgba(244, 67, 54, 0.1);
  color: #f44336;
}
</style>

