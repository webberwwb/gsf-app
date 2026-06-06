<template>
  <template v-if="hasContent">
    <!-- Variants: 产品细节 -->
    <div v-if="variants.length" class="product-details">
      <div class="details-head">
        <span class="details-title">产品细节</span>
      </div>
      <div class="chip-row" role="radiogroup" aria-label="产品细节">
        <button
          v-for="v in variants"
          :key="v.id"
          type="button"
          role="radio"
          :aria-checked="variantId === v.id"
          class="mini-chip"
          :class="{ selected: variantId === v.id }"
          @click="$emit('update:variantId', v.id)"
        >
          <span>{{ v.name }}</span>
          <span v-if="hasDelta(v)" class="chip-extra">{{ formatDelta(v.price_delta) }}</span>
        </button>
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
          <span v-if="priceLabel" class="sub-price">{{ priceLabel }}</span>
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
import { formatSubstitutePriceLabel } from '../utils/orderItemPricing'
import { formatVariantDelta } from '../utils/productPriceDisplay'

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
    productId: { type: [Number, String], required: true },
    variants: { type: Array, default: () => [] },
    substitute: { type: Object, default: null },
    variantId: { type: [Number, null], default: null },
    acceptSubstitute: { type: [Boolean, null], default: null }
  },
  emits: ['update:variantId', 'update:acceptSubstitute'],
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
    priceLabel() {
      return formatSubstitutePriceLabel(this.substitute)
    }
  },
  methods: {
    hasDelta(v) {
      return parseFloat(v.price_delta || 0) !== 0
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
.product-details,
.substitute-section {
  margin: 0.5rem 0 0.625rem;
  padding: 0.5rem 0.625rem 0.5625rem;
  border-radius: 10px;
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
  font-size: 0.6875rem;
  opacity: 0.85;
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
