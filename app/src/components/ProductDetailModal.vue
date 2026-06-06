<template>
  <Transition name="modal">
    <div v-if="show" class="modal-overlay" @click.self="handleClose">
      <div class="modal-container" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">商品详情</h3>
          <button @click="handleClose" class="modal-close">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div class="modal-body" v-if="product">
          <!-- Product Images Carousel -->
          <div class="product-image-section">
            <div v-if="productImages.length > 0" class="image-carousel">
              <div class="carousel-main">
                <img 
                  :src="productImages[currentImageIndex]" 
                  :alt="product.name" 
                  @click="openFullScreen"
                  class="carousel-main-image"
                />
                <!-- Sold Out Badge -->
                <div v-if="isOutOfStock(product)" class="sold-out-badge">
                  已售罄
                </div>
                <button 
                  v-if="productImages.length > 1"
                  @click.stop="previousImage" 
                  class="carousel-btn carousel-btn-prev"
                  aria-label="Previous image"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
                  </svg>
                </button>
                <button 
                  v-if="productImages.length > 1"
                  @click.stop="nextImage" 
                  class="carousel-btn carousel-btn-next"
                  aria-label="Next image"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                </button>
                <div v-if="productImages.length > 1" class="carousel-indicator">
                  {{ currentImageIndex + 1 }} / {{ productImages.length }}
                </div>
              </div>
              <div v-if="productImages.length > 1" class="carousel-thumbnails">
                <div
                  v-for="(img, index) in productImages"
                  :key="index"
                  :class="['thumbnail', { active: index === currentImageIndex }]"
                  @click="currentImageIndex = index"
                >
                  <img :src="img" :alt="`${product.name} - Image ${index + 1}`" />
                </div>
              </div>
            </div>
            <div v-else class="product-image">
              <div class="image-placeholder">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                </svg>
              </div>
            </div>
          </div>

          <!-- Product Info -->
          <div class="product-info-section">
            <h2 class="product-name">{{ product.name }}</h2>
            
            <!-- Price Display -->
            <div class="product-price-section">
              <div class="price-label">价格:</div>
              <div class="price-value">
                <template v-if="product.pricing_type === 'per_item'">
                  <span class="sale-price">${{ formatPrice(product) }}</span>
                </template>
                <template v-else-if="product.pricing_type === 'weight_range'">
                  <div class="weight-range-pricing">
                    <div class="pricing-header">
                      <span class="sale-price">{{ formatPriceRange(product) }}</span>
                      <span class="price-note">按重量区间定价</span>
                    </div>
                    <div class="pricing-breakdown">
                      <div class="breakdown-title">价格明细</div>
                      <div class="weight-ranges-table">
                        <div 
                          v-for="(range, idx) in getSortedWeightRanges(product)" 
                          :key="idx"
                          class="range-row"
                        >
                          <div class="range-weight">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="range-icon">
                              <path stroke-linecap="round" stroke-linejoin="round" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
                            </svg>
                            <span class="weight-text">{{ formatWeightRange(range, product.pricing_data?.unit) }}</span>
                          </div>
                          <div class="range-price">${{ moneyPlain(range.price || 0) }}</div>
                        </div>
                      </div>
                      <div class="pricing-note">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="note-icon">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>取货时按实际重量称重结算，实际重量可能超出上述区间</span>
                      </div>
                    </div>
                  </div>
                </template>
                <template v-else-if="product.pricing_type === 'unit_weight'">
                  <div class="unit-weight-pricing">
                    <div class="pricing-header">
                      <span class="sale-price">${{ moneyPlain(product.pricing_data?.price_per_unit || 0) }}</span>
                      <span class="price-note">/ {{ product.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }}</span>
                    </div>
                    <div class="pricing-breakdown">
                      <div class="breakdown-title">价格计算方式</div>
                      <div class="calculation-formula">
                        <div class="formula-line">
                          <span class="formula-label">最终价格 =</span>
                          <span class="formula-value">实际重量 × ${{ moneyPlain(product.pricing_data?.price_per_unit || 0) }}/{{ product.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }}</span>
                        </div>
                      </div>
                      <div class="pricing-examples">
                        <div class="example-title">价格示例:</div>
                        <div class="example-row">
                          <span class="example-weight">1 {{ product.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }}</span>
                          <span class="example-arrow">→</span>
                          <span class="example-price">${{ moneyPlain(product.pricing_data?.price_per_unit || 0) }}</span>
                        </div>
                        <div class="example-row">
                          <span class="example-weight">2 {{ product.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }}</span>
                          <span class="example-arrow">→</span>
                          <span class="example-price">${{ moneyPlain((product.pricing_data?.price_per_unit || 0) * 2) }}</span>
                        </div>
                        <div class="example-row">
                          <span class="example-weight">3 {{ product.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }}</span>
                          <span class="example-arrow">→</span>
                          <span class="example-price">${{ moneyPlain((product.pricing_data?.price_per_unit || 0) * 3) }}</span>
                        </div>
                      </div>
                      <div class="pricing-note">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="note-icon">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>取货时称重，按实际重量计算最终价格</span>
                      </div>
                    </div>
                  </div>
                </template>
                <template v-else-if="product.pricing_type === 'bundled_weight'">
                  <div class="bundled-weight-pricing">
                    <div class="pricing-header">
                      <span class="sale-price">{{ formatBundledPrice(product) }}</span>
                      <span class="price-note">/ 份</span>
                    </div>
                    <div class="pricing-breakdown">
                      <div class="breakdown-title">价格计算方式</div>
                      <div class="bundled-info-grid">
                        <div class="info-item">
                          <div class="info-label">每份参考重量</div>
                          <div class="info-value">{{ product.pricing_data?.min_weight || 7 }} - {{ product.pricing_data?.max_weight || 15 }} {{ product.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }}</div>
                        </div>
                        <div class="info-item">
                          <div class="info-label">单价</div>
                          <div class="info-value">${{ moneyPlain(product.pricing_data?.price_per_unit || 0) }}/{{ product.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }}</div>
                        </div>
                      </div>
                      <div class="calculation-formula">
                        <div class="formula-line">
                          <span class="formula-label">最终价格 =</span>
                          <span class="formula-value">实际重量 × ${{ moneyPlain(product.pricing_data?.price_per_unit || 0) }}/{{ product.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }}</span>
                        </div>
                      </div>
                      <div class="pricing-examples">
                        <div class="example-title">价格示例 (每份):</div>
                        <div class="example-row">
                          <span class="example-weight">{{ product.pricing_data?.min_weight || 7 }} {{ product.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }}</span>
                          <span class="example-arrow">→</span>
                          <span class="example-price">${{ moneyPlain((product.pricing_data?.price_per_unit || 0) * (product.pricing_data?.min_weight || 7)) }}</span>
                        </div>
                        <div class="example-row">
                          <span class="example-weight">{{ Math.round((product.pricing_data?.min_weight || 7) + (product.pricing_data?.max_weight || 15)) / 2 }} {{ product.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }}</span>
                          <span class="example-arrow">→</span>
                          <span class="example-price">${{ moneyPlain((product.pricing_data?.price_per_unit || 0) * Math.round(((product.pricing_data?.min_weight || 7) + (product.pricing_data?.max_weight || 15)) / 2)) }}</span>
                        </div>
                        <div class="example-row">
                          <span class="example-weight">{{ product.pricing_data?.max_weight || 15 }} {{ product.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }}</span>
                          <span class="example-arrow">→</span>
                          <span class="example-price">${{ moneyPlain((product.pricing_data?.price_per_unit || 0) * (product.pricing_data?.max_weight || 15)) }}</span>
                        </div>
                      </div>
                      <div class="pricing-note">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="note-icon">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>每份重量通常在此范围内，取货时按实际重量称重结算</span>
                      </div>
                    </div>
                  </div>
                </template>
                <template v-else>
                  <span class="sale-price">${{ formatPrice(product) }}</span>
                </template>
              </div>
            </div>

            <!-- Description -->
            <div v-if="product.description" class="product-description-section">
              <h3 class="section-label">商品描述</h3>
              <p class="product-description">{{ product.description }}</p>
            </div>

            <!-- Stock Info (if available) -->
            <div v-if="product.deal_stock_limit" class="product-stock-section">
              <h3 class="section-label">库存</h3>
              <p class="stock-info">{{ product.deal_stock_limit }} 件</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Transition>

  <!-- Full Screen Image Viewer -->
  <Transition name="fullscreen">
    <div v-if="showFullScreen" class="fullscreen-overlay" @click="closeFullScreen">
      <div class="fullscreen-container" @click.stop>
        <button @click="closeFullScreen" class="fullscreen-close">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        <img 
          :src="productImages[fullScreenImageIndex]" 
          :alt="product.name" 
          class="fullscreen-image"
        />
        <button 
          v-if="productImages.length > 1"
          @click.stop="previousFullScreenImage" 
          class="fullscreen-btn fullscreen-btn-prev"
          aria-label="Previous image"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <button 
          v-if="productImages.length > 1"
          @click.stop="nextFullScreenImage" 
          class="fullscreen-btn fullscreen-btn-next"
          aria-label="Next image"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </button>
        <div v-if="productImages.length > 1" class="fullscreen-indicator">
          {{ fullScreenImageIndex + 1 }} / {{ productImages.length }}
        </div>
      </div>
    </div>
  </Transition>
