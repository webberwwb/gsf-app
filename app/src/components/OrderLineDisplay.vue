<template>
  <div
    class="order-line"
    :class="{
      'is-declined': isDeclined,
      'is-pending-sub': isPending
    }"
  >
    <div class="line-main">
      <span class="line-name">{{ displayName }}</span>
      <div v-if="detailTags.length" class="line-tags">
        <span v-for="(tag, i) in detailTags" :key="i" class="detail-tag">{{ tag }}</span>
      </div>
      <span v-if="item.is_substituted" class="badge badge-sub">已换备选</span>
      <span v-if="isDeclined" class="badge badge-declined">缺货·不要备选</span>
      <span v-else-if="isPending" class="badge badge-pending">待确认备选</span>
    </div>
    <div class="line-meta">
      <span v-if="qtyLabel" class="line-qty">{{ qtyLabel }}</span>
      <span class="line-price" :class="{ zero: isZeroPrice, range: !!item.price_display }">{{ displayPrice }}</span>
    </div>
  </div>
</template>

<script>
import {
  formatSubstitutePreferenceLabel,
  formatLinePrice,
  resolveOrderLineTotal,
  isOrderLinePriceEstimated,
  getOrderLineWeightLabel,
  isDeclinedSubstituteLine,
  isPendingSubstituteLine
} from '../utils/orderItemPricing'

export default {
  name: 'OrderLineDisplay',
  props: {
    item: { type: Object, required: true }
  },
  computed: {
    isDeclined() {
      return isDeclinedSubstituteLine(this.item)
    },
    isPending() {
      return isPendingSubstituteLine(this.item)
    },
    displayName() {
      return this.item.display_name || this.item.product?.name || '商品'
    },
    variantLabel() {
      if (this.item.variant?.name) return this.item.variant.name
      if (this.item.variant_name) return this.item.variant_name
      return null
    },
    substitutePreferenceLabel() {
      if (this.item.is_substituted) return null
      if (this.item.substitute_preference_label) return this.item.substitute_preference_label
      if (this.item.show_substitute_preference === false) return null
      if (this.item.accept_substitute == null && !this.item.show_substitute_preference) return null
      return formatSubstitutePreferenceLabel(this.item.accept_substitute)
    },
    weightLabel() {
      return getOrderLineWeightLabel(this.item)
    },
    detailTags() {
      const tags = []
      if (this.variantLabel) tags.push(this.variantLabel)
      const sub = this.substitutePreferenceLabel
      if (sub) tags.push(sub)
      const w = this.weightLabel
      if (w) tags.push(w)
      return tags
    },
    qtyLabel() {
      const q = this.item.quantity
      if (!q) return null
      const suffix = this.item.product?.pricing_type === 'bundled_weight' ? ' 份' : ''
      return `×${q}${suffix}`
    },
    displayPrice() {
      if (this.item.price_display) return this.item.price_display
      return formatLinePrice(resolveOrderLineTotal(this.item), {
        estimated: isOrderLinePriceEstimated(this.item)
      })
    },
    isZeroPrice() {
      const total = resolveOrderLineTotal(this.item)
      return total === 0 && (this.isDeclined || this.isPending || this.item.is_unavailable)
    }
  }
}
</script>

<style scoped>
.order-line {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.5rem 0.35rem;
  border-radius: 6px;
}

.order-line.is-declined {
  background: #ffebee;
  border-left: 3px solid #c62828;
  padding-left: 0.5rem;
}

.order-line.is-pending-sub {
  background: #fff8e1;
  border-left: 3px solid #f57c00;
  padding-left: 0.5rem;
}

.line-main {
  flex: 1;
  min-width: 0;
}

.line-name {
  font-weight: 500;
  font-size: 0.9375rem;
  color: var(--md-on-surface);
}

.order-line.is-declined .line-name {
  color: #b71c1c;
}

.line-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  margin-top: 0.25rem;
}

.detail-tag {
  display: inline-block;
  font-size: 0.6875rem;
  font-weight: 400;
  line-height: 1.2;
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
  color: var(--md-on-surface-variant);
  background: rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.badge {
  display: inline-block;
  font-size: 0.6875rem;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  margin-top: 0.2rem;
  margin-right: 0.25rem;
  vertical-align: middle;
}

.badge-sub {
  background: #e8f5e9;
  color: #2e7d32;
}

.badge-declined {
  background: #ffcdd2;
  color: #b71c1c;
  font-weight: 600;
}

.badge-pending {
  background: #ffe0b2;
  color: #e65100;
}

.line-meta {
  text-align: right;
  flex-shrink: 0;
}

.line-qty {
  display: block;
  font-size: 0.75rem;
  color: var(--md-on-surface-variant);
}

.line-price {
  font-weight: 600;
  font-size: 0.875rem;
  font-variant-numeric: tabular-nums;
  color: var(--md-on-surface);
}

.line-price.range {
  font-size: 0.8125rem;
  font-weight: 500;
}

.line-price.zero {
  color: var(--md-on-surface-variant);
}
</style>
