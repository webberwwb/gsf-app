<template>
  <div class="checkout-page">
    <header class="page-header">
      <button @click="$router.back()" class="back-btn">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1>确认订单</h1>
      <div class="header-spacer"></div>
    </header>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="checkout-content">
      <!-- Order Summary -->
      <div class="order-summary-section">
        <h3 class="section-title">订单摘要</h3>
        <div v-if="deal" class="deal-info">
          <h4>{{ deal.title }}</h4>
          <p class="deal-date">取货日期: {{ formatDate(deal.pickup_date) }}</p>
        </div>
        <div class="products-section">
          <div class="items-list">
          <div v-for="item in orderItems" :key="item.product_id" class="order-item-summary">
            <div class="item-info">
              <span class="item-name">{{ getProductName(item.product_id) }}</span>
              <span class="item-quantity">x{{ item.quantity }}</span>
            </div>
            <span class="item-price">${{ item.estimated_price || '0.00' }}</span>
          </div>
          </div>
        </div>
        <div class="order-total">
          <span class="total-label">{{ hasEstimatedTotal ? '预估总计' : '总计' }}:</span>
          <span class="total-amount">${{ calculateTotal() }}</span>
        </div>
      </div>

      <!-- Delivery Method Selection -->
      <div class="delivery-section">
        <h3 class="section-title">取货方式</h3>
        <div class="delivery-options">
          <button 
            @click="deliveryMethod = 'pickup'" 
            :class="['delivery-option', { active: deliveryMethod === 'pickup' }]"
          >
            <div class="option-icon">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <div class="option-content">
              <h4>自取</h4>
              <p>到指定地点自取</p>
            </div>
            <div class="option-check">
              <svg v-if="deliveryMethod === 'pickup'" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </button>

          <button 
            @click="deliveryMethod = 'delivery'" 
            :class="['delivery-option', { active: deliveryMethod === 'delivery' }]"
          >
            <div class="option-icon">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div class="option-content">
              <h4>配送</h4>
              <p>配送到指定地址</p>
            </div>
            <div class="option-check">
              <svg v-if="deliveryMethod === 'delivery'" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </button>
        </div>

        <!-- Address Selection for Delivery -->
        <div v-if="deliveryMethod === 'delivery'" class="address-selection">
          <div v-if="addressesLoading" class="loading-addresses">加载地址中...</div>
          <div v-else-if="addresses.length === 0" class="no-addresses">
            <p>您还没有添加配送地址</p>
            <button @click="goToAddresses" class="add-address-btn">添加地址</button>
          </div>
          <div v-else class="addresses-list">
            <div 
              v-for="address in addresses" 
              :key="address.id"
              @click="selectedAddressId = address.id"
              :class="['address-card', { active: selectedAddressId === address.id }]"
            >
              <div class="address-header">
                <span class="recipient-name">{{ address.recipient_name }}</span>
                <span class="recipient-phone">{{ address.phone }}</span>
                <span v-if="address.is_default" class="default-badge">默认</span>
              </div>
              <div class="address-details">
                <p>{{ address.address_line1 }}</p>
                <p v-if="address.address_line2">{{ address.address_line2 }}</p>
                <p>{{ address.city }}, {{ address.postal_code }}</p>
              </div>
              <div class="address-check">
                <svg v-if="selectedAddressId === address.id" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
            <button @click="goToAddresses" class="add-new-address-btn">+ 添加新地址</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Fixed Bottom Bar -->
    <div v-if="!loading && !error" class="bottom-bar">
      <div class="total-info">
        <span class="total-label">{{ hasEstimatedTotal ? '预估总计' : '总计' }}:</span>
        <span class="total-amount">${{ calculateTotal() }}</span>
      </div>
      <button 
        @click="confirmOrder" 
        :disabled="!canConfirm"
        class="confirm-btn"
      >
        确认订单
      </button>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'

