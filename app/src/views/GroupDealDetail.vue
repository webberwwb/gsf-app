<template>
  <div class="deal-detail-page">
    <header class="page-header">
      <button @click="$router.back()" class="back-btn">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <div class="header-center">
        <h1>团购详情</h1>
      </div>
      <div class="header-spacer"></div>
    </header>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="deal" class="deal-content">
      <!-- Deal Info Section -->
      <div class="deal-info-section">
        <div class="deal-header">
          <h2>{{ deal.title }}</h2>
          <span :class="['deal-badge', deal.status]">
            {{ getStatusLabel(deal.status) }}
          </span>
        </div>
        <p v-if="deal.description" class="deal-description">{{ deal.description }}</p>
        
        <div class="deal-dates">
          <div class="date-row">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="date-icon">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <div class="date-info">
              <span class="date-label">下单时间</span>
              <span class="date-value">{{ formatDate(deal.order_start_date) }} - {{ formatDate(deal.order_end_date) }}</span>
            </div>
          </div>
          <div class="date-row">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="date-icon">
              <path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
            <div class="date-info">
              <span class="date-label">取货日期</span>
              <span class="date-value">{{ formatDate(deal.pickup_date) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Products Section -->
      <div class="products-section">
        <h3 class="section-title">可选商品</h3>
        
        <div v-if="deal.products && deal.products.length === 0" class="empty-products">
          <p>暂无商品</p>
        </div>
        <div v-else class="products-list">
          <div
            v-for="product in deal.products"
            :key="product.id"
            class="product-item"
          >
            <div class="product-image" @click="openProductModal(product)">
              <img v-if="getProductImage(product)" :src="getProductImage(product)" :alt="product.name" />
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
            <div class="product-details">
              <div class="product-name-row">
                <h4 class="product-name" @click="openProductModal(product)">{{ product.name }}</h4>
                <span v-if="product.counts_toward_free_shipping === false" class="shipping-excluded-badge">
                  不计入免运
                </span>
              </div>
              <p v-if="product.description" class="product-description-preview" @click="openProductModal(product)">
                {{ product.description.length > 80 ? product.description.substring(0, 80) + '...' : product.description }}
              </p>
              
              <!-- Price Display -->
              <div class="product-price">
                <span class="price-label">团购价:</span>
                <span v-if="product.pricing_type === 'bundled_weight'" class="price-value">
                  ${{ (product.pricing_data?.price_per_unit || 0).toFixed(2) }}/{{ product.pricing_data?.unit === 'kg' ? 'kg' : 'lb' }}
                </span>
                <span v-else-if="product.pricing_type === 'weight_range' || product.pricing_type === 'unit_weight'" class="price-value price-range">
                  {{ formatPriceRange(product) }}
                </span>
                <span v-else class="price-value">${{ formatPrice(product) }}</span>
                <span v-if="product.original_price && product.original_price > (product.deal_price || product.display_price) && product.pricing_type === 'per_item'" class="original-price">
                  ${{ product.original_price }}
                </span>
              </div>
              <!-- Debug: Remove after testing -->
              <!-- <div style="font-size: 10px; color: gray;">
                Type: {{ product.pricing_type }}, 
                Has ranges: {{ product.pricing_data?.ranges ? 'yes' : 'no' }},
                Deal price: {{ product.deal_price }}
              </div> -->

              <!-- Stock Info -->
              <div v-if="product.deal_stock_limit !== undefined && product.deal_stock_limit !== null" class="stock-info" :class="{ 'out-of-stock': isOutOfStock(product) }">
                <span v-if="isOutOfStock(product)">缺货</span>
                <span v-else>库存: {{ product.deal_stock_limit }} 件</span>
              </div>
              <div v-else-if="product.stock_limit !== undefined && product.stock_limit !== null && product.stock_limit === 0" class="stock-info out-of-stock">
                <span>缺货</span>
              </div>

              <!-- Product Selection Controls -->
              <div class="product-selection" :class="{ 'disabled': isOutOfStock(product) }">
                <!-- Per Item Pricing -->
                <div v-if="product.pricing_type === 'per_item'" class="selection-controls">
                  <div class="quantity-control">
                    <button @click="decreaseQuantity(product)" :disabled="getQuantity(product) === 0 || !isOrderEditable || isOutOfStock(product)" class="qty-btn">-</button>
                    <input
                      type="number"
                      :value="getQuantity(product)"
                      @input="setQuantity(product, $event.target.value)"
                      min="0"
                      :max="product.deal_stock_limit || 999"
                      :disabled="!isOrderEditable || isOutOfStock(product)"
                      class="qty-input"
                    />
                    <button @click="increaseQuantity(product)" :disabled="(product.deal_stock_limit && getQuantity(product) >= product.deal_stock_limit) || !isOrderEditable || isOutOfStock(product)" class="qty-btn">+</button>
                  </div>
                  <div class="item-total">
                    小计: ${{ calculateItemTotal(product) }}
                  </div>
                </div>

                <!-- Weight Range Pricing -->
                <div v-else-if="product.pricing_type === 'weight_range'" class="selection-controls">
                  <div class="quantity-control">
                    <label>数量:</label>
                    <button @click="decreaseQuantity(product)" :disabled="getQuantity(product) === 0 || !isOrderEditable || isOutOfStock(product)" class="qty-btn">-</button>
                    <input
                      type="number"
                      :value="getQuantity(product)"
                      @input="setQuantity(product, $event.target.value)"
                      min="0"
                      :disabled="!isOrderEditable || isOutOfStock(product)"
                      class="qty-input"
                    />
                    <button @click="increaseQuantity(product)" :disabled="!isOrderEditable || isOutOfStock(product)" class="qty-btn">+</button>
                  </div>
                  <div class="item-total estimated">
                    <span>预估小计: ${{ calculateItemTotal(product) }}</span>
                    <div class="tooltip-container" @click.stop="showPriceInfo('价格基于中等重量估算，实际价格可能因实际重量而有所不同，取货时确认最终价格')">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="info-icon">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                  </div>
                </div>

                <!-- Unit Weight Pricing -->
                <div v-else-if="product.pricing_type === 'unit_weight'" class="selection-controls">
                  <div class="quantity-control">
                    <label>数量:</label>
                    <button @click="decreaseQuantity(product)" :disabled="getQuantity(product) === 0 || !isOrderEditable || isOutOfStock(product)" class="qty-btn">-</button>
                    <input
                      type="number"
                      :value="getQuantity(product)"
                      @input="setQuantity(product, $event.target.value)"
                      min="0"
                      :disabled="!isOrderEditable || isOutOfStock(product)"
                      class="qty-input"
                    />
                    <button @click="increaseQuantity(product)" :disabled="!isOrderEditable || isOutOfStock(product)" class="qty-btn">+</button>
                  </div>
                  <div class="item-total estimated">
                    <span>预估小计: ${{ calculateItemTotal(product) }}</span>
                    <div class="tooltip-container" @click="showPriceInfo('价格基于中等重量估算，实际价格可能因实际重量而有所不同，取货时确认最终价格')">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="info-icon">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                  </div>
                </div>

                <!-- Bundled Weight Pricing -->
                <div v-else-if="product.pricing_type === 'bundled_weight'" class="selection-controls">
                  <div class="quantity-control">
                    <label>份数:</label>
                    <button @click="decreaseQuantity(product)" :disabled="getQuantity(product) === 0 || !isOrderEditable || isOutOfStock(product)" class="qty-btn">-</button>
                    <input
                      type="number"
                      :value="getQuantity(product)"
                      @input="setQuantity(product, $event.target.value)"
                      min="0"
                      step="1"
                      :disabled="!isOrderEditable || isOutOfStock(product)"
                      class="qty-input"
                    />
                    <button @click="increaseQuantity(product)" :disabled="!isOrderEditable || isOutOfStock(product)" class="qty-btn">+</button>
                  </div>
                  <div class="package-info-wrapper">
                    <span class="package-info">(每份 {{ product.pricing_data?.min_weight || 7 }}-{{ product.pricing_data?.max_weight || 15 }}{{ product.pricing_data?.unit === 'kg' ? 'kg' : 'lb' }})</span>
                  </div>
                  <div class="item-total estimated">
                    <span>预估小计: {{ calculateBundledItemTotal(product) }}</span>
                    <div class="tooltip-container" @click="showPriceInfo('价格基于每份重量范围估算，实际价格可能因实际重量而有所不同，取货时确认最终价格')">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="info-icon">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Fixed Bottom Bar -->
    <div v-if="deal && hasSelectedItems()" class="bottom-bar">
      <div class="total-info">
        <span class="total-label">{{ isOrderCompleted ? '最终价格' : (hasEstimatedTotal() ? '预估总计' : '总计') }}:</span>
        <span class="total-amount">${{ calculateTotal().total }}</span>
        <span v-if="hasEstimatedTotal() && !isOrderCompleted" class="estimated-note">(估算)</span>
      </div>
      <button @click="confirmOrder" class="confirm-order-btn" :disabled="isDealClosed">
        {{ isDealClosed ? '已截单' : '确认订单' }}
      </button>
    </div>

    <!-- Product Detail Modal -->
    <ProductDetailModal
      :show="showProductModal"
      :product="selectedProduct"
      @close="closeProductModal"
    />

    <!-- Price Info Modal -->
    <Modal
      :show="showPriceInfoModal"
      type="info"
      title="价格说明"
      :message="priceInfoMessage"
      :showCancel="false"
      :icon="true"
      confirmText="知道了"
      @confirm="closePriceInfoModal"
      @close="closePriceInfoModal"
    />
  </div>
</template>

<script>
import apiClient from '../api/client'
import { useCheckoutStore } from '../stores/checkout'
import { useAuthStore } from '../stores/auth'
import { formatDateEST_CN } from '../utils/date'
import { useModal } from '../composables/useModal'
import ProductDetailModal from '../components/ProductDetailModal.vue'
import Modal from '../components/Modal.vue'

export default {
  name: 'GroupDealDetail',
  components: {
    ProductDetailModal,
    Modal
  },
  data() {
    return {
      loading: true,
      error: null,
      deal: null,
      selectedItems: {}, // { productId: { quantity } }
      showProductModal: false,
      selectedProduct: null,
      showPriceInfoModal: false,
      priceInfoMessage: ''
    }
  },
  setup() {
    const checkoutStore = useCheckoutStore()
    const authStore = useAuthStore()
    const { warning, error: showError } = useModal()
    return { checkoutStore, authStore, warning, showError }
  },
  computed: {
    isAuthenticated() {
      return this.authStore.isAuthenticated
    }
  },
  async mounted() {
    // Load auth from storage if not already loaded
    // This allows guest browsing - no forced authentication
    if (!this.authStore.token) {
      this.authStore.loadFromStorage()
    }
    
    // Debug: Log auth status
    console.log('GroupDealDetail mounted - isAuthenticated:', this.isAuthenticated, 'token:', !!this.authStore.token)
    
    await this.loadDeal()
  },
  computed: {
    isDealClosed() {
      return this.deal && this.deal.status === 'closed'
    },
    isOrderEditable() {
      // Always allow editing if deal is not closed
      return !this.isDealClosed
    }
  },
  methods: {
    async loadDeal() {
      this.loading = true
      this.error = null
      try {
        const dealId = this.$route.params.id
        const response = await apiClient.get(`/group-deals/${dealId}`)
        this.deal = response.data.deal
        
        // Initialize selected items - always start clean
        if (this.deal.products) {
          this.deal.products.forEach(product => {
            this.selectedItems[product.id] = {
              quantity: 0
            }
          })
        }
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || '加载团购详情失败'
        console.error('Failed to load deal:', error)
      } finally {
        this.loading = false
      }
    },
    formatDate(dateString) {
      // This shows date only, not datetime
      return formatDateEST_CN(dateString)
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
      return '0.00'
    },
    formatPriceRange(product) {
      if (product.pricing_type === 'weight_range') {
        const ranges = product.pricing_data?.ranges || []
        if (ranges.length === 0) {
          // Fallback to deal_price if no ranges
          if (product.deal_price) {
            return `$${parseFloat(product.deal_price).toFixed(2)}`
          }
          return '价格待定'
        }
        
        // Sort ranges by min weight
        const sortedRanges = [...ranges].sort((a, b) => (a.min || 0) - (b.min || 0))
        
        // Get min and max prices from ranges
        const prices = sortedRanges
          .map(r => parseFloat(r.price || 0))
          .filter(p => p > 0) // Filter out invalid prices
        
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
          // Fallback to deal_price if no price_per_unit
          if (product.deal_price) {
            return `$${parseFloat(product.deal_price).toFixed(2)}/${unit}`
          }
          return '价格待定'
        }
        
        // Show price per unit
        return `$${parseFloat(pricePerUnit).toFixed(2)}/${unit}`
      } else if (product.pricing_type === 'bundled_weight') {
        const pricePerUnit = product.pricing_data?.price_per_unit || 0
        const minWeight = product.pricing_data?.min_weight || 7
        const maxWeight = product.pricing_data?.max_weight || 15
        const unit = product.pricing_data?.unit || 'lb'
        
        if (pricePerUnit === 0) {
          if (product.deal_price) {
            return `$${parseFloat(product.deal_price).toFixed(2)}/份`
          }
          return '价格待定'
        }
        
        const minPrice = pricePerUnit * minWeight
        const maxPrice = pricePerUnit * maxWeight
        const unitPriceDisplay = `$${pricePerUnit.toFixed(2)}/${unit}`
        
        if (minPrice === maxPrice) {
          return `$${minPrice.toFixed(2)}/份 (${minWeight}-${maxWeight}${unit}/份) · ${unitPriceDisplay}`
        }
        return `$${minPrice.toFixed(2)} - $${maxPrice.toFixed(2)}/份 (${minWeight}-${maxWeight}${unit}/份) · ${unitPriceDisplay}`
      }
      return '价格待定'
    },
    getStatusLabel(status) {
      const labels = {
        'upcoming': '即将开始',
        'active': '进行中',
        'closed': '已截单',
        'completed': '已完成'
      }
      return labels[status] || status
    },
    getQuantity(product) {
      return this.selectedItems[product.id]?.quantity || 0
    },
    setQuantity(product, value) {
      // Check if product is out of stock
      if (this.isOutOfStock(product)) {
        return
      }
      
      const qty = parseInt(value) || 0
      const maxQty = product.deal_stock_limit || 999
      const finalQty = Math.max(0, Math.min(qty, maxQty))
      
      // Vue 3 handles reactivity automatically, no need for $set
      if (!this.selectedItems[product.id]) {
        this.selectedItems[product.id] = { quantity: 0 }
      }
      this.selectedItems[product.id].quantity = finalQty
    },
    increaseQuantity(product) {
      // Check if product is out of stock
      if (this.isOutOfStock(product)) {
        return
      }
      
      const current = this.getQuantity(product)
      const maxQty = product.deal_stock_limit || 999
      this.setQuantity(product, Math.min(current + 1, maxQty))
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
    decreaseQuantity(product) {
      const current = this.getQuantity(product)
      this.setQuantity(product, Math.max(current - 1, 0))
    },
    calculateItemTotal(product) {
      const quantity = this.getQuantity(product)
      if (quantity === 0) return '0.00'
      
      if (product.pricing_type === 'per_item') {
        const price = product.deal_price || product.display_price || product.sale_price || 0
        return (parseFloat(price) * quantity).toFixed(2)
      } else if (product.pricing_type === 'weight_range') {
        // Use LOWEST price for estimation (conservative estimate)
        const ranges = product.pricing_data?.ranges || []
        if (ranges.length === 0) return '0.00'
        
        // Find the minimum price across all ranges for conservative estimate
        const minPrice = Math.min(...ranges.map(r => parseFloat(r.price || 0)))
        
        return (minPrice * quantity).toFixed(2)
      } else if (product.pricing_type === 'unit_weight') {
        // Use a default estimated weight (1 unit) for estimation
        const pricePerUnit = product.pricing_data?.price_per_unit || 0
        const estimatedWeight = 1 // Default 1 unit (kg or lb) for estimation
        return (parseFloat(pricePerUnit) * estimatedWeight * quantity).toFixed(2)
      } else if (product.pricing_type === 'bundled_weight') {
        // quantity = number of packages
        // Use mid-weight (average) for estimation
        const pricePerUnit = product.pricing_data?.price_per_unit || 0
        const minWeight = product.pricing_data?.min_weight || 7
        const maxWeight = product.pricing_data?.max_weight || 15
        const midWeight = (minWeight + maxWeight) / 2
        
        if (pricePerUnit === 0) return '0.00'
        
        // Return single estimated price using mid-weight
        return (pricePerUnit * midWeight * quantity).toFixed(2)
      }
      return '0.00'
    },
    calculateBundledItemTotal(product) {
      const quantity = this.getQuantity(product)
      if (quantity === 0) return '$0.00'
      
      // quantity = number of packages
      const pricePerUnit = product.pricing_data?.price_per_unit || 0
      const minWeight = product.pricing_data?.min_weight || 7
      const maxWeight = product.pricing_data?.max_weight || 15
      
      if (pricePerUnit === 0) return '$0.00'
      
      const minPrice = pricePerUnit * minWeight * quantity
      const maxPrice = pricePerUnit * maxWeight * quantity
      
      if (minPrice === maxPrice) {
        return `$${minPrice.toFixed(2)}`
      }
      return `$${minPrice.toFixed(2)} - $${maxPrice.toFixed(2)}`
    },
    calculateTotal() {
      if (!this.deal || !this.deal.products) return '0.00'
      
      let total = 0
      let hasEstimatedItems = false
      this.deal.products.forEach(product => {
        const itemTotal = parseFloat(this.calculateItemTotal(product))
        total += itemTotal
        if (itemTotal > 0 && (product.pricing_type === 'weight_range' || product.pricing_type === 'unit_weight' || product.pricing_type === 'bundled_weight')) {
          hasEstimatedItems = true
        }
      })
      return { total: total.toFixed(2), hasEstimated: hasEstimatedItems }
    },
    hasSelectedItems() {
      return Object.values(this.selectedItems).some(item => item.quantity > 0)
    },
    hasEstimatedTotal() {
      const result = this.calculateTotal()
      return result.hasEstimated
    },
    async confirmOrder() {
      // Build order items from current selections
      const orderItems = []
      
      this.deal.products.forEach(product => {
        const selection = this.selectedItems[product.id]
        if (selection && selection.quantity > 0) {
          // Calculate estimated price for this item
          const quantity = selection.quantity
          let estimatedPrice = 0
          let isEstimated = false
          
          if (product.pricing_type === 'per_item') {
            const price = product.deal_price || product.display_price || product.sale_price || 0
            estimatedPrice = parseFloat(price) * quantity
          } else if (product.pricing_type === 'weight_range') {
            // Use LOWEST price for estimation (conservative estimate)
            const ranges = product.pricing_data?.ranges || []
            if (ranges.length > 0) {
              const minPrice = Math.min(...ranges.map(r => parseFloat(r.price || 0)))
              estimatedPrice = minPrice * quantity
              isEstimated = true
            }
          } else if (product.pricing_type === 'unit_weight') {
            // Use a default estimated weight (1 unit) for estimation
            const pricePerUnit = product.pricing_data?.price_per_unit || 0
            const estimatedWeight = 1 // Default 1 unit (kg or lb) for estimation
            estimatedPrice = parseFloat(pricePerUnit) * estimatedWeight * quantity
            isEstimated = true
          } else if (product.pricing_type === 'bundled_weight') {
            // quantity = number of packages
            // Use mid-weight (average) for estimation
            const pricePerUnit = product.pricing_data?.price_per_unit || 0
            const minWeight = product.pricing_data?.min_weight || 7
            const maxWeight = product.pricing_data?.max_weight || 15
            const midWeight = (minWeight + maxWeight) / 2
            estimatedPrice = parseFloat(pricePerUnit) * midWeight * quantity
            isEstimated = true
          }
          
          orderItems.push({
            product_id: product.id,
            quantity: selection.quantity,
            pricing_type: product.pricing_type,
            estimated_price: estimatedPrice.toFixed(2),
            is_estimated: isEstimated,
            counts_toward_free_shipping: product.counts_toward_free_shipping !== undefined 
              ? product.counts_toward_free_shipping 
              : true
          })
        }
      })
      
      if (orderItems.length === 0) {
        await this.warning('请至少选择一个商品')
        return
      }
      
      // Store data in Pinia store for checkout page
      this.checkoutStore.setDeal(this.deal)
      this.checkoutStore.setOrderItems(orderItems)
      
      // Clear existing order data - always create new order
      this.checkoutStore.setExistingOrder(null, null, null)
      
      // Navigate to checkout page - it will use the store data
      this.$router.push('/checkout')
    },
    openProductModal(product) {
      this.selectedProduct = product
      this.showProductModal = true
    },
    closeProductModal() {
      this.showProductModal = false
      this.selectedProduct = null
    },
    showPriceInfo(message) {
      this.priceInfoMessage = message
      this.showPriceInfoModal = true
    },
    closePriceInfoModal() {
      this.showPriceInfoModal = false
      this.priceInfoMessage = ''
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
.deal-detail-page {
  min-height: 100vh;
  background: var(--md-background);
  padding-bottom: calc(80px + env(safe-area-inset-bottom)); /* Space for bottom nav */
}

.page-header {
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  padding: var(--md-spacing-lg);
  padding-top: calc(var(--md-spacing-lg) + env(safe-area-inset-top));
  box-shadow: var(--md-elevation-2);
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
}

.back-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  padding: var(--md-spacing-xs);
  cursor: pointer;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--md-radius-sm);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
  width: 40px;
  height: 40px;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.back-btn svg {
  width: 24px;
  height: 24px;
  color: white;
}

.header-spacer {
  width: 40px;
  flex-shrink: 0;
}

.header-center {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--md-spacing-sm);
}

.header-logo {
  width: 32px;
  height: 32px;
  object-fit: contain;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.15));
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

.deal-content {
  padding: var(--md-spacing-md);
  padding-bottom: 150px;
}

.deal-info-section {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  margin-bottom: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.deal-info-section:hover {
  box-shadow: var(--md-elevation-2);
}

.deal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--md-spacing-md);
  gap: var(--md-spacing-sm);
  flex-wrap: wrap;
}

@media (max-width: 480px) {
  .deal-header h2 {
    font-size: var(--md-title-size);
  }
  
  .deal-badge {
    font-size: 0.75rem;
    padding: 4px 8px;
  }
}

.deal-header h2 {
  font-size: var(--md-headline-size);
  color: var(--md-on-surface);
  font-weight: 500;
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

.deal-badge.closed {
  background: #FFF3E0;
  color: #F57C00;
  box-shadow: 0 2px 4px rgba(245, 124, 0, 0.3);
}

.deal-description {
  color: var(--md-on-surface-variant);
  font-size: var(--md-body-size);
  margin-bottom: var(--md-spacing-lg);
  line-height: 1.5;
  white-space: pre-line;
}

.deal-dates {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
}

.date-row {
  display: flex;
  align-items: flex-start;
  gap: var(--md-spacing-md);
}

@media (max-width: 480px) {
  .date-row {
    gap: var(--md-spacing-sm);
  }
  
  .date-value {
    font-size: 0.75rem;
  }
}

.date-icon {
  width: 14px;
  height: 14px;
  color: var(--md-primary);
  flex-shrink: 0;
}

.date-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-xs);
}

