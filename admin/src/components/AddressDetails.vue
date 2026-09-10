<template>
  <div class="address-details" :class="{ compact, empty: !address }">
    <template v-if="address">
      <div v-if="address.recipient_name || address.phone" class="address-contact">
        <span v-if="address.recipient_name" class="recipient-name">{{ address.recipient_name }}</span>
        <a
          v-if="address.phone"
          class="address-phone"
          :href="`tel:${address.phone}`"
          @click.stop
        >{{ address.phone }}</a>
      </div>
      <div v-if="address.address_line1" class="address-line">{{ address.address_line1 }}</div>
      <div v-if="address.address_line2" class="address-line">{{ address.address_line2 }}</div>
      <div v-if="cityLine" class="address-line">{{ cityLine }}</div>
      <div v-if="address.delivery_instructions" class="delivery-instructions">
        <span class="instructions-label">配送说明：</span>{{ address.delivery_instructions }}
      </div>
      <div v-if="showEmail && address.notification_email" class="address-email">
        通知邮箱：{{ address.notification_email }}
      </div>
    </template>
    <template v-else>无地址</template>
  </div>
</template>

<script>
export default {
  name: 'AddressDetails',
  props: {
    address: {
      type: Object,
      default: null
    },
    compact: {
      type: Boolean,
      default: false
    },
    showEmail: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    cityLine() {
      const a = this.address
      if (!a) return ''
      return [a.city, a.postal_code].filter(Boolean).join(', ')
    }
  }
}
</script>

<style scoped>
.address-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  overflow-wrap: anywhere;
}

.address-details.empty {
  color: rgba(0, 0, 0, 0.5);
}

.address-contact {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 8px;
}

.recipient-name {
  font-weight: 600;
  color: rgba(0, 0, 0, 0.87);
}

.address-phone {
  display: inline-flex;
  align-items: center;
  color: #1565C0;
  text-decoration: none;
  font-weight: 600;
  padding: 2px 8px;
  background: #E3F2FD;
  border-radius: 8px;
  line-height: 1.3;
  white-space: nowrap;
  overflow-wrap: normal;
  word-break: keep-all;
  flex-shrink: 0;
  min-height: 0;
  min-width: 0;
  height: auto;
}

.address-line {
  color: rgba(0, 0, 0, 0.8);
  line-height: 1.45;
}

.delivery-instructions {
  margin-top: 2px;
  color: rgba(0, 0, 0, 0.8);
  line-height: 1.45;
  white-space: pre-wrap;
}

.instructions-label {
  font-weight: 600;
  color: #E65100;
}

.address-email {
  font-size: 0.8125rem;
  color: rgba(0, 0, 0, 0.6);
}

.compact .recipient-name,
.compact .address-line,
.compact .delivery-instructions,
.compact .address-email {
  font-size: 0.8125rem;
}

.compact .address-phone {
  font-size: 0.75rem;
}
</style>
