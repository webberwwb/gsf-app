<template>
  <div class="group-deals-page">
    <div v-if="loading" class="loading-container">
      <div class="loading">加载中...</div>
    </div>
    <div v-else-if="error" class="error-container">
      <div class="error">{{ error }}</div>
    </div>
    <div v-else-if="redirectDealId" class="redirecting">
      <!-- Will redirect via mounted hook -->
    </div>
    <div v-else class="coming-soon-container">
      <div class="icon-wrapper">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z" />
        </svg>
      </div>
      <h2>即将上线</h2>
      <p class="description">
        新的团购活动正在筹备中，敬请期待！
      </p>
      <p class="sub-description">
        我们会第一时间通知您最新的团购信息
      </p>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'
import { parseDateEST, getNowEST } from '../utils/date'

export default {
  name: 'GroupDeals',
  data() {
    return {
      loading: true,
      error: null,
      redirectDealId: null
    }
  },
  async mounted() {
    await this.loadDeals()
  },
  methods: {
    async loadDeals() {
      this.loading = true
      this.error = null
      
      try {
        const response = await apiClient.get('/group-deals')
        const deals = response.data.deals || []
        
        if (deals.length === 0) {
          // No deals at all
          this.loading = false
          return
        }
        
        const now = getNowEST()
        
        // Find active deal (status = 'active' and order_end_date > now)
        const activeDeal = deals.find(deal => {
          const endDate = parseDateEST(deal.order_end_date)
          return deal.status === 'active' && endDate && endDate > now
        })
        
        if (activeDeal) {
          // Redirect to active deal
          this.redirectDealId = activeDeal.id
          this.$router.replace(`/group-deals/${activeDeal.id}`)
          return
        }
        
        // Find next upcoming deal (status = 'upcoming' and order_start_date > now)
        const upcomingDeals = deals
          .filter(deal => {
            const startDate = parseDateEST(deal.order_start_date)
            return deal.status === 'upcoming' && startDate && startDate > now
          })
          .sort((a, b) => {
            const dateA = parseDateEST(a.order_start_date)
            const dateB = parseDateEST(b.order_start_date)
            if (!dateA || !dateB) return 0
            return dateA - dateB
          })
        
        if (upcomingDeals.length > 0) {
          // Redirect to next upcoming deal
          this.redirectDealId = upcomingDeals[0].id
          this.$router.replace(`/group-deals/${upcomingDeals[0].id}`)
          return
        }
        
        // No active or upcoming deals - show placeholder
        this.loading = false
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || '加载团购信息失败'
        console.error('Failed to load deals:', error)
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.group-deals-page {
  min-height: 100vh;
  background: var(--md-background);
  padding-bottom: 80px; /* Space for bottom nav */
}

.loading-container,
.error-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 200px);
  padding: var(--md-spacing-xl);
}

.loading {
  font-size: var(--md-body-size);
  color: var(--md-on-surface-variant);
}

.error {
  font-size: var(--md-body-size);
  color: #C62828;
  text-align: center;
}

.coming-soon-container {
  text-align: center;
  max-width: 500px;
  margin: 0 auto;
  padding: var(--md-spacing-xl);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 200px);
}

.icon-wrapper {
  width: 120px;
  height: 120px;
  margin-bottom: var(--md-spacing-xl);
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(255, 140, 0, 0.1) 0%, rgba(255, 215, 0, 0.1) 100%);
  border-radius: 50%;
  color: var(--md-primary);
}

.icon-wrapper svg {
  width: 64px;
  height: 64px;
}

.coming-soon-container h2 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-lg);
  font-weight: 500;
}

.description {
  font-size: var(--md-body-size);
  color: var(--md-on-surface-variant);
  line-height: 1.8;
  margin-bottom: var(--md-spacing-md);
}

.sub-description {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  opacity: 0.8;
  font-style: italic;
}

@media (max-width: 480px) {
  .coming-soon-container {
    padding: var(--md-spacing-lg);
  }
  
  .icon-wrapper {
    width: 100px;
    height: 100px;
  }
  
  .icon-wrapper svg {
    width: 48px;
    height: 48px;
  }
}
</style>



