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

a {
  color: inherit;
  text-decoration: none;
}

:root {
  --app-safe-top: env(safe-area-inset-top, 0px);

  /* Brand — Grain Gold */
  --md-primary: #F0A800;
  --brand-hover: #D99800;
  --brand-pressed: #B88000;
  --brand-light: #F5BE43;
  --brand-gradient-start: var(--brand-light);
  --md-primary-variant: var(--brand-hover);

  --gradient-primary: linear-gradient(
    135deg,
    var(--brand-light),
    var(--md-primary)
  );

  --brand-tint: #FFF8E8;
  --brand-tint-strong: #FCEBC2;
  --brand-focus: rgba(240, 168, 0, 0.24);
  --brand-ink: #805600;

  /* Warm neutral foundation */
  --surface-page: #F7F4F0;
  --surface-card: #FFFEFC;
  --surface-subtle: #F3EEE8;
  --border-default: #E7DFD6;

  --text-primary: #302C29;
  --text-secondary: #756B61;
  --text-on-brand: #FFFFFF;

  --warning-text: #A34C25;
  --warning-bg: #FFF0E4;

  /* Existing tokens, pointed at the warm system */
  --md-surface: var(--surface-card);
  --md-surface-variant: var(--surface-subtle);
  --md-background: var(--surface-page);
  --md-on-surface: var(--text-primary);
  --md-on-surface-variant: var(--text-secondary);
  --md-outline: #A89B8E;
  --md-outline-variant: var(--border-default);
  --md-shadow: rgba(48, 44, 41, 0.08);

  --gradient-secondary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --gradient-accent: linear-gradient(135deg, #FF4444 0%, #FF6B35 100%);
  --gradient-success: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  --gradient-card: linear-gradient(to bottom, rgba(240, 168, 0, 0.04), var(--surface-card));
  --gradient-card-hover: linear-gradient(to bottom, rgba(240, 168, 0, 0.08), var(--surface-card));

  --overlay-light: rgba(255, 254, 252, 0.95);
  --overlay-primary: rgba(240, 168, 0, 0.1);
  --overlay-accent: rgba(255, 68, 68, 0.1);

  --md-elevation-1: 0 1px 2px rgba(48, 44, 41, 0.06);
  --md-elevation-2: 0 1px 3px rgba(48, 44, 41, 0.08);
  --md-elevation-3: 0 4px 12px rgba(48, 44, 41, 0.08);
  --md-elevation-4: 0 8px 24px rgba(48, 44, 41, 0.1);
  
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

/*
 * Narrow viewports + installed PWA (tablet/phone): hide scrollbars on
 * horizontal regions. Scroll / swipe still works.
 */
@media (max-width: 767px), ((display-mode: standalone) and (max-width: 1024px)) {
  .hide-x-scrollbar,
  .tabs,
  .tabs-container,
  .table-wrap,
  .repurchase-table-wrap,
  .products-table-container,
  .order-tabs,
  .table-container,
  .records-table-container,
  .attempts-table,
  .markdown-body pre {
    scrollbar-width: none;
    -ms-overflow-style: none;
  }

  .hide-x-scrollbar::-webkit-scrollbar,
  .tabs::-webkit-scrollbar,
  .tabs-container::-webkit-scrollbar,
  .table-wrap::-webkit-scrollbar,
  .repurchase-table-wrap::-webkit-scrollbar,
  .products-table-container::-webkit-scrollbar,
  .order-tabs::-webkit-scrollbar,
  .table-container::-webkit-scrollbar,
  .records-table-container::-webkit-scrollbar,
  .attempts-table::-webkit-scrollbar,
  .markdown-body pre::-webkit-scrollbar {
    display: none;
    width: 0;
    height: 0;
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

