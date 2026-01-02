import { defineStore } from 'pinia'

export const useCartStore = defineStore('cart', {
  state: () => ({
    items: []
  }),
  
  getters: {
    itemCount: (state) => state.items.length,
    
    totalQuantity: (state) => {
      return state.items.reduce((sum, item) => sum + item.quantity, 0)
    },
    
    totalPrice: (state) => {
      return state.items.reduce((sum, item) => {
        return sum + (parseFloat(item.price) * item.quantity)
      }, 0)
    },
    
    hasItems: (state) => state.items.length > 0
  },
  
  actions: {
    /**
     * Load cart from localStorage on init (for backward compatibility during migration)
     */
    loadFromStorage() {
      const savedCart = localStorage.getItem('cart')
      if (savedCart) {
        try {
          this.items = JSON.parse(savedCart)
        } catch (error) {
          console.error('Failed to parse cart from storage:', error)
          this.items = []
        }
      }
    },
    
    /**
     * Add item to cart
     */
    addItem(product, quantity = 1) {
      const existingItem = this.items.find(item => item.id === product.id)
      
      if (existingItem) {
        existingItem.quantity += quantity
      } else {
        this.items.push({
          id: product.id,
          name: product.name,
          price: product.price,
          image: product.image || null,
          quantity: quantity
        })
      }
    },
    
    /**
     * Update item quantity
     */
    updateQuantity(productId, quantity) {
      const item = this.items.find(item => item.id === productId)
      if (item) {
        if (quantity <= 0) {
          this.removeItem(productId)
        } else {
          item.quantity = quantity
        }
      }
    },
    
    /**
     * Increase item quantity
     */
    increaseQuantity(productId) {
      const item = this.items.find(item => item.id === productId)
      if (item) {
        item.quantity++
      }
    },
    
    /**
     * Decrease item quantity
     */
    decreaseQuantity(productId) {
      const item = this.items.find(item => item.id === productId)
      if (item) {
        if (item.quantity > 1) {
          item.quantity--
        } else {
          this.removeItem(productId)
        }
      }
    },
    
    /**
     * Remove item from cart
     */
    removeItem(productId) {
      this.items = this.items.filter(item => item.id !== productId)
    },
    
    /**
     * Clear entire cart
     */
    clearCart() {
      this.items = []
    },
    
    /**
     * Get item by ID
     */
    getItem(productId) {
      return this.items.find(item => item.id === productId)
    }
  }
})



