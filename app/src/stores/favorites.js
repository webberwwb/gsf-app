import { defineStore } from 'pinia'

export const useFavoritesStore = defineStore('favorites', {
  state: () => ({
    items: []
  }),
  
  getters: {
    count: (state) => state.items.length,
    
    hasItems: (state) => state.items.length > 0,
    
    isFavorite: (state) => (productId) => {
      return state.items.some(item => item.id === productId)
    }
  },
  
  actions: {
    /**
     * Load favorites from localStorage on init (for backward compatibility during migration)
     */
    loadFromStorage() {
      const savedFavorites = localStorage.getItem('favorites')
      if (savedFavorites) {
        try {
          this.items = JSON.parse(savedFavorites)
        } catch (error) {
          console.error('Failed to parse favorites from storage:', error)
          this.items = []
        }
      }
    },
    
    /**
     * Add product to favorites
     */
    addFavorite(product) {
      // Check if already in favorites
      if (this.isFavorite(product.id)) {
        return
      }
      
      this.items.push({
        id: product.id,
        name: product.name,
        price: product.price,
        image: product.image || null,
        description: product.description || null
      })
    },
    
    /**
     * Remove product from favorites
     */
    removeFavorite(productId) {
      this.items = this.items.filter(item => item.id !== productId)
    },
    
    /**
     * Toggle favorite status
     */
    toggleFavorite(product) {
      if (this.isFavorite(product.id)) {
        this.removeFavorite(product.id)
        return false
      } else {
        this.addFavorite(product)
        return true
      }
    },
    
    /**
     * Clear all favorites
     */
    clearFavorites() {
      this.items = []
    },
    
    /**
     * Get favorite by ID
     */
    getFavorite(productId) {
      return this.items.find(item => item.id === productId)
    }
  }
})




