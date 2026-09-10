<template>
  <div class="earnings-page">
    <div class="page-header-actions">
      <select v-if="isAdmin" v-model="selectedUserId" class="deal-select" @change="loadEarnings">
        <option v-for="person in staff" :key="person.user_id" :value="String(person.user_id)">
          {{ person.user?.nickname || person.user?.email }}
        </option>
      </select>
      <div class="date-range">
        <label class="date-field">
          <span>开始</span>
          <input v-model="fromDate" type="date" class="date-input" @change="loadEarnings" />
        </label>
        <span class="date-sep">至</span>
        <label class="date-field">
          <span>结束</span>
          <input v-model="toDate" type="date" class="date-input" @change="loadEarnings" />
        </label>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="earnings">
      <section class="billing-card">
        <div class="billing-row">
          <div>
            <div class="label">结算周期</div>
            <div class="value">{{ earnings.billing?.cycle_label || '双周' }}</div>
          </div>
          <div>
            <div class="label">下次发薪</div>
            <div class="value highlight-text">
              {{ earnings.billing?.next_pay_date }}
              <span v-if="earnings.billing?.next_pay_weekday">（{{ earnings.billing.next_pay_weekday }}）</span>
            </div>
          </div>
        </div>
        <p class="billing-period">
          本期 {{ earnings.billing?.period_start }} 至 {{ earnings.billing?.period_end }}
        </p>
        <div class="rate-row">
          <div class="rate-chip">
            <span class="label">时薪</span>
            <strong>${{ rateDisplay(earnings.profile?.hourly_rate) }} / 小时</strong>
          </div>
          <div class="rate-chip">
            <span class="label">每单配送费</span>
            <strong>${{ rateDisplay(earnings.profile?.delivery_fee_per_order) }} / 单</strong>
          </div>
        </div>
      </section>

      <div class="summary-grid">
        <div class="summary-card">
          <div class="label">配货时间</div>
          <div class="value">{{ earnings.totals.hours }} 小时</div>
          <div class="sub">${{ earnings.totals.labor.toFixed(2) }}</div>
        </div>
        <div class="summary-card">
          <div class="label">配送费</div>
          <div class="value">{{ earnings.totals.delivery_count }} 单</div>
          <div class="sub">${{ earnings.totals.delivery.toFixed(2) }}</div>
        </div>
        <div class="summary-card">
          <div class="label">已付</div>
          <div class="value">${{ earnings.totals.paid.toFixed(2) }}</div>
        </div>
        <div class="summary-card highlight">
          <div class="label">待付</div>
          <div class="value">${{ earnings.totals.outstanding.toFixed(2) }}</div>
        </div>
      </div>

      <section class="panel">
        <div class="panel-header">
          <h3>打卡 / 配货时间</h3>
          <div class="panel-actions">
            <button v-if="!earnings.open_session" class="add-btn" @click="clockIn">上班打卡</button>
            <button v-else class="add-btn" @click="clockOut">下班打卡</button>
            <button class="ghost-btn" @click="showSessionForm = true">手动添加配货时间</button>
          </div>
        </div>
        <p v-if="earnings.open_session" class="open-session">
          进行中：{{ earnings.open_session.work_date }} {{ earnings.open_session.start_time }} 开始
        </p>
        <div v-if="showSessionForm" class="session-form">
          <input v-model="sessionForm.work_date" type="date" class="date-input" />
          <input v-model="sessionForm.start_time" type="time" class="date-input" />
          <input v-model="sessionForm.end_time" type="time" class="date-input" />
          <input v-model="sessionForm.notes" type="text" class="text-input" placeholder="备注，如周六配货" />
          <button class="add-btn compact" @click="saveSession">保存</button>
          <button class="ghost-btn" @click="showSessionForm = false">取消</button>
        </div>
        <div v-if="!earnings.sessions.length" class="empty-inline">暂无配货时间记录</div>
        <div v-for="session in earnings.sessions" :key="session.id" class="row-card">
          <div>
            <strong>{{ session.work_date }}</strong>
            <span class="muted"> {{ session.start_time }} – {{ session.end_time || '进行中' }}</span>
            <div class="muted">{{ session.minutes ?? Math.round((session.hours || 0) * 60) }} 分钟 × ${{ (session.hourly_rate_snapshot || 0).toFixed(2) }} ÷ 60 = ${{ session.labor_amount.toFixed(2) }}</div>
            <div v-if="session.notes" class="muted">{{ session.notes }}</div>
          </div>
          <button class="ghost-btn" @click="removeSession(session)">删除</button>
        </div>
      </section>

      <section class="panel">
        <div class="panel-header">
          <h3>配送费</h3>
        </div>
        <div v-if="!earnings.deliveries.length" class="empty-inline">暂无已完成的自己配送订单</div>
        <div v-for="row in earnings.deliveries" :key="row.order_id" class="row-card">
          <div>
            <strong>{{ row.order_number }}</strong>
            <div class="muted">{{ row.group_deal_title || '团购' }} · {{ row.delivered_at || '' }}</div>
          </div>
          <strong>${{ row.fee.toFixed(2) }}</strong>
        </div>
      </section>

      <section v-if="isAdmin" class="panel">
        <div class="panel-header">
          <h3>费率与付款</h3>
        </div>
        <div class="session-form">
          <label>时薪
            <input v-model="rateForm.hourly_rate" type="number" min="0" step="0.01" class="date-input" />
          </label>
          <label>每单配送费
            <input v-model="rateForm.delivery_fee_per_order" type="number" min="0" step="0.01" class="date-input" />
          </label>
          <button class="add-btn compact" @click="saveRates">保存费率</button>
        </div>
        <div class="session-form">
          <input v-model="payoutForm.amount" type="number" min="0" step="0.01" class="date-input" placeholder="付款金额" />
          <input v-model="payoutForm.notes" type="text" class="text-input" placeholder="备注" />
          <button class="add-btn compact" @click="savePayout">记录付款</button>
        </div>
        <div v-for="payout in earnings.payouts" :key="payout.id" class="row-card">
          <div>
            <strong>${{ payout.amount.toFixed(2) }}</strong>
            <div class="muted">{{ payout.paid_at }} {{ payout.notes || '' }}</div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'
