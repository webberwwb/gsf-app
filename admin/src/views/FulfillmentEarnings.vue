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
            <input
              v-if="isAdmin && editingRate"
              v-model="rateForm.hourly_rate"
              type="number"
              min="0"
              step="0.01"
              class="date-input rate-input"
              aria-label="时薪"
            />
            <div v-else class="value rate-value">
              <span>${{ rateDisplay(earnings.profile?.hourly_rate) }}</span>
              <button
                v-if="isAdmin"
                type="button"
                class="session-icon-btn"
                title="编辑时薪"
                aria-label="编辑时薪"
                @click="startRateEdit"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                </svg>
              </button>
            </div>
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
        <div v-if="isAdmin && editingRate" class="rate-edit">
          <button type="button" class="ghost-btn" :disabled="savingRate" @click="cancelRateEdit">取消</button>
          <button type="button" class="add-btn" :disabled="savingRate" @click="saveRates">保存</button>
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

      <div v-else-if="activeTab === 'delivery'" class="settlement-tab">
        <div v-if="!deliveryCycles.length" class="empty-inline">暂无已完成的自己配送订单</div>
        <section
          v-for="cycle in deliveryCycles"
          :key="`delivery-deal-${cycle.group_deal_id || 'unassigned'}`"
          class="billing-card"
        >
          <button
            type="button"
            class="cycle-toggle"
            :aria-expanded="deliveryOpen(cycle) ? 'true' : 'false'"
            @click="toggleLog('delivery', cycle)"
          >
            <div class="cycle-heading">
              <div class="value">{{ cycle.group_deal_title || '未关联团购' }}</div>
              <div v-if="cycle.pickup_date" class="muted">
                取货 {{ cycle.pickup_date }}
                <span v-if="cycle.group_deal_status_label"> · {{ cycle.group_deal_status_label }}</span>
              </div>
            </div>
            <span class="cycle-toggle-side">
              <span class="cycle-earn">${{ rateDisplay(cycle.totals?.delivery) }}</span>
              <span class="cycle-toggle-meta">
                <span>{{ cycle.deliveries.length }} 单</span>
                <span class="cycle-chevron" :class="{ open: deliveryOpen(cycle) }" aria-hidden="true"></span>
              </span>
            </span>
          </button>
          <div v-show="deliveryOpen(cycle)">
          <div
            v-for="row in cycle.deliveries"
            :key="row.order_id"
            class="row-card delivery-row"
            :class="{ 'is-editing': isAdmin && editingFeeId === row.order_id }"
          >
            <div class="delivery-head">
              <strong>{{ row.recipient_name || '客户' }}</strong>
              <span v-if="Number(row.cash_collected) > 0" class="delivery-cash">${{ rateDisplay(row.cash_collected) }}</span>
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
                <span class="fee-readout">${{ Number(row.fee).toFixed(2) }}</span>
                <button
                  v-if="isAdmin"
                  type="button"
                  class="session-icon-btn"
                  :title="row.fee_overridden ? `已更正，系统建议 $${rateDisplay(row.suggested_fee)}` : '更正配送费'"
                  aria-label="更正配送费"
                  @click="startFeeEdit(row)"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                  </svg>
                </button>
              </template>
            </div>
            <div class="delivery-address">{{ row.address || '无地址' }}</div>
          </div>
          </div>
        </section>
      </div>

      <div v-else class="settlement-tab">
        <div v-if="!(earnings.cycles || []).length" class="empty-inline">暂无团购结算</div>
        <section
          v-for="cycle in (earnings.cycles || [])"
          :key="cycle.group_deal_id || 'unassigned'"
          class="billing-card"
        >
          <div class="cycle-heading-row">
            <div class="cycle-heading">
              <div class="label">团购</div>
              <div class="value">{{ cycle.group_deal_title || '未关联团购' }}</div>
              <div v-if="cycle.pickup_date" class="muted">
                取货 {{ cycle.pickup_date }}
                <span v-if="cycle.group_deal_status_label"> · {{ cycle.group_deal_status_label }}</span>
              </div>
            </div>
            <div class="cycle-settle">
              <span v-if="cycle.settled" class="settled-badge">已结算</span>
              <button
                v-if="isAdmin && !cycle.settled"
                type="button"
                class="add-btn"
                :disabled="settlingId === (cycle.group_deal_id || 'unassigned')"
                @click="markSettled(cycle, true)"
              >标为已结算</button>
              <button
                v-else-if="isAdmin && cycle.settled"
                type="button"
                class="ghost-btn"
                :disabled="settlingId === (cycle.group_deal_id || 'unassigned')"
                @click="markSettled(cycle, false)"
              >撤销</button>
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
              <div class="label">代收现金</div>
              <div class="value">-${{ rateDisplay(cycle.totals.cash_collected) }}</div>
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
          <button
            type="button"
            class="log-toggle"
            :aria-expanded="logOpen('settlement', cycle) ? 'true' : 'false'"
            @click="toggleLog('settlement', cycle)"
          >
            <span>{{ logOpen('settlement', cycle) ? '收起明细' : '展开明细' }}</span>
            <span class="muted">{{ (cycle.sessions || []).length }} 次配货 · {{ (cycle.deliveries || []).length }} 单配送</span>
            <span class="cycle-chevron" :class="{ open: logOpen('settlement', cycle) }" aria-hidden="true"></span>
          </button>
          <div v-show="logOpen('settlement', cycle)" class="cycle-detail">
            <div class="cycle-detail-title">配货记录</div>
            <div v-if="!(cycle.sessions || []).length" class="empty-inline">这个团购没有配货时间</div>
            <div v-for="session in cycle.sessions" :key="`session-${session.id}`" class="session-card">
              <div class="session-row">
                <strong>{{ session.work_date }}</strong>
                <strong>${{ rateDisplay(session.labor_amount) }}</strong>
              </div>
              <div class="muted">{{ session.start_time }} – {{ session.end_time || '进行中' }}<span v-if="session.hours != null"> · {{ hoursDisplay(session.hours) }} 小时</span></div>
              <div v-if="session.notes" class="muted">{{ session.notes }}</div>
            </div>
            <div class="cycle-detail-title">配送记录</div>
            <div v-if="!(cycle.deliveries || []).length" class="empty-inline">这个团购没有配送订单</div>
            <div v-for="row in cycle.deliveries" :key="`delivery-${row.order_id}`" class="row-card delivery-row">
              <div class="delivery-head">
                <strong>{{ row.recipient_name || '客户' }}</strong>
                <span class="delivery-earn">${{ Number(row.fee || 0).toFixed(2) }}</span>
                <span v-if="Number(row.cash_collected) > 0" class="delivery-cash">${{ rateDisplay(row.cash_collected) }}</span>
              </div>
              <div class="delivery-address">{{ row.address || '无地址' }}</div>
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
      editingRate: false,
      savingRate: false,
      payoutForm: { amount: '', notes: '' },
      editingFeeId: null,
      editingFeeAmount: '',
      savingFee: false,
      settlingId: null,
      expandedLogs: {}
    }
  },
  computed: {
    totalEarned() {
      const totals = this.earnings?.totals || {}
      if (totals.earned != null) return totals.earned
      return Number(totals.labor || 0) + Number(totals.delivery || 0)
    },
    deliveryCycles() {
      return (this.earnings?.cycles || []).filter((cycle) => (cycle.deliveries || []).length)
    }
  },
  mounted() {
    this.init()
  },
  methods: {
    logKey(scope, cycle) {
      return `${scope}:${cycle.group_deal_id || 'unassigned'}`
    },
    logOpen(scope, cycle) {
      return !!this.expandedLogs[this.logKey(scope, cycle)]
    },
    toggleLog(scope, cycle) {
      const key = this.logKey(scope, cycle)
      this.expandedLogs = {
        ...this.expandedLogs,
        [key]: !this.expandedLogs[key]
      }
    },
    deliveryOpen(cycle) {
      if (this.logOpen('delivery', cycle)) return true
      return (cycle.deliveries || []).some((row) => row.order_id === this.editingFeeId)
    },
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
    startRateEdit() {
      this.rateForm.hourly_rate = this.earnings?.profile?.hourly_rate ?? 0
      this.editingRate = true
    },
    cancelRateEdit() {
      this.editingRate = false
      this.rateForm.hourly_rate = this.earnings?.profile?.hourly_rate ?? 0
    },
    async saveRates() {
      this.savingRate = true
      try {
        await apiClient.put(`/admin/fulfillment/profiles/${this.selectedUserId}`, {
          hourly_rate: this.rateForm.hourly_rate
        })
        this.editingRate = false
        await this.success('时薪已更新')
        await this.loadEarnings()
      } catch (e) {
        await this.showError(e.response?.data?.error || '保存失败')
      } finally {
        this.savingRate = false
      }
    },
    async markSettled(cycle, settled) {
      const title = cycle.group_deal_title || '未关联团购'
      const ok = await this.confirm(
        settled ? `把「${title}」标为已结算？这一期的待付会记成已付。` : `撤销「${title}」的已结算？`,
        { type: 'warning' }
      )
      if (!ok) return
      const key = cycle.group_deal_id || 'unassigned'
      this.settlingId = key
      try {
        await apiClient.post('/admin/fulfillment/settlements', {
          user_id: this.selectedUserId,
          group_deal_id: cycle.group_deal_id,
          settled
        })
        await this.loadEarnings()
      } catch (e) {
        await this.showError(e.response?.data?.error || '结算失败')
      } finally {
        this.settlingId = null
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
.overview-card .rate-value {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.1rem;
}
.overview-card .rate-value .session-icon-btn {
  width: 28px;
  height: 28px;
  min-width: 28px;
  min-height: 28px;
}
.overview-card .rate-input {
  width: 6.5rem;
  max-width: 100%;
  height: 36px;
  margin-top: 0.15rem;
  text-align: center;
  box-sizing: border-box;
}
.rate-edit {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 0.85rem;
  margin-bottom: 0;
  padding-top: 0.85rem;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}
.rate-edit .add-btn,
.rate-edit .ghost-btn {
  width: auto;
  min-height: 42px;
  height: 42px;
  padding: 0 0.9rem;
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
.cycle-heading .value {
  overflow-wrap: anywhere;
}
.cycle-heading-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}
.cycle-heading {
  min-width: 0;
}
.cycle-settle {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex: 0 0 auto;
}
.cycle-settle .add-btn,
.cycle-settle .ghost-btn {
  width: auto;
  min-height: 36px;
  padding: 0.35rem 0.7rem;
  white-space: nowrap;
}
.settled-badge {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 0.55rem;
  border-radius: 999px;
  background: rgba(46, 125, 50, 0.12);
  color: #2e7d32;
  font-size: 13px;
  font-weight: 600;
}
.cycle-toggle {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  width: 100%;
  margin: 0;
  padding: 0;
  border: none;
  background: transparent;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}
.cycle-toggle-side,
.log-toggle {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  flex: 0 0 auto;
  color: var(--md-on-surface-variant);
  font-size: 13px;
}
.log-toggle {
  width: 100%;
  min-height: 44px;
  margin-top: var(--md-spacing-md);
  padding: 0.65rem 0 0;
  border: none;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  background: transparent;
  color: inherit;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  text-align: left;
  cursor: pointer;
}
.cycle-toggle-side {
  flex-direction: column;
  align-items: flex-end;
  gap: 0.1rem;
}
.cycle-earn {
  color: var(--md-on-surface);
  font-size: 18px;
  font-weight: 600;
  line-height: 1.3;
  font-variant-numeric: tabular-nums;
}
.cycle-toggle-meta {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}
.log-toggle .muted {
  font-weight: 400;
  margin-right: auto;
}
.cycle-chevron {
  width: 0.4rem;
  height: 0.4rem;
  border-right: 2px solid currentColor;
  border-bottom: 2px solid currentColor;
  transform: rotate(45deg);
  margin-top: -0.15rem;
  flex: 0 0 auto;
}
.cycle-chevron.open {
  transform: rotate(-135deg);
  margin-top: 0.15rem;
}
.cycle-detail {
  margin-top: var(--md-spacing-md);
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}
.cycle-detail-title {
  margin-top: var(--md-spacing-md);
  font-size: var(--md-label-size);
  font-weight: 600;
  color: var(--md-on-surface);
}
@media (min-width: 800px) {
  .billing-row--rates {
    grid-template-columns: repeat(3, 1fr);
  }
  .billing-row--stats {
    grid-template-columns: repeat(5, 1fr);
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
.delivery-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  column-gap: 0.75rem;
  row-gap: 0.2rem;
  align-items: center;
  padding: 0.8rem 0;
}
.delivery-head {
  display: flex;
  align-items: baseline;
  gap: 0.35rem;
  min-width: 0;
}
.delivery-head strong {
  flex: 1 1 auto;
  min-width: 2.5rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 15px;
  line-height: 1.3;
}
.delivery-earn {
  flex: 0 0 auto;
  font-size: 16px;
  line-height: 1.3;
  color: var(--md-on-surface);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.delivery-cash {
  flex: 0 0 auto;
  margin-left: auto;
  font-size: 14px;
  line-height: 1.3;
  color: #c62828;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.delivery-address {
  grid-column: 1 / -1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  line-height: 1.35;
  color: var(--md-on-surface-variant);
  font-weight: 400;
}
.delivery-row.is-editing {
  grid-template-columns: minmax(0, 1fr);
}
.delivery-row.is-editing .fee-cell {
  grid-column: 1 / -1;
  justify-content: flex-start;
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
  gap: 0.35rem;
  flex-shrink: 0;
  flex-wrap: nowrap;
}
.fee-readout {
  font-size: 16px;
  font-weight: 600;
  color: var(--md-on-surface);
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}
.fee-cell .ghost-btn,
.fee-cell .add-btn {
  min-height: 32px;
  width: auto;
  padding: 0.2rem 0.5rem;
  font-size: 12px;
}
.fee-cell .fee-edit {
  min-height: 32px;
  height: auto;
  min-width: 3.6rem;
  padding: 0.2rem 0.5rem;
  font-size: 16px;
  font-weight: 600;
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
  color: var(--md-on-surface);
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
  .cycle-settle .add-btn,
  .cycle-settle .ghost-btn {
    width: auto;
    min-height: 36px;
  }
  .rate-edit {
    flex-direction: row;
    align-items: center;
    justify-content: flex-end;
  }
  .rate-edit .add-btn,
  .rate-edit .ghost-btn {
    width: auto;
    min-width: 72px;
    min-height: 42px;
  }
  .fee-cell .ghost-btn,
  .fee-cell .add-btn {
    min-height: 36px;
    width: auto;
    padding: 0.2rem 0.55rem;
  }
  .fee-cell .fee-edit {
    min-height: 32px;
    height: auto;
    min-width: 3.6rem;
    width: auto;
    padding: 0.2rem 0.5rem;
    font-size: 16px;
    font-weight: 600;
    line-height: 1.2;
  }
  .delivery-head strong {
    font-size: 15px;
  }
  .delivery-earn {
    font-size: 16px;
  }
  .delivery-cash {
    font-size: 14px;
  }
  .delivery-address {
    font-size: 13px;
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
  .fee-cell .fee-edit {
    min-width: 3.6rem;
    width: auto;
  }
  .session-icon-btn {
    width: 33px;
    height: 33px;
    min-width: 33px;
    min-height: 33px;
  }
}
</style>
