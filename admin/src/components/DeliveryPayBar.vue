<template>
  <div class="pay-bar" :class="kind">{{ text }}</div>
</template>

<script>
import { deliveryPayKind, deliveryPayText } from '../utils/deliveryPay'

export default {
  name: 'DeliveryPayBar',
  props: {
    order: {
      type: Object,
      required: true
    }
  },
  computed: {
    kind() {
      return deliveryPayKind(this.order)
    },
    text() {
      return deliveryPayText(this.order)
    }
  }
}
</script>

<style scoped>
.pay-bar {
  margin-top: 0.5rem;
  text-align: center;
  font-weight: 800;
  font-size: 1.05rem;
  letter-spacing: 0.04em;
  padding: 0.4rem 0.65rem;
  border-radius: var(--md-radius-sm);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pay-bar.cash {
  background: #b71c1c;
  color: #fff;
}

.pay-bar.prepaid {
  background: #e8f5e9;
  color: #1b5e20;
  border: 1px solid #2e7d32;
  font-weight: 700;
  font-size: 0.95rem;
}
</style>
