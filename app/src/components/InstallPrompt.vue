<template>
  <div v-if="showPrompt" class="install-prompt">
    <div class="install-prompt-content">
      <div class="install-prompt-icon">📱</div>
      <div class="install-prompt-text">
        <h3>添加到主屏幕</h3>
        <p>将谷语农庄添加到您的主屏幕，获得更好的体验！</p>
      </div>
      <div class="install-prompt-actions">
        <button @click="dismissPrompt" class="dismiss-btn">稍后</button>
        <button @click="installApp" class="install-btn">安装</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'InstallPrompt',
  data() {
    return {
      showPrompt: false,
      deferredPrompt: null,
      dismissed: false
    }
  },
  mounted() {
    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      return
    }

    // Check if user has dismissed before
    const dismissed = localStorage.getItem('pwa-install-dismissed')
    if (dismissed) {
      const dismissedTime = parseInt(dismissed)
      const daysSinceDismissed = (Date.now() - dismissedTime) / (1000 * 60 * 60 * 24)
      // Show again after 7 days
      if (daysSinceDismissed < 7) {
        return
      }
    }

    // Listen for beforeinstallprompt event
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault()
      this.deferredPrompt = e
      // Show prompt after a delay (better UX)
      setTimeout(() => {
        this.showPrompt = true
      }, 3000)
    })

    // Register service worker
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js')
        .then((registration) => {
          console.log('Service Worker registered:', registration)
        })
        .catch((error) => {
          console.log('Service Worker registration failed:', error)
        })
    }
  },
  methods: {
    async installApp() {
      if (!this.deferredPrompt) {
        return
      }

      // Show the install prompt
      this.deferredPrompt.prompt()

      // Wait for user response
      const { outcome } = await this.deferredPrompt.userChoice

      if (outcome === 'accepted') {
        console.log('User accepted the install prompt')
      } else {
        console.log('User dismissed the install prompt')
      }

      this.deferredPrompt = null
      this.showPrompt = false
    },
    dismissPrompt() {
      this.showPrompt = false
      localStorage.setItem('pwa-install-dismissed', Date.now().toString())
    }
  }
}
</script>

<style scoped>
.install-prompt {
  position: fixed;
  bottom: 80px; /* Above bottom nav */
  left: 0;
  right: 0;
  padding: var(--md-spacing-md);
  z-index: 1000;
  animation: slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.install-prompt-content {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-4);
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
  max-width: 500px;
  margin: 0 auto;
}

.install-prompt-icon {
  font-size: 2.5rem;
  flex-shrink: 0;
}

.install-prompt-text {
  flex: 1;
}

.install-prompt-text h3 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin: 0 0 var(--md-spacing-xs) 0;
  font-weight: 500;
}

.install-prompt-text p {
  font-size: var(--md-body-size);
  color: var(--md-on-surface-variant);
  margin: 0;
}

.install-prompt-actions {
  display: flex;
  gap: var(--md-spacing-sm);
  flex-shrink: 0;
}

.dismiss-btn,
.install-btn {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border-radius: var(--md-radius-md);
  font-size: var(--md-label-size);
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.dismiss-btn {
  background: transparent;
  color: var(--md-on-surface-variant);
}

.dismiss-btn:hover {
  background: var(--md-surface-variant);
}

.install-btn {
  background: var(--md-primary);
  color: white;
}

.install-btn:hover {
  background: #FF7F00;
  box-shadow: var(--md-elevation-2);
}
</style>