import { getCurrentUser, isAdmin } from '../utils/auth'
import { useModal } from '../composables/useModal'

export default {
  name: 'FulfillmentEarnings',
  setup() {
    const { confirm, success, error: showError } = useModal()
    return { confirm, success, showError }
  },
  data() {
    const user = getCurrentUser()
    return {
      isAdmin: isAdmin(user),
      staff: [],
      selectedUserId: user?.id ? String(user.id) : '',
      fromDate: '',
      toDate: '',
      earnings: null,
      loading: false,
      error: null,
      showSessionForm: false,
      sessionForm: {
        work_date: new Date().toISOString().slice(0, 10),
        start_time: '16:00',
        end_time: '19:00',
        notes: ''
      },
      rateForm: { hourly_rate: 0, delivery_fee_per_order: 0 },
      payoutForm: { amount: '', notes: '' }
    }
  },
  mounted() {
    this.init()
  },
  methods: {
    async init() {
      if (this.isAdmin) {
        const res = await apiClient.get('/admin/fulfillment/staff')
        this.staff = res.data.staff || []
        if (this.staff.length && !this.staff.some((s) => String(s.user_id) === this.selectedUserId)) {
          this.selectedUserId = String(this.staff[0].user_id)
        }
      }
      await this.loadEarnings({ applyPeriod: true })
    },
    rateDisplay(value) {
      return Number(value || 0).toFixed(2)
    },
    async loadEarnings(options = {}) {
      const applyPeriod = options && options.applyPeriod === true
      this.loading = true
      this.error = null
      try {
        const params = {}
        if (this.selectedUserId) params.user_id = this.selectedUserId
        if (this.fromDate) params.from = this.fromDate
        if (this.toDate) params.to = this.toDate
        const res = await apiClient.get('/admin/fulfillment/earnings', { params })
        this.earnings = res.data
        if (res.data.profile) {
          this.rateForm.hourly_rate = res.data.profile.hourly_rate
          this.rateForm.delivery_fee_per_order = res.data.profile.delivery_fee_per_order
        }
        if (applyPeriod && res.data.billing && !this.fromDate && !this.toDate) {
          this.fromDate = res.data.billing.period_start
          this.toDate = res.data.billing.period_end
          await this.loadEarnings()
          return
        }
      } catch (e) {
        this.error = e.response?.data?.error || '加载收入失败'
      } finally {
        this.loading = false
      }
    },
    async clockIn() {
      try {
        await apiClient.post('/admin/fulfillment/work-sessions/clock-in', {
          user_id: this.selectedUserId
        })
        await this.success('已上班打卡')
        await this.loadEarnings()
      } catch (e) {
        await this.showError(e.response?.data?.error || '打卡失败')
      }
    },
    async clockOut() {
      try {
        await apiClient.post('/admin/fulfillment/work-sessions/clock-out', {
          user_id: this.selectedUserId
        })
        await this.success('已下班打卡')
        await this.loadEarnings()
      } catch (e) {
        await this.showError(e.response?.data?.error || '打卡失败')
      }
    },
    async saveSession() {
      try {
        await apiClient.post('/admin/fulfillment/work-sessions', {
          user_id: this.selectedUserId,
          ...this.sessionForm
        })
        this.showSessionForm = false
        await this.success('配货时间已保存')
        await this.loadEarnings()
      } catch (e) {
        await this.showError(e.response?.data?.error || '保存失败')
      }
    },
    async removeSession(session) {
      const ok = await this.confirm('删除这条配货时间？', { type: 'warning' })
      if (!ok) return
      try {
        await apiClient.delete(`/admin/fulfillment/work-sessions/${session.id}`)
        await this.loadEarnings()
      } catch (e) {
        await this.showError(e.response?.data?.error || '删除失败')
      }
    },
    async saveRates() {
      try {
        await apiClient.put(`/admin/fulfillment/profiles/${this.selectedUserId}`, this.rateForm)
        await this.success('费率已更新')
        await this.loadEarnings()
      } catch (e) {
        await this.showError(e.response?.data?.error || '保存失败')
      }
    },
    async savePayout() {
      if (!this.payoutForm.amount) return
      try {
        await apiClient.post('/admin/fulfillment/payouts', {
          user_id: this.selectedUserId,
          amount: this.payoutForm.amount,
          notes: this.payoutForm.notes
        })
        this.payoutForm = { amount: '', notes: '' }
        await this.success('已记录付款')
        await this.loadEarnings()
      } catch (e) {
        await this.showError(e.response?.data?.error || '保存失败')
      }
    }
  }
}
</script>