.date-label {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.date-value {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  font-weight: 500;
}

.products-section {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.products-section:hover {
  box-shadow: var(--md-elevation-2);
}

.section-title {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-lg);
  font-weight: 500;
}

.empty-products {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.products-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-lg);
}

.product-item {
  display: flex;
  gap: var(--md-spacing-md);
  padding-bottom: var(--md-spacing-lg);
  border-bottom: 1px solid var(--md-surface-variant);
  flex-wrap: wrap;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.product-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.product-image {
  position: relative;
  width: 100px;
  height: 100px;
  flex-shrink: 0;
  border-radius: var(--md-radius-md);
  overflow: hidden;
  background: var(--md-surface-variant);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.product-image:hover {
  transform: scale(1.05);
  box-shadow: var(--md-elevation-2);
}

@media (max-width: 480px) {
  .product-image {
    width: 80px;
    height: 80px;
  }
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
  color: var(--md-on-surface-variant);
}

.image-placeholder svg {
  width: 32px;
  height: 32px;
}

.product-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
}

.product-name-row {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-xs);
  flex-wrap: wrap;
}

.product-name {
  font-size: var(--md-body-size);
  font-weight: 500;
  color: var(--md-on-surface);
  cursor: pointer;
  transition: color 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  margin: 0;
}