</template>

<script>
import {
  formatMoney,
  formatMoneyDisplay,
  formatProductListPrice,
  formatProductPriceRange
} from '../utils/productPriceDisplay'

export default {
  name: 'ProductDetailModal',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    product: {
      type: Object,
      default: null
    }
  },
  emits: ['close'],
  data() {
    return {
      currentImageIndex: 0,
      showFullScreen: false,
      fullScreenImageIndex: 0
    }
  },
  computed: {
    productImages() {
      if (!this.product) return []
      // Support both old single image format and new multiple images format
      if (this.product.images && Array.isArray(this.product.images)) {
        return this.product.images.filter(img => img) // Filter out null/empty images
      }
      if (this.product.image) {
        return [this.product.image]
      }
      return []
    }
  },
  watch: {
    show(newVal) {
      if (newVal) {
        this.currentImageIndex = 0
        this.showFullScreen = false
      }
    },
    showFullScreen(newVal) {
      if (newVal) {
        document.body.style.overflow = 'hidden'
        this.fullScreenImageIndex = this.currentImageIndex
      } else {
        document.body.style.overflow = ''
      }
    }
  },
  mounted() {
    document.addEventListener('keydown', this.handleKeydown)
  },
  beforeUnmount() {
    document.removeEventListener('keydown', this.handleKeydown)
    document.body.style.overflow = ''
  },
  methods: {
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
    handleClose() {
      this.$emit('close')
    },
    nextImage() {
      if (this.productImages.length > 0) {
        this.currentImageIndex = (this.currentImageIndex + 1) % this.productImages.length
      }
    },
    previousImage() {
      if (this.productImages.length > 0) {
        this.currentImageIndex = (this.currentImageIndex - 1 + this.productImages.length) % this.productImages.length
      }
    },
    formatPrice(product) {
      return formatProductListPrice(product)
    },
    formatPriceRange(product) {
      return formatProductPriceRange(product)
    },
    formatBundledPrice(product) {
      if (product?.pricing_type !== 'bundled_weight') return '价格待定'
      const label = formatProductPriceRange(product)
      return label.includes('/份') ? label.split(' · ')[0] : label
    },
    moneyPlain(value) {
      return formatMoney(value)
    },
    openFullScreen() {
      if (this.productImages.length > 0) {
        this.showFullScreen = true
        this.fullScreenImageIndex = this.currentImageIndex
      }
    },
    closeFullScreen() {
      this.showFullScreen = false
      this.currentImageIndex = this.fullScreenImageIndex
    },
    nextFullScreenImage() {
      if (this.productImages.length > 0) {
        this.fullScreenImageIndex = (this.fullScreenImageIndex + 1) % this.productImages.length
      }
    },
    previousFullScreenImage() {
      if (this.productImages.length > 0) {
        this.fullScreenImageIndex = (this.fullScreenImageIndex - 1 + this.productImages.length) % this.productImages.length
      }
    },
    handleKeydown(event) {
      if (!this.showFullScreen) return
      
      if (event.key === 'Escape') {
        this.closeFullScreen()
      } else if (event.key === 'ArrowLeft') {
        this.previousFullScreenImage()
      } else if (event.key === 'ArrowRight') {
        this.nextFullScreenImage()
      }
    },
    getSortedWeightRanges(product) {
      if (!product.pricing_data?.ranges) return []
      return [...product.pricing_data.ranges].sort((a, b) => (a.min || 0) - (b.min || 0))
    },
    formatWeightRange(range, unit = 'lb') {
      const displayUnit = unit === 'kg' ? 'lb' : 'lb'
      if (range.max === null || range.max === undefined) {
        return `${range.min}+ ${displayUnit}`
      }
      return `${range.min} - ${range.max} ${displayUnit}`
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 16px;
}

.modal-container {
  background: white;
  border-radius: 16px;
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  color: #6b7280;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.modal-close:hover {
  background: #f3f4f6;
  color: #111827;
}

.modal-close svg {
  width: 20px;
  height: 20px;
}

.modal-body {
  padding: 24px;
  flex: 1;
  overflow-y: auto;
}

.product-image-section {
  margin-bottom: 24px;
}

.image-carousel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.carousel-main {
  position: relative;
  width: 100%;
  height: 300px;
  border-radius: 12px;
  overflow: hidden;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
}

.carousel-main img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.carousel-main-image {
  cursor: pointer;
  transition: transform 0.2s;
}

.carousel-main-image:hover {
  transform: scale(1.02);
}

.sold-out-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  background: linear-gradient(135deg, #D32F2F 0%, #B71C1C 100%);
  color: white;
  padding: 8px 16px;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(211, 47, 47, 0.4);
  z-index: 20;
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

.carousel-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(255, 255, 255, 0.9);
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 10;
}

.carousel-btn:hover {
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}

.carousel-btn svg {
  width: 20px;
  height: 20px;
  color: #374151;
}

.carousel-btn-prev {
  left: 12px;
}

.carousel-btn-next {
  right: 12px;
}

.carousel-indicator {
  position: absolute;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
}

.carousel-thumbnails {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 4px 0;
  scrollbar-width: thin;
}

.carousel-thumbnails::-webkit-scrollbar {
  height: 4px;
}

.carousel-thumbnails::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 2px;
}

