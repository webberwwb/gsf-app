<template>
  <div v-if="variants.length" class="variant-picker">
    <span class="picker-label">规格</span>
    <div class="chip-row" role="radiogroup" :aria-label="'规格选项'">
      <button
        v-if="allowNone"
        type="button"
        role="radio"
        :aria-checked="modelValue == null"
        class="option-chip"
        :class="{ selected: modelValue == null }"
        @click="$emit('update:modelValue', null)"
      >
        <span class="chip-label">无</span>
      </button>
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
        <span v-if="priceLabel(v)" class="chip-meta">{{ priceLabel(v) }}</span>
      </button>
    </div>
  </div>
</template>

<script>
import { formatVariantDelta, formatVariantPriceLabel, formatMoneyDisplay } from '../utils/productPriceDisplay'

export default {
  name: 'ProductVariantPicker',
  props: {
    variants: { type: Array, default: () => [] },
    modelValue: { type: [Number, null], default: null },
    allowNone: { type: Boolean, default: false },
    product: { type: Object, default: null }
  },
  emits: ['update:modelValue'],
  methods: {
    priceLabel(v) {
      if (this.product) {
        return formatVariantPriceLabel(this.product, v)
      }
      const d = parseFloat(v.price_delta || 0)
      if (d) return formatVariantDelta(d)
      if (v.price != null) return formatMoneyDisplay(v.price)
      return ''
    }
  }
}
</script>

<style scoped>
.variant-picker {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
  margin-top: 0.35rem;
}

.picker-label {
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--md-on-surface-variant);
  flex-shrink: 0;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.option-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  min-height: 28px;
  padding: 0.2rem 0.6rem;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 999px;
  background: #fff;
  color: var(--md-on-surface-variant);
  font-size: 0.6875rem;
  font-weight: 500;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s, background 0.15s;
}

.option-chip:hover:not(.selected) {
  border-color: rgba(255, 140, 0, 0.45);
  color: var(--md-on-surface);
}

.option-chip.selected {
  border-color: var(--md-primary);
  background: rgba(255, 140, 0, 0.1);
  color: var(--md-primary);
  font-weight: 600;
}

.chip-meta {
  font-size: 0.625rem;
  font-weight: 600;
  opacity: 0.9;
}
</style>
