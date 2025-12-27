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

        <!-- Pickup Location Selection -->
        <div v-if="deliveryMethod === 'pickup'" class="pickup-location-selection">
          <h4 class="selection-subtitle">选择自取点</h4>
          <div class="pickup-locations">
            <div 
              @click="selectedPickupLocation = 'markham'"
              :class="['pickup-location-card', { active: selectedPickupLocation === 'markham' }]"
            >
              <div class="location-icon">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <div class="location-content">
                <h5>Markham</h5>
                <p>Woodbine Ave & 16th Avenue</p>
              </div>
              <div class="location-check">
                <svg v-if="selectedPickupLocation === 'markham'" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>

            <div 
              @click="selectedPickupLocation = 'northyork'"
              :class="['pickup-location-card', { active: selectedPickupLocation === 'northyork' }]"
            >
              <div class="location-icon">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <div class="location-content">
                <h5>North York</h5>
                <p>Yorkdale附近</p>
              </div>
              <div class="location-check">
                <svg v-if="selectedPickupLocation === 'northyork'" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        <!-- Address Selection for Delivery -->
        <div v-if="deliveryMethod === 'delivery'" class="address-selection">
          <button @click="openAddressModal" class="select-address-btn">
            <div class="btn-content">
              <div class="btn-icon">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <div class="btn-text">
                <div v-if="selectedAddress" class="selected-address-preview">
                  <div class="preview-header">
                    <span class="preview-name">{{ selectedAddress.recipient_name }}</span>
                    <span class="preview-phone">{{ selectedAddress.phone }}</span>
                  </div>
                  <div class="preview-address">
                    {{ selectedAddress.address_line1 }}, {{ selectedAddress.city }}
                  </div>
                </div>
                <div v-else class="no-address-selected">
                  <span>选择配送地址</span>
                  <span class="hint">点击选择或添加新地址</span>
                </div>
              </div>
              <div class="btn-arrow">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </div>
          </button>
        </div>
      </div>

      <!-- Payment Method Selection -->
      <div class="payment-section">
        <h3 class="section-title">支付方式</h3>
        <div class="payment-options">
          <label 
            :class="['payment-option', { active: paymentMethod === 'cash' }]"
          >
            <input 
              type="radio" 
              name="paymentMethod" 
              value="cash" 
              v-model="paymentMethod"
              class="payment-radio"
            />
            <div class="option-icon">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <div class="option-content">
              <h4>现金</h4>
            </div>
            <div class="option-check">
              <svg v-if="paymentMethod === 'cash'" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </label>

          <label 
            :class="['payment-option', { active: paymentMethod === 'etransfer' }]"
          >
            <input 
              type="radio" 
              name="paymentMethod" 
              value="etransfer" 
              v-model="paymentMethod"
              class="payment-radio"
            />
            <div class="option-icon">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
            </div>
            <div class="option-content">
              <h4>e-transfer</h4>
            </div>
            <div class="option-check">
              <svg v-if="paymentMethod === 'etransfer'" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </label>
        </div>
        <p class="payment-note">取货时根据实际重量支付</p>
      </div>

      <!-- Notes Section -->
      <div class="notes-section">
        <h3 class="section-title">备注</h3>
        <textarea
          v-model="notes"
          placeholder="请输入您的特殊要求或备注（选填）"
          class="notes-input"
          rows="3"
          maxlength="1000"
        ></textarea>
        <p class="notes-hint">{{ notes.length }}/1000</p>
      </div>

      <!-- Confirm Order Button -->
      <div class="confirm-order-section">
        <button 
          @click="confirmOrder" 
          :disabled="!canConfirm"
          class="confirm-order-btn"
        >
          <span class="btn-text">确认订单</span>
          <span class="btn-amount">{{ hasEstimatedTotal ? '预估' : '' }}${{ calculateTotal() }}</span>
        </button>
        <p v-if="hasEstimatedTotal" class="estimate-note">* 最终价格以实际称重为准</p>
      </div>
    </div>

    <!-- Address Selection Modal -->
    <div v-if="showAddressModal" class="modal-overlay" @click="closeAddressModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>选择配送地址</h2>
          <button @click="closeAddressModal" class="close-btn">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <div v-if="addressesLoading" class="loading-addresses">加载地址中...</div>
          <div v-else-if="addresses.length === 0" class="no-addresses">
            <div class="empty-icon">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <p>您还没有添加配送地址</p>
            <button @click="openAddAddressModal" class="add-first-address-btn">添加新地址</button>
          </div>
          <div v-else class="addresses-list-modal">
            <div 
              v-for="address in addresses" 
              :key="address.id"
              @click="selectAddress(address.id)"
              :class="['address-card-modal', { active: selectedAddressId === address.id }]"
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
            <button @click="openAddAddressModal" class="add-new-address-btn">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
              </svg>
              <span>添加新地址</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Add/Edit Address Form Modal -->
    <AddressForm
      :show="showAddressForm"
      :address="editingAddress"
      @close="closeAddressForm"
      @saved="handleAddressSaved"
    />
  </div>
