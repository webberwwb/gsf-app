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
      <!-- Global Loading State -->
      <div v-if="loading" class="global-loading">
        <div class="loading">加载中...</div>
      </div>
      <!-- Active Group Deals Section -->
      <section v-if="!loading && activeDeals.length > 0" class="deals-section">
        <h2 class="section-title">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="title-icon">
            <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z" />
          </svg>
          正在进行中的团购
        </h2>
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
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="date-icon">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                下单截止: {{ formatDate(deal.order_end_date) }}
              </span>
              <span class="date-item">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="date-icon">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
                取货日期: {{ formatDate(deal.pickup_date) }}
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
      <section v-if="!loading && upcomingDeals.length > 0" class="deals-section">
        <h2 class="section-title">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="title-icon">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          即将开始
        </h2>
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
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="date-icon">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                开始时间: {{ formatDate(deal.order_start_date) }}
              </span>
            </div>
          </div>
        </div>
      </section>

      <!-- Hot Products Section (Browse Only) -->
      <section v-if="!loading && products.length > 0" class="products-section">
        <h2 class="section-title">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="title-icon">
            <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z" />
          </svg>
          热门商品
        </h2>
        <p class="section-subtitle">浏览商品，下单请参与团购活动</p>
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="products.length === 0" class="empty-state">
          <p>暂无商品</p>
        </div>
        <div v-else class="products-grid">
          <div
            v-for="product in products"
            :key="product.id"
            class="product-card browse-only"
            @click="openProductModal(product)"
          >
            <div class="product-image">
              <img
                v-if="getProductImage(product)"
                :src="getProductImage(product)"
                :alt="product.name"
              />
              <div v-else class="image-placeholder">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                </svg>
              </div>
              <!-- Sold Out Badge -->
              <div v-if="isOutOfStock(product)" class="sold-out-badge">
                已售罄
              </div>
            </div>
            <div class="product-info">
              <h3 class="product-name">{{ product.name }}</h3>
              <div v-if="product.counts_toward_free_shipping === false" class="shipping-excluded-badge">
                不计入免运门槛
              </div>
              <div class="product-price">
                <template v-if="product.pricing_type === 'per_item'">
                  <span class="sale-price">${{ product.price }}</span>
                </template>
                <template v-else-if="product.pricing_type === 'weight_range'">
                  <span class="sale-price">${{ formatWeightRangePrice(product) }}</span>
                  <span class="price-note">按重量区间</span>
                </template>
                <template v-else-if="product.pricing_type === 'unit_weight'">
                  <span class="sale-price">${{ product.pricing_data?.price_per_unit || product.price }}</span>
                  <span class="price-note">/ {{ product.pricing_data?.unit === 'kg' ? 'kg' : 'lb' }}</span>
                </template>
                <template v-else-if="product.pricing_type === 'bundled_weight'">
                  <div class="bundled-price-compact">
                    <span class="sale-price">{{ formatBundledPrice(product) }}</span>
                    <span class="price-note">/ 份</span>
                    <span class="unit-price-note">(${{ (product.pricing_data?.price_per_unit || 0).toFixed(2) }}/{{ product.pricing_data?.unit === 'kg' ? 'kg' : 'lb' }})</span>
                  </div>
                </template>
                <template v-else>
                  <span class="sale-price">${{ product.price }}</span>
                </template>
              </div>
              <div v-if="getNextSaleDate(product)" :class="['next-sale-badge', { 'active-deal': isProductInActiveDeal(product) }]">
                {{ getNextSaleDate(product) }}
              </div>
              <div v-else class="browse-only-badge">暂无团购</div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- Product Detail Modal -->
    <ProductDetailModal
      :show="showProductModal"
      :product="selectedProduct"
      @close="closeProductModal"
    />
  </div>
</template>

<script>
import apiClient from '../api/client'
import { formatDateEST_CN, parseDateEST, getNowEST } from '../utils/date'
import ProductDetailModal from '../components/ProductDetailModal.vue'

