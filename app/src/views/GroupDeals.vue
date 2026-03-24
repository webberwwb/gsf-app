<template>
  <div class="group-deals-page" @touchstart="handleTouchStart" @touchmove="handleTouchMove" @touchend="handleTouchEnd">
    <header class="page-header">
      <h1>团购下单</h1>
    </header>

    <div v-if="groupDealsStore.loading" class="loading">加载中...</div>
    <div v-else-if="groupDealsStore.error" class="error">{{ groupDealsStore.error }}</div>
    <div v-else-if="groupDealsStore.deals.length === 0" class="empty-state">
      <div class="empty-icon">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z" />
        </svg>
      </div>
      <h2>即将上线</h2>
      <p>新的团购活动正在筹备中，敬请期待！</p>
    </div>
    <div v-else class="deals-container">
      <!-- Current Deals Section -->
      <div v-if="groupDealsStore.currentDeals.length > 0" class="deals-section">
        <h2 class="section-title current">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="title-icon">
            <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z" />
          </svg>
          本期团购
        </h2>
        <div 
          v-for="deal in groupDealsStore.currentDeals" 
          :key="deal.id" 
          class="deal-card current-deal"
          :class="getDealStatusClass(deal.status)"
          @click="viewDeal(deal)">
          <div class="deal-header">
            <div class="deal-info">
              <h3>{{ deal.title }}</h3>
              <span v-if="deal.description" class="deal-description">{{ deal.description }}</span>
            </div>
            <span :class="['status-badge', getDealStatusClass(deal.status)]">
              {{ getDealStatusLabel(deal.status) }}
            </span>
          </div>

          <div class="deal-dates">
            <span v-if="deal.order_end_date" class="date-item">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="date-icon">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              截单时间: {{ formatDateTime(deal.order_end_date) }}
            </span>
            <span v-if="deal.pickup_date" class="date-item">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="date-icon">
                <path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
              取货时间: {{ formatPickupDate(deal.pickup_date) }}
            </span>
          </div>

          <div v-if="deal.products && deal.products.length > 0" class="deal-products">
            <div v-for="product in deal.products.slice(0, 3)" :key="product.id" class="product-item">
              <div v-if="product.image" class="product-image">
                <img :src="product.image" :alt="product.name" />
              </div>
              <div v-else class="product-image placeholder">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                </svg>
              </div>
              <div class="product-details">
                <h4>{{ product.name }}</h4>
                <span class="product-price">${{ parseFloat(product.price || 0).toFixed(2) }}</span>
              </div>
            </div>
            <div v-if="deal.products.length > 3" class="more-products">
              +{{ deal.products.length - 3 }} 更多商品
            </div>
          </div>

          <div class="deal-footer">
            <button v-if="getUserOrderForDeal(deal.id)" @click.stop="viewOrder(getUserOrderForDeal(deal.id))" class="view-order-btn">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              查看订单
            </button>
            <div v-else class="no-order-chip">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
              未参与团购
            </div>
          </div>
        </div>
      </div>

      <!-- Past Deals Section -->
      <div v-if="groupDealsStore.pastDeals.length > 0" class="deals-section">
        <h2 class="section-title past">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="title-icon">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          往期团购
        </h2>
        <div 
          v-for="deal in groupDealsStore.pastDeals" 
          :key="deal.id" 
          class="deal-card past-deal"
          :class="getDealStatusClass(deal.status)"
          @click="viewDeal(deal)">
          <div class="deal-header">
            <div class="deal-info">
              <h3>{{ deal.title }}</h3>
              <span v-if="deal.description" class="deal-description">{{ deal.description }}</span>
            </div>
            <span :class="['status-badge', getDealStatusClass(deal.status)]">
              {{ getDealStatusLabel(deal.status) }}
            </span>
          </div>

          <div class="deal-dates">
            <span v-if="deal.order_end_date" class="date-item">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="date-icon">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              截单时间: {{ formatDateTime(deal.order_end_date) }}
            </span>
            <span v-if="deal.pickup_date" class="date-item">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="date-icon">
                <path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
              取货时间: {{ formatPickupDate(deal.pickup_date) }}
            </span>
          </div>

          <div v-if="deal.products && deal.products.length > 0" class="deal-products">
            <div v-for="product in deal.products.slice(0, 3)" :key="product.id" class="product-item">
              <div v-if="product.image" class="product-image">
                <img :src="product.image" :alt="product.name" />
              </div>
              <div v-else class="product-image placeholder">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                </svg>
              </div>
              <div class="product-details">
                <h4>{{ product.name }}</h4>
                <span class="product-price">${{ parseFloat(product.price || 0).toFixed(2) }}</span>
              </div>
            </div>
            <div v-if="deal.products.length > 3" class="more-products">
              +{{ deal.products.length - 3 }} 更多商品
            </div>
          </div>

          <div class="deal-footer">
            <button v-if="getUserOrderForDeal(deal.id)" @click.stop="viewOrder(getUserOrderForDeal(deal.id))" class="view-order-btn">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              查看订单
            </button>
            <div v-else class="no-order-chip">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
              未参与团购
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useAuthStore } from '../stores/auth'
import { useGroupDealsStore } from '../stores/groupDeals'