<style scoped>
.earnings-page {
  min-width: 0;
  max-width: 100%;
}
.page-header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--md-spacing-md);
  margin-bottom: var(--md-spacing-lg);
  align-items: center;
}
.deal-select, .date-input, .text-input {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: var(--md-radius-md);
  background: #fff;
  font-size: 16px;
}
.text-input {
  min-width: 180px;
}
.date-range {
  display: flex;
  gap: var(--md-spacing-sm);
  align-items: flex-end;
  min-width: 0;
}
.date-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0;
  flex: 1;
}
.date-field span {
  color: var(--md-on-surface-variant);
  font-size: var(--md-label-size);
}
.date-sep {
  padding-bottom: 0.7rem;
  color: var(--md-on-surface-variant);
}
.date-input {
  min-width: 0;
  max-width: 100%;
  width: 100%;
  box-sizing: border-box;
}
.loading, .error {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}
.billing-card {
  background: #fff;
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12);
  margin-bottom: var(--md-spacing-lg);
  border: 1px solid rgba(255, 140, 0, 0.28);
}
.billing-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--md-spacing-md);
}
.billing-card .label {
  color: var(--md-on-surface-variant);
  font-size: var(--md-label-size);
}
.billing-card .value {
  font-size: 1.15rem;
  font-weight: 600;
  margin-top: 0.2rem;
}
.highlight-text {
  color: #E65100;
}
.billing-period {
  margin: 0.65rem 0 0;
  color: var(--md-on-surface-variant);
  font-size: var(--md-label-size);
}
.rate-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.6rem;
  margin-top: var(--md-spacing-md);
}
.rate-chip {
  background: #FFF8F0;
  border-radius: var(--md-radius-md);
  padding: 0.7rem 0.8rem;
}
.rate-chip .label {
  display: block;
  margin-bottom: 0.2rem;
}
.rate-chip strong {
  font-size: 1rem;
}
.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--md-spacing-md);
  margin-bottom: var(--md-spacing-lg);
}
@media (min-width: 800px) {
  .summary-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
.summary-card {
  background: #fff;
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12);
  min-width: 0;
}
.summary-card.highlight {
  border: 1px solid rgba(255, 140, 0, 0.35);
}
.summary-card .label {
  color: var(--md-on-surface-variant);
  font-size: var(--md-label-size);
}
.summary-card .value {
  font-size: 1.4rem;
  font-weight: 600;
  margin-top: 0.25rem;
  overflow-wrap: anywhere;
}
.summary-card .sub {
  color: var(--md-on-surface-variant);
}
.panel {
  background: #fff;
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12);
  margin-bottom: var(--md-spacing-lg);
  min-width: 0;
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--md-spacing-md);
  flex-wrap: wrap;
  margin-bottom: var(--md-spacing-md);
}
.panel-header h3 {
  margin: 0;
}
.panel-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.add-btn, .ghost-btn {
  border: none;
  border-radius: var(--md-radius-sm);
  padding: 0.45rem 0.8rem;
  cursor: pointer;
  font-weight: 500;
}
.add-btn {
  background: var(--md-primary);
  color: #fff;
}
.ghost-btn {
  background: rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.12);
}
.row-card {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--md-spacing-md);
  padding: var(--md-spacing-md) 0;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  min-width: 0;
}
.row-card > div {
  min-width: 0;
}
.muted {
  color: var(--md-on-surface-variant);
  font-size: var(--md-label-size);
  overflow-wrap: anywhere;
}
.session-form {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: var(--md-spacing-md);
  align-items: center;
}
.session-form label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}
.open-session {
  background: #FFF3E0;
  color: #E65100;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border-radius: var(--md-radius-sm);
}
.empty-inline {
  color: var(--md-on-surface-variant);
}

