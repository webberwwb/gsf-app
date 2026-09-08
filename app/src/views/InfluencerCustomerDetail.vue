<template>
  <div class="inf-page">
    <header class="page-header">
      <button type="button" class="back-btn" @click="$router.push('/influencer/customers')">‹</button>
      <h1>{{ title }}</h1>
    </header>
    <main class="page-content">
      <div v-if="error" class="error">{{ error }}</div>
      <div v-else-if="loading" class="loading">加载中...</div>
      <template v-else>
        <p v-if="detail.customer?.wechat_masked" class="meta">微信：{{ detail.customer.wechat_masked }}</p>
        <p v-if="!detail.orders?.length" class="empty">暂无订单</p>
        <div v-for="order in detail.orders" :key="order.id" class="card">
          <div class="card-top">
            <span class="name">{{ order.group_deal_title || '团购' }}</span>
            <span class="status" :class="order.phase">{{ order.phase === 'closed' ? '已结束' : '进行中' }}</span>
          </div>
          <p v-if="order.created_at" class="meta">下单 {{ formatDate(order.created_at) }}</p>
          <div class="items">
            <div v-for="(item, idx) in order.items" :key="idx" class="item">
              <div class="item-top">
                <span class="item-name">{{ item.product_name || '商品' }}{{ item.variant_name ? ' · ' + item.variant_name : '' }}</span>
                <span class="item-comm-type">{{ item.commission_type === 'per_weight' ? '按重量' : '按件' }}</span>
              </div>
              <p class="item-line">
                收益单价 ${{ money(item.commission_rate) }}/{{ item.commission_unit }}
                × {{ commissionUnitsLabel(item) }}
              </p>
              <p class="item-line totals">
                {{ item.commission_estimated ? '预估收益' : '收益' }} ${{ money(item.commission_amount) }}
              </p>
            </div>
          </div>
          <p class="commission">
            {{ order.commission ? '收益' : '预估收益' }}
            ${{ money(order.commission ? order.commission.amount : order.estimated_commission) }}
          </p>
        </div>
      </template>
    </main>
  </div>
</template>

<script>
import apiClient from '../api/client'
import { formatOrderMoney2 } from '../utils/orderPricing'
import { formatDateEST_CN } from '../utils/date'

export default {
  name: 'InfluencerCustomerDetail',
  data() {
    return { loading: true, error: null, detail: { customer: {}, orders: [] } }
  },
  computed: {
    title() {
      return this.detail.customer?.nickname || '客户详情'
    }
  },
  async mounted() {
    try {
      const res = await apiClient.get(`/influencer/customers/${this.$route.params.id}`)
      this.detail = res.data
    } catch (e) {
      this.error = e.response?.data?.error || '加载失败'
    } finally {
      this.loading = false
    }
  },
  methods: {
    money(v) {
      return formatOrderMoney2(v || 0)
    },
    formatDate(value) {
      return formatDateEST_CN(value)
    },
    commissionUnitsLabel(item) {
      if (item.commission_type === 'per_weight') {
        const w = item.weight != null ? item.weight : item.commission_units
        const prefix = item.weight_estimated || item.commission_estimated ? '预估 ' : ''
        return `${prefix}${w} ${item.commission_unit}`
      }
      return `${item.quantity || 0} 件`
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
}
.page-content { padding: 1rem; display: flex; flex-direction: column; gap: var(--md-spacing-sm); }
.loading, .error, .empty { text-align: center; padding: 1.5rem; color: var(--md-on-surface-variant); }
.meta { margin: 0 0 0.5rem; color: var(--md-on-surface-variant); font-size: 0.85rem; }
.card {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  box-shadow: var(--md-elevation-1);
  padding: var(--md-spacing-md);
}
.card-top { display: flex; justify-content: space-between; gap: 0.5rem; flex-wrap: wrap; }
.name { font-weight: 600; }
.status { font-size: 0.75rem; color: var(--md-on-surface-variant); }
.status.in_progress { color: var(--md-primary); font-weight: 600; }
.items { margin: 0.5rem 0 0; display: flex; flex-direction: column; gap: 0.75rem; }
.item { padding-top: 0.5rem; border-top: 1px solid var(--md-surface-variant); }
.item:first-child { padding-top: 0; border-top: none; }
.item-top { display: flex; justify-content: space-between; gap: 0.5rem; align-items: baseline; }
.item-name { font-weight: 600; color: var(--md-on-surface); font-size: 0.9rem; }
.item-comm-type {
  flex-shrink: 0;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--md-primary);
  background: rgba(255, 140, 0, 0.12);
  padding: 0.1rem 0.4rem;
  border-radius: 999px;
}
.item-line { margin: 0.2rem 0 0; font-size: 0.78rem; color: var(--md-on-surface-variant); }
.item-line.totals { color: var(--md-on-surface); }
.commission { margin: 0.75rem 0 0; font-weight: 600; color: var(--md-primary); }
</style>
