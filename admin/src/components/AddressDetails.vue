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
      <div v-if="mapsCopyText" class="civic-row">
        <div class="civic-text">
          <div v-if="address.address_line1" class="address-line civic">{{ address.address_line1 }}</div>
          <div v-if="address.address_line2" class="address-line">{{ address.address_line2 }}</div>
          <div v-if="cityLine" class="address-line civic">{{ cityLine }}</div>
        </div>
        <button
          type="button"
          class="copy-address-btn"
          :title="copied ? '已复制' : '复制地址到地图'"
          @click.stop="copyForMaps"
        >
          <svg v-if="!copied" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </button>
      </div>
      <div v-if="address.delivery_instructions" class="address-line">{{ address.delivery_instructions }}</div>
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
  data() {
    return {
      copied: false,
      copyTimer: null
    }
  },
  computed: {
    cityLine() {
      const a = this.address
      if (!a) return ''
      return [a.city, a.postal_code].filter(Boolean).join(', ')
    },
    mapsCopyText() {
      const a = this.address
      if (!a) return ''
      const cityPostal = [a.city, a.postal_code].filter(Boolean).join(' ')
      return [a.address_line1, a.address_line2, cityPostal].filter(Boolean).join(', ')
    }
  },
  beforeUnmount() {
    clearTimeout(this.copyTimer)
  },
  methods: {
    async copyForMaps() {
      const text = this.mapsCopyText
      if (!text) return
      try {
        await navigator.clipboard.writeText(text)
      } catch {
        const el = document.createElement('textarea')
        el.value = text
        el.setAttribute('readonly', '')
        el.style.position = 'fixed'
        el.style.left = '-9999px'
        document.body.appendChild(el)
        el.select()
        document.execCommand('copy')
        document.body.removeChild(el)
      }
      this.copied = true
      clearTimeout(this.copyTimer)
      this.copyTimer = setTimeout(() => {
        this.copied = false
      }, 1500)
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
  width: 100%;
  max-width: 100%;
  overflow-wrap: break-word;
  word-break: break-word;
  font-size: var(--md-label-size);
  line-height: 1.45;
}

.address-details.empty {
  color: rgba(0, 0, 0, 0.5);
}

.address-contact {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 6px 12px;
  width: 100%;
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
  font-size: inherit;
  line-height: inherit;
  padding: 0 8px;
  background: #E3F2FD;
  border-radius: 8px;
  white-space: nowrap;
  overflow-wrap: normal;
  word-break: keep-all;
  flex-shrink: 0;
  min-height: 0;
  min-width: 0;
  height: auto;
  margin-right: 4px;
}

.civic-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  min-width: 0;
}

.civic-text {
  flex: 1;
  min-width: 0;
}

.address-line {
  color: rgba(0, 0, 0, 0.8);
}

.address-line.civic {
  font-weight: 700;
  color: rgba(0, 0, 0, 0.87);
}

.copy-address-btn {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  margin: -2px 0 0;
  border: none;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.05);
  color: rgba(0, 0, 0, 0.55);
  cursor: pointer;
  min-height: 0;
  min-width: 0;
  margin-left: auto;
  margin-right: 4px;
}

.copy-address-btn svg {
  width: 16px;
  height: 16px;
}

.copy-address-btn:hover {
  background: rgba(0, 0, 0, 0.1);
  color: rgba(0, 0, 0, 0.75);
}

.address-email {
  color: rgba(0, 0, 0, 0.6);
}
</style>
