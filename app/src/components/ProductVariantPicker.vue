<template>
  <div v-if="variants.length" class="variant-picker">
    <div class="picker-header">
      <span class="picker-title">选项</span>
      <span class="picker-badge">必选</span>
    </div>
    <div class="chip-row" role="radiogroup" :aria-label="'选项'">
      <button
        v-for="v in variants"
        :key="v.id"
        type="button"
        role="radio"
        :aria-checked="modelValue === v.id"
        class="option-chip"
        :class="{ selected: modelValue === v.id }"
        @click="$emit('update:modelValue', v.id)"
      >
        <span class="chip-label">{{ v.name }}</span>
        <span v-if="hasDelta(v)" class="chip-meta">
          {{ formatDelta(v.price_delta) }}
        </span>
        <svg
          v-if="modelValue === v.id"
          class="chip-check"
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          aria-hidden="true"
        >
          <path
            fill-rule="evenodd"
            d="M16.704 5.29a1 1 0 010 1.42l-7.25 7.25a1 1 0 01-1.42 0l-3.25-3.25a1 1 0 111.42-1.42l2.54 2.54 6.54-6.54a1 1 0 011.42 0z"
            clip-rule="evenodd"
          />
        </svg>
      </button>
    </div>
  </div>
</template>


<script>
import { formatVariantDelta } from '../utils/productPriceDisplay'

export default {
  name: 'ProductVariantPicker',
  props: {
    productId: { type: [Number, String], required: true },
    variants: { type: Array, default: () => [] },
    modelValue: { type: [Number, null], default: null }
  },
  emits: ['update:modelValue'],
  methods: {
    hasDelta(v) {
      const d = parseFloat(v.price_delta || 0)
      return d !== 0
    },
    formatDelta(delta) {
      const d = parseFloat(delta || 0)
      if (d === 0) return ''
      return formatVariantDelta(d)
    }
  }
}
</script>

<style scoped>
.variant-picker {
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

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.option-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  min-height: 36px;
  padding: 0.4rem 0.85rem;
  border: 1.5px solid var(--md-outline-variant);
  border-radius: 999px;
  background: var(--md-surface);
  color: var(--md-on-surface);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition:
    border-color 0.2s ease,
    background 0.2s ease,
    box-shadow 0.2s ease;
  -webkit-tap-highlight-color: transparent;
}

.option-chip:hover {
  border-color: var(--md-primary);
  background: var(--md-surface-variant);
}

.option-chip.selected {
  border-color: var(--md-primary);
  background: rgba(255, 140, 0, 0.1);
  box-shadow: 0 1px 4px rgba(255, 140, 0, 0.15);
  padding-right: 0.65rem;
}

.chip-label {
  line-height: 1.2;
}

.chip-meta {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--md-primary);
  opacity: 0.9;
}

.chip-check {
  width: 1rem;
  height: 1rem;
  color: var(--md-primary);
  flex-shrink: 0;
}
</style>
