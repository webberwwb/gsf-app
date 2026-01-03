<template>
  <transition name="slide-up">
    <div v-if="showPrompt" class="update-prompt">
      <div class="update-content">
        <div class="update-icon">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </div>
        <div class="update-text">
          <h3>新版本可用</h3>
          <p>点击刷新以获取最新功能</p>
        </div>
        <button @click="updateApp" class="update-btn">
          刷新
        </button>
        <button @click="dismissPrompt" class="dismiss-btn">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  </transition>
</template>

<script>
export default {
  name: 'UpdatePrompt',
  data() {
    return {
      showPrompt: false,
      registration: null
    }
  },
  mounted() {
    this.checkForUpdates()
  },
  methods: {
    checkForUpdates() {
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.ready.then((registration) => {
          this.registration = registration
          
          // Check for updates every 5 minutes
          setInterval(() => {
            registration.update()
          }, 5 * 60 * 1000)
          
          // Listen for new service worker waiting
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing
            
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                // New service worker available
                this.showPrompt = true
              }
            })
          })
          
          // Check if there's already a waiting service worker
          if (registration.waiting) {
            this.showPrompt = true
          }
        })
      }
    },
    updateApp() {
      if (this.registration && this.registration.waiting) {
        // Tell the waiting service worker to skip waiting
        this.registration.waiting.postMessage({ type: 'SKIP_WAITING' })
        
        // Reload the page when the new service worker takes control
        navigator.serviceWorker.addEventListener('controllerchange', () => {
          window.location.reload()
        })
      } else {
        // Force reload to get latest version
        window.location.reload(true)
      }
    },
    dismissPrompt() {
      this.showPrompt = false
    }
  }
}
</script>

<style scoped>
.update-prompt {
  position: fixed;
  bottom: var(--md-spacing-lg);
  left: 50%;
  transform: translateX(-50%);
  z-index: 10000;
  width: 90%;
  max-width: 450px;
  padding: 0 var(--md-spacing-md);
}

.update-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-md);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
  position: relative;
  backdrop-filter: blur(10px);
}

.update-icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.update-icon svg {
  width: 24px;
  height: 24px;
  color: white;
}

.update-text {
  flex: 1;
  color: white;
}

.update-text h3 {
  font-size: var(--md-body-size);
  font-weight: 600;
  margin: 0 0 0.25rem 0;
}

.update-text p {
  font-size: var(--md-label-size);
  margin: 0;
  opacity: 0.9;
}

.update-btn {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  background: white;
  color: #667eea;
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-label-size);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
}

.update-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.update-btn:active {
  transform: scale(0.95);
}

.dismiss-btn {
  position: absolute;
  top: var(--md-spacing-xs);
  right: var(--md-spacing-xs);
  width: 28px;
  height: 28px;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 0;
}

.dismiss-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.dismiss-btn svg {
  width: 16px;
  height: 16px;
  color: white;
}

/* Slide up animation */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-up-enter-from {
  transform: translate(-50%, 100px);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translate(-50%, 100px);
  opacity: 0;
}

@media (max-width: 767px) {
  .update-prompt {
    bottom: var(--md-spacing-md);
    width: calc(100% - var(--md-spacing-md) * 2);
  }
  
  .update-content {
    padding: var(--md-spacing-sm);
  }

  .update-text h3 {
    font-size: var(--md-label-size);
  }

  .update-text p {
    font-size: 12px;
  }

  .update-btn {
    padding: var(--md-spacing-xs) var(--md-spacing-sm);
    font-size: 12px;
  }
}
</style>






