import { defineStore } from 'pinia'
import { fetchShippingConfig } from '../utils/shipping'
import { previewOrderTotals } from '../utils/orderPricing'

export const useCheckoutStore = defineStore('checkout', {
  state: () => ({
    // Deal information
    deal: null,
    
    // Selected order items from GroupDealDetail
    orderItems: [],
    
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
    
    previewLines(state) {
      return state.orderItems.map((item) => ({
        product: {
          counts_toward_free_shipping: item.counts_toward_free_shipping !== false
        },
        total_price: parseFloat(item.estimated_price || 0),
        quantity: item.quantity,
        cutting: !!item.cutting,
        cutting_fee: item.cutting_fee || 0
      }))
    },

    previewTotals(state) {
      const credit = parseFloat(state.storeCreditToApply || 0) || 0
      return previewOrderTotals({
        items: state.orderItems.map((item) => ({
          product: {
            counts_toward_free_shipping: item.counts_toward_free_shipping !== false
          },
          total_price: parseFloat(item.estimated_price || 0),
          quantity: item.quantity,
          cutting: !!item.cutting,
          cutting_fee: item.cutting_fee || 0
        })),
        deliveryMethod: state.deliveryMethod,
        storeCredit: credit,
        adjustment: 0,
        shippingConfig: state.shippingConfig ?? undefined
      })
    },
    
    subtotal(state) {
      return state.previewTotals.subtotal
    },
    
    hasEstimatedTotal: (state) => {
      return state.orderItems.some(item => item.is_estimated)
    },
    
    shippingFee(state) {
      return state.previewTotals.shipping
    },
    
    total: (state) => {
      return state.previewTotals.subtotal + state.previewTotals.shipping
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
      if (method === 'pickup' && this.paymentMethod === 'card') {
        this.paymentMethod = 'cash'
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
          accept_substitute: item.accept_substitute,
          cutting: !!item.cutting
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
