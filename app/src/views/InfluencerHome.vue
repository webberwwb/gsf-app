<template>
  <div class="inf-page">
    <header class="page-header">
      <h1>推广收益</h1>
    </header>
    <main class="page-content">
      <div v-if="error" class="error">{{ error }}</div>
      <div v-else-if="loading" class="loading">加载中...</div>
      <template v-else>
        <div class="credit-referral-panel">
          <div class="panel-block">
            <h3 class="panel-title">邀请码</h3>
            <div class="ref-code-row">
              <span class="ref-code">{{ dash.referral_code || '—' }}</span>
              <button type="button" class="mini-btn" :disabled="!dash.referral_code" @click="copyCode">复制</button>
            </div>
            <button type="button" class="outline-btn" :disabled="!dash.referral_code" @click="copyLink">复制邀请链接</button>
            <p class="panel-hint">客户用此链接注册或填写推荐码后会绑定到您名下。</p>
          </div>
          <div class="panel-block">
            <h3 class="panel-title">结算方式</h3>
            <p class="panel-emphasis-sm">{{ payoutLabel }}</p>
            <p v-if="dash.payout_type !== 'cash'" class="panel-hint">可直接用于下单。</p>
          </div>
          <div class="stats-grid">
            <div class="stat">
              <span class="stat-label">客户数</span>
              <span class="stat-value">{{ dash.customer_count || 0 }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">订单数</span>
              <span class="stat-value">{{ dash.order_count || 0 }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">客户订单总金额</span>
              <span class="stat-value">${{ money(dash.customer_order_total) }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">累计总收益</span>
              <span class="stat-value">${{ money(dash.lifetime_earnings) }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">当前账户余额</span>
              <span class="stat-value">${{ money(dash.account_balance) }}</span>
            </div>
          </div>
        </div>
        <div class="menu-section">
          <div class="menu-item" @click="$router.push('/influencer/customers')">
            <span class="menu-label">我的客户</span>
            <span class="menu-arrow">›</span>
          </div>
          <div class="menu-item" @click="$router.push('/influencer/rates')">
            <span class="menu-label">收益费率</span>
            <span class="menu-arrow">›</span>
          </div>
        </div>
      </template>
    </main>
  </div>
</template>

<script>
import apiClient from '../api/client'
import { getAppPublicOrigin } from '@/config/api'
import { formatOrderMoney2 } from '../utils/orderPricing'
import { useModal } from '../composables/useModal'

export default {
  name: 'InfluencerHome',
  setup() {
    const { success, error: showError } = useModal()
    return { success, showError }
  },
  data() {
    return { loading: true, error: null, dash: {} }
  },
  async mounted() {
    await this.load()
  },
  computed: {
    payoutLabel() {
      return this.dash.payout_type === 'cash' ? '现金' : '代金券'
    }
  },
  methods: {
    money(v) {
      return formatOrderMoney2(v || 0)
    },
    async load() {
      this.loading = true
      this.error = null
      try {
        const res = await apiClient.get('/influencer/me')
        this.dash = res.data || {}
      } catch (e) {
        this.error = e.response?.data?.error || '加载失败'
      } finally {
        this.loading = false
      }
    },
    async copyCode() {
      if (!this.dash.referral_code) return
      try {
        await navigator.clipboard.writeText(this.dash.referral_code)
        await this.success('已复制到剪贴板', { title: '完成' })
      } catch (_) {
        await this.showError('复制失败，请手动复制')
      }
    },
    async copyLink() {
      if (!this.dash.referral_code) return
      const url = `${getAppPublicOrigin()}/login?ref=${encodeURIComponent(this.dash.referral_code)}`
      try {
        await navigator.clipboard.writeText(url)
        await this.success('已复制到剪贴板', { title: '完成' })
      } catch (_) {
        await this.showError('复制失败，请手动复制')
      }
    }
  }
}
</script>

<style scoped>
.inf-page {
  min-height: 100vh;
  background: var(--md-background);
  padding-bottom: calc(80px + env(safe-area-inset-bottom));
}
.page-header {
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  padding: var(--md-spacing-lg);
  padding-top: calc(var(--md-spacing-lg) + env(safe-area-inset-top));
}
.page-header h1 {
  margin: 0;
  color: #fff;
  font-size: var(--md-headline-size);
  font-weight: 500;
  text-align: center;
}
.page-content { padding: 1rem; }
.loading, .error { text-align: center; padding: 2rem 1rem; color: var(--md-on-surface-variant); }
.credit-referral-panel {
  margin: 0 0 var(--md-spacing-md);
  padding: var(--md-spacing-md);
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  box-shadow: var(--md-elevation-1);
}
.panel-block + .panel-block {
  margin-top: var(--md-spacing-lg);
  padding-top: var(--md-spacing-md);
  border-top: 1px solid var(--md-surface-variant);
}
.panel-title {
  font-size: 0.95rem;
  font-weight: 600;
  margin: 0 0 var(--md-spacing-sm);
  color: var(--md-on-surface);
}
.panel-hint {
  font-size: 0.8rem;
  color: var(--md-on-surface-variant);
  margin: var(--md-spacing-xs) 0 0;
  line-height: 1.4;
}
.panel-emphasis-sm {
  font-size: 1.15rem;
  font-weight: 700;
  margin: 0;
  color: var(--md-primary);
}
.ref-code-row {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
}
.ref-code {
  font-size: 1.25rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--md-on-surface);
}
.mini-btn, .outline-btn {
  padding: var(--md-spacing-xs) var(--md-spacing-sm);
  border-radius: var(--md-radius-sm);
  border: 1px solid var(--md-outline);
  background: var(--md-surface);
  color: var(--md-primary);
  font-size: 0.85rem;
  font-weight: 600;
}
.outline-btn {
  margin-top: var(--md-spacing-sm);
  width: 100%;
  padding: var(--md-spacing-sm);
}
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--md-spacing-sm);
  margin-top: var(--md-spacing-lg);
}
.stat {
  background: var(--md-surface-variant);
  border-radius: var(--md-radius-md);
  padding: var(--md-spacing-sm);
}
.stat-label {
  display: block;
  font-size: 0.75rem;
  color: var(--md-on-surface-variant);
  margin-bottom: 0.25rem;
}
.stat-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--md-on-surface);
}
.menu-section {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  overflow: hidden;
  box-shadow: var(--md-elevation-1);
}
.menu-item {
  display: flex;
  align-items: center;
  padding: var(--md-spacing-md);
  border-bottom: 1px solid var(--md-surface-variant);
}
.menu-item:last-child { border-bottom: none; }
.menu-label { flex: 1; color: var(--md-on-surface); }
.menu-arrow { color: var(--md-on-surface-variant); }
</style>
