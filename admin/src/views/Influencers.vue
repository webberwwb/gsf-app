<template>
  <div class="promo-page">
    <p class="page-description">
      配置推荐官邀请奖励与商品收益，查看客户与现金待付。在用户管理中为账号添加「推荐官」角色。
    </p>

    <div class="tabs">
      <button type="button" :class="['tab', { active: tab === 'people' }]" @click="tab = 'people'">推荐官</button>
      <button type="button" :class="['tab', { active: tab === 'rates' }]" @click="tab = 'rates'">商品费率</button>
      <button type="button" :class="['tab', { active: tab === 'config' }]" @click="tab = 'config'">邀请奖励</button>
    </div>

    <div v-show="tab === 'config'" class="panel-card">
      <h2 class="panel-heading">客户绑定奖励</h2>
      <p class="hint">客户通过推荐官邀请码绑定时立即获得代金券。管理员手动改推荐人不发奖。</p>
      <div class="form-row">
        <label>奖励金额（$）</label>
        <input v-model.number="configForm.lead_bonus_amount" type="number" step="0.01" min="0" class="form-input" />
      </div>
      <label class="checkbox-label">
        <input v-model="configForm.is_active" type="checkbox" />
        启用邀请奖励
      </label>
      <button type="button" class="btn-primary" :disabled="saving" @click="saveConfig">
        {{ saving ? '保存中…' : '保存' }}
      </button>
    </div>

    <div v-show="tab === 'rates'" class="panel-card">
      <h2 class="panel-heading">全局商品收益</h2>
      <p class="hint">所有推荐官默认使用此表。改完保存后，未设专属覆盖的推荐官立即按新费率计提。0 表示不计提。</p>
      <div v-if="ratesLoading" class="muted">加载中...</div>
      <div v-else class="rate-list">
        <div v-for="rate in rates" :key="rate.product_id" class="rate-row">
          <div class="rate-name">
            {{ rate.product_name }}
            <span v-if="!rate.is_active" class="muted">（下架）</span>
          </div>
          <select v-model="rate.commission_type" class="form-input form-input--sm">
            <option value="per_item">按件</option>
            <option value="per_weight">按磅</option>
          </select>
          <input v-model.number="rate.amount" type="number" step="0.01" min="0" class="form-input form-input--sm" />
          <button type="button" class="btn-secondary" @click="saveRate(rate)">保存</button>
        </div>
        <button
          v-if="rates.length"
          type="button"
          class="btn-primary"
          :disabled="saving"
          @click="saveAllRates"
        >
          {{ saving ? '保存中…' : '保存全部' }}
        </button>
      </div>
    </div>

    <div v-show="tab === 'people'" class="panel-card">
      <h2 class="panel-heading">推荐官列表</h2>
      <div v-if="listLoading" class="muted">加载中...</div>
      <p v-else-if="!influencers.length" class="muted">还没有推荐官。请到用户管理添加角色。</p>
      <div v-else class="people-list">
        <button
          v-for="row in influencers"
          :key="row.user_id"
          type="button"
          class="person-card"
          :class="{ active: selectedId === row.user_id }"
          @click="selectInfluencer(row.user_id)"
        >
          <div class="person-top">
            <strong>{{ row.nickname || row.phone || ('用户' + row.user_id) }}</strong>
            <span class="chip">{{ row.payout_type === 'cash' ? '现金' : '代金券' }}</span>
            <span v-if="!row.is_active" class="muted">已停用</span>
          </div>
          <div class="person-meta">
            码 {{ row.referral_code || '—' }} · 客户 {{ row.customer_count }} ·
            代金券 ${{ money(row.credited) }} · 待付 ${{ money(row.payable) }}
          </div>
        </button>
      </div>

      <div v-if="detail" class="detail">
        <h3 class="panel-heading">{{ detail.nickname || ('用户' + detail.user_id) }}</h3>
        <div class="form-row">
          <label>结算方式</label>
          <select v-model="detail.payout_type" class="form-input form-input--sm" @change="savePayout">
            <option value="credit">代金券</option>
            <option value="cash">现金</option>
          </select>
        </div>

        <h4>专属费率覆盖</h4>
        <div class="override-row">
          <select v-model.number="overrideForm.product_id" class="form-input">
            <option :value="null">选择商品</option>
            <option v-for="rate in rates" :key="rate.product_id" :value="rate.product_id">
              {{ rate.product_name }}
            </option>
          </select>
          <select v-model="overrideForm.commission_type" class="form-input form-input--sm">
            <option value="per_item">按件</option>
            <option value="per_weight">按磅</option>
          </select>
          <input v-model.number="overrideForm.amount" type="number" step="0.01" min="0" class="form-input form-input--sm" />
          <button type="button" class="btn-secondary" @click="saveOverride">保存覆盖</button>
        </div>
        <ul class="plain-list">
          <li v-for="ov in detail.overrides || []" :key="ov.product_id">
            {{ ov.product?.name || ov.product_id }} · {{ ov.commission_type }} ${{ money(ov.amount) }}
            <button type="button" class="link-btn" @click="removeOverride(ov.product_id)">删除</button>
          </li>
        </ul>

        <h4>客户</h4>
        <p v-if="!(detail.customers || []).length" class="muted">暂无客户</p>
        <ul class="plain-list">
          <li v-for="c in detail.customers || []" :key="c.id">
            {{ c.nickname }} · 进行中 {{ c.in_progress_order_count || 0 }} · 已结束 {{ c.closed_order_count || 0 }} · 消费 ${{ money(c.spend) }} · 收益 ${{ money(c.commission) }}
          </li>
        </ul>

        <h4>待付现金</h4>
        <p v-if="!(detail.payable_entries || []).length" class="muted">无待付记录</p>
        <ul class="plain-list">
          <li v-for="e in detail.payable_entries || []" :key="e.id">
            订单 {{ e.order_id }} · ${{ money(e.amount) }}
            <button type="button" class="btn-secondary" @click="markPaid([e.id])">标记已付</button>
          </li>
        </ul>
        <button
          v-if="(detail.payable_entries || []).length > 1"
          type="button"
          class="btn-primary"
          @click="markPaid(detail.payable_entries.map(e => e.id))"
        >
          全部标记已付
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'

