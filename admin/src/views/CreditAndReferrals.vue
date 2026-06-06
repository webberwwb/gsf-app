<template>
  <div class="promo-page">
    <p class="page-description">
      配置邀请奖励、查看邀请与代金券流水，或手动调整用户代金券余额。
    </p>

    <div class="tabs">
      <button
        v-for="t in tabs"
        :key="t.id"
        type="button"
        :class="['tab', { active: activeTab === t.id }]"
        @click="activeTab = t.id"
      >
        {{ t.label }}
      </button>
    </div>

    <div v-show="activeTab === 'config'" class="panel-card">
      <h2 class="panel-heading">邀请奖励设置</h2>
      <div v-if="config" class="form-stack">
        <div class="form-group">
          <label>受邀人奖励（$）</label>
          <input
            v-model.number="configForm.invitee_bonus_amount"
            type="number"
            step="0.01"
            min="0"
            class="form-input"
          />
        </div>
        <div class="form-group">
          <label>邀请人奖励（$）</label>
          <input
            v-model.number="configForm.inviter_reward_amount"
            type="number"
            step="0.01"
            min="0"
            class="form-input"
          />
        </div>
        <div class="form-group form-group--inline">
          <label class="checkbox-label">
            <input v-model="configForm.is_active" type="checkbox" class="checkbox-input" />
            <span>启用推荐计划</span>
          </label>
        </div>
        <div class="form-actions">
          <button type="button" class="btn-primary" :disabled="saving" @click="saveConfig">
            {{ saving ? '保存中…' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <div v-show="activeTab === 'grant'" class="panel-card">
      <h2 class="panel-heading">代金券调整</h2>
      <div class="form-stack">
        <div class="form-group">
          <label>用户</label>
          <div v-if="!grantSelectedUser" class="user-picker">
            <div class="user-picker__input-wrap">
              <input
                v-model.trim="grantUserQuery"
                type="text"
                class="form-input"
                placeholder="搜索手机号、昵称、微信号或用户 ID"
                autocomplete="off"
                @focus="onGrantUserFocus"
                @input="onGrantUserInput"
                @blur="onGrantUserBlur"
                @keydown.escape.prevent="closeGrantUserDropdown"
              />
              <div
                v-show="grantUserOpen && grantUserResults.length"
                class="user-picker__dropdown"
                role="listbox"
              >
                <button
                  v-for="u in grantUserResults"
                  :key="u.id"
                  type="button"
                  class="user-picker__option"
                  @mousedown.prevent="selectGrantUser(u)"
                >
                  <span class="user-picker__opt-main">{{ u.nickname || '（无昵称）' }}</span>
                  <span class="user-picker__opt-sub">
                    {{ u.phone || u.wechat || u.email || '—' }} · ID {{ u.id }}
                  </span>
                  <span class="user-picker__opt-credit">代金券 ${{ formatMoney(u.store_credit_balance) }}</span>
                </button>
              </div>
            </div>
            <p v-if="grantUserSearchLoading" class="user-picker__hint">搜索中…</p>
            <p
              v-else-if="grantUserOpen && grantUserQuery.length && !grantUserResults.length"
              class="user-picker__hint"
            >
              无匹配用户
            </p>
          </div>
          <div v-else class="user-picker__selected">
            <div class="user-picker__selected-info">
              <span class="user-picker__selected-name">{{ grantSelectedUser.nickname || '（无昵称）' }}</span>
              <span class="user-picker__selected-meta">
                {{ grantSelectedUser.phone || grantSelectedUser.wechat || grantSelectedUser.email || '—' }}
              </span>
              <span class="user-picker__selected-meta">ID {{ grantSelectedUser.id }}</span>
              <span class="user-picker__selected-meta">
                代金券 ${{ formatMoney(grantSelectedUser.store_credit_balance) }}
              </span>
            </div>
            <button type="button" class="btn-secondary btn-sm" @click="clearGrantUser">更换</button>
          </div>
        </div>
        <div class="form-group">
          <label>金额（可负）</label>
          <input
            v-model="grantForm.amount"
            type="text"
            class="form-input"
            placeholder="例如 10 或 -5"
          />
        </div>
        <div class="form-group">
          <label>原因（必填）</label>
          <input v-model="grantForm.reason" type="text" class="form-input" />
        </div>
        <div class="form-actions">
          <button type="button" class="btn-primary" :disabled="grantLoading" @click="submitGrant">
            {{ grantLoading ? '提交中…' : '提交' }}
          </button>
        </div>
      </div>
    </div>

    <div v-show="activeTab === 'tx'" class="panel-card">
      <h2 class="panel-heading">代金券流水</h2>
      <div class="toolbar">
        <div class="form-group toolbar-field">
          <label>用户 ID</label>
          <input
            v-model.number="txUserId"
            type="number"
            min="1"
            placeholder="可选，筛选"
            class="form-input form-input--narrow"
          />
        </div>
        <button type="button" class="btn-secondary" @click="loadTx">查询</button>
      </div>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>时间</th>
              <th>用户</th>
              <th>类型</th>
              <th>变动</th>
              <th>余额</th>
              <th>说明</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in transactions" :key="r.id">
              <td>{{ r.created_at }}</td>
              <td class="tx-user-cell">
                <template v-if="r.user">
                  <div class="tx-user-line tx-user-line--name">
                    {{ r.user.nickname || '（无昵称）' }}
                  </div>
                  <div class="tx-user-line tx-user-line--contact">
                    {{ formatTxUserContact(r.user) }}
                  </div>
                  <div class="tx-user-line tx-user-line--id">ID {{ r.user.id }}</div>
                </template>
                <template v-else>
                  <span class="tx-user-fallback">用户 #{{ r.user_id }}</span>
                </template>
              </td>
              <td>{{ formatTxType(r.tx_type) }}</td>
              <td>{{ r.delta }}</td>
              <td>{{ r.balance_after }}</td>
              <td>{{ r.reason || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="!transactions.length" class="empty-hint">暂无记录</p>
    </div>

    <div v-show="activeTab === 'refs'" class="panel-card">
      <div class="panel-heading-row">
        <h2 class="panel-heading">邀请记录</h2>
        <button type="button" class="btn-secondary btn-sm" @click="loadRefs">刷新</button>
      </div>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>时间</th>
              <th>邀请人</th>
              <th>受邀人</th>
              <th>状态</th>
              <th>受邀人完成订单</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in referrals" :key="r.id">
              <td>{{ r.created_at }}</td>
              <td class="tx-user-cell">
                <template v-if="r.inviter">
                  <div class="tx-user-line tx-user-line--name">
                    {{ r.inviter.nickname || '（无昵称）' }}
                  </div>
                  <div class="tx-user-line tx-user-line--contact">
                    {{ formatTxUserContact(r.inviter) }}
                  </div>
                  <div class="tx-user-line tx-user-line--id">ID {{ r.inviter.id }}</div>
                </template>
                <template v-else>
                  <span class="tx-user-fallback">—</span>
                </template>
              </td>
              <td class="tx-user-cell">
                <template v-if="r.invitee">
                  <div class="tx-user-line tx-user-line--name">
                    {{ r.invitee.nickname || '（无昵称）' }}
                  </div>
                  <div class="tx-user-line tx-user-line--contact">
                    {{ formatTxUserContact(r.invitee) }}
                  </div>
                  <div class="tx-user-line tx-user-line--id">ID {{ r.invitee.id }}</div>
                </template>
                <template v-else>
                  <span class="tx-user-fallback">—</span>
                </template>
              </td>
              <td>{{ formatReferralStatus(r) }}</td>
              <td>{{ r.invitee_has_completed_order ? '是' : '否' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="!referrals.length" class="empty-hint">暂无记录</p>
    </div>
  </div>
</template>

<script>
import apiClient from '@/api/client'
import { useModal } from '@/composables/useModal'
import { formatOrderMoney2 } from '../utils/orderPricing'

/** Mirrors backend credit_service TX_* constants */
const CREDIT_TX_TYPE_LABELS = {
  admin_grant: '管理员调整',
  referral_invitee_bonus: '邀请好友成功下单',
  referral_inviter_reward: '邀请好友成功下单',
  order_spend: '订单使用',
  order_credit_refund: '订单退回代金券'
}

/** Fallback if API omits status_label */
const REFERRAL_RECORD_STATUS_LABELS = {
  pending_order: '已绑定，未下单',
  rewarded: '已发放奖励'
}

export default {
  name: 'CreditAndReferrals',
  setup() {
    const { alert, error: showError } = useModal()
    return { alert, showError }
  },
  data() {
    return {
      activeTab: 'config',
      tabs: [
        { id: 'config', label: '邀请奖励设置' },
        { id: 'refs', label: '邀请记录' },
        { id: 'tx', label: '代金券流水' },
        { id: 'grant', label: '代金券调整' }
      ],
      config: null,
      configForm: {
        invitee_bonus_amount: 5,
        inviter_reward_amount: 5,
        is_active: true
      },
      saving: false,
      grantForm: { user_id: null, amount: '', reason: '' },
      grantUserQuery: '',
      grantUserResults: [],
      grantUserOpen: false,
      grantUserSearchLoading: false,
      grantSelectedUser: null,
      grantUserSearchTimer: null,
      grantLoading: false,
      txUserId: null,
      transactions: [],
      referrals: []
    }
  },
  mounted() {
    this.loadConfig()
    this.loadTx()
    this.loadRefs()
  },
  beforeUnmount() {
    if (this.grantUserSearchTimer) {
      clearTimeout(this.grantUserSearchTimer)
    }
  },
  methods: {
    formatMoney(v) {
      if (v === null || v === undefined || Number.isNaN(Number(v))) return '0.00'
      return formatOrderMoney2(v)
    },
    formatTxUserContact(user) {
      if (!user) return '—'
      const parts = []
      if (user.phone) parts.push(user.phone)
      if (user.wechat) parts.push(`微信 ${user.wechat}`)
      else if (user.wechat_nickname) parts.push(`微信 ${user.wechat_nickname}`)
      if (user.email) parts.push(user.email)
      return parts.length ? parts.join(' · ') : '—'
    },
    formatTxType(txType) {
      if (txType == null || txType === '') return '—'
      return CREDIT_TX_TYPE_LABELS[txType] || txType
    },
    formatReferralStatus(r) {
      if (r.status_label) return r.status_label
      if (r.status == null || r.status === '') return '—'
      return REFERRAL_RECORD_STATUS_LABELS[r.status] || r.status
    },
    onGrantUserFocus() {
      if (this.grantSelectedUser) return
      if (this.grantUserQuery.length) this.scheduleGrantUserSearch()
    },
    onGrantUserInput() {
      if (this.grantSelectedUser) return
      this.grantUserOpen = true
      this.scheduleGrantUserSearch()
    },
    scheduleGrantUserSearch() {
      if (this.grantUserSearchTimer) clearTimeout(this.grantUserSearchTimer)
      const q = this.grantUserQuery.trim()
      if (!q.length) {
        this.grantUserResults = []
        this.grantUserOpen = false
        return
      }
      this.grantUserSearchTimer = setTimeout(() => this.runGrantUserSearch(q), 320)
    },
    async runGrantUserSearch(q) {
      this.grantUserSearchLoading = true
      try {
        const r = await apiClient.get('/admin/users', {
          params: { search: q, page: 1, per_page: 30 }
        })
        this.grantUserResults = r.data.users || []
        this.grantUserOpen = true
      } catch (e) {
        this.grantUserResults = []
        await this.showError(e.response?.data?.error || '搜索用户失败')
      } finally {
        this.grantUserSearchLoading = false
      }
    },
    onGrantUserBlur() {
      setTimeout(() => {
        this.grantUserOpen = false
      }, 180)
    },
    selectGrantUser(u) {
      this.grantSelectedUser = u
      this.grantForm.user_id = u.id
      this.grantUserQuery = ''
      this.grantUserResults = []
      this.grantUserOpen = false
    },
    clearGrantUser() {
      this.grantSelectedUser = null
      this.grantForm.user_id = null
      this.grantUserQuery = ''
      this.grantUserResults = []
      this.grantUserOpen = false
    },
    closeGrantUserDropdown() {
      this.grantUserOpen = false
    },
    async loadConfig() {
      try {
        const r = await apiClient.get('/admin/referral-program-config')
        this.config = r.data.config
        this.configForm = {
          invitee_bonus_amount: this.config.invitee_bonus_amount,
          inviter_reward_amount: this.config.inviter_reward_amount,
          is_active: this.config.is_active
        }
      } catch (e) {
        await this.showError(e.response?.data?.error || '加载配置失败')
      }
    },
    async saveConfig() {
      this.saving = true
      try {
        const r = await apiClient.put('/admin/referral-program-config', this.configForm)
        this.config = r.data.config
        await this.alert('已保存')
      } catch (e) {
        await this.showError(e.response?.data?.error || '保存失败')
      } finally {
        this.saving = false
      }
    },
    async submitGrant() {
      if (!this.grantForm.user_id || !this.grantForm.reason) {
        await this.showError('请选择用户并填写原因')
        return
      }
      this.grantLoading = true
      try {
        const amount = parseFloat(this.grantForm.amount)
        if (Number.isNaN(amount) || amount === 0) {
          await this.showError('金额无效')
          return
        }
        await apiClient.post(`/admin/users/${this.grantForm.user_id}/credit`, {
          amount,
          reason: this.grantForm.reason
        })
        await this.alert('已调整')
        this.clearGrantUser()
        this.grantForm.amount = ''
        this.grantForm.reason = ''
        this.loadTx()
      } catch (e) {
        await this.showError(e.response?.data?.error || '操作失败')
      } finally {
        this.grantLoading = false
      }
    },
    async loadTx() {
      try {
        const params = { limit: 100, offset: 0 }
        if (this.txUserId) params.user_id = this.txUserId
        const r = await apiClient.get('/admin/credit-transactions', { params })
        this.transactions = r.data.transactions || []
      } catch (e) {
        await this.showError(e.response?.data?.error || '加载代金券流水失败')
      }
    },
    async loadRefs() {
      try {
        const r = await apiClient.get('/admin/referrals', { params: { limit: 200, offset: 0 } })
        this.referrals = r.data.referrals || []
      } catch (e) {
        await this.showError(e.response?.data?.error || '加载邀请记录失败')
      }
    }
  }
}
</script>

<style scoped>
.promo-page {
  /* Match Users.vue: constrain width but stay flush-left in .content-area (no margin: auto) */
  max-width: 1200px;
  box-sizing: border-box;
}

.page-description {
  margin: 0 0 var(--md-spacing-lg);
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  line-height: 1.5;
  max-width: 48rem;
}

/* Tabs — match Users.vue */
.tabs {
  display: flex;
  gap: var(--md-spacing-xs);
  margin-bottom: var(--md-spacing-lg);
  border-bottom: 2px solid var(--md-outline-variant, #cac4d0);
  flex-wrap: wrap;
  padding-top: 4px;
}

.tab {
  position: relative;
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  border-radius: 10px 10px 0 0;
  font-size: var(--md-body-size);
  font-weight: 500;
  color: var(--md-on-surface-variant);
  cursor: pointer;
  margin-bottom: -2px;
  min-height: auto;
  min-width: auto;
  transition:
    color 0.22s cubic-bezier(0.4, 0, 0.2, 1),
    background 0.22s cubic-bezier(0.4, 0, 0.2, 1),
    box-shadow 0.22s cubic-bezier(0.4, 0, 0.2, 1),
    border-bottom-color 0.22s ease,
    transform 0.22s cubic-bezier(0.4, 0, 0.2, 1);
}

.tab:hover:not(.active) {
  color: var(--md-primary);
  background: rgba(255, 140, 0, 0.14);
  background: color-mix(in srgb, var(--md-primary) 16%, var(--md-surface, #fff) 84%);
  box-shadow:
    0 -1px 0 rgba(255, 140, 0, 0.12),
    0 6px 16px rgba(255, 140, 0, 0.14);
  transform: translateY(-2px);
  border-bottom-color: transparent;
}

.tab:focus-visible {
  outline: 2px solid var(--md-primary);
  outline-offset: 2px;
}

.tab:active:not(.active) {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(255, 140, 0, 0.1);
}

@media (prefers-reduced-motion: reduce) {
  .tab {
    transition: color 0.15s ease, background 0.15s ease, border-bottom-color 0.15s ease;
  }

  .tab:hover:not(.active),
  .tab:active:not(.active) {
    transform: none;
  }
}

.tab.active {
  color: var(--md-primary);
  border-bottom-color: var(--md-primary);
  background: rgba(255, 140, 0, 0.09);
  background: color-mix(in srgb, var(--md-primary) 10%, var(--md-surface, #fff) 90%);
  box-shadow: 0 6px 14px rgba(255, 140, 0, 0.08);
}

.panel-card {
  background: var(--md-surface);
  border-radius: var(--md-radius-md);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
  margin-bottom: var(--md-spacing-lg);
  animation: fadeIn 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.panel-heading {
  font-size: var(--md-title-size);
  font-weight: 600;
  color: var(--md-on-surface);
  margin: 0 0 var(--md-spacing-md);
}

.panel-heading-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--md-spacing-md);
  margin-bottom: var(--md-spacing-md);
  flex-wrap: wrap;
}

.panel-heading-row .panel-heading {
  margin: 0;
}

.form-stack {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
  max-width: 28rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
}

.form-group label {
  font-size: var(--md-label-size);
  font-weight: 500;
  color: var(--md-on-surface);
}

.form-group--inline {
  flex-direction: row;
  align-items: center;
}

.user-picker {
  width: 100%;
}

.user-picker__input-wrap {
  position: relative;
}

.user-picker__dropdown {
  position: absolute;
  left: 0;
  right: 0;
  top: 100%;
  margin-top: 4px;
  max-height: 240px;
  overflow-y: auto;
  z-index: 20;
  background: var(--md-surface);
  border: 1px solid var(--md-outline-variant, #cac4d0);
  border-radius: var(--md-radius-sm);
  box-shadow: var(--md-elevation-2, 0 4px 12px rgba(0, 0, 0, 0.12));
}

.user-picker__option {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  width: 100%;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: none;
  border-bottom: 1px solid var(--md-outline-variant, #cac4d0);
  background: transparent;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  color: var(--md-on-surface);
}

.user-picker__option:last-child {
  border-bottom: none;
}

.user-picker__option:hover {
  background: var(--md-surface-variant);
}

.user-picker__opt-main {
  font-weight: 600;
  font-size: var(--md-body-size);
}

.user-picker__opt-sub {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.user-picker__opt-credit {
  font-size: var(--md-label-size);
  color: var(--md-primary);
  font-weight: 500;
}

.user-picker__hint {
  margin: var(--md-spacing-xs) 0 0;
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.user-picker__selected {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--md-spacing-md);
  padding: var(--md-spacing-md);
  border: 1px solid var(--md-outline-variant, #cac4d0);
  border-radius: var(--md-radius-sm);
  background: var(--md-surface-variant);
}

.user-picker__selected-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.user-picker__selected-name {
  font-weight: 600;
  color: var(--md-on-surface);
}

.user-picker__selected-meta {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.checkbox-label {
  display: inline-flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  cursor: pointer;
  font-weight: 500;
  color: var(--md-on-surface);
}

.checkbox-input {
  width: 1.125rem;
  height: 1.125rem;
  accent-color: var(--md-primary);
}

.form-input {
  width: 100%;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: 1px solid var(--md-outline-variant, #cac4d0);
  border-radius: var(--md-radius-sm);
  font-size: var(--md-body-size);
  font-family: inherit;
  color: var(--md-on-surface);
  background: var(--md-surface);
  transition: var(--transition-fast);
}

.form-input:focus {
  outline: none;
  border-color: var(--md-primary);
  box-shadow: 0 0 0 3px var(--overlay-primary);
}

.form-input--narrow {
  max-width: 12rem;
}

.form-actions {
  display: flex;
  gap: var(--md-spacing-sm);
  padding-top: var(--md-spacing-sm);
}

.btn-primary {
  padding: var(--md-spacing-sm) var(--md-spacing-lg);
  background: var(--gradient-primary);
  color: white;
  border: none;
  border-radius: var(--md-radius-sm);
  font-size: var(--md-label-size);
  font-weight: 600;
  cursor: pointer;
  box-shadow: var(--md-elevation-1);
  transition: var(--transition-fast);
}

.btn-primary:hover:not(:disabled) {
  filter: brightness(0.96);
  box-shadow: var(--md-elevation-2);
  transform: translateY(-1px);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-secondary {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  background: var(--md-surface);
  color: var(--md-on-surface-variant);
  border: 1px solid var(--md-outline-variant, #cac4d0);
  border-radius: var(--md-radius-sm);
  font-size: var(--md-label-size);
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition-fast);
}

.btn-secondary:hover {
  background: var(--md-surface-variant);
  color: var(--md-on-surface);
  border-color: var(--md-outline);
}

.btn-sm {
  padding: var(--md-spacing-xs) var(--md-spacing-md);
  font-size: var(--md-label-size);
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: var(--md-spacing-md);
  margin-bottom: var(--md-spacing-md);
}

.toolbar-field {
  margin: 0;
  min-width: 12rem;
}

.table-wrap {
  overflow-x: auto;
  border-radius: var(--md-radius-sm);
  border: 1px solid var(--md-outline-variant, #cac4d0);
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-x: contain;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--md-label-size);
}

.data-table th,
.data-table td {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  text-align: left;
  border-bottom: 1px solid var(--md-outline-variant, #cac4d0);
}

.data-table th {
  background: var(--md-surface-variant);
  font-weight: 600;
  color: var(--md-on-surface);
  white-space: nowrap;
}

.data-table tbody tr:hover {
  background: var(--overlay-primary);
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.tx-user-cell {
  min-width: 160px;
  vertical-align: top;
}

.tx-user-line {
  line-height: 1.35;
}

.tx-user-line--name {
  font-weight: 600;
  color: var(--md-on-surface);
}

.tx-user-line--contact {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin-top: 2px;
  word-break: break-word;
}

.tx-user-line--id {
  font-size: 11px;
  color: var(--md-on-surface-variant);
  margin-top: 2px;
  opacity: 0.85;
}

.tx-user-fallback {
  color: var(--md-on-surface-variant);
}

.empty-hint {
  margin: var(--md-spacing-md) 0 0;
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

@media (max-width: 767px) {
  .promo-page {
    max-width: none;
    width: 100%;
    padding: 0;
  }

  .page-description {
    font-size: 0.8125rem;
    margin-bottom: var(--md-spacing-md);
    max-width: none;
  }

  .tabs {
    flex-wrap: nowrap;
    overflow-x: auto;
    overflow-y: hidden;
    -webkit-overflow-scrolling: touch;
    gap: 6px;
    margin-bottom: var(--md-spacing-md);
    padding-bottom: 2px;
    margin-left: -2px;
    margin-right: -2px;
    padding-left: 2px;
    padding-right: 2px;
  }

  .tab {
    flex-shrink: 0;
    min-height: 44px;
    padding: 10px 14px;
    font-size: 0.875rem;
    border-radius: 8px 8px 0 0;
  }

  .panel-card {
    padding: var(--md-spacing-md);
    margin-bottom: var(--md-spacing-md);
  }

  .panel-heading {
    font-size: 1.05rem;
  }

  .toolbar {
    flex-direction: column;
    align-items: stretch;
    gap: var(--md-spacing-sm);
  }

  .toolbar-field {
    min-width: 0;
    width: 100%;
  }

  .toolbar .btn-secondary {
    min-height: 44px;
    width: 100%;
  }

  .form-input--narrow {
    max-width: none;
  }

  .form-actions .btn-primary {
    width: 100%;
    min-height: 44px;
  }

  .panel-heading-row {
    align-items: flex-start;
  }

  .panel-heading-row .btn-secondary {
    min-height: 44px;
  }

  .user-picker__dropdown {
    max-height: min(50vh, 280px);
  }

  .user-picker__selected {
    flex-direction: column;
    align-items: stretch;
  }

  .user-picker__selected .btn-sm {
    align-self: flex-start;
    min-height: 40px;
  }

  /* Wide tables: horizontal pan; keep columns readable */
  .data-table {
    min-width: 36rem;
    font-size: 0.8125rem;
  }

  .data-table th,
  .data-table td {
    padding: 8px 10px;
  }

  .tx-user-cell {
    min-width: 8.5rem;
  }

  .form-stack {
    max-width: none;
  }
}
</style>