export default {
  name: 'GroupDeals',
  setup() {
    const authStore = useAuthStore()
    const groupDealsStore = useGroupDealsStore()
    return { authStore, groupDealsStore }
  },
  data() {
    return {
      isPulling: false,
      pullDistance: 0,
      touchStartY: 0,
      isRefreshing: false,
      userOrders: []
    }
  },
  computed: {
    isAdmin() {
      return this.authStore.isAdmin
    }
  },
  async mounted() {
    await this.groupDealsStore.fetchDeals()
    if (this.authStore.isAuthenticated) {
      await this.loadUserOrders()
    }
  },
  methods: {
    handleTouchStart(e) {
      if (window.scrollY === 0) {
        this.touchStartY = e.touches[0].clientY
      }
    },
    handleTouchMove(e) {
      if (this.isRefreshing || window.scrollY > 0) return
      
      const touchY = e.touches[0].clientY
      const distance = touchY - this.touchStartY
      
      if (distance > 0 && distance < 120) {
        this.isPulling = true
        this.pullDistance = distance
      }
    },
    async handleTouchEnd() {
      if (this.pullDistance >= 80 && !this.isRefreshing) {
        this.isRefreshing = true
        await this.groupDealsStore.refreshDeals()
        if (this.authStore.isAuthenticated) {
          await this.loadUserOrders()
        }
        this.isRefreshing = false
      }
      
      this.isPulling = false
      this.pullDistance = 0
      this.touchStartY = 0
    },
    async loadUserOrders() {
      if (!this.authStore.isAuthenticated) return
      
      try {
        const response = await fetch('http://localhost:5001/api/orders', {
          headers: {
            'Authorization': `Bearer ${this.authStore.token}`
          }
        })
        if (response.ok) {
          const data = await response.json()
          this.userOrders = data.orders || []
        }
      } catch (err) {
        console.error('Error loading user orders:', err)
      }
    },
    getUserOrderForDeal(dealId) {
      return this.userOrders.find(order => order.group_deal_id === dealId)
    },
    viewOrder(order) {
      this.$router.push(`/orders/${order.id}`)
    },
    viewDeal(deal) {
      const userOrder = this.getUserOrderForDeal(deal.id)
      if (userOrder) {
        // User has an order, go to order detail
        this.$router.push(`/orders/${userOrder.id}`)
      } else {
        // No order, go to deal detail
        this.$router.push(`/group-deals/${deal.id}`)
      }
    },
    getDealStatusLabel(status) {
      const labels = {
        'active': '进行中',
        'upcoming': '即将开始',
        'draft': '草稿',
        'closed': '已截单',
        'completed': '已完成',
        'ready_for_pickup': '可以取货'
      }
      return labels[status] || status
    },
    getDealStatusClass(status) {
      const classes = {
        'active': 'active',
        'upcoming': 'upcoming',
        'draft': 'draft',
        'closed': 'closed',
        'completed': 'completed',
        'ready_for_pickup': 'active'
      }
      return classes[status] || 'active'
    },
    formatDateTime(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN', {
        month: 'numeric',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      })
    },
    formatPickupDate(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN', {
        month: 'numeric',
        day: 'numeric',
        weekday: 'short'
      })
    }
  }
}
</script>

