<template>
  <div class="deals-list-page">
    <header class="page-header">
      <div class="header-center">
        <h1>团购下单</h1>
      </div>
    </header>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="deals.length === 0" class="no-deal-placeholder">
      <div class="no-deal-icon">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z" />
        </svg>
      </div>
      <p class="no-deal-title">暂无团购</p>
      <p class="no-deal-sub">请查看产品介绍，耐心等待下次团购。</p>
    </div>
    <div v-else class="deals-content">
      <button
        v-for="deal in deals"
        :key="deal.id"
        type="button"
        class="deal-card"
        :class="{ 'deal-card--draft': isAdmin && deal.status === 'draft' }"
        @click="goToDeal(deal.id)"
      >
        <div class="deal-card-header">
          <h2 class="deal-card-title">{{ deal.title }}</h2>
          <span :class="['deal-badge', deal.status]">
            {{ getStatusLabel(deal.status) }}
          </span>
        </div>
        <span v-if="isAdmin && deal.status === 'draft'" class="admin-draft-tag">
          仅管理员可见
        </span>
        <p v-if="deal.description" class="deal-card-description">{{ deal.description }}</p>
        <div class="deal-card-dates">
          <div class="date-row">
            <span class="date-label">开团</span>
            <span class="date-value">{{ formatDateTime(deal.order_start_date) }}</span>
          </div>
          <div class="date-row">
            <span class="date-label">截单</span>
            <span class="date-value">{{ formatDateTime(deal.order_end_date) }}</span>
          </div>
          <div class="date-row">
            <span class="date-label">取货</span>
            <span class="date-value">{{ formatPickupDate(deal.pickup_date) }}</span>
          </div>
        </div>
        <div class="deal-card-action">
          <span>{{ deal.status === 'active' ? '立即下单' : '查看详情' }}</span>
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </button>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'
import { useAuthStore } from '../stores/auth'
import { formatDateTimeEST_CN, formatPickupDateTime_CN } from '../utils/date'
import { getGroupDealStatusLabel } from '@shared/status-enums.js'

export default {
  name: 'GroupDealsList',
  data() {
    return {
      loading: true,
      error: null,
      deals: []
    }
  },
  setup() {
    const authStore = useAuthStore()
    return { authStore }
  },
  computed: {
    isAdmin() {
      return this.authStore.isAdmin
    }
  },
  async mounted() {
    if (!this.authStore.token) {
      this.authStore.loadFromStorage()
    }
    await this.loadDeals()
  },
  methods: {
    async loadDeals() {
      this.loading = true
      this.error = null
      try {
        const response = await apiClient.get('/group-deals/open')
        this.deals = response.data.deals || []
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || '加载团购列表失败'
        console.error('Failed to load deals:', error)
      } finally {
        this.loading = false
      }
    },
    goToDeal(dealId) {
      this.$router.push(`/group-deals/${dealId}`)
    },
    formatDateTime(dateString) {
      return formatDateTimeEST_CN(dateString)
    },
    formatPickupDate(dateString) {
      return formatPickupDateTime_CN(dateString)
    },
    getStatusLabel(status) {
      return getGroupDealStatusLabel(status)
    }
  }
}
</script>

<style scoped>
.deals-list-page {
  min-height: 100vh;
  background: var(--md-background);
  padding-bottom: calc(80px + env(safe-area-inset-bottom));
}

.page-header {
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  padding: var(--md-spacing-lg);
  padding-top: calc(var(--md-spacing-lg) + env(safe-area-inset-top));
  box-shadow: var(--md-elevation-2);
  position: sticky;
  top: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-center {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--md-spacing-sm);
  flex-wrap: wrap;
}

.page-header h1 {
  font-size: var(--md-headline-size);
  color: white;
  font-weight: 500;
  text-align: center;
  letter-spacing: -0.5px;
  margin: 0;
}

.loading, .error {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.error {
  color: #C62828;
}

.no-deal-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: var(--md-spacing-xl);
  min-height: 45vh;
  color: var(--md-on-surface-variant);
}

.no-deal-icon {
  width: 72px;
  height: 72px;
  opacity: 0.35;
  margin-bottom: var(--md-spacing-md);
}

.no-deal-icon svg {
  width: 100%;
  height: 100%;
}

.no-deal-title {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  font-weight: 500;
  margin: 0 0 var(--md-spacing-xs);
}

.no-deal-sub {
  font-size: var(--md-body-size);
  margin: 0;
  opacity: 0.85;
}

.deals-content {
  padding: var(--md-spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.deal-card {
  width: 100%;
  text-align: left;
  background: var(--md-surface);
  border: none;
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
  cursor: pointer;
  transition: box-shadow 0.2s cubic-bezier(0.4, 0, 0.2, 1), transform 0.15s ease;
}

.deal-card:hover {
  box-shadow: var(--md-elevation-2);
}

.deal-card:active {
  transform: scale(0.99);
}

.deal-card--draft {
  border: 2px dashed #9C27B0;
  background: linear-gradient(135deg, rgba(156, 39, 176, 0.03) 0%, rgba(103, 58, 183, 0.03) 100%);
}

.deal-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--md-spacing-sm);
  margin-bottom: var(--md-spacing-sm);
}

.deal-card-title {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  font-weight: 500;
  margin: 0;
  flex: 1;
}

.deal-badge {
  padding: 0.375rem 0.875rem;
  border-radius: var(--md-radius-xl);
  font-size: var(--md-label-size);
  font-weight: 500;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  white-space: nowrap;
  flex-shrink: 0;
}

.deal-badge.active {
  background: #FF4444;
  color: white;
}

.deal-badge.upcoming {
  background: #E8F5E9;
  color: #2E7D32;
}

.deal-badge.closed {
  background: #FFF3E0;
  color: #F57C00;
}

.deal-badge.preparing {
  background: #E3F2FD;
  color: #1565C0;
}

.deal-badge.ready_for_pickup {
  background: #E8F5E9;
  color: #2E7D32;
}

.deal-badge.draft {
  background: #E0E0E0;
  color: #616161;
}

.admin-draft-tag {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  margin-bottom: var(--md-spacing-sm);
  background: rgba(156, 39, 176, 0.1);
  color: #9C27B0;
  border-radius: var(--md-radius-xl);
  font-size: 0.75rem;
  font-weight: 600;
}

.deal-card-description {
  font-size: var(--md-body-size);
  color: var(--md-on-surface-variant);
  margin: 0 0 var(--md-spacing-md);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.deal-card-dates {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-xs);
  margin-bottom: var(--md-spacing-md);
}

.date-row {
  display: flex;
  align-items: baseline;
  gap: var(--md-spacing-sm);
  font-size: var(--md-body-size);
}

.date-label {
  color: var(--md-on-surface-variant);
  min-width: 2.5rem;
  flex-shrink: 0;
}

.date-value {
  color: var(--md-on-surface);
}

.deal-card-action {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.25rem;
  color: var(--md-primary);
  font-size: var(--md-label-size);
  font-weight: 500;
}

.deal-card-action svg {
  width: 18px;
  height: 18px;
}
</style>
