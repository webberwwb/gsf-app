import { defineStore } from 'pinia'

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
    notes: ''
  }),
  
  getters: {
    hasItems: (state) => state.orderItems.length > 0,
    
    subtotal: (state) => {
      return state.orderItems.reduce((sum, item) => {
        return sum + parseFloat(item.estimated_price || 0)
      }, 0)
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
      
      const subtotal = state.orderItems.reduce((sum, item) => {
        return sum + parseFloat(item.estimated_price || 0)
      }, 0)
      
      // Free shipping for orders >= $150
      if (subtotal >= 150) {
        return 0
      }
      
      // GTA shipping fee for orders < $150
      return 7.50
    },
    
    total: (state) => {
      const subtotal = state.orderItems.reduce((sum, item) => {
        return sum + parseFloat(item.estimated_price || 0)
      }, 0)
      
      let shipping = 0
      if (state.deliveryMethod === 'delivery') {
        shipping = subtotal >= 150 ? 0 : 7.50
      }
      
      return subtotal + shipping
    }
  },
  
  actions: {
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
    },
    
    /**
     * Get order data for API submission
     */
    getOrderData() {
      return {
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
    }
  }
})

