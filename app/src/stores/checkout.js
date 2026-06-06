import { defineStore } from 'pinia'
import { fetchShippingConfig, calculateShippingFee } from '../utils/shipping'
import { roundMoney } from '../utils/productPriceDisplay'

export const useCheckoutStore = defineStore('checkout', {
  state: () => ({
    // Deal information
    deal: null,
    
    // Selected order items from GroupDealDetail
    orderItems: [],
    
    // Existing order information (for updates)
    existingOrderId: null,
    existingOrderData: null,
    existingOrderStatus: null, // Store order status to check if completed
    
    // Checkout form data
    paymentMethod: 'cash',
    deliveryMethod: 'pickup',
    selectedPickupLocation: 'markham',
    selectedAddressId: null,
    notes: '',
    
    // Shipping fee configuration
    shippingConfig: null,

    /** Credit to apply when computing shipping tier base (set by Checkout.vue). */
    storeCreditToApply: 0
  }),
  
  getters: {
    hasItems: (state) => state.orderItems.length > 0,
    
    subtotal: (state) => {
      return roundMoney(state.orderItems.reduce((sum, item) => {
        return sum + parseFloat(item.estimated_price || 0)
      }, 0))
    },
    
    hasEstimatedTotal: (state) => {
      // If order is completed, don't show estimated total
      if (state.existingOrderStatus === 'completed') {
        return false
      }
      return state.orderItems.some(item => item.is_estimated)
    },
    
    isOrderCompleted: (state) => {
      return state.existingOrderStatus === 'completed'
    },
    
    shippingFee: (state) => {
      if (state.deliveryMethod === 'pickup') {
        return 0
      }

      const credit = parseFloat(state.storeCreditToApply || 0) || 0
      const tierBase = Math.max(0, state.orderItems.reduce((sum, item) => {
        return sum + parseFloat(item.estimated_price || 0)
      }, 0) - credit)

      const freeShippingSubtotal = state.orderItems.reduce((sum, item) => {
        const countsTowardFreeShipping = item.counts_toward_free_shipping !== false
        if (countsTowardFreeShipping) {
          const lineShare = parseFloat(item.estimated_price || 0)
          const subtotal = state.orderItems.reduce((s, i) => s + parseFloat(i.estimated_price || 0), 0)
          if (subtotal <= 0) return sum
          return sum + (lineShare / subtotal) * tierBase
        }
        return sum
      }, 0)

      return calculateShippingFee(freeShippingSubtotal, state.shippingConfig)
    },
    
    total: (state) => {
      const subtotal = state.orderItems.reduce((sum, item) => {
        return sum + parseFloat(item.estimated_price || 0)
      }, 0)
      
      let shipping = 0
      if (state.deliveryMethod === 'delivery') {
        // Calculate free shipping subtotal (excluding products that don't count)
        const freeShippingSubtotal = state.orderItems.reduce((sum, item) => {
          const countsTowardFreeShipping = item.counts_toward_free_shipping !== false
          if (countsTowardFreeShipping) {
            return sum + parseFloat(item.estimated_price || 0)
          }
          return sum
        }, 0)
        shipping = calculateShippingFee(freeShippingSubtotal, state.shippingConfig)
      }
      
      return roundMoney(subtotal + shipping)
    }
  },
  
  actions: {
    /**
     * Credit applied toward shipping tier (Checkout.vue sets this from toggle).
     */
    setStoreCreditToApply(amount) {
      this.storeCreditToApply = parseFloat(amount) || 0
    },

    /**
     * Load shipping fee configuration
     */
    async loadShippingConfig() {
      if (!this.shippingConfig) {
        this.shippingConfig = await fetchShippingConfig()
      }
      return this.shippingConfig
    },
    
    /**
     * Set deal information
     */
    setDeal(deal) {
      this.deal = deal
    },
    
    /**
     * Set order items from GroupDealDetail selection
     */
    setOrderItems(items) {
      this.orderItems = items
    },
    
    /**
     * Set existing order information (for updates)
     */
    setExistingOrder(orderId, orderData, orderStatus = null) {
      this.existingOrderId = orderId
      this.existingOrderData = orderData
      this.existingOrderStatus = orderStatus
      
      // Restore saved preferences if available
      if (orderData) {
        if (orderData.paymentMethod) {
          this.paymentMethod = orderData.paymentMethod
        }
        if (orderData.deliveryMethod) {
          this.deliveryMethod = orderData.deliveryMethod
        }
        if (orderData.pickupLocation) {
          this.selectedPickupLocation = orderData.pickupLocation
        }
        if (orderData.addressId) {
          this.selectedAddressId = orderData.addressId
        }
        if (orderData.notes) {
          this.notes = orderData.notes
        }
      }
    },
    
    /**
     * Update payment method
     */
    setPaymentMethod(method) {
      this.paymentMethod = method
    },
    
    /**
     * Update delivery method
     */
    setDeliveryMethod(method) {
      this.deliveryMethod = method
      // If delivery method is set to delivery, automatically set payment to etransfer
      if (method === 'delivery' && this.paymentMethod === 'cash') {
        this.paymentMethod = 'etransfer'
      }
    },
    
    /**
     * Update pickup location
     */
    setPickupLocation(location) {
      this.selectedPickupLocation = location
    },
    
    /**
     * Update selected address
     */
    setAddress(addressId) {
      this.selectedAddressId = addressId
    },
    
    /**
     * Update notes
     */
    setNotes(notes) {
      this.notes = notes
    },
    
    /**
     * Clear all checkout data
     */
    clearCheckout() {
      this.deal = null
      this.orderItems = []
      this.existingOrderId = null
      this.existingOrderData = null
      this.existingOrderStatus = null
      this.paymentMethod = 'cash'
      this.deliveryMethod = 'pickup'
      this.selectedPickupLocation = 'markham'
      this.selectedAddressId = null
      this.notes = ''
      this.storeCreditToApply = 0
    },
    
    /**
     * Get order data for API submission
     */
    getOrderData() {
      return {
        items: this.orderItems.map(item => ({
          product_id: item.product_id,
          quantity: item.quantity,
          pricing_type: item.pricing_type,
          variant_id: item.variant_id ?? undefined,
          accept_substitute: item.accept_substitute
        })),
        payment_method: this.paymentMethod,
        delivery_method: this.deliveryMethod,
        address_id: this.deliveryMethod === 'delivery' ? this.selectedAddressId : null,
        pickup_location: this.deliveryMethod === 'pickup' ? this.selectedPickupLocation : null,
        notes: this.notes.trim() || null
      }
    }
  }
})

