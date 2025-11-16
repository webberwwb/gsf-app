<template>
  <div class="shop-page">
    <!-- Header -->
    <header class="shop-header">
      <div class="header-content">
        <img src="/logos/gsf-icon.png" alt="谷语农庄" class="logo" />
        <div class="header-text">
          <h1>谷语农庄</h1>
          <p>精品生态农产品团购</p>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="shop-content">
      <!-- Active Group Deals Section -->
      <section v-if="activeDeals.length > 0" class="deals-section">
        <h2 class="section-title">🔥 正在进行中的团购</h2>
        <div class="deals-list">
          <div
            v-for="deal in activeDeals"
            :key="deal.id"
            class="deal-card"
            @click="viewDeal(deal)"
          >
            <div class="deal-header">
              <h3>{{ deal.title }}</h3>
              <span class="deal-badge active">进行中</span>
            </div>
            <p class="deal-description">{{ deal.description || '精选优质农产品' }}</p>
            <div class="deal-dates">
              <span class="date-item">
                📅 下单截止: {{ formatDate(deal.order_end_date) }}
              </span>
              <span class="date-item">
                📦 取货日期: {{ formatDate(deal.pickup_date) }}
              </span>
            </div>
            <div class="deal-products-preview">
              <span
                v-for="(product, idx) in deal.products.slice(0, 3)"
                :key="product.id"
                class="product-tag"
              >
                {{ product.name }}
              </span>
              <span v-if="deal.products.length > 3" class="product-tag more">
                +{{ deal.products.length - 3 }} 更多
              </span>
            </div>
          </div>
        </div>
      </section>

      <!-- Upcoming Deals Section -->
      <section v-if="upcomingDeals.length > 0" class="deals-section">
        <h2 class="section-title">⏰ 即将开始</h2>
        <div class="deals-list">
          <div
            v-for="deal in upcomingDeals"
            :key="deal.id"
            class="deal-card upcoming"
            @click="viewDeal(deal)"
          >
            <div class="deal-header">
              <h3>{{ deal.title }}</h3>
              <span class="deal-badge upcoming">即将开始</span>
            </div>
            <p class="deal-description">{{ deal.description || '精选优质农产品' }}</p>
            <div class="deal-dates">
              <span class="date-item">
                🕐 开始时间: {{ formatDate(deal.order_start_date) }}
              </span>
            </div>
          </div>
        </div>
      </section>

      <!-- All Products Section -->
      <section class="products-section">
        <h2 class="section-title">🛍️ 全部商品</h2>
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="products.length === 0" class="empty-state">
          <p>暂无商品</p>
        </div>
        <div v-else class="products-grid">
          <div
            v-for="product in products"
            :key="product.id"
            class="product-card"
            @click="addToCart(product)"
          >
            <div class="product-image">
              <img
                v-if="product.image"
                :src="product.image"
                :alt="product.name"
              />
              <div v-else class="image-placeholder">🛒</div>
            </div>
            <div class="product-info">
              <h3 class="product-name">{{ product.name }}</h3>
              <p v-if="product.description" class="product-description">
                {{ product.description.substring(0, 50) }}...
              </p>
              <div class="product-price">
                <span class="sale-price">${{ product.sale_price }}</span>
                <span v-if="product.original_price > product.sale_price" class="original-price">
                  ${{ product.original_price }}
                </span>
              </div>
              <button class="add-to-cart-btn">加入购物车</button>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script>
import apiClient from '../api/client'

export default {
  name: 'Home',
  data() {
    return {
      loading: true,
      products: [],
      deals: [],
      activeDeals: [],
      upcomingDeals: []
    }
  },
  async mounted() {
    await this.loadData()
  },
  methods: {
    async loadData() {
      this.loading = true
      try {
        // Load products and deals in parallel
        const [productsRes, dealsRes] = await Promise.all([
          apiClient.get('/products'),
          apiClient.get('/group-deals')
        ])
        
        this.products = productsRes.data.products || []
        this.deals = dealsRes.data.deals || []
        
        // Separate active and upcoming deals
        const now = new Date()
        this.activeDeals = this.deals.filter(deal => {
          const endDate = new Date(deal.order_end_date)
          return deal.status === 'active' && endDate > now
        })
        
        this.upcomingDeals = this.deals.filter(deal => {
          const startDate = new Date(deal.order_start_date)
          return deal.status === 'upcoming' && startDate > now
        })
      } catch (error) {
        console.error('Failed to load data:', error)
      } finally {
        this.loading = false
      }
    },
    formatDate(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleDateString('zh-CN', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    },
    viewDeal(deal) {
      // TODO: Navigate to deal detail page
      console.log('View deal:', deal)
    },
    addToCart(product) {
      // Get current cart
      const cart = JSON.parse(localStorage.getItem('cart') || '[]')
      
      // Check if product already in cart
      const existingItem = cart.find(item => item.id === product.id)
      
      if (existingItem) {
        existingItem.quantity++
      } else {
        cart.push({
          id: product.id,
          name: product.name,
          price: product.sale_price,
          image: product.image,
          quantity: 1
        })
      }
      
      // Save cart
      localStorage.setItem('cart', JSON.stringify(cart))
      
      // Show feedback
      this.$root.$emit('cart-updated')
      
      // Show toast (simple alert for now)
      alert(`已添加 ${product.name} 到购物车`)
    }
  }
}
</script>

<style scoped>
.shop-page {
  min-height: 100vh;
  background: var(--md-background);
  padding-bottom: 80px; /* Space for bottom nav */
}

.shop-header {
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-2);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
  max-width: 600px;
  margin: 0 auto;
}

