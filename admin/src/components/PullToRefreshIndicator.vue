<template>
  <div
    class="pull-to-refresh-indicator"
    :class="{ refreshing, ready: readyToRefresh && !refreshing }"
    :style="{ height: `${height}px` }"
    aria-live="polite"
  >
    <svg
      class="ptr-spinner"
      :class="{ spinning: refreshing }"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle class="ptr-track" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
      <path
        class="ptr-head"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
    <span class="ptr-label">{{ statusText }}</span>
  </div>
</template>

<script>
export default {
  name: 'PullToRefreshIndicator',
  props: {
    height: {
      type: Number,
      default: 0
    },
    refreshing: {
      type: Boolean,
      default: false
    },
    readyToRefresh: {
      type: Boolean,
      default: false
    },
    statusText: {
      type: String,
      default: '下拉刷新'
    }
  }
}
</script>

<style scoped>
.pull-to-refresh-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  overflow: hidden;
  color: var(--md-primary);
  transition: height 0.2s ease;
  user-select: none;
  pointer-events: none;
}

.ptr-spinner {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
  transform: rotate(calc(var(--pull-rotation, 0) * 1deg));
  transition: transform 0.15s ease;
}

.ptr-spinner.spinning {
  animation: ptr-spin 0.8s linear infinite;
}

.ptr-track {
  opacity: 0.25;
}

.ptr-label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--md-on-surface-variant);
}

.pull-to-refresh-indicator.ready .ptr-label {
  color: var(--md-primary);
}

@keyframes ptr-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
