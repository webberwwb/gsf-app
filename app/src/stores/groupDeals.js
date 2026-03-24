import { defineStore } from 'pinia'
import { useAuthStore } from './auth'
import apiClient from '../api/client'

export const useGroupDealsStore = defineStore('groupDeals', {
  state: () => ({
    deals: [],
    loading: false,
    error: null,
    lastFetched: null
  }),
  
  getters: {
    currentDeals: (state) => {
      const authStore = useAuthStore()
      return state.deals.filter(d => {
        if (d.status === 'draft') {
          return authStore.isAdmin
        }
        return d.status === 'active' || 
               d.status === 'upcoming' || 
               d.status === 'ready_for_pickup' || 
               d.status === 'closed'
      })
    },
    
    pastDeals: (state) => {
      return state.deals.filter(d => d.status === 'completed')
    },
    
    hasDeals: (state) => state.deals.length > 0
  },
  
  actions: {
    async fetchDeals(force = false) {
      // Skip if already loaded and not forcing refresh
      if (!force && this.deals.length > 0 && this.lastFetched) {
        return
      }
      
      this.loading = true
      this.error = null
      
      try {
        const response = await apiClient.get('/group-deals')
        this.deals = response.data.deals || []
        this.lastFetched = Date.now()
      } catch (err) {
        console.error('Error loading deals:', err)
        this.error = err.response?.data?.message || err.response?.data?.error || '加载失败，请稍后重试'
      } finally {
        this.loading = false
      }
    },
    
    async refreshDeals() {
      await this.fetchDeals(true)
    },
    
    getDealById(id) {
      return this.deals.find(d => d.id === id)
    },
    
    clearDeals() {
      this.deals = []
      this.lastFetched = null
    }
  }
})
