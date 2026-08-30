<template>
  <template v-if="hasContent">
    <!-- Variants: 产品细节 with qty per option -->
    <div v-if="variants.length" class="product-details">
      <div class="variant-qty-list">
        <div
          v-for="v in variants"
          :key="v.id"
          class="variant-qty-row"
        >
          <div class="variant-qty-info">
            <span class="variant-qty-name">{{ v.name }}</span>
            <span v-if="variantPriceLabel(v)" class="chip-extra">{{ variantPriceLabel(v) }}</span>
          </div>
          <div class="variant-qty-control">
            <button
              type="button"
              class="vq-btn"
              :disabled="disabled || variantQty(v.id) === 0"
              @click="$emit('change-variant-qty', v.id, variantQty(v.id) - 1)"
            >-</button>
            <input
              type="number"
              class="vq-input"
              min="0"
              :value="variantQty(v.id)"
              :disabled="disabled"
              @input="$emit('change-variant-qty', v.id, $event.target.value)"
            />
            <button
              type="button"
              class="vq-btn"
              :disabled="disabled"
              @click="$emit('change-variant-qty', v.id, variantQty(v.id) + 1)"
            >+</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Substitute: 备选产品 -->
    <div v-if="substitute" class="substitute-section">
      <div class="details-head">
        <span class="details-title">备选产品</span>
        <button
          type="button"
          class="info-trigger"
          aria-label="备选产品说明"
          @click.stop="showSubstituteInfo = true"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="info-icon" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </button>
      </div>
      <div class="sub-inline">
        <img
          v-if="substituteImage"
          :src="substituteImage"
          alt=""
          class="sub-thumb"
        />
        <div class="sub-text">
          <span class="sub-name">{{ substitute.name }}</span>
          <span v-if="substitute.description" class="sub-desc">{{ substitute.description }}</span>
          <span v-if="substitutePriceLabel" class="sub-price">{{ substitutePriceLabel }}</span>
        </div>
      </div>
      <div class="chip-row" role="radiogroup" aria-label="备选产品">
        <button
          type="button"
          role="radio"
          :aria-checked="acceptSubstitute === true"
          class="mini-chip"
          :class="{ selected: acceptSubstitute === true }"
          @click="$emit('update:acceptSubstitute', true)"
        >
          接受备选
        </button>
        <button
          type="button"
          role="radio"
          :aria-checked="acceptSubstitute === false"
          class="mini-chip"
          :class="{ selected: acceptSubstitute === false }"
          @click="$emit('update:acceptSubstitute', false)"
        >
          不要备选
        </button>
      </div>
    </div>

    <Modal
      :show="showSubstituteInfo"
      type="info"
      title="备选产品说明"
      :message="substituteInfoMessage"
      :show-cancel="false"
      :icon="true"
      confirm-text="知道了"
      @confirm="showSubstituteInfo = false"
      @close="showSubstituteInfo = false"
    />
  </template>
</template>

<script>
import Modal from './Modal.vue'
import { formatSubstitutePriceLabel, getVariantQuantity } from '../utils/orderItemPricing'
import { formatVariantPriceLabel } from '../utils/productPriceDisplay'

const SUBSTITUTE_INFO_MESSAGE = `
<p>若您订购的原商品缺货：</p>
<ul>
  <li><strong>接受备选</strong>：将自动更换为备选产品，并按备选产品的价格结算（通常更优惠）。</li>
  <li><strong>不要备选</strong>：我们会尽量为您找原商品；若最终无法供应，该商品会被自动取消，可能影响配送费档位。</li>
</ul>
<p>请在下单前选择您的偏好。</p>
`.trim()

export default {
  name: 'ProductDetailsSection',
  components: { Modal },
  props: {
    product: { type: Object, default: null },
    productId: { type: [Number, String], required: true },
    variants: { type: Array, default: () => [] },
    substitute: { type: Object, default: null },
    variantId: { type: [Number, null], default: null },
    variantQuantities: { type: Object, default: () => ({}) },
    acceptSubstitute: { type: [Boolean, null], default: null },
    disabled: { type: Boolean, default: false }
  },
  emits: ['update:variantId', 'update:acceptSubstitute', 'change-variant-qty'],
  data() {
    return {
      showSubstituteInfo: false,
      substituteInfoMessage: SUBSTITUTE_INFO_MESSAGE
    }
  },
  computed: {
    hasContent() {
      return (this.variants && this.variants.length > 0) || !!this.substitute
    },
    substituteImage() {
      if (!this.substitute) return null
      const imgs = this.substitute.images || []
      return imgs[0] || this.substitute.image || null
    },
    substitutePriceLabel() {
      return formatSubstitutePriceLabel(this.substitute)
    }
  },
  methods: {
    variantQty(variantId) {
      return getVariantQuantity(
        { variant_quantities: this.variantQuantities, variant_id: this.variantId },
        variantId
      )
    },
    variantPriceLabel(v) {
      return formatVariantPriceLabel(this.product, v)
    }
  }
}
</script>