.thumbnail {
  flex-shrink: 0;
  width: 60px;
  height: 60px;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
  opacity: 0.6;
}

.thumbnail:hover {
  opacity: 0.8;
  border-color: #6366f1;
}

.thumbnail.active {
  opacity: 1;
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-image {
  width: 100%;
  height: 300px;
  border-radius: 12px;
  overflow: hidden;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.3;
  color: #6b7280;
}

.image-placeholder svg {
  width: 64px;
  height: 64px;
}

.product-info-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.product-name {
  font-size: 24px;
  font-weight: 600;
  color: #111827;
  margin: 0;
  line-height: 1.3;
}

.product-price-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.price-label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.price-value {
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
}

.sale-price {
  font-size: 28px;
  color: #FF4444;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.original-price {
  font-size: 16px;
  color: #9ca3af;
  text-decoration: line-through;
}

.price-note {
  font-size: 14px;
  color: #6b7280;
}

.bundled-price-display {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.package-price {
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
}

.unit-price {
  display: flex;
  align-items: baseline;
  gap: 4px;
  font-size: 14px;
  color: #6b7280;
}

.unit-price-label {
  font-weight: 500;
}

.unit-price-value {
  font-weight: 600;
  color: #374151;
}

.unit-price-unit {
  color: #6b7280;
}

/* Weight Range Pricing Styles */
.weight-range-pricing,
.unit-weight-pricing,
.bundled-weight-pricing {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.pricing-header {
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
}

.pricing-breakdown {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.breakdown-title {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 4px;
}

.weight-ranges-table {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.range-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
}

.range-row:hover {
  border-color: #FF4444;
  box-shadow: 0 2px 4px rgba(255, 68, 68, 0.1);
}

.range-weight {
  display: flex;
  align-items: center;
  gap: 8px;
}

.range-icon {
  width: 16px;
  height: 16px;
  color: #6b7280;
  flex-shrink: 0;
}

.weight-text {
  font-size: 14px;
  color: #374151;
  font-weight: 500;
}

.range-price {
  font-size: 16px;
  font-weight: 700;
  color: #FF4444;
}

.calculation-formula {
  background: white;
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #e5e7eb;
}

.formula-line {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.formula-label {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.formula-value {
  font-size: 14px;
  color: #6b7280;
  font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
}

.pricing-examples {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.example-title {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 4px;
}

.example-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.example-weight {
  font-size: 14px;
  color: #374151;
  font-weight: 500;
  min-width: 60px;
}

.example-arrow {
  color: #9ca3af;
  font-weight: 600;
}

.example-price {
  font-size: 15px;
  font-weight: 700;
  color: #FF4444;
  margin-left: auto;
}

.bundled-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.info-item {
  background: white;
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #e5e7eb;
}

.info-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 6px;
  font-weight: 500;
}

.info-value {
  font-size: 15px;
  color: #111827;
  font-weight: 600;
}

.pricing-note {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 8px;
  margin-top: 4px;
}

.note-icon {
  width: 16px;
  height: 16px;
  color: #f59e0b;
  flex-shrink: 0;
  margin-top: 1px;
}

.pricing-note span {
  font-size: 13px;
  color: #92400e;
  line-height: 1.4;
}

@media (max-width: 480px) {
  .bundled-price-display {
    gap: 6px;
  }
  
  .package-price {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .sale-price {
    font-size: 24px;
  }
  
  .unit-price {
    font-size: 12px;
  }
  
  .pricing-breakdown {
    padding: 12px;
  }
  
  .range-row {
    padding: 8px 10px;
  }
  
  .weight-text {
    font-size: 13px;
  }
  
  .range-price {
    font-size: 15px;
  }
  
  .bundled-info-grid {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  
  .example-row {
    padding: 6px 10px;
  }
  
  .formula-line {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}

.product-description-section,
.product-stock-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-label {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.product-description {
  font-size: 16px;
  color: #374151;
  line-height: 1.6;
  margin: 0;
  white-space: pre-wrap;
}

.stock-info {
  font-size: 16px;
  color: #374151;
  margin: 0;
}

/* Transitions */
.modal-enter-active, .modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.modal-enter-from, .modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
  opacity: 0;
}

/* Full Screen Image Viewer */
.fullscreen-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  padding: 20px;
}

.fullscreen-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fullscreen-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  user-select: none;
}

.fullscreen-close {
  position: absolute;
  top: 20px;
  right: 20px;
  background: rgba(255, 255, 255, 0.9);
  border: none;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  z-index: 10001;
}

.fullscreen-close:hover {
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  transform: scale(1.1);
}

.fullscreen-close svg {
  width: 24px;
  height: 24px;
  color: #111827;
}

.fullscreen-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(255, 255, 255, 0.9);
  border: none;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  z-index: 10001;
}

.fullscreen-btn:hover {
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  transform: translateY(-50%) scale(1.1);
}

.fullscreen-btn svg {
  width: 28px;
  height: 28px;
  color: #111827;
}

.fullscreen-btn-prev {
  left: 20px;
}

.fullscreen-btn-next {
  right: 20px;
}

.fullscreen-indicator {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

/* Fullscreen transitions */
.fullscreen-enter-active, .fullscreen-leave-active {
  transition: opacity 0.3s ease;
}

.fullscreen-enter-active .fullscreen-container,
.fullscreen-leave-active .fullscreen-container {
  transition: transform 0.3s ease;
}

.fullscreen-enter-from, .fullscreen-leave-to {
  opacity: 0;
}

.fullscreen-enter-from .fullscreen-container,
.fullscreen-leave-to .fullscreen-container {
  transform: scale(0.9);
}
</style>

