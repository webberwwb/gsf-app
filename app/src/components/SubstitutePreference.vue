<template>
  <div v-if="substitute" class="substitute-preference">
    <div class="picker-header">
      <span class="picker-title">备选产品</span>
      <span class="picker-badge">必选</span>
    </div>

    <div class="substitute-card">
      <img
        v-if="substituteImage"
        :src="substituteImage"
        alt=""
        class="substitute-thumb"
      />
      <div class="substitute-info">
        <div class="substitute-name">{{ substitute.name }}</div>
        <p v-if="substitute.description" class="substitute-desc">{{ substitute.description }}</p>
        <p v-if="priceLabel" class="substitute-price">{{ priceLabel }}</p>
      </div>
    </div>

    <div class="segmented" role="radiogroup" aria-label="备选产品">
      <button
        type="button"
        role="radio"
        :aria-checked="modelValue === true"
        class="segment"
        :class="{ active: modelValue === true }"
        @click="$emit('update:modelValue', true)"
      >
        接受备选
      </button>
      <button
        type="button"
        role="radio"
        :aria-checked="modelValue === false"
        class="segment"
        :class="{ active: modelValue === false }"
        @click="$emit('update:modelValue', false)"
      >
        不要备选
      </button>
    </div>
    <p class="decline-hint">若原商品缺货，我们会尽量找货；若无法供应该商品会被取消，可能影响配送费档位。</p>
  </div>
</template>

<script>
import { formatSubstitutePriceLabel } from '../utils/orderItemPricing'

export default {
  name: 'SubstitutePreference',
  props: {
    substitute: { type: Object, default: null },
    modelValue: { type: [Boolean, null], default: null }
  },
  emits: ['update:modelValue'],
  computed: {
    substituteImage() {
      if (!this.substitute) return null
      const imgs = this.substitute.images || []
      return imgs[0] || this.substitute.image || null
    },
    priceLabel() {
      return formatSubstitutePriceLabel(this.substitute)
    }
  }
}
</script>

<style scoped>
.substitute-preference {
  margin: 0.75rem 0;
}

.picker-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.picker-title {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--md-on-surface);
  letter-spacing: 0.01em;
}

.picker-badge {
  font-size: 0.6875rem;
  font-weight: 600;
  line-height: 1;
  padding: 0.2rem 0.45rem;
  border-radius: 999px;
  color: var(--md-primary);
  background: rgba(255, 140, 0, 0.12);
}

.substitute-card {
  display: flex;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  margin-bottom: 0.5rem;
  background: var(--md-surface);
  border: 1px solid var(--md-outline-variant);
  border-radius: var(--md-radius-md);
}

.substitute-thumb {
  width: 48px;
  height: 48px;
  object-fit: cover;
  border-radius: var(--md-radius-sm);
  flex-shrink: 0;
}

.substitute-info {
  flex: 1;
  min-width: 0;
}

.substitute-name {
  font-weight: 600;
  font-size: 0.875rem;
  line-height: 1.3;
}

.substitute-desc {
  font-size: 0.75rem;
  color: var(--md-on-surface-variant);
  margin: 0.15rem 0 0;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.substitute-price {
  font-size: 0.8125rem;
  margin: 0.2rem 0 0;
  color: var(--md-primary);
  font-weight: 600;
}

.segmented {
  display: flex;
  padding: 3px;
  gap: 3px;
  background: var(--md-surface-variant);
  border-radius: 10px;
  border: 1px solid var(--md-outline-variant);
}

.segment {
  flex: 1;
  min-height: 38px;
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--md-on-surface-variant);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    box-shadow 0.2s ease;
  -webkit-tap-highlight-color: transparent;
}

.segment:hover:not(.active) {
  color: var(--md-on-surface);
}

.segment.active {
  background: var(--md-surface);
  color: var(--md-primary);
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.decline-hint {
  font-size: 0.75rem;
  color: var(--md-on-surface-variant);
  margin: 0.5rem 0 0;
  line-height: 1.4;
}
</style>