@media (max-width: 767px) {
  .page-header-actions {
    flex-direction: column;
    align-items: stretch;
    gap: var(--md-spacing-sm);
    margin-bottom: var(--md-spacing-md);
  }
  .deal-select, .date-range, .text-input, .date-input, .date-field {
    width: 100%;
    box-sizing: border-box;
  }
  .date-range {
    flex-direction: column;
    align-items: stretch;
  }
  .date-sep {
    display: none;
  }
  .billing-card {
    padding: var(--md-spacing-md);
    margin-bottom: var(--md-spacing-md);
  }
  .billing-row,
  .rate-row {
    grid-template-columns: 1fr;
  }
  .summary-grid {
    gap: 0.6rem;
    margin-bottom: var(--md-spacing-md);
  }
  .summary-card {
    padding: var(--md-spacing-md);
  }
  .summary-card .value {
    font-size: 1.15rem;
  }
  .panel {
    padding: var(--md-spacing-md);
    margin-bottom: var(--md-spacing-md);
  }
  .panel-header {
    flex-direction: column;
    align-items: stretch;
  }
  .panel-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }
  .add-btn, .ghost-btn {
    min-height: 44px;
    width: 100%;
  }
  .session-form {
    flex-direction: column;
    align-items: stretch;
  }
  .session-form label,
  .session-form .date-input,
  .session-form .text-input {
    width: 100%;
    box-sizing: border-box;
  }
  .row-card {
    flex-wrap: wrap;
  }
  .row-card .ghost-btn {
    width: auto;
    min-width: 72px;
  }
}
</style>
