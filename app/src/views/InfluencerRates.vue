<template>
  <div class="inf-page">
    <header class="page-header">
      <button type="button" class="back-btn" @click="$router.push('/influencer')">‹</button>
      <h1>收益费率</h1>
    </header>
    <main class="page-content">
      <div v-if="error" class="error">{{ error }}</div>
      <div v-else-if="loading" class="loading">加载中...</div>
      <p v-else-if="!rates.length" class="empty">暂无商品。</p>
      <div v-else class="credit-referral-panel">
        <div v-for="rate in rates" :key="rate.product_id" class="rate-row">
          <div>
            <p class="name">{{ rate.product_name }}</p>
            <p class="meta">{{ rate.commission_type === 'per_weight' ? '按重量' : '按件' }}</p>
          </div>
          <div class="right">
            <span class="amt">${{ money(rate.amount) }}/{{ rate.commission_unit || (rate.commission_type === 'per_weight' ? 'lb' : '件') }}</span>
            <span v-if="rate.source === 'override'" class="chip">专属</span>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import apiClient from '../api/client'
import { formatOrderMoney2 } from '../utils/orderPricing'

export default {
  name: 'InfluencerRates',
  data() {
    return { loading: true, error: null, rates: [] }
  },
  async mounted() {
    try {
      const res = await apiClient.get('/influencer/rates')
      this.rates = res.data.rates || []
    } catch (e) {
      this.error = e.response?.data?.error || '加载失败'
    } finally {
      this.loading = false
    }
  },
  methods: {
    money(v) {
      return formatOrderMoney2(v || 0)
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
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
}
.page-header h1 {
  margin: 0;
  color: #fff;
  font-size: var(--md-headline-size);
  font-weight: 500;
  flex: 1;
  text-align: center;
}
.back-btn {
  border: none;
  background: transparent;
  color: #fff;
  font-size: 1.6rem;
}
.page-content { padding: 1rem; }
.loading, .error, .empty { text-align: center; padding: 2rem 1rem; color: var(--md-on-surface-variant); }
.credit-referral-panel {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  box-shadow: var(--md-elevation-1);
  padding: var(--md-spacing-md);
}
.rate-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--md-spacing-sm);
  padding: var(--md-spacing-sm) 0;
  border-bottom: 1px solid var(--md-surface-variant);
}
.rate-row:last-child { border-bottom: none; }
.name { margin: 0; font-weight: 600; color: var(--md-on-surface); }
.meta { margin: 0.15rem 0 0; font-size: 0.75rem; color: var(--md-on-surface-variant); }
.right { display: flex; align-items: center; gap: 0.4rem; }
.amt { font-weight: 700; color: var(--md-primary); }
.chip {
  padding: 0.125rem 0.5rem;
  border-radius: var(--md-radius-sm);
  font-size: var(--md-label-size);
  font-weight: 500;
  background: rgba(255, 140, 0, 0.2);
  color: var(--md-primary);
}
</style>