.product-name:hover {
  color: var(--md-primary);
}

.shipping-excluded-badge {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  background: #FFF3E0;
  color: #E65100;
  flex-shrink: 0;
}

.product-description-preview {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  line-height: 1.4;
  cursor: pointer;
  transition: color 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: pre-line;
}

.product-description-preview:hover {
  color: var(--md-on-surface);
}

.package-info-wrapper {
  width: 100%;
  margin-top: var(--md-spacing-xs);
}

.package-info {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  white-space: normal;
}

.product-price {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
}

.price-label {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.price-value {
  font-size: var(--md-body-size);
  font-weight: 600;
  color: var(--md-primary);
}

.price-value.price-range {
  white-space: nowrap;
}

.original-price {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  text-decoration: line-through;
}

.stock-info {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin-bottom: var(--md-spacing-xs);
}

.stock-info.out-of-stock {
  color: #D32F2F;
  font-weight: 600;
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


.product-selection.disabled {
  opacity: 0.6;
  pointer-events: none;
}

.product-selection.disabled .quantity-control {
  opacity: 0.5;
}

.product-selection {
  margin-top: var(--md-spacing-sm);
}

.selection-controls {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
  width: 100%;
}

@media (max-width: 480px) {
  .selection-controls {
    gap: var(--md-spacing-xs);
    flex-direction: column;
  }
  
  .quantity-control {
    flex-wrap: wrap;
    gap: var(--md-spacing-xs);
  }
  
  .quantity-control label {
    min-width: auto;
    width: 100%;
  }
  
  .package-info-wrapper {
    margin-top: 2px;
  }
  
  .package-info {
    font-size: 0.75rem;
    line-height: 1.4;
  }
  
  .item-total {
    width: 100%;
    text-align: left;
    flex-wrap: wrap;
  }
  
  .item-total.estimated {
    flex-direction: row;
    align-items: center;
    gap: var(--md-spacing-xs);
  }
  
  .price-value.price-range {
    font-size: 0.9rem;
    line-height: 1.4;
  }
  
  .product-item {
    padding: var(--md-spacing-md);
  }
  
  .product-details {
    gap: var(--md-spacing-sm);
  }
  
  .product-price {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .price-value {
    font-size: 1rem;
  }
  
  .tooltip-container {
    padding: 8px;
    margin-left: 6px;
  }
  
  .info-icon {
    width: 18px;
    height: 18px;
  }
}

.quantity-control {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
}

.quantity-control label {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  min-width: 40px;
}

.qty-btn {
  width: 32px;
  height: 32px;
  border: 1px solid var(--md-outline);
  background: var(--md-surface);
  border-radius: var(--md-radius-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--md-on-surface);
  font-size: 18px;
  font-weight: 500;
}

.qty-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.qty-btn:not(:disabled):hover {
  background: var(--md-surface-variant);
}

.qty-input {
  width: 60px;
  height: 32px;
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-sm);
  text-align: center;
  font-size: var(--md-body-size);
  padding: 0 var(--md-spacing-xs);
}

.weight-input-group {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  flex-wrap: wrap;
}

@media (max-width: 480px) {
  .weight-input-group {
    width: 100%;
  }
  
  .weight-input-group label {
    min-width: 60px;
    font-size: 0.8rem;
  }
  
  .weight-input {
    flex: 1;
    min-width: 80px;
  }
}

.weight-input-group label {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  min-width: 80px;
}

.weight-input {
  flex: 1;
  max-width: 120px;
  height: 32px;
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-sm);
  padding: 0 var(--md-spacing-sm);
  font-size: var(--md-body-size);
}

.unit-label {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  min-width: 30px;
}

.item-total {
  font-size: var(--md-body-size);
  font-weight: 600;
  color: var(--md-primary);
  margin-top: var(--md-spacing-xs);
  display: flex;
  align-items: center;
  gap: var(--md-spacing-xs);
}

.item-total.estimated {
  color: var(--md-on-surface-variant);
}

.tooltip-container {
  position: relative;
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  padding: 4px;
  margin-left: 4px;
  border-radius: 50%;
  transition: background-color 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  -webkit-tap-highlight-color: transparent;
}

.tooltip-container:hover {
  background-color: var(--md-surface-variant);
}

.tooltip-container:active {
  background-color: var(--md-outline-variant);
}

.info-icon {
  width: 16px;
  height: 16px;
  color: var(--md-on-surface-variant);
  flex-shrink: 0;
  opacity: 0.7;
  transition: opacity 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.tooltip-container:hover .info-icon,
.tooltip-container:active .info-icon {
  opacity: 1;
}


.bottom-bar {
  position: fixed;
  bottom: calc(80px + env(safe-area-inset-bottom)); /* Above bottom nav */
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.95);
  padding: var(--md-spacing-md);
  box-shadow: var(--md-elevation-4);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--md-spacing-md);
  z-index: 99;
  padding-bottom: calc(var(--md-spacing-md) + env(safe-area-inset-bottom));
}

.total-info {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-xs);
}

.total-label {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  display: flex;
  align-items: center;
  gap: var(--md-spacing-xs);
}

.total-amount {
  font-size: var(--md-headline-size);
  font-weight: 600;
  color: var(--md-primary);
}

.estimated-note {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  font-weight: 400;
  margin-left: var(--md-spacing-xs);
}

.confirm-order-btn {
  flex: 1;
  max-width: 200px;
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  background: var(--md-primary);
  color: white;
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
}

.confirm-order-btn:disabled {
  background: #4CAF50;
  cursor: default;
  opacity: 1;
}

@media (max-width: 480px) {
  .confirm-order-btn {
    padding: var(--md-spacing-sm) var(--md-spacing-md);
    font-size: var(--md-label-size);
  }
  
  .total-amount {
    font-size: var(--md-title-size);
  }
}

.confirm-order-btn:hover {
  background: #FF7F00;
  box-shadow: var(--md-elevation-2);
}
</style>