.logo {
  width: 64px;
  height: 64px;
  object-fit: contain;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.15));
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.logo:hover {
  transform: scale(1.05);
}

.header-text h1 {
  font-size: var(--md-headline-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-xs);
  font-weight: 500;
  letter-spacing: -0.5px;
}

.header-text p {
  font-size: var(--md-label-size);
  color: var(--md-on-surface);
  opacity: 0.87;
  font-weight: 400;
}

.shop-content {
  padding: var(--md-spacing-md);
  max-width: 600px;
  margin: 0 auto;
}

.section-title {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin: var(--md-spacing-xl) 0 var(--md-spacing-md);
  font-weight: 500;
  letter-spacing: 0.15px;
}

.deals-section {
  margin-bottom: 2rem;
}

.deals-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.deal-card {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: none;
  overflow: hidden;
  position: relative;
}

.deal-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--md-primary-variant), var(--md-primary));
  transform: scaleX(0);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.deal-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--md-elevation-3);
}

.deal-card:hover::before {
  transform: scaleX(1);
}

.deal-card:active {
  transform: translateY(-2px);
  box-shadow: var(--md-elevation-2);
}

.deal-card.upcoming {
  opacity: 0.8;
}

.deal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.deal-header h3 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  font-weight: 500;
  letter-spacing: 0.15px;
}

.deal-badge {
  padding: 0.375rem 0.875rem;
  border-radius: var(--md-radius-xl);
  font-size: var(--md-label-size);
  font-weight: 500;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.deal-badge.active {
  background: #FF4444;
  color: white;
  box-shadow: 0 2px 4px rgba(255, 68, 68, 0.3);
}

.deal-badge.upcoming {
  background: var(--md-primary-variant);
  color: var(--md-on-surface);
}

.deal-description {
  color: var(--md-on-surface-variant);
  font-size: var(--md-body-size);
  margin-bottom: var(--md-spacing-md);
  line-height: 1.5;
}

.deal-dates {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
  margin-bottom: var(--md-spacing-md);
}

.date-item {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  display: flex;
  align-items: center;
  gap: var(--md-spacing-xs);
}

.deal-products-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.product-tag {
  background: var(--md-surface-variant);
  padding: 0.375rem 0.875rem;
  border-radius: var(--md-radius-xl);
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  font-weight: 500;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.product-tag.more {
  background: var(--md-primary-variant);
  color: var(--md-on-surface);
}

.products-section {
  margin-bottom: 2rem;
}

.loading, .empty-state {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.product-card {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  overflow: hidden;
  box-shadow: var(--md-elevation-1);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--md-elevation-3);
}

.product-card:active {
  transform: translateY(-2px);
  box-shadow: var(--md-elevation-2);
}

.product-image {
  width: 100%;
  height: 160px;
  background: var(--md-surface-variant);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
}

.product-image::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to bottom, transparent, rgba(0, 0, 0, 0.02));
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.product-card:hover .product-image img {
  transform: scale(1.05);
}

.image-placeholder {
  font-size: 3rem;
  opacity: 0.2;
}

.product-info {
  padding: var(--md-spacing-md);
}

.product-name {
  font-size: var(--md-body-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-sm);
  font-weight: 500;
  letter-spacing: 0.15px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.4;
}

.product-description {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin-bottom: var(--md-spacing-sm);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.4;
}

.product-price {
  display: flex;
  align-items: baseline;
  gap: var(--md-spacing-sm);
  margin-bottom: var(--md-spacing-md);
}

.sale-price {
  font-size: 1.25rem;
  color: #FF4444;
  font-weight: 600;
  letter-spacing: -0.5px;
}

.original-price {
  font-size: var(--md-label-size);
  color: var(--md-outline);
  text-decoration: line-through;
}

.add-to-cart-btn {
  width: 100%;
  background: var(--md-primary);
  color: white;
  border: none;
  padding: 0.625rem;
  border-radius: var(--md-radius-sm);
  font-size: var(--md-label-size);
  font-weight: 500;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  text-transform: uppercase;
  box-shadow: 0 2px 4px rgba(255, 140, 0, 0.2);
  position: relative;
  overflow: hidden;
}

.add-to-cart-btn:hover {
  background: #FF7F00;
  box-shadow: 0 4px 8px rgba(255, 140, 0, 0.3);
  transform: translateY(-1px);
}

.add-to-cart-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(255, 140, 0, 0.2);
}
</style>