export default {
  name: 'Checkout',
  data() {
    return {
      loading: true,
      error: null,
      deal: null,
      orderItems: [],
      deliveryMethod: 'pickup', // 'pickup' or 'delivery'
      selectedAddressId: null,
      addresses: [],
      addressesLoading: false
    }
  },
  computed: {
    canConfirm() {
      if (this.deliveryMethod === 'delivery') {
        return this.selectedAddressId !== null
      }
      return true
    },
    hasEstimatedTotal() {
      return this.orderItems.some(item => item.is_estimated)
    },
    hasEstimatedTotal() {
      return this.orderItems.some(item => item.is_estimated)
    }
  },
  async mounted() {
    await this.loadCheckoutData()
    if (this.deliveryMethod === 'delivery') {
      await this.loadAddresses()
    }
  },
  watch: {
    deliveryMethod(newVal) {
      if (newVal === 'delivery') {
        this.loadAddresses()
        // Auto-select default address if available
        const defaultAddress = this.addresses.find(addr => addr.is_default)
        if (defaultAddress) {
          this.selectedAddressId = defaultAddress.id
        }
      } else {
        this.selectedAddressId = null
      }
    }
  },
  methods: {
    async loadCheckoutData() {
      this.loading = true
      this.error = null
      try {
        // Get order items from sessionStorage (passed from GroupDealDetail)
        const orderDataStr = sessionStorage.getItem('checkout_order_data')
        if (!orderDataStr) {
          this.error = '订单数据无效，请重新选择商品'
          this.loading = false
          return
        }

        const orderData = JSON.parse(orderDataStr)
        if (!orderData || !orderData.items || !orderData.dealId) {
          this.error = '订单数据无效'
          sessionStorage.removeItem('checkout_order_data')
          this.loading = false
          return
        }

        this.orderItems = orderData.items
        const dealId = orderData.dealId

        // Load deal info
        const response = await apiClient.get(`/group-deals/${dealId}`)
        this.deal = response.data.deal
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || '加载订单信息失败'
        console.error('Failed to load checkout data:', error)
        sessionStorage.removeItem('checkout_order_data')
      } finally {
        this.loading = false
      }
    },
    async loadAddresses() {
      this.addressesLoading = true
      try {
        const response = await apiClient.get('/addresses')
        this.addresses = response.data.addresses || []
        // Auto-select default address
        const defaultAddress = this.addresses.find(addr => addr.is_default)
        if (defaultAddress) {
          this.selectedAddressId = defaultAddress.id
        } else if (this.addresses.length === 1) {
          this.selectedAddressId = this.addresses[0].id
        }
      } catch (error) {
        console.error('Failed to load addresses:', error)
      } finally {
        this.addressesLoading = false
      }
    },
    getProductName(productId) {
      if (!this.deal || !this.deal.products) return '商品'
      const product = this.deal.products.find(p => p.id === productId)
      return product ? product.name : '商品'
    },
    calculateTotal() {
      return this.orderItems.reduce((sum, item) => {
        return sum + parseFloat(item.estimated_price || 0)
      }, 0).toFixed(2)
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
    goToAddresses() {
      this.$router.push('/addresses')
    },
    async confirmOrder() {
      if (!this.canConfirm) {
        return
      }

      try {
        // Prepare order data
        const orderData = {
          group_deal_id: this.deal.id,
          items: this.orderItems.map(item => ({
            product_id: item.product_id,
            quantity: item.quantity,
            pricing_type: item.pricing_type
          })),
          delivery_method: this.deliveryMethod,
          address_id: this.deliveryMethod === 'delivery' ? this.selectedAddressId : null
        }

        // Create order
        const response = await apiClient.post('/orders', orderData)
        
        // Clear checkout data and redirect to orders page
        sessionStorage.removeItem('checkout_order_data')
        alert('订单创建成功！')
        this.$router.push('/orders')
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || '创建订单失败'
        alert(errorMsg)
        console.error('Failed to create order:', error)
      }
    }
  }
}
</script>

<style scoped>
.checkout-page {
  min-height: 100vh;
  background: var(--md-background);
  padding-bottom: calc(80px + env(safe-area-inset-bottom)); /* Space for bottom nav */
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
  justify-content: space-between;
  padding-top: calc(var(--md-spacing-lg) + env(safe-area-inset-top));
  padding-left: var(--md-spacing-md);
  padding-right: var(--md-spacing-md);
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

.page-header h1 {
  font-size: var(--md-headline-size);
  color: white;
  font-weight: 500;
  flex: 1;
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

.checkout-content {
  padding: var(--md-spacing-md);
  transition: padding-bottom 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.order-summary-section,
.delivery-section {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  margin-bottom: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
  animation: fadeInUp 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes fadeInUp {
  0% {
    opacity: 0;
    transform: translateY(20px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

.order-summary-section {
  animation-delay: 0.1s;
  animation-fill-mode: both;
}

.delivery-section {
  animation-delay: 0.2s;
  animation-fill-mode: both;
}

.section-title {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-lg);
  font-weight: 500;
}

.deal-info {
  margin-bottom: var(--md-spacing-md);
  padding-bottom: var(--md-spacing-md);
  border-bottom: 1px solid var(--md-surface-variant);
}

.deal-info h4 {
  font-size: var(--md-body-size);
  font-weight: 600;
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-xs);
}

.deal-date {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.products-section {
  transition: margin-bottom 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
  margin-bottom: var(--md-spacing-md);
}

.order-item-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-sm) 0;
  animation: slideInRight 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  animation-fill-mode: both;
}

.order-item-summary:nth-child(1) { animation-delay: 0.1s; }
.order-item-summary:nth-child(2) { animation-delay: 0.15s; }
.order-item-summary:nth-child(3) { animation-delay: 0.2s; }
.order-item-summary:nth-child(4) { animation-delay: 0.25s; }
.order-item-summary:nth-child(5) { animation-delay: 0.3s; }

@keyframes slideInRight {
  0% {
    opacity: 0;
    transform: translateX(-20px);
  }
  100% {
    opacity: 1;
    transform: translateX(0);
  }
}

.item-info {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  flex: 1;
}

.item-name {
  font-size: var(--md-body-size);
  color: var(--md-on-surface);
}

.item-quantity {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.item-price {
  font-size: var(--md-body-size);
  font-weight: 600;
  color: var(--md-primary);
}

.order-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--md-spacing-md);
  border-top: 2px solid var(--md-primary);
  margin-top: var(--md-spacing-md);
}

.total-label {
  font-size: var(--md-body-size);
  font-weight: 500;
  color: var(--md-on-surface);
}

.total-amount {
  font-size: var(--md-headline-size);
  font-weight: 600;
  color: var(--md-primary);
}

.delivery-options {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.delivery-option {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
  padding: var(--md-spacing-md);
  border: 2px solid var(--md-outline-variant);
  border-radius: var(--md-radius-md);
  background: var(--md-surface);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: left;
  position: relative;
  overflow: hidden;
}

.delivery-option::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 140, 0, 0.1), transparent);
  transition: left 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.delivery-option:hover::before {
  left: 100%;
}

.delivery-option:hover {
  border-color: var(--md-primary);
  background: var(--md-surface-variant);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.delivery-option.active {
  border-color: var(--md-primary);
  background: rgba(255, 140, 0, 0.05);
  box-shadow: 0 4px 12px rgba(255, 140, 0, 0.2);
  animation: optionSelect 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes optionSelect {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.02);
  }
  100% {
    transform: scale(1);
  }
}

.option-icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  color: var(--md-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.delivery-option:hover .option-icon {
  transform: scale(1.1) rotate(5deg);
}

.delivery-option.active .option-icon {
  animation: iconPulse 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.option-icon svg {
  width: 24px;
  height: 24px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.delivery-option.active .option-icon svg {
  filter: drop-shadow(0 2px 4px rgba(255, 140, 0, 0.3));
}

@keyframes iconPulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.15) rotate(-5deg);
  }
  100% {
    transform: scale(1);
  }
}

.option-content {
  flex: 1;
}

.option-content h4 {
  font-size: var(--md-body-size);
  font-weight: 600;
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-xs);
}

.option-content p {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin: 0;
}

.option-check {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  color: var(--md-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.option-check svg {
  width: 20px;
  height: 20px;
  animation: checkmarkPop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes checkmarkPop {
  0% {
    transform: scale(0) rotate(-180deg);
    opacity: 0;
  }
  50% {
    transform: scale(1.2) rotate(10deg);
  }
  100% {
    transform: scale(1) rotate(0deg);
    opacity: 1;
  }
}

.address-selection {
  margin-top: var(--md-spacing-lg);
  padding-top: var(--md-spacing-lg);
  border-top: 1px solid var(--md-surface-variant);
  padding-bottom: var(--md-spacing-md);
  margin-bottom: var(--md-spacing-lg);
}

.loading-addresses,
.no-addresses {
  text-align: center;
  padding: var(--md-spacing-lg);
  color: var(--md-on-surface-variant);
}

.add-address-btn,
.add-new-address-btn {
  margin-top: var(--md-spacing-md);
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  background: var(--md-primary);
  color: white;
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  min-height: 44px; /* Ensure minimum touch target size */
}

.add-address-btn:hover,
.add-new-address-btn:hover {
  background: #FF7F00;
}

.addresses-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
  padding-bottom: var(--md-spacing-md);
}

.address-card {
  position: relative;
  padding: var(--md-spacing-md);
  border: 2px solid var(--md-outline-variant);
  border-radius: var(--md-radius-md);
  background: var(--md-surface);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: visible; /* Changed from hidden to visible to ensure clickable area */
  min-height: 80px; /* Ensure minimum touch target size */
  margin-bottom: var(--md-spacing-sm); /* Extra spacing between cards */
}

.address-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 140, 0, 0.05), transparent);
  transition: left 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.address-card:hover::before {
  left: 100%;
}

.address-card:hover {
  border-color: var(--md-primary);
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.address-card.active {
  border-color: var(--md-primary);
  background: rgba(255, 140, 0, 0.05);
  box-shadow: 0 4px 12px rgba(255, 140, 0, 0.2);
  animation: addressSelect 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes addressSelect {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.02);
  }
  100% {
    transform: scale(1);
  }
}

.address-header {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  margin-bottom: var(--md-spacing-xs);
  flex-wrap: wrap;
}

.recipient-name {
  font-size: var(--md-body-size);
  font-weight: 600;
  color: var(--md-on-surface);
}

.recipient-phone {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.default-badge {
  padding: 0.125rem 0.5rem;
  background: var(--md-primary);
  color: white;
  border-radius: var(--md-radius-xl);
  font-size: var(--md-label-size);
  font-weight: 500;
}

.address-details {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  line-height: 1.5;
}

.address-details p {
  margin: 0;
}

.address-check {
  position: absolute;
  top: var(--md-spacing-md);
  right: var(--md-spacing-md);
  width: 28px;
  height: 28px;
  color: var(--md-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 140, 0, 0.1);
  border-radius: 50%;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.address-card.active .address-check {
  background: rgba(255, 140, 0, 0.2);
  animation: checkmarkCircle 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.address-check svg {
  width: 20px;
  height: 20px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.address-card.active .address-check svg {
  animation: checkmarkDraw 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
  filter: drop-shadow(0 2px 4px rgba(255, 140, 0, 0.4));
}

@keyframes checkmarkCircle {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes checkmarkDraw {
  0% {
    opacity: 0;
    transform: scale(0.3) rotate(-45deg);
  }
  50% {
    opacity: 1;
    transform: scale(1.2) rotate(5deg);
  }
  100% {
    opacity: 1;
    transform: scale(1) rotate(0deg);
  }
}

.bottom-bar {
  position: fixed;
  bottom: calc(80px + env(safe-area-inset-bottom));
  left: 0;
  right: 0;
  background: var(--md-surface);
  padding: var(--md-spacing-md);
  box-shadow: var(--md-elevation-4);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--md-spacing-md);
  z-index: 99;
  padding-bottom: calc(var(--md-spacing-md) + env(safe-area-inset-bottom));
  min-height: 80px; /* Ensure consistent height */
}

.total-info {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-xs);
}

.total-label {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.total-amount {
  font-size: var(--md-headline-size);
  font-weight: 600;
  color: var(--md-primary);
}

.confirm-btn {
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
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
  position: relative;
  overflow: hidden;
}

.confirm-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s;
}

.confirm-btn:not(:disabled):hover::before {
  width: 300px;
  height: 300px;
}

.confirm-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.confirm-btn:not(:disabled):hover {
  background: #FF7F00;
  box-shadow: 0 4px 12px rgba(255, 140, 0, 0.4);
  transform: translateY(-2px);
}

.confirm-btn:not(:disabled):active {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(255, 140, 0, 0.3);
}

@media (max-width: 480px) {
  .confirm-btn {
    padding: var(--md-spacing-sm) var(--md-spacing-md);
    font-size: var(--md-label-size);
  }
  
  .total-amount {
    font-size: var(--md-title-size);
  }
}
</style>

