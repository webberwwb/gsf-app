<template>
  <div
    class="page-loading"
    :class="{ overlay }"
    role="status"
    aria-live="polite"
    aria-busy="true"
  >
    <div class="card">
      <div class="orb" aria-hidden="true">
        <span class="glow"></span>
        <span class="ring outer"></span>
        <span class="ring inner"></span>
        <span class="hub"></span>
      </div>
      <p class="label">{{ label }}</p>
      <p v-if="hint" class="hint">{{ hint }}</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PageLoading',
  props: {
    label: {
      type: String,
      default: '加载中…'
    },
    hint: {
      type: String,
      default: ''
    },
    overlay: {
      type: Boolean,
      default: false
    }
  }
}
</script>

<style scoped>
.page-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: min(56vh, 440px);
  padding: 2.5rem 1.25rem;
  box-sizing: border-box;
}

.page-loading.overlay {
  position: absolute;
  inset: 0;
  z-index: 8;
  min-height: 0;
  background: rgba(255, 252, 247, 0.78);
  backdrop-filter: blur(7px);
  -webkit-backdrop-filter: blur(7px);
}

.card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.85rem;
  padding: 1.75rem 1.75rem 1.5rem;
  border-radius: 20px;
  background: #fff;
  box-shadow:
    0 1px 2px rgba(255, 140, 0, 0.08),
    0 18px 40px rgba(255, 140, 0, 0.14);
  animation: rise 0.35s ease-out;
}

.orb {
  position: relative;
  width: 72px;
  height: 72px;
}

.glow {
  position: absolute;
  inset: 8px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 140, 0, 0.28) 0%, rgba(255, 140, 0, 0) 70%);
  animation: breathe 1.4s ease-in-out infinite;
}

.ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 3.5px solid transparent;
  box-sizing: border-box;
}

.ring.outer {
  border-top-color: var(--md-primary, #FF8C00);
  border-right-color: var(--md-primary, #FF8C00);
  animation: spin 0.85s linear infinite;
}

.ring.inner {
  inset: 12px;
  border-bottom-color: #FFB347;
  border-left-color: rgba(255, 140, 0, 0.35);
  animation: spin-rev 1.25s linear infinite;
}

.hub {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 10px;
  height: 10px;
  margin: -5px 0 0 -5px;
  border-radius: 50%;
  background: var(--md-primary, #FF8C00);
  box-shadow: 0 0 0 4px rgba(255, 140, 0, 0.16);
}

.label {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--md-on-surface, #1c1b16);
}

.hint {
  margin: 0;
  font-size: 0.875rem;
  color: var(--md-on-surface-variant, #6b6558);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes spin-rev {
  to { transform: rotate(-360deg); }
}

@keyframes breathe {
  0%, 100% { opacity: 0.45; transform: scale(0.92); }
  50% { opacity: 1; transform: scale(1.08); }
}

@keyframes rise {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (prefers-reduced-motion: reduce) {
  .ring, .glow, .card {
    animation: none;
  }
}
</style>