export default {
  name: 'Influencers',
  data() {
    return {
      tab: 'people',
      saving: false,
      listLoading: false,
      ratesLoading: false,
      influencers: [],
      rates: [],
      configForm: { lead_bonus_amount: 5, is_active: true },
      selectedId: null,
      detail: null,
      overrideForm: { product_id: null, commission_type: 'per_item', amount: 0 }
    }
  },
  async mounted() {
    await Promise.all([this.loadList(), this.loadRates(), this.loadConfig()])
  },
  methods: {
    money(v) {
      const n = Number(v || 0)
      return n.toFixed(2)
    },
    async loadList() {
      this.listLoading = true
      try {
        const res = await apiClient.get('/admin/influencers')
        this.influencers = res.data.influencers || []
      } finally {
        this.listLoading = false
      }
    },
    async loadRates() {
      this.ratesLoading = true
      try {
        const res = await apiClient.get('/admin/influencers/rates')
        this.rates = res.data.rates || []
      } finally {
        this.ratesLoading = false
      }
    },
    async loadConfig() {
      const res = await apiClient.get('/admin/influencers/config')
      const cfg = res.data.config || {}
      this.configForm = {
        lead_bonus_amount: cfg.lead_bonus_amount ?? 5,
        is_active: cfg.is_active !== false
      }
    },
    async saveConfig() {
      this.saving = true
      try {
        await apiClient.put('/admin/influencers/config', this.configForm)
      } finally {
        this.saving = false
      }
    },
    async saveRate(rate) {
      await apiClient.put('/admin/influencers/rates', {
        product_id: rate.product_id,
        commission_type: rate.commission_type,
        amount: rate.amount || 0
      })
    },
    async saveAllRates() {
      this.saving = true
      try {
        for (const rate of this.rates) {
          await this.saveRate(rate)
        }
      } finally {
        this.saving = false
      }
    },
    async selectInfluencer(userId) {
      this.selectedId = userId
      const res = await apiClient.get(`/admin/influencers/${userId}`)
      this.detail = res.data.influencer
    },
    async savePayout() {
      if (!this.detail) return
      await apiClient.patch(`/admin/influencers/${this.detail.user_id}`, {
        payout_type: this.detail.payout_type
      })
      await this.loadList()
    },
    async saveOverride() {
      if (!this.detail || !this.overrideForm.product_id) return
      await apiClient.put(`/admin/influencers/${this.detail.user_id}/overrides`, this.overrideForm)
      await this.selectInfluencer(this.detail.user_id)
    },
    async removeOverride(productId) {
      await apiClient.delete(`/admin/influencers/${this.detail.user_id}/overrides/${productId}`)
      await this.selectInfluencer(this.detail.user_id)
    },
    async markPaid(ids) {
      await apiClient.post('/admin/influencers/cash-payouts', { entry_ids: ids })
      await this.selectInfluencer(this.detail.user_id)
      await this.loadList()
    }
  }
}
</script>