export default {
  name: 'Home',
  components: {
    ProductDetailModal
  },
  data() {
    return {
      loading: true,
      products: [],
      deals: [],
      activeDeals: [],
      upcomingDeals: [],
      showProductModal: false,
      selectedProduct: null
    }
  },
  async mounted() {
    await this.loadData()
  },
  methods: {
    async loadData() {
      this.loading = true
      try {
        // Load products (sorted by popularity) and deals in parallel
        const [productsRes, dealsRes] = await Promise.all([
          apiClient.get('/products?sort=popularity&days=30&include_stats=true'),
          apiClient.get('/group-deals')
        ])
        
        // Filter out inactive products for hot products section
        this.products = (productsRes.data.products || []).filter(product => product.is_active === true)
        this.deals = dealsRes.data.deals || []
        
        // Separate active and upcoming deals
        // Use EST for date comparisons since backend dates are in EST
        const now = getNowEST()
        this.activeDeals = this.deals.filter(deal => {
          const endDate = parseDateEST(deal.order_end_date)
          return deal.status === 'active' && endDate && endDate > now
        })
        
        this.upcomingDeals = this.deals.filter(deal => {
          const startDate = parseDateEST(deal.order_start_date)
          return deal.status === 'upcoming' && startDate && startDate > now
        })
      } catch (error) {
        console.error('Failed to load data:', error)
        // Ensure we still show something even if loading fails
        this.products = []
        this.deals = []
        this.activeDeals = []
        this.upcomingDeals = []
      } finally {
        this.loading = false
      }
    },
    formatDate(dateString) {
      return formatDateEST_CN(dateString)
    },
    isOutOfStock(product) {
      if (!product) return false
      
      // Check deal_stock_limit (deal-specific inventory) first, then stock_limit (product-level inventory)
      // null or undefined means unlimited stock, only 0 means out of stock
      // Explicitly check for 0 to handle both deal_stock_limit = 0 and stock_limit = 0
      if (product.deal_stock_limit !== undefined && product.deal_stock_limit !== null) {
        return product.deal_stock_limit === 0
      }
      
      if (product.stock_limit !== undefined && product.stock_limit !== null) {
        return product.stock_limit === 0
      }
      
      return false // No stock limit means unlimited stock
    },
    formatWeightRangePrice(product) {
      if (product.pricing_data && product.pricing_data.ranges && product.pricing_data.ranges.length > 0) {
        const firstRange = product.pricing_data.ranges[0]
        return firstRange.price || '0.00'
      }
      return product.price || '0.00'
    },
    formatBundledPrice(product) {
      if (product.pricing_type === 'bundled_weight') {
        const pricePerUnit = product.pricing_data?.price_per_unit || 0
        const minWeight = product.pricing_data?.min_weight || 7
        const maxWeight = product.pricing_data?.max_weight || 15
        
        if (pricePerUnit === 0) {
          return product.price || '0.00'
        }
        
        const minPrice = pricePerUnit * minWeight
        const maxPrice = pricePerUnit * maxWeight
        
        if (minPrice === maxPrice) {
          return `$${minPrice.toFixed(2)}`
        }
        return `$${minPrice.toFixed(2)} - $${maxPrice.toFixed(2)}`
      }
      return product.price || '0.00'
    },
    getNextSaleDate(product) {
      if (!product || !this.deals || this.deals.length === 0) {
        return null
      }
      
      const now = getNowEST()
      const productId = product.id
      
      // Find all deals that include this product (active or upcoming)
      const relevantDeals = this.deals.filter(deal => {
        if (!deal.products || deal.products.length === 0) {
          return false
        }
        // Check if product is in deal's products
        return deal.products.some(p => p.id === productId)
      })
      
      if (relevantDeals.length === 0) {
        return null
      }
      
      // Check for active deals first
      const activeDeal = relevantDeals.find(deal => {
        const endDate = parseDateEST(deal.order_end_date)
        return deal.status === 'active' && endDate && endDate > now
      })
      
      if (activeDeal) {
        return '正在开团'
      }
      
      // Find the next upcoming deal
      const nextDeal = relevantDeals
        .filter(deal => {
          const startDate = parseDateEST(deal.order_start_date)
          return deal.status === 'upcoming' && startDate && startDate > now
        })
        .sort((a, b) => {
          // Sort by order_start_date, earliest first
          const dateA = parseDateEST(a.order_start_date)
          const dateB = parseDateEST(b.order_start_date)
          if (!dateA || !dateB) return 0
          return dateA - dateB
        })[0]
      
      if (!nextDeal) {
        return null
      }
      
      // Format the date: "1月1日开团"
      const saleDate = parseDateEST(nextDeal.order_start_date)
      if (!saleDate) return null
      const month = saleDate.getMonth() + 1
      const day = saleDate.getDate()
      
      return `${month}月${day}日开团`
    },
    isProductInActiveDeal(product) {
      if (!product || !this.deals || this.deals.length === 0) {
        return false
      }
      
      const now = getNowEST()
      const productId = product.id
      
      // Check if product is in any active deal
      return this.deals.some(deal => {
        if (!deal.products || deal.products.length === 0) {
          return false
        }
        const endDate = parseDateEST(deal.order_end_date)
        return deal.status === 'active' && 
               endDate && endDate > now &&
               deal.products.some(p => p.id === productId)
      })
    },
    viewDeal(deal) {
      this.$router.push(`/group-deals/${deal.id}`)
    },
    openProductModal(product) {
      this.selectedProduct = product
      this.showProductModal = true
    },
    closeProductModal() {
      this.showProductModal = false
      this.selectedProduct = null
    },
    getProductImage(product) {
      // Support both old single image format and new multiple images format
      if (product.images && Array.isArray(product.images) && product.images.length > 0) {
        return product.images[0]
      }
      if (product.image) {
        return product.image
      }
      return null
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
  color: white;
  margin-bottom: var(--md-spacing-xs);
  font-weight: 500;
  letter-spacing: -0.5px;
}

.header-text p {
  font-size: var(--md-label-size);
  color: rgba(255, 255, 255, 0.9);
  opacity: 1;
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
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
}

.title-icon {
  width: 20px;
  height: 20px;
  color: var(--md-primary);
  flex-shrink: 0;
}

.section-subtitle {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin-bottom: var(--md-spacing-md);
  text-align: center;
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
  border: 2px solid transparent;
  overflow: hidden;
  position: relative;
}

/* Active deal card - red/orange accent */
.deal-card:not(.upcoming) {
  border: 2px solid rgba(255, 68, 68, 0.2);
  background: linear-gradient(to bottom, rgba(255, 68, 68, 0.03), var(--md-surface));
  box-shadow: 0 2px 8px rgba(255, 68, 68, 0.15);
}

.deal-card:not(.upcoming)::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #FF4444, #FF6B35);
  transform: scaleX(1);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.deal-card:not(.upcoming):hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(255, 68, 68, 0.25);
  border-color: rgba(255, 68, 68, 0.4);
}

.deal-card:not(.upcoming):active {
  transform: translateY(-2px);
  box-shadow: 0 2px 12px rgba(255, 68, 68, 0.2);
}

/* Upcoming deal card - subtle yellow/gold accent */
.deal-card.upcoming {
  border: 2px solid rgba(255, 215, 0, 0.3);
  background: linear-gradient(to bottom, rgba(255, 215, 0, 0.02), var(--md-surface));
  opacity: 0.9;
}

.deal-card.upcoming::before {
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

.deal-card.upcoming:hover {
  transform: translateY(-4px);
  box-shadow: var(--md-elevation-3);
  border-color: rgba(255, 215, 0, 0.5);
  opacity: 1;
}

.deal-card.upcoming:hover::before {
  transform: scaleX(1);
}

.deal-card.upcoming:active {
  transform: translateY(-2px);
  box-shadow: var(--md-elevation-2);
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
  white-space: pre-line;
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

.date-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
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

.global-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 50vh;
  padding: 2rem;
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
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  border: 2px solid transparent;
}

.product-card.browse-only {
  cursor: pointer;
}

.product-card.browse-only:hover {
  transform: translateY(-4px);
  box-shadow: var(--md-elevation-3);
  border-color: var(--md-primary-variant);
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
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.2;
  color: var(--md-on-surface-variant);
}

.image-placeholder svg {
  width: 32px;
  height: 32px;
}

.sold-out-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: linear-gradient(135deg, #D32F2F 0%, #B71C1C 100%);
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(211, 47, 47, 0.4);
  z-index: 10;
  text-transform: uppercase;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.9;
    transform: scale(1.02);
  }
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

.shipping-excluded-badge {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  background: #FFF3E0;
  color: #E65100;
  margin-bottom: var(--md-spacing-xs);
  width: fit-content;
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

.price-note {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin-left: var(--md-spacing-xs);
}

.bundled-price-compact {
  display: flex;
  align-items: baseline;
  gap: 4px;
  flex-wrap: wrap;
}

.unit-price-note {
  font-size: 0.75rem;
  color: #999;
}

@media (max-width: 480px) {
  .bundled-price-compact {
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
  }
  
  .unit-price-note {
    font-size: 0.7rem;
  }
}

.browse-only-badge {
  width: 100%;
  background: var(--md-surface-variant);
  color: var(--md-on-surface-variant);
  border: none;
  padding: 0.625rem;
  border-radius: var(--md-radius-sm);
  font-size: var(--md-label-size);
  font-weight: 500;
  letter-spacing: 0.5px;
  text-align: center;
  margin-top: var(--md-spacing-sm);
}

.next-sale-badge {
  width: 100%;
  background: linear-gradient(135deg, rgba(255, 140, 0, 0.15), rgba(255, 215, 0, 0.15));
  color: var(--md-on-surface-variant);
  border: 1.5px solid var(--md-primary-variant);
  padding: 0.625rem;
  border-radius: var(--md-radius-sm);
  font-size: var(--md-label-size);
  font-weight: 500;
  letter-spacing: 0.5px;
  text-align: center;
  margin-top: var(--md-spacing-sm);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.next-sale-badge.active-deal {
  background: linear-gradient(135deg, #FF4444, #FF6B35);
  color: white;
  border: none;
  box-shadow: 0 2px 8px rgba(255, 68, 68, 0.3);
  font-weight: 600;
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% {
    box-shadow: 0 2px 8px rgba(255, 68, 68, 0.3);
  }
  50% {
    box-shadow: 0 4px 12px rgba(255, 68, 68, 0.5);
  }
}
</style>