</template>

<script>
import apiClient from '../api/client'
import AddressForm from '../components/AddressForm.vue'

export default {
  name: 'Checkout',
  components: {
    AddressForm
  },
  data() {
    return {
      loading: true,
      error: null,
      deal: null,
      orderItems: [],
      paymentMethod: 'cash', // 'cash' or 'etransfer'
      deliveryMethod: 'pickup', // 'pickup' or 'delivery'
      selectedPickupLocation: 'markham', // 'markham' or 'northyork'
      selectedAddressId: null,
      addresses: [],
      addressesLoading: false,
      showAddressModal: false,
      showAddressForm: false,
      editingAddress: null,
      existingOrderId: null, // Store existing order ID if found
      notes: '' // User custom notes
    }
  },
  computed: {
    canConfirm() {
      if (this.deliveryMethod === 'delivery') {
        return this.selectedAddressId !== null
      } else if (this.deliveryMethod === 'pickup') {
        return this.selectedPickupLocation !== null
      }
      return true
    },
    hasEstimatedTotal() {
      return this.orderItems.some(item => item.is_estimated)
    },
    selectedAddress() {
      if (!this.selectedAddressId) return null
      return this.addresses.find(addr => addr.id === this.selectedAddressId)
    }
  },
  async mounted() {
    await this.loadCheckoutData()
  },
  watch: {
    deliveryMethod(newVal) {
      if (newVal === 'delivery' && this.addresses.length === 0) {
        // Load addresses when switching to delivery mode
        this.loadAddresses()
      }
    }
  },
  methods: {
    async loadCheckoutData() {
      this.loading = true
      this.error = null
      try {
        // Get dealId from route query
        const dealId = this.$route.query.dealId
        if (!dealId) {
          this.error = '订单数据无效，请重新选择商品'
          this.loading = false
          return
        }

        // Load deal info (includes order if user has one)
        const response = await apiClient.get(`/group-deals/${dealId}`)
        this.deal = response.data.deal
        
        // Check if order is included in the group deal response
        if (response.data.order) {
          const order = response.data.order
          this.existingOrderId = order.id
          
          // Build order items from existing order
          this.orderItems = order.items.map(item => ({
            product_id: item.product_id,
            quantity: item.quantity,
            pricing_type: item.product?.pricing_type || 'per_item',
            estimated_price: parseFloat(item.total_price || 0).toFixed(2),
            is_estimated: false // Order items have final prices
          }))
          
          // Restore payment method
          if (order.payment_method) {
            this.paymentMethod = order.payment_method
          }
          
          // Restore delivery method
          if (order.delivery_method) {
            this.deliveryMethod = order.delivery_method
            
            // If delivery, restore address ID and load addresses
            if (order.delivery_method === 'delivery' && order.address_id) {
              this.selectedAddressId = order.address_id
              await this.loadAddresses()
            }
            
            // If pickup, restore pickup location
            if (order.delivery_method === 'pickup' && order.pickup_location) {
              this.selectedPickupLocation = order.pickup_location
            }
          }
          
          // Restore notes
          if (order.notes) {
            this.notes = order.notes
          }
        } else {
          // No existing order - user needs to select items
          // This shouldn't happen if coming from GroupDealDetail, but handle gracefully
          this.error = '请先在商品详情页选择商品'
        }
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || '加载订单信息失败'
        console.error('Failed to load checkout data:', error)
      } finally {
        this.loading = false
      }
    },
    async loadAddresses() {
      this.addressesLoading = true
      try {
        const response = await apiClient.get('/addresses')
        this.addresses = response.data.addresses || []
        
        // Auto-select default address if not already selected
        if (!this.selectedAddressId) {
          const defaultAddress = this.addresses.find(addr => addr.is_default)
          if (defaultAddress) {
            this.selectedAddressId = defaultAddress.id
          } else if (this.addresses.length === 1) {
            this.selectedAddressId = this.addresses[0].id
          }
        }
      } catch (error) {
        console.error('Failed to load addresses:', error)
      } finally {
        this.addressesLoading = false
      }
    },
    openAddressModal() {
      // Load addresses if not already loaded
      if (this.addresses.length === 0 && !this.addressesLoading) {
        this.loadAddresses()
      }
      this.showAddressModal = true
    },
    closeAddressModal() {
      this.showAddressModal = false
    },
    selectAddress(addressId) {
      this.selectedAddressId = addressId
      this.closeAddressModal()
    },
    openAddAddressModal() {
      this.editingAddress = null
      this.showAddressForm = true
    },
    closeAddressForm() {
      this.showAddressForm = false
      this.editingAddress = null
    },
    async handleAddressSaved() {
      await this.loadAddresses()
      this.closeAddressForm()
      // If this was the first address, select it automatically
      if (this.addresses.length === 1) {
        this.selectedAddressId = this.addresses[0].id
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
      // Only show date, no time
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
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
          items: this.orderItems.map(item => ({
            product_id: item.product_id,
            quantity: item.quantity,
            pricing_type: item.pricing_type
          })),
          payment_method: this.paymentMethod,
          delivery_method: this.deliveryMethod,
          address_id: this.deliveryMethod === 'delivery' ? this.selectedAddressId : null,
          pickup_location: this.deliveryMethod === 'pickup' ? this.selectedPickupLocation : null,
          notes: this.notes.trim() || null
        }

        let response
        let isNew = true
        
        // Check if we have an existing order ID or need to check for one
        if (this.existingOrderId) {
          // Update existing order using PATCH
          response = await apiClient.patch(`/orders/${this.existingOrderId}`, orderData)
          isNew = false
        } else {
          // Try to create new order
          try {
            orderData.group_deal_id = this.deal.id
            response = await apiClient.post('/orders', orderData)
            isNew = true
          } catch (error) {
            // If we get a 409 (conflict), it means order exists - try to get it and update
            if (error.response?.status === 409 && error.response?.data?.order_id) {
              const orderId = error.response.data.order_id
              // Remove group_deal_id for PATCH request
              delete orderData.group_deal_id
              response = await apiClient.patch(`/orders/${orderId}`, orderData)
              isNew = false
            } else {
              throw error
            }
          }
        }
        
        // Redirect to result page with order info in query params
        const orderNumber = response.data.order?.order_number || null
        
        this.$router.push({
          path: '/order-result',
          query: {
            status: 'success',
            orderNumber: orderNumber,
            isNew: isNew ? 'true' : 'false'
          }
        })
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || '创建订单失败'
        const errorDetails = error.response?.data?.details || null
        
        // Redirect to result page with error info in query params
        this.$router.push({
          path: '/order-result',
          query: {
            status: 'error',
            error: errorMsg,
            errorDetails: errorDetails
          }
        })
        console.error('Failed to create/update order:', error)
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
.payment-section,
.delivery-section,
.notes-section {
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
  animation-delay: 0.15s;
  animation-fill-mode: both;
}

.payment-section {
  animation-delay: 0.2s;
  animation-fill-mode: both;
}

.notes-section {
  animation-delay: 0.25s;
  animation-fill-mode: both;
}

.notes-input {
  width: 100%;
  padding: var(--md-spacing-md);
  border: 2px solid var(--md-outline-variant);
  border-radius: var(--md-radius-md);
  background: var(--md-surface);
  font-size: var(--md-body-size);
  font-family: inherit;
  color: var(--md-on-surface);
  resize: vertical;
  min-height: 80px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.notes-input:focus {
  outline: none;
  border-color: var(--md-primary);
  box-shadow: 0 0 0 3px rgba(255, 140, 0, 0.1);
}

.notes-input::placeholder {
  color: var(--md-on-surface-variant);
}

.notes-hint {
  margin-top: var(--md-spacing-xs);
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  text-align: right;
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

.payment-options {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.payment-option {
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

.payment-radio {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.payment-option::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 140, 0, 0.1), transparent);
  transition: left 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.payment-option:hover::before {
  left: 100%;
}

.payment-option:hover {
  border-color: var(--md-primary);
  background: var(--md-surface-variant);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.payment-option.active {
  border-color: var(--md-primary);
  background: rgba(255, 140, 0, 0.05);
  box-shadow: 0 4px 12px rgba(255, 140, 0, 0.2);
  animation: optionSelect 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.payment-note {
  margin-top: var(--md-spacing-md);
  padding-top: var(--md-spacing-md);
  border-top: 1px solid var(--md-surface-variant);
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  text-align: center;
  font-style: italic;
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

/* Pickup Location Selection */
.pickup-location-selection {
  margin-top: var(--md-spacing-lg);
  padding-top: var(--md-spacing-lg);
  border-top: 1px solid var(--md-surface-variant);
}

.selection-subtitle {
  font-size: var(--md-body-size);
  font-weight: 500;
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-md);
}

.pickup-locations {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.pickup-location-card {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
  padding: var(--md-spacing-md);
  border: 2px solid var(--md-outline-variant);
  border-radius: var(--md-radius-md);
  background: var(--md-surface);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  min-height: 72px;
}

.pickup-location-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 140, 0, 0.1), transparent);
  transition: left 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.pickup-location-card:hover::before {
  left: 100%;
}

.pickup-location-card:hover {
  border-color: var(--md-primary);
  background: var(--md-surface-variant);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.pickup-location-card.active {
  border-color: var(--md-primary);
  background: rgba(255, 140, 0, 0.05);
  box-shadow: 0 4px 12px rgba(255, 140, 0, 0.2);
  animation: locationSelect 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes locationSelect {
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

.location-icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  color: var(--md-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.pickup-location-card:hover .location-icon {
  transform: scale(1.1);
}

.pickup-location-card.active .location-icon {
  animation: iconBounce 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes iconBounce {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.2) translateY(-4px);
  }
  100% {
    transform: scale(1);
  }
}

.location-icon svg {
  width: 24px;
  height: 24px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.pickup-location-card.active .location-icon svg {
  filter: drop-shadow(0 2px 4px rgba(255, 140, 0, 0.3));
}

.location-content {
  flex: 1;
}

.location-content h5 {
  font-size: var(--md-body-size);
  font-weight: 600;
  color: var(--md-on-surface);
  margin: 0 0 var(--md-spacing-xs) 0;
}

.location-content p {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin: 0;
  line-height: 1.4;
}

.location-check {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  color: var(--md-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 140, 0, 0.1);
  border-radius: 50%;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.pickup-location-card.active .location-check {
  background: rgba(255, 140, 0, 0.2);
  animation: checkmarkCircle 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.location-check svg {
  width: 20px;
  height: 20px;
  animation: checkmarkPop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* Address Selection */
.address-selection {
  margin-top: var(--md-spacing-lg);
  padding-top: var(--md-spacing-lg);
  border-top: 1px solid var(--md-surface-variant);
}

.select-address-btn {
  width: 100%;
  background: var(--md-surface);
  border: 2px solid var(--md-outline-variant);
  border-radius: var(--md-radius-md);
  padding: var(--md-spacing-md);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.select-address-btn:hover {
  border-color: var(--md-primary);
  background: var(--md-surface-variant);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.btn-content {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
}

.btn-icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  color: var(--md-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-icon svg {
  width: 24px;
  height: 24px;
}

.btn-text {
  flex: 1;
  text-align: left;
}

.selected-address-preview .preview-header {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  margin-bottom: var(--md-spacing-xs);
}

.preview-name {
  font-size: var(--md-body-size);
  font-weight: 600;
  color: var(--md-on-surface);
}

.preview-phone {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.preview-address {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  line-height: 1.4;
}

.no-address-selected {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.no-address-selected span:first-child {
  font-size: var(--md-body-size);
  font-weight: 500;
  color: var(--md-on-surface);
}

.no-address-selected .hint {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.btn-arrow {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  color: var(--md-on-surface-variant);
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-arrow svg {
  width: 20px;
  height: 20px;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-content {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg) var(--md-radius-lg) 0 0;
  width: 100%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  animation: slideUp 0.3s ease-out;
  box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.2);
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
  }
  to {
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-lg);
  border-bottom: 1px solid var(--md-outline-variant);
  flex-shrink: 0;
}

.modal-header h2 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  font-weight: 500;
  margin: 0;
}

.close-btn {
  background: transparent;
  border: none;
  padding: var(--md-spacing-xs);
  cursor: pointer;
  color: var(--md-on-surface-variant);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--md-radius-sm);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  width: 32px;
  height: 32px;
}

.close-btn:hover {
  background: var(--md-surface-variant);
  color: var(--md-on-surface);
}

.close-btn svg {
  width: 24px;
  height: 24px;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--md-spacing-lg);
}

.loading-addresses,
.no-addresses {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.no-addresses {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--md-spacing-md);
}

.empty-icon {
  width: 64px;
  height: 64px;
  color: var(--md-on-surface-variant);
  opacity: 0.5;
}

.empty-icon svg {
  width: 100%;
  height: 100%;
}

.add-first-address-btn {
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  background: var(--md-primary);
  color: white;
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  min-height: 44px;
}

.add-first-address-btn:hover {
  background: #FF7F00;
  box-shadow: var(--md-elevation-2);
}

.addresses-list-modal {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.address-card-modal {
  position: relative;
  padding: var(--md-spacing-md);
  padding-right: 48px;
  border: 2px solid var(--md-outline-variant);
  border-radius: var(--md-radius-md);
  background: var(--md-surface);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  min-height: 80px;
}

.address-card-modal:hover {
  border-color: var(--md-primary);
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.address-card-modal.active {
  border-color: var(--md-primary);
  background: rgba(255, 140, 0, 0.05);
  box-shadow: 0 4px 12px rgba(255, 140, 0, 0.2);
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
  margin-bottom: var(--md-spacing-xs);
}

.address-details p:last-child {
  margin-bottom: 0;
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

.address-card-modal.active .address-check {
  background: rgba(255, 140, 0, 0.2);
  animation: checkmarkCircle 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.address-check svg {
  width: 20px;
  height: 20px;
  animation: checkmarkPop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
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

.add-new-address-btn {
  width: 100%;
  padding: var(--md-spacing-md);
  background: transparent;
  color: var(--md-primary);
  border: 2px dashed var(--md-primary);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--md-spacing-sm);
  min-height: 56px;
}

.add-new-address-btn:hover {
  background: rgba(255, 140, 0, 0.1);
  border-style: solid;
}

.add-new-address-btn svg {
  width: 20px;
  height: 20px;
}

/* Confirm Order Section */
.confirm-order-section {
  padding: var(--md-spacing-xl) var(--md-spacing-md);
  margin-top: var(--md-spacing-lg);
}

.confirm-order-btn {
  width: 100%;
  padding: var(--md-spacing-lg) var(--md-spacing-md);
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  color: white;
  border: none;
  border-radius: var(--md-radius-lg);
  font-size: var(--md-body-size);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: var(--md-elevation-2);
  position: relative;
  overflow: hidden;
  min-height: 56px;
}

.confirm-order-btn::before {
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

.confirm-order-btn:not(:disabled):hover::before {
  width: 500px;
  height: 500px;
}

.confirm-order-btn:not(:disabled):hover {
  transform: translateY(-2px);
  box-shadow: var(--md-elevation-4);
}

.confirm-order-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--md-surface-variant);
  color: var(--md-on-surface-variant);
}

.confirm-order-btn:not(:disabled):active {
  transform: translateY(0);
  box-shadow: var(--md-elevation-2);
}

.btn-text {
  font-size: var(--md-title-size);
  position: relative;
  z-index: 1;
}

.btn-amount {
  font-size: var(--md-headline-size);
  font-weight: 700;
  position: relative;
  z-index: 1;
}

.estimate-note {
  text-align: center;
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin-top: var(--md-spacing-sm);
  font-style: italic;
}

@media (max-width: 480px) {
  .btn-text {
    font-size: var(--md-body-size);
  }
  
  .btn-amount {
    font-size: var(--md-title-size);
  }
}
</style>