<style scoped>
.group-deals-page {
  min-height: 100vh;
  background: var(--md-background);
  padding-bottom: calc(80px + env(safe-area-inset-bottom));
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

.error {
  color: #C62828;
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

.deals-container {
  padding: var(--md-spacing-md);
  max-width: 600px;
  margin: 0 auto;
}

.deals-section {
  margin-bottom: var(--md-spacing-xxl);
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: var(--md-spacing-lg);
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  padding: var(--md-spacing-md) 0;
  letter-spacing: 0.5px;
  border-left: 4px solid transparent;
  padding-left: var(--md-spacing-md);
}

.section-title.current {
  color: #F57C00;
  border-left-color: #FF9800;
}

.section-title.past {
  color: #757575;
  border-left-color: #BDBDBD;
}

.title-icon {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
}

.deal-card {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-md);
  margin-bottom: var(--md-spacing-md);
  box-shadow: var(--md-elevation-1);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.deal-card:hover {
  box-shadow: var(--md-elevation-2);
  transform: translateY(-2px);
}

.deal-card.past-deal {
  background: #EEEEEE;
}

.deal-card.past-deal:hover {
  background: #E0E0E0;
}

.deal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--md-spacing-md);
  padding-bottom: var(--md-spacing-sm);
  border-bottom: 1px solid var(--md-outline-variant);
  gap: var(--md-spacing-md);
}

.deal-info {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-xs);
  flex: 1;
  min-width: 0;
}

.deal-info h3 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin: 0;
  font-weight: 500;
}

.deal-description {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: var(--md-radius-xl);
  font-size: var(--md-label-size);
  font-weight: 500;
  white-space: nowrap;
  flex-shrink: 0;
}

.status-badge.active {
  background: #E8F5E9;
  color: #2E7D32;
}

.status-badge.upcoming {
  background: #E3F2FD;
  color: #1565C0;
}

.status-badge.draft {
  background: #F3E5F5;
  color: #7B1FA2;
}

.status-badge.closed {
  background: #FFF3E0;
  color: #E65100;
}

.status-badge.completed {
  background: #4CAF50;
  color: white;
}

.deal-dates {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-xs);
  margin-bottom: var(--md-spacing-md);
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

.deal-products {
  margin-bottom: var(--md-spacing-sm);
}

.product-item {
  display: flex;
  gap: var(--md-spacing-md);
  padding: var(--md-spacing-sm) 0;
  border-bottom: 1px solid var(--md-outline-variant);
}

.product-item:last-child {
  border-bottom: none;
}

.product-image {
  width: 60px;
  height: 60px;
  border-radius: var(--md-radius-md);
  overflow: hidden;
  flex-shrink: 0;
  background: var(--md-surface-variant);
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-image.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--md-on-surface-variant);
  opacity: 0.5;
}

.product-image.placeholder svg {
  width: 32px;
  height: 32px;
}

.product-details {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.product-details h4 {
  font-size: var(--md-body-size);
  color: var(--md-on-surface);
  font-weight: 500;
  margin: 0;
}

.product-price {
  font-size: var(--md-label-size);
  font-weight: 600;
  color: var(--md-primary);
}

.more-products {
  padding: var(--md-spacing-sm);
  text-align: center;
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  font-style: italic;
}

.deal-footer {
  padding-top: var(--md-spacing-sm);
  border-top: 1px solid var(--md-outline-variant);
  margin-top: var(--md-spacing-sm);
  display: flex;
  justify-content: center;
  align-items: center;
}

.view-order-btn {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-xs);
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  background: var(--md-primary);
  color: white;
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-label-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 4px rgba(255, 165, 0, 0.2);
}

.view-order-btn svg {
  width: 16px;
  height: 16px;
}

.view-order-btn:hover {
  background: #FF8C00;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(255, 165, 0, 0.3);
}

.view-order-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(255, 165, 0, 0.2);
}

.no-order-chip {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-xs);
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  background: #E0E0E0;
  color: #757575;
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-label-size);
  font-weight: 500;
}

.no-order-chip svg {
  width: 16px;
  height: 16px;
}

@media (max-width: 480px) {
  .page-header {
    padding: var(--md-spacing-md);
    padding-top: calc(var(--md-spacing-md) + env(safe-area-inset-top));
  }
}
</style>



