import { defineStore } from 'pinia'

export const useUIStore = defineStore('ui', {
  state: () => ({
    pwaInstallDismissed: null, // timestamp when dismissed
    pwaInstallPromptShown: false
  }),
  
  getters: {
    shouldShowPWAInstall: (state) => {
      if (!state.pwaInstallDismissed) return true
      
      // Show again after 7 days
      const daysSinceDismissed = (Date.now() - state.pwaInstallDismissed) / (1000 * 60 * 60 * 24)
      return daysSinceDismissed >= 7
    }
  },
  
  actions: {
    /**
     * Load UI settings from localStorage on init (for backward compatibility during migration)
     */
    loadFromStorage() {
      const dismissed = localStorage.getItem('pwa-install-dismissed')
      if (dismissed) {
        this.pwaInstallDismissed = parseInt(dismissed)
      }
    },
    
    /**
     * Dismiss PWA install prompt
     */
    dismissPWAInstall() {
      this.pwaInstallDismissed = Date.now()
      // Keep in localStorage for persistence across sessions
      localStorage.setItem('pwa-install-dismissed', this.pwaInstallDismissed.toString())
    },
    
    /**
     * Reset PWA install dismissal (user accepted install)
     */
    resetPWAInstallDismissal() {
      this.pwaInstallDismissed = null
      localStorage.removeItem('pwa-install-dismissed')
    }
  }
})