<style scoped>
.product-details,
.substitute-section {
  margin: 0.25rem 0 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: 12px;
  background: linear-gradient(
    145deg,
    rgba(255, 140, 0, 0.05) 0%,
    rgba(255, 255, 255, 0.4) 42%,
    rgba(0, 0, 0, 0.015) 100%
  );
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.03),
    inset 0 1px 0 rgba(255, 255, 255, 0.65);
}

.substitute-section {
  background: linear-gradient(
    145deg,
    rgba(0, 0, 0, 0.02) 0%,
    rgba(255, 255, 255, 0.35) 50%,
    rgba(0, 0, 0, 0.01) 100%
  );
}

.details-head {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  margin-bottom: 0.375rem;
}

.info-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: transparent;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
  transition: background 0.18s ease;
}

.info-trigger:hover,
.info-trigger:active {
  background: rgba(0, 0, 0, 0.05);
}

.info-icon {
  width: 14px;
  height: 14px;
  color: var(--md-on-surface-variant);
  opacity: 0.65;
}

.info-trigger:hover .info-icon,
.info-trigger:active .info-icon {
  opacity: 1;
  color: var(--md-primary);
}

.details-title {
  font-size: 0.6875rem;
  font-weight: 500;
  letter-spacing: 0.06em;
  color: var(--md-on-surface-variant);
  opacity: 0.72;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
}

.substitute-section .chip-row {
  margin-top: 0.375rem;
}

.mini-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  min-height: 26px;
  padding: 0.2rem 0.55rem;
  border: 1px solid rgba(0, 0, 0, 0.07);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.55);
  color: var(--md-on-surface-variant);
  font-size: 0.75rem;
  font-weight: 400;
  line-height: 1.2;
  cursor: pointer;
  transition:
    border-color 0.18s ease,
    background 0.18s ease,
    color 0.18s ease,
    box-shadow 0.18s ease,
    transform 0.12s ease;
  -webkit-tap-highlight-color: transparent;
}

.mini-chip:hover {
  border-color: rgba(255, 140, 0, 0.28);
  background: rgba(255, 255, 255, 0.85);
  color: var(--md-on-surface);
}

.mini-chip:active {
  transform: scale(0.97);
}

.mini-chip.selected {
  border-color: rgba(255, 140, 0, 0.45);
  background: rgba(255, 140, 0, 0.09);
  color: var(--md-primary);
  font-weight: 500;
  box-shadow: 0 1px 3px rgba(255, 140, 0, 0.12);
}

.chip-extra {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--md-primary);
  opacity: 0.9;
  white-space: nowrap;
  flex-shrink: 0;
}

.variant-qty-list {
  display: flex;
  flex-direction: column;
}

.variant-qty-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: nowrap;
  min-height: 44px;
  padding: 0.2rem 0;
}

.variant-qty-row + .variant-qty-row {
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.variant-qty-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 0;
  flex: 1;
}

.variant-qty-name {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--md-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.variant-qty-control {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  flex-shrink: 0;
}

.vq-btn {
  width: 36px;
  height: 36px;
  border: 1px solid var(--md-outline-variant);
  border-radius: 10px;
  background: var(--md-surface);
  color: var(--md-on-surface);
  font-size: 1.125rem;
  font-weight: 500;
  line-height: 1;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.vq-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.vq-input {
  width: 2.5rem;
  height: 36px;
  text-align: center;
  border: 1px solid var(--md-outline-variant);
  border-radius: 10px;
  font-size: 1rem;
  -moz-appearance: textfield;
}

.vq-input::-webkit-outer-spin-button,
.vq-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.sub-inline {
  display: flex;
  align-items: flex-start;
  gap: 0.4375rem;
  min-width: 0;
}

.sub-thumb {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  object-fit: cover;
  flex-shrink: 0;
  opacity: 0.92;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}

.sub-text {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  min-width: 0;
}

.sub-name {
  font-size: 0.75rem;
  font-weight: 400;
  color: var(--md-on-surface-variant);
  line-height: 1.25;
}

.sub-desc {
  font-size: 0.6875rem;
  color: var(--md-on-surface-variant);
  opacity: 0.75;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.sub-price {
  font-size: 0.6875rem;
  font-weight: 500;
  color: var(--md-primary);
  opacity: 0.88;
}
</style>