<style scoped>
.promo-page { max-width: 960px; }
.page-description {
  color: var(--md-on-surface-variant);
  margin: 0 0 var(--md-spacing-md);
}
.tabs {
  display: flex;
  gap: var(--md-spacing-xs);
  margin-bottom: var(--md-spacing-md);
}
.tab {
  padding: 0.4rem 0.9rem;
  border: none;
  background: var(--md-surface-variant);
  border-radius: var(--md-radius-sm);
  cursor: pointer;
  font-weight: 500;
}
.tab.active {
  background: rgba(255, 140, 0, 0.2);
  color: var(--md-primary);
}
.panel-card {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  box-shadow: var(--md-elevation-1);
  padding: var(--md-spacing-lg);
  margin-bottom: var(--md-spacing-md);
}
.panel-heading {
  margin: 0 0 var(--md-spacing-sm);
  font-size: var(--md-title-size);
}
.hint, .muted { color: var(--md-on-surface-variant); font-size: 0.85rem; }
.form-row {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin: var(--md-spacing-sm) 0;
  max-width: 16rem;
}
.form-input {
  padding: var(--md-spacing-sm);
  border: 1px solid var(--md-outline-variant, #cac4d0);
  border-radius: var(--md-radius-sm);
  font-family: inherit;
}
.form-input--sm { max-width: 8rem; }
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: var(--md-spacing-sm) 0;
}
.btn-primary, .btn-secondary {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border-radius: var(--md-radius-sm);
  border: none;
  font-weight: 600;
  cursor: pointer;
}
.btn-primary { background: var(--md-primary); color: #fff; }
.btn-secondary {
  background: var(--md-surface);
  border: 1px solid var(--md-outline-variant, #cac4d0);
  color: var(--md-on-surface);
}
.rate-list { display: flex; flex-direction: column; gap: 0.5rem; }
.rate-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}
.rate-name { min-width: 8rem; flex: 1; }
.people-list { display: flex; flex-direction: column; gap: 0.5rem; }
.person-card {
  text-align: left;
  border: 1px solid var(--md-surface-variant);
  background: var(--md-surface);
  border-radius: var(--md-radius-md);
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  cursor: pointer;
}
.person-card.active { border-color: var(--md-primary); background: rgba(255, 140, 0, 0.06); }
.person-top { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
.person-meta { font-size: 0.8rem; color: var(--md-on-surface-variant); margin-top: 0.25rem; }
.chip {
  padding: 0.125rem 0.5rem;
  border-radius: var(--md-radius-sm);
  background: rgba(255, 140, 0, 0.2);
  color: var(--md-primary);
  font-size: var(--md-label-size);
  font-weight: 500;
}
.detail { margin-top: var(--md-spacing-lg); padding-top: var(--md-spacing-md); border-top: 1px solid var(--md-surface-variant); }
.plain-list { padding-left: 1.1rem; }
.override-row { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.5rem; }
.link-btn {
  border: none;
  background: none;
  color: var(--md-primary);
  cursor: pointer;
  font-weight: 600;
}
</style>
