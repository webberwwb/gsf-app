<template>
  <div v-if="showPrompt" class="install-prompt">
    <div class="install-prompt-content" :class="{ 'ios-instructions': isIOS }">
      <div class="install-prompt-icon">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
      </div>
      <div class="install-prompt-text">
        <h3>添加到主屏幕</h3>
        <p v-if="!isIOS">将管理后台添加到您的主屏幕，获得更好的体验！</p>
        <div v-else class="ios-instructions-text">
          <p class="instruction-step">
            <span class="step-number">1</span>
            点击底部的 <span class="highlight">分享按钮</span> <svg class="share-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" /></svg>
          </p>
          <p class="instruction-step">
            <span class="step-number">2</span>
            选择 <span class="highlight">"添加到主屏幕"</span>
          </p>
          <p class="instruction-step">
            <span class="step-number">3</span>
            点击 <span class="highlight">"添加"</span> 完成安装
          </p>
        </div>
      </div>
      <div class="install-prompt-actions">
        <button @click="dismissPrompt" class="dismiss-btn">稍后</button>
        <button v-if="!isIOS" @click="installApp" class="install-btn">安装</button>
        <button v-else @click="dismissPrompt" class="install-btn">知道了</button>
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
      dismissed: false,
      isIOS: false
    }
  },
  mounted() {
    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches || 
        window.navigator.standalone === true) {
      return
    }

    // Check if user has dismissed before
    const dismissed = localStorage.getItem('admin-pwa-install-dismissed')
    if (dismissed) {
      const dismissedTime = parseInt(dismissed)
      const daysSinceDismissed = (Date.now() - dismissedTime) / (1000 * 60 * 60 * 24)
      // Show again after 7 days
      if (daysSinceDismissed < 7) {
        return
      }
    }

    // Register service worker first (required for installability)
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js', { scope: '/' })
        .then((registration) => {
          // Check for updates
          registration.update()
        })
        .catch((error) => {
          console.error('Service Worker registration failed:', error)
        })
    }

    // Listen for beforeinstallprompt event (Chrome/Edge)
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault()
      this.deferredPrompt = e
      // Show prompt after a delay (better UX)
      setTimeout(() => {
        if (this.deferredPrompt) {
          this.showPrompt = true
        }
      }, 3000)
    })

    // Detect iOS Safari
    this.isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream
    const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent)
    
    if (this.isIOS && isSafari) {
      // iOS Safari doesn't support beforeinstallprompt
      // Show manual install instructions after a delay
      setTimeout(() => {
        this.showPrompt = true
      }, 3000)
    }
  },
  methods: {
    async installApp() {
      if (this.isIOS) {
        // iOS Safari - instructions are already shown
        this.dismissPrompt()
        return
      }

      if (!this.deferredPrompt) {
        this.showPrompt = false
        return
      }

      try {
        // Show the install prompt
        this.deferredPrompt.prompt()

        // Wait for user response
        const { outcome } = await this.deferredPrompt.userChoice

        if (outcome === 'accepted') {
          localStorage.removeItem('admin-pwa-install-dismissed')
        } else {
          this.dismissPrompt()
        }
      } catch (error) {
        console.error('Error showing install prompt:', error)
      }

      this.deferredPrompt = null
      this.showPrompt = false
    },
    dismissPrompt() {
      this.showPrompt = false
      localStorage.setItem('admin-pwa-install-dismissed', Date.now().toString())
    }
  }
}
</script>

<style scoped>
.install-prompt {
  position: fixed;
  bottom: var(--md-spacing-lg);
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
  width: 48px;
  height: 48px;
  flex-shrink: 0;
  color: var(--md-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.install-prompt-icon svg {
  width: 100%;
  height: 100%;
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

.ios-instructions {
  flex-direction: column;
  align-items: flex-start;
}

.ios-instructions-text {
  margin-top: var(--md-spacing-sm);
}

.instruction-step {
  font-size: var(--md-body-size);
  color: var(--md-on-surface-variant);
  margin: var(--md-spacing-sm) 0;
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  line-height: 1.6;
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: var(--md-primary);
  color: white;
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 600;
  flex-shrink: 0;
}

.highlight {
  color: var(--md-primary);
  font-weight: 600;
}

.share-icon {
  width: 18px;
  height: 18px;
  display: inline-block;
  vertical-align: middle;
  margin: 0 2px;
  color: var(--md-primary);
}

@media (max-width: 767px) {
  .install-prompt {
    bottom: var(--md-spacing-md);
    padding: var(--md-spacing-sm);
  }

  .install-prompt-content {
    padding: var(--md-spacing-md);
  }

  .install-prompt-actions {
    flex-direction: column;
    width: 100%;
  }

  .dismiss-btn,
  .install-btn {
    width: 100%;
  }
}
</style>



