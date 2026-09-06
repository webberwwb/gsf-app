<template>
  <div v-if="show" class="card-setup-overlay" @click.self="close">
    <div class="card-setup-sheet">
      <div class="card-setup-header">
        <h3>谷语农庄APP</h3>
        <button type="button" class="card-setup-close" @click="close">×</button>
      </div>
      <p class="card-setup-hint">下单不扣款。称重和运费确定后一次性扣款。</p>
      <p class="card-setup-privacy">{{ privacyNote }}</p>
      <div v-if="loading" class="card-setup-status">加载中...</div>
      <div v-else-if="initError" class="card-setup-error">{{ initError }}</div>
      <div v-show="!loading && !initError" ref="paymentEl" class="card-setup-element"></div>
      <button
        type="button"
        class="card-setup-submit"
        :disabled="loading || submitting || !!initError"
        @click="submit"
      >
        {{ submitting ? '绑定中...' : '确认绑卡' }}
      </button>
      <p v-if="submitError" class="card-setup-error">{{ submitError }}</p>
    </div>
  </div>
</template>

<script>
import { loadStripe } from '@stripe/stripe-js'
import apiClient from '../api/client'
import { CARD_PRIVACY_NOTE } from '../utils/stripeCard'

const FARM_EMAIL = 'grainstoryfarm@gmail.com'

export default {
  name: 'CardSetupModal',
  props: {
    show: { type: Boolean, default: false },
    customerName: { type: String, default: '' },
    customerPhone: { type: String, default: '' }
  },
  emits: ['close', 'saved'],
  data() {
    return {
      loading: false,
      submitting: false,
      initError: null,
      submitError: null,
      stripe: null,
      elements: null,
      paymentElement: null,
      setupIntentId: null,
      privacyNote: CARD_PRIVACY_NOTE
    }
  },
  watch: {
    show(open) {
      if (open) {
        this.$nextTick(() => this.start())
      } else {
        this.teardown()
      }
    }
  },
  methods: {
    close() {
      if (this.submitting) return
      this.$emit('close')
    },
    teardown() {
      if (this.paymentElement) {
        try { this.paymentElement.unmount() } catch (e) { /* already gone */ }
      }
      this.stripe = null
      this.elements = null
      this.paymentElement = null
      this.setupIntentId = null
      this.initError = null
      this.submitError = null
      this.loading = false
      this.submitting = false
    },
    async start() {
      this.loading = true
      this.initError = null
      this.submitError = null
      try {
        const { data } = await apiClient.post('/payments/setup-intent')
        const pk = data.publishable_key
        if (!pk || !data.client_secret) {
          throw new Error('在线支付尚未配置')
        }
        this.setupIntentId = data.setup_intent_id
        this.stripe = await loadStripe(pk)
        this.elements = this.stripe.elements({
          clientSecret: data.client_secret,
          locale: 'zh',
          appearance: {
            theme: 'stripe',
            variables: {
              colorPrimary: '#ff8c00',
              borderRadius: '10px'
            }
          }
        })
        this.paymentElement = this.elements.create('payment', {
          fields: {
            billingDetails: {
              email: 'never',
              name: 'never',
              phone: 'never'
            }
          },
          wallets: {
            applePay: 'auto',
            googlePay: 'auto',
            link: 'never'
          }
        })
        this.paymentElement.mount(this.$refs.paymentEl)
      } catch (e) {
        this.initError = e.response?.data?.error || e.message || '无法打开绑卡'
      } finally {
        this.loading = false
      }
    },
    async submit() {
      if (!this.stripe || !this.elements) return
      this.submitting = true
      this.submitError = null
      try {
        const { error, setupIntent } = await this.stripe.confirmSetup({
          elements: this.elements,
          confirmParams: {
            return_url: `${window.location.origin}${this.$route.path}`,
            payment_method_data: {
              billing_details: {
                email: FARM_EMAIL,
                name: this.customerName || '谷语农庄客户',
                phone: this.customerPhone || undefined
              }
            }
          },
          redirect: 'if_required'
        })
        if (error) {
          this.submitError = error.message || '绑卡失败'
          return
        }
        const intentId = setupIntent?.id || this.setupIntentId
        const { data } = await apiClient.post(`/payments/setup-intent/${intentId}`)
        this.$emit('saved', data)
        this.$emit('close')
      } catch (e) {
        this.submitError = e.response?.data?.error || e.message || '绑卡失败'
      } finally {
        this.submitting = false
      }
    }
  }
}
</script>

<style scoped>
.card-setup-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 1200;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.card-setup-sheet {
  width: 100%;
  max-width: 480px;
  background: #fff;
  border-radius: 16px 16px 0 0;
  padding: 16px 16px calc(16px + env(safe-area-inset-bottom));
  box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.12);
}

.card-setup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.card-setup-header h3 {
  margin: 0;
  font-size: 1.1rem;
}

.card-setup-close {
  border: none;
  background: transparent;
  font-size: 1.6rem;
  line-height: 1;
  color: #666;
}

.card-setup-hint {
  margin: 0 0 8px;
  font-size: 0.8125rem;
  color: #666;
}

.card-setup-privacy {
  margin: 0 0 12px;
  font-size: 0.75rem;
  line-height: 1.45;
  color: #888;
}

.card-setup-element {
  min-height: 80px;
}

.card-setup-status,
.card-setup-error {
  margin: 8px 0 0;
  font-size: 0.8125rem;
}

.card-setup-error {
  color: #c62828;
}

.card-setup-submit {
  width: 100%;
  margin-top: 16px;
  padding: 12px 16px;
  border: none;
  border-radius: 12px;
  background: #ff8c00;
  color: #fff;
  font-weight: 600;
}
</style>
