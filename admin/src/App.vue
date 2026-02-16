<template>
  <div id="app">
    <router-view />
    <Modal
      :show="modalState.show"
      :type="modalState.type"
      :title="modalState.title"
      :message="modalState.message"
      :confirmText="modalState.confirmText"
      :cancelText="modalState.cancelText"
      :showCancel="modalState.showCancel"
      :showClose="modalState.showClose"
      :icon="modalState.icon"
      :closeOnOverlay="modalState.closeOnOverlay"
      @confirm="modalState.onConfirm"
      @cancel="modalState.onCancel"
      @close="modalState.onCancel"
    />
    <InstallPrompt />
    <UpdatePrompt />
  </div>
</template>

<script>
import Modal from './components/Modal.vue'
import InstallPrompt from './components/InstallPrompt.vue'
import UpdatePrompt from './components/UpdatePrompt.vue'
import { useModal } from './composables/useModal'

export default {
  name: 'App',
  components: {
    Modal,
    InstallPrompt,
    UpdatePrompt
  },
  setup() {
    const { modalState } = useModal()
    return { modalState }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  /* Material Design 3 Colors */
  --md-primary: #FF8C00;
  --md-primary-variant: #FFD700;
  --md-surface: #FFFFFF;
  --md-surface-variant: #F5F5F5;
  --md-background: linear-gradient(135deg, #fafbfc 0%, #f5f7fa 100%);
  --md-on-surface: #1C1B1F;
  --md-on-surface-variant: #49454F;
  --md-outline: #79747E;
  --md-shadow: rgba(0, 0, 0, 0.15);
  
  /* Gradient Colors */
  --gradient-primary: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  --gradient-secondary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --gradient-accent: linear-gradient(135deg, #FF4444 0%, #FF6B35 100%);
  --gradient-success: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  --gradient-card: linear-gradient(to bottom, rgba(255, 140, 0, 0.05), rgba(255, 255, 255, 1));
  --gradient-card-hover: linear-gradient(to bottom, rgba(255, 140, 0, 0.1), rgba(255, 255, 255, 1));
  
  /* Semi-transparent overlays */
  --overlay-light: rgba(255, 255, 255, 0.95);
  --overlay-primary: rgba(255, 140, 0, 0.1);
  --overlay-accent: rgba(255, 68, 68, 0.1);
  
  /* Elevation shadows with color tints */
  --md-elevation-1: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
  --md-elevation-2: 0 3px 6px rgba(255, 140, 0, 0.16), 0 3px 6px rgba(255, 140, 0, 0.23);
  --md-elevation-3: 0 10px 20px rgba(255, 140, 0, 0.19), 0 6px 6px rgba(255, 140, 0, 0.23);
  --md-elevation-4: 0 14px 28px rgba(255, 140, 0, 0.25), 0 10px 10px rgba(255, 140, 0, 0.22);
  
  /* Typography */
  --md-font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', Oxygen, Ubuntu, Cantarell, sans-serif;
  --md-headline-size: 1.5rem;
  --md-title-size: 1.25rem;
  --md-body-size: 1rem;
  --md-label-size: 0.875rem;
  
  /* Spacing */
  --md-spacing-xs: 0.25rem;
  --md-spacing-sm: 0.5rem;
  --md-spacing-md: 1rem;
  --md-spacing-lg: 1.5rem;
  --md-spacing-xl: 2rem;
  
  /* Border radius */
  --md-radius-sm: 8px;
  --md-radius-md: 12px;
  --md-radius-lg: 16px;
  --md-radius-xl: 24px;
  
  /* Transitions */
  --transition-fast: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  --transition-normal: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

body {
  font-family: var(--md-font-family);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: var(--md-background);
  background-attachment: fixed;
  color: var(--md-on-surface);
  line-height: 1.5;
  min-height: 100vh;
  overflow-x: hidden;
  max-width: 100vw;
}

#app {
  min-height: 100vh;
  /* Prevent horizontal scroll on mobile */
  overflow-x: hidden;
  max-width: 100vw;
}

/* Material Design transitions */
.material-transition {
  transition: var(--transition-normal);
}

/* Gradient animations */
@keyframes gradient-shift {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

/* Pulse animation */
@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.9;
  }
}

/* Fade in animation */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Ripple effect */
@keyframes ripple {
  0% {
    transform: scale(0);
    opacity: 1;
  }
  100% {
    transform: scale(4);
    opacity: 0;
  }
}

/* Mobile-specific improvements */
@media (max-width: 767px) {
  body {
    /* Prevent text size adjustment on iOS */
    -webkit-text-size-adjust: 100%;
    text-size-adjust: 100%;
  }

  /* Improve touch targets */
  button, a {
    min-height: 44px;
    min-width: 44px;
  }

  /* Prevent pull-to-refresh on mobile */
  body {
    overscroll-behavior-y: contain;
  }
}

/* Safe area support for iOS */
@supports (padding: max(0px)) {
  #app {
    padding-left: max(0px, env(safe-area-inset-left));
    padding-right: max(0px, env(safe-area-inset-right));
  }
}
</style>

