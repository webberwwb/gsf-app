<template>
  <div class="inf-page">
    <header class="page-header">
      <button type="button" class="back-btn" @click="$router.push('/influencer')">‹</button>
      <h1>我的客户</h1>
    </header>
    <main class="page-content">
      <div v-if="error" class="error">{{ error }}</div>
      <div v-else-if="loading" class="loading">加载中...</div>
      <p v-else-if="!customers.length" class="empty">暂无客户。请分享邀请链接。</p>
      <button
        v-else
        v-for="c in customers"
        :key="c.id"
        type="button"
        class="card"
        @click="$router.push(`/influencer/customers/${c.id}`)"
      >
        <div class="card-top">
          <span class="name">{{ c.nickname }}</span>
          <span class="arrow">›</span>
        </div>
        <p v-if="c.wechat_masked" class="meta">微信：{{ c.wechat_masked }}</p>
        <div class="row">
          <span>进行中 {{ c.in_progress_order_count || 0 }}</span>
          <span>已结束 {{ c.closed_order_count || 0 }}</span>
          <span>消费 ${{ money(c.spend) }}</span>
          <span>收益 ${{ money(c.commission) }}</span>
        </div>
      </button>
    </main>
  </div>
</template>

<script>
import apiClient from '../api/client'
import { formatOrderMoney2 } from '../utils/orderPricing'

export default {
  name: 'InfluencerCustomers',
  data() {
    return { loading: true, error: null, customers: [] }
  },
  async mounted() {
    try {
      const res = await apiClient.get('/influencer/customers')
      this.customers = res.data.customers || []
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
  line-height: 1;
  padding: 0 0.25rem;
}
.page-content { padding: 1rem; display: flex; flex-direction: column; gap: var(--md-spacing-sm); }
.loading, .error, .empty { text-align: center; padding: 2rem 1rem; color: var(--md-on-surface-variant); }
.card {
  text-align: left;
  border: none;
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  box-shadow: var(--md-elevation-1);
  padding: var(--md-spacing-md);
}
.card-top { display: flex; justify-content: space-between; align-items: center; }
.name { font-weight: 600; color: var(--md-on-surface); }
.arrow { color: var(--md-on-surface-variant); }
.meta { margin: 0.25rem 0 0; font-size: 0.85rem; color: var(--md-on-surface-variant); }
.row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 0.5rem;
  font-size: 0.8rem;
  color: var(--md-on-surface-variant);
}
</style>
