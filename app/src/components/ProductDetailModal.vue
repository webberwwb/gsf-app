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
                  <span v-if="product.original_price && product.original_price > (product.deal_price || product.display_price || product.price)" class="original-price">
                    ${{ product.original_price }}
                  </span>
                </template>
                <template v-else-if="product.pricing_type === 'weight_range'">
                  <span class="sale-price">{{ formatPriceRange(product) }}</span>
                  <span class="price-note">按重量区间</span>
                </template>
                <template v-else-if="product.pricing_type === 'unit_weight'">
                  <span class="sale-price">${{ product.pricing_data?.price_per_unit || product.price }}</span>
                  <span class="price-note">/ {{ product.pricing_data?.unit === 'kg' ? 'kg' : 'lb' }}</span>
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
      if (product.deal_price) {
        return parseFloat(product.deal_price).toFixed(2)
      }
      if (product.display_price) {
        return parseFloat(product.display_price).toFixed(2)
      }
      if (product.sale_price) {
        return parseFloat(product.sale_price).toFixed(2)
      }
      if (product.price) {
        return parseFloat(product.price).toFixed(2)
      }
      return '0.00'
    },
    formatPriceRange(product) {
      if (product.pricing_type === 'weight_range') {
        const ranges = product.pricing_data?.ranges || []
        if (ranges.length === 0) {
          if (product.deal_price) {
            return `$${parseFloat(product.deal_price).toFixed(2)}`
          }
          return '价格待定'
        }
        
        const sortedRanges = [...ranges].sort((a, b) => (a.min || 0) - (b.min || 0))
        const prices = sortedRanges
          .map(r => parseFloat(r.price || 0))
          .filter(p => p > 0)
        
        if (prices.length === 0) {
          if (product.deal_price) {
            return `$${parseFloat(product.deal_price).toFixed(2)}`
          }
          return '价格待定'
        }
        
        const minPrice = Math.min(...prices)
        const maxPrice = Math.max(...prices)
        
        if (minPrice === maxPrice) {
          return `$${minPrice.toFixed(2)}`
        }
        return `$${minPrice.toFixed(2)} - $${maxPrice.toFixed(2)}`
      } else if (product.pricing_type === 'unit_weight') {
        const pricePerUnit = product.pricing_data?.price_per_unit || 0
        const unit = product.pricing_data?.unit || 'kg'
        
        if (pricePerUnit === 0) {
          if (product.deal_price) {
            return `$${parseFloat(product.deal_price).toFixed(2)}/${unit}`
          }
          return '价格待定'
        }
        
        return `$${parseFloat(pricePerUnit).toFixed(2)}/${unit}`
      }
      return '价格待定'
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

