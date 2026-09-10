<template>
  <div class="earnings-page">
    <div v-if="isAdmin" class="page-header-actions">
      <select v-model="selectedUserId" class="deal-select" @change="loadEarnings">
        <option v-for="person in staff" :key="person.user_id" :value="String(person.user_id)">
          {{ person.user?.nickname || person.user?.email }}
        </option>
      </select>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="earnings">
      <section class="billing-card overview-card">
        <div class="overview-grid">
          <div>
            <div class="label">时薪</div>
            <div class="value">${{ rateDisplay(earnings.profile?.hourly_rate) }}</div>
          </div>
          <div>
            <div class="label">万锦 / 列治文山</div>
            <div class="value">${{ rateDisplay(earnings.delivery_fees?.nearby_fee) }}</div>
          </div>
          <div>
            <div class="label">其他地区</div>
            <div class="value">${{ rateDisplay(earnings.delivery_fees?.other_fee) }}</div>
          </div>
          <div>
            <div class="label">累计配货时间</div>
            <div class="value">{{ hoursDisplay(earnings.totals?.hours) }}<span class="unit">小时</span></div>
          </div>
          <div>
            <div class="label">累计配送订单</div>
            <div class="value">{{ earnings.totals?.delivery_count || 0 }}<span class="unit">单</span></div>
          </div>
          <div>
            <div class="label">累计收入</div>
            <div class="value highlight-text">${{ rateDisplay(totalEarned) }}</div>
          </div>
        </div>
        <div v-if="isAdmin" class="session-form rate-edit">
          <label>时薪
            <input v-model="rateForm.hourly_rate" type="number" min="0" step="0.01" class="date-input" />
          </label>
          <button class="add-btn compact" @click="saveRates">保存费率</button>
        </div>
      </section>

      <div class="lane-tabs" role="tablist">
        <button
          type="button"
          role="tab"
          class="lane-tab"
          :class="{ active: activeTab === 'packing' }"
          :aria-selected="activeTab === 'packing'"
          @click="activeTab = 'packing'"
        >配货记录</button>
        <button
          type="button"
          role="tab"
          class="lane-tab"
          :class="{ active: activeTab === 'delivery' }"
          :aria-selected="activeTab === 'delivery'"
          @click="activeTab = 'delivery'"
        >配送记录</button>
        <button
          type="button"
          role="tab"
          class="lane-tab"
          :class="{ active: activeTab === 'settlement' }"
          :aria-selected="activeTab === 'settlement'"
          @click="activeTab = 'settlement'"
        >结算记录</button>
      </div>

      <section v-if="activeTab === 'packing'" class="panel">
        <div class="panel-header">
          <div class="panel-actions">
            <button v-if="!earnings.open_session" class="add-btn" @click="clockIn">上班打卡</button>
            <button v-else class="add-btn" @click="clockOut">下班打卡</button>
            <button class="ghost-btn" @click="startAddSession">手动添加配货时间</button>
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
          <button class="ghost-btn" @click="cancelSessionForm">取消</button>
        </div>
        <div v-if="!earnings.sessions.length" class="empty-inline">暂无配货时间记录</div>
        <div v-for="session in earnings.sessions" :key="session.id" class="session-card">
          <div class="session-row">
            <strong>{{ session.work_date }}</strong>
            <strong>${{ rateDisplay(session.labor_amount) }}</strong>
          </div>
          <div class="session-row">
            <span class="muted">{{ session.start_time }} – {{ session.end_time || '进行中' }}</span>
            <div class="session-actions">
              <button
                type="button"
                class="session-icon-btn"
                title="编辑"
                aria-label="编辑配货时间"
                @click="startEditSession(session)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                </svg>
              </button>
              <button
                type="button"
                class="session-icon-btn session-icon-btn--danger"
                title="删除"
                aria-label="删除配货时间"
                @click="removeSession(session)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                </svg>
              </button>
            </div>
          </div>
          <div v-if="session.notes" class="muted">{{ session.notes }}</div>
        </div>
      </section>

      <section v-else-if="activeTab === 'delivery'" class="panel">
        <div v-if="!earnings.deliveries.length" class="empty-inline">暂无已完成的自己配送订单</div>
        <div v-for="row in earnings.deliveries" :key="row.order_id" class="row-card">
          <div>
            <strong>{{ row.order_number }}</strong>
            <div class="muted">{{ row.group_deal_title || '团购' }}<span v-if="row.city"> · {{ row.city }}</span> · {{ row.delivered_at || '' }}</div>
            <div v-if="row.fee_overridden" class="muted">已更正（系统建议 ${{ rateDisplay(row.suggested_fee) }}）</div>
          </div>
          <div class="fee-cell">
            <template v-if="isAdmin && editingFeeId === row.order_id">
              <input
                v-model="editingFeeAmount"
                type="number"
                min="0"
                step="0.01"
                class="date-input fee-input"
              />
              <button type="button" class="add-btn compact" :disabled="savingFee" @click="saveFee(row)">保存</button>
              <button type="button" class="ghost-btn" :disabled="savingFee" @click="cancelFeeEdit">取消</button>
            </template>
            <template v-else>
              <strong>${{ row.fee.toFixed(2) }}</strong>
              <button v-if="isAdmin" type="button" class="ghost-btn" @click="startFeeEdit(row)">更正</button>
            </template>
          </div>
        </div>
      </section>

      <div v-else class="settlement-tab">
        <section
          v-for="cycle in (earnings.cycles || [])"
          :key="cycle.period_end"
          class="billing-card"
        >
          <div class="billing-row">
            <div>
              <div class="label">结算周期</div>
              <div class="value">{{ cycle.period_start }} 至 {{ cycle.period_end }}</div>
            </div>
            <div>
              <div class="label">结算日期</div>
              <div class="value highlight-text">
                {{ cycle.pay_date }}
                <span v-if="cycle.pay_weekday">（{{ cycle.pay_weekday }}）</span>
              </div>
            </div>
          </div>
          <div class="billing-row billing-row--stats">
            <div>
              <div class="label">配货时间</div>
              <div class="value">{{ cycle.totals.hours }} 小时</div>
              <div class="muted">${{ cycle.totals.labor.toFixed(2) }}</div>
            </div>
            <div>
              <div class="label">配送费</div>
              <div class="value">{{ cycle.totals.delivery_count }} 单</div>
              <div class="muted">${{ cycle.totals.delivery.toFixed(2) }}</div>
            </div>
            <div>
              <div class="label">已付</div>
              <div class="value">${{ cycle.totals.paid.toFixed(2) }}</div>
            </div>
            <div>
              <div class="label">待付</div>
              <div class="value highlight-text">${{ cycle.totals.outstanding.toFixed(2) }}</div>
            </div>
          </div>
        </section>
        <section v-if="isAdmin" class="panel">
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
      earnings: null,
      activeTab: 'packing',
      loading: false,
      error: null,
      showSessionForm: false,
      editingSessionId: null,
      sessionForm: {
        work_date: new Date().toISOString().slice(0, 10),
        start_time: '16:00',
        end_time: '19:00',
        notes: ''
      },
      rateForm: { hourly_rate: 0 },
      payoutForm: { amount: '', notes: '' },
      editingFeeId: null,
      editingFeeAmount: '',
      savingFee: false
    }
  },
  computed: {
    totalEarned() {
      const totals = this.earnings?.totals || {}
      if (totals.earned != null) return totals.earned
      return Number(totals.labor || 0) + Number(totals.delivery || 0)
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
      await this.loadEarnings()
    },
    rateDisplay(value) {
      return Number(value || 0).toFixed(2)
    },
    hoursDisplay(value) {
      const hours = Number(value || 0)
      if (Number.isInteger(hours)) return String(hours)
      return hours.toFixed(1)
    },
    async loadEarnings() {
      this.loading = true
      this.error = null
      try {
        const params = {}
        if (this.selectedUserId) params.user_id = this.selectedUserId
        const res = await apiClient.get('/admin/fulfillment/earnings', { params })
        this.earnings = res.data
        if (res.data.profile) {
          this.rateForm.hourly_rate = res.data.profile.hourly_rate
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
    blankSessionForm() {
      return {
        work_date: new Date().toISOString().slice(0, 10),
        start_time: '16:00',
        end_time: '19:00',
        notes: ''
      }
    },
    startAddSession() {
      this.editingSessionId = null
      this.sessionForm = this.blankSessionForm()
      this.showSessionForm = true
    },
    startEditSession(session) {
      this.editingSessionId = session.id
      this.sessionForm = {
        work_date: session.work_date,
        start_time: session.start_time || '',
        end_time: session.end_time || '',
        notes: session.notes || ''
      }
      this.showSessionForm = true
    },
    cancelSessionForm() {
      this.showSessionForm = false
      this.editingSessionId = null
      this.sessionForm = this.blankSessionForm()
    },
    async saveSession() {
      try {
        if (this.editingSessionId) {
          await apiClient.patch(`/admin/fulfillment/work-sessions/${this.editingSessionId}`, this.sessionForm)
        } else {
          await apiClient.post('/admin/fulfillment/work-sessions', {
            user_id: this.selectedUserId,
            ...this.sessionForm
          })
        }
        this.cancelSessionForm()
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
    startFeeEdit(row) {
      this.editingFeeId = row.order_id
      this.editingFeeAmount = Number(row.fee).toFixed(2)
    },
    cancelFeeEdit() {
      this.editingFeeId = null
      this.editingFeeAmount = ''
      this.savingFee = false
    },
    async saveFee(row) {
      this.savingFee = true
      try {
        await apiClient.put(`/admin/fulfillment/orders/${row.order_id}/driver-fee`, {
          amount: this.editingFeeAmount
        })
        this.cancelFeeEdit()
        await this.success('配送费已更正')
        await this.loadEarnings()
      } catch (e) {
        await this.showError(e.response?.data?.error || '更正失败')
      } finally {
        this.savingFee = false
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
.overview-card {
  padding: 0.7rem var(--md-spacing-md);
}
.overview-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.4rem;
  align-items: center;
}
.overview-grid > * {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  min-height: 2.6rem;
}
.overview-card .label {
  font-size: 0.78rem;
  line-height: 1.25;
}
.overview-card .value {
  font-size: 1rem;
  font-weight: 600;
  margin-top: 0.1rem;
  letter-spacing: -0.01em;
  overflow-wrap: anywhere;
}
.overview-card .unit {
  margin-left: 0.15rem;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--md-on-surface-variant);
}
.overview-grid > :nth-child(n + 4) {
  padding-top: 1rem;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}
.rate-edit {
  margin-top: var(--md-spacing-md);
  margin-bottom: 0;
}
.lane-tabs {
  display: flex;
  gap: 0.4rem;
  margin: 0 0 var(--md-spacing-md);
  padding: 0.35rem 0 0.55rem;
}
.lane-tab {
  flex: 1;
  min-height: 44px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: var(--md-radius-md);
  background: #fff;
  color: var(--md-on-surface-variant);
  font-size: 13px;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.lane-tab.active {
  background: var(--md-primary);
  border-color: var(--md-primary);
  color: #fff;
}
.highlight-text {
  color: #E65100;
}
.billing-row--stats {
  margin-top: var(--md-spacing-md);
}
@media (min-width: 800px) {
  .billing-row--rates {
    grid-template-columns: repeat(3, 1fr);
  }
  .billing-row--stats {
    grid-template-columns: repeat(4, 1fr);
  }
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
  justify-content: flex-end;
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
.session-card {
  padding: 1rem 0;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}
.session-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--md-spacing-md);
}
.session-row + .session-row {
  margin-top: 0.12rem;
}
.session-actions {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  gap: 0;
}
.session-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 33px;
  height: 33px;
  min-width: 33px;
  min-height: 33px;
  padding: 0;
  border: none;
  background: transparent;
  color: #8a8a8a;
  border-radius: var(--md-radius-sm);
  cursor: pointer;
}
.session-icon-btn svg {
  width: 15px;
  height: 15px;
  display: block;
}
.session-icon-btn:hover {
  background: rgba(0, 0, 0, 0.06);
  color: var(--md-primary);
}
.session-icon-btn--danger:hover {
  color: #c62828;
  background: rgba(198, 40, 40, 0.08);
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
.fee-cell {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.4rem;
  flex-shrink: 0;
  flex-wrap: wrap;
}
.fee-input {
  width: 96px;
  min-width: 96px;
}

@media (max-width: 767px) {
  .overview-card .label {
    font-size: 0.72rem;
  }
  .overview-card .value {
    font-size: 0.92rem;
  }
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
  .billing-row--rates {
    grid-template-columns: 1fr;
  }
  .billing-row--stats {
    grid-template-columns: 1fr 1fr;
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
  .row-card .ghost-btn,
  .fee-cell .add-btn,
  .fee-cell .ghost-btn {
    width: auto;
    min-width: 72px;
  }
  .session-icon-btn {
    width: 33px;
    height: 33px;
    min-width: 33px;
    min-height: 33px;
  }
}
</style>
