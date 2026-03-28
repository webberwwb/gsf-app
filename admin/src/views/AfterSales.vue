<template>
  <div class="after-sales-page">
    <div class="tabs">
      <button
        type="button"
        @click="activeTab = 'first-time'"
        :class="['tab', { active: activeTab === 'first-time' }]"
      >
        首单回访
      </button>
      <button
        type="button"
        @click="activeTab = 'churned'"
        :class="['tab', { active: activeTab === 'churned' }]"
      >
        近两期未下单
      </button>
    </div>

    <div class="search-toolbar">
      <label class="filter-label filter-label--icon" for="after-sales-search" title="搜索">
        <span class="visually-hidden">搜索</span>
        <svg
          class="filter-icon-svg"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
          />
        </svg>
      </label>
      <input
        id="after-sales-search"
        v-model.trim="searchQuery"
        type="search"
        class="search-input"
        placeholder="搜索昵称、手机号、微信号…"
        enterkeyhint="search"
        autocomplete="off"
        @input="scheduleSearchReload"
      />
      <button
        v-if="searchQuery"
        type="button"
        class="search-clear"
        @click="clearSearch"
      >
        清除
      </button>
    </div>

    <!-- First-time buyers -->
    <div v-if="activeTab === 'first-time'" class="tab-content">
      <div v-if="groupDealOptions.length" class="filter-row filter-row--deal">
        <label class="filter-label filter-label--icon" for="first-time-deal-select" title="选择团购">
          <span class="visually-hidden">选择团购</span>
          <svg
            class="filter-icon-svg"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="1.5"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007zM8.625 10.5a.375.375 0 11-.75 0 .375.375 0 01.75 0zm7.5 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z"
            />
          </svg>
        </label>
        <select
          id="first-time-deal-select"
          v-model.number="firstTimeDealId"
          class="deal-select"
          @change="loadFirstTime"
        >
          <option v-for="d in groupDealOptions" :key="d.id" :value="d.id">
            {{ dealOptionLabel(d) }}
          </option>
        </select>
      </div>
      <div class="hint-block">
        <div class="hint-main hint-main--single">
          <span class="hint-text">
            展示所选团购中<strong>首次在本店下单</strong>的客户：全店仅有 1 笔有效订单，且该订单即发生在该期（不含管理员）。默认展示<strong>最新一期</strong>（截单时间最近），可在上方切换团购。
          </span>
        </div>
        <p class="hint-note">客户反馈可多次登记；尚无记录时显示为 0 条。</p>
      </div>

      <div v-if="loadingFirst" class="loading">加载中...</div>
      <div v-else-if="errorFirst" class="error">{{ errorFirst }}</div>
      <div v-else-if="!groupDealOptions.length" class="empty-state">
        <p>暂无团购数据</p>
      </div>
      <div v-else-if="firstTimeItems.length === 0" class="empty-state">
        <p>{{ searchQuery ? '无匹配客户，可更换关键词或清除搜索' : '暂无符合条件的首单客户' }}</p>
      </div>
      <div v-else class="card-list">
        <div
          v-for="row in firstTimeItems"
          :key="row.order.id"
          :class="['card', { 'card--has-feedback': hasFeedback(row) }]"
          role="button"
          tabindex="0"
          :aria-label="cardAriaLabel(row)"
          @click="openFollowUpModal(row, 'first-time')"
          @keydown.enter.prevent="openFollowUpModal(row, 'first-time')"
          @keydown.space.prevent="openFollowUpModal(row, 'first-time')"
        >
          <div class="card-main">
            <div class="card-title-row">
              <div class="card-title">
                {{ row.user.nickname || row.user.phone || '用户' + row.user.id }}
                <span v-if="row.user.wechat" class="muted">微信 {{ row.user.wechat }}</span>
              </div>
              <span
                class="status-pill"
                :class="hasFeedback(row) ? 'status-pill--done' : 'status-pill--todo'"
              >{{ hasFeedback(row) ? '已回访' : '待回访' }}</span>
            </div>
            <div v-if="row.deal_chips && row.deal_chips.length" class="deal-chips">
              <span
                v-for="d in row.deal_chips"
                :key="d.id"
                class="deal-chip"
                :class="d.has_order ? 'deal-chip--ordered' : 'deal-chip--none'"
                :title="d.title"
              >{{ d.title }}</span>
            </div>
            <div class="card-meta">
              <span>{{ row.user.phone || '—' }}</span>
              <span v-if="row.group_deal">团购 {{ row.group_deal.title }}</span>
              <span>订单 {{ row.order.order_number }}</span>
              <span v-if="row.order.final_total != null" class="order-total">合计 ${{ formatOrderMoney(row.order.final_total) }}</span>
              <span>{{ formatDateTime(row.order.created_at) }}</span>
              <span class="fu-count">反馈记录 {{ row.feedback && row.feedback.count != null ? row.feedback.count : 0 }} 条</span>
            </div>
            <div v-if="row.feedback && row.feedback.records && row.feedback.records.length" class="record-snippet">
              <div
                v-for="rec in row.feedback.records.slice(0, 2)"
                :key="rec.id"
                class="record-line"
              >
                <span class="outcome-tag">{{ outcomeLabel(rec.outcome) }}</span>
                <span v-if="rec.notes">{{ rec.notes }}</span>
                <span class="rec-time">{{ formatDateTime(rec.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Churned -->
    <div v-if="activeTab === 'churned'" class="tab-content">
      <div class="hint-block hint-block--plain">
        <p class="hint-main hint-main--single">
          曾下过单（不含管理员），但在「最近两期」团购中均未再下单。「最近两期」按截单时间从新到旧取前两期<span v-if="churnedMeta.recent_group_deals.length">：{{ churnedScopeLine }}</span>。
        </p>
      </div>

      <div v-if="loadingChurned" class="loading">加载中...</div>
      <div v-else-if="errorChurned" class="error">{{ errorChurned }}</div>
      <div v-else-if="churnedItems.length === 0" class="empty-state">
        <p>{{ searchQuery ? '无匹配客户，可更换关键词或清除搜索' : '暂无符合条件的客户' }}</p>
      </div>
      <div v-else class="card-list">
        <div
          v-for="row in churnedItems"
          :key="row.user.id"
          :class="['card', { 'card--has-feedback': hasFeedback(row) }]"
          role="button"
          tabindex="0"
          :aria-label="cardAriaLabel(row)"
          @click="openFollowUpModal(row, 'churned')"
          @keydown.enter.prevent="openFollowUpModal(row, 'churned')"
          @keydown.space.prevent="openFollowUpModal(row, 'churned')"
        >
          <div class="card-main">
            <div class="card-title-row">
              <div class="card-title">
                {{ row.user.nickname || row.user.phone || '用户' + row.user.id }}
                <span v-if="row.user.wechat" class="muted">微信 {{ row.user.wechat }}</span>
              </div>
              <span
                class="status-pill"
                :class="hasFeedback(row) ? 'status-pill--done' : 'status-pill--todo'"
              >{{ hasFeedback(row) ? '已回访' : '待回访' }}</span>
            </div>
            <div v-if="row.deal_chips && row.deal_chips.length" class="deal-chips">
              <span
                v-for="d in row.deal_chips"
                :key="d.id"
                class="deal-chip"
                :class="d.has_order ? 'deal-chip--ordered' : 'deal-chip--none'"
                :title="d.title"
              >{{ d.title }}</span>
            </div>
            <div class="card-meta">
              <span>有效订单数 {{ row.total_non_cancelled_orders }}</span>
              <span v-if="row.last_group_deal">上次团购 {{ row.last_group_deal.title }}</span>
              <span v-if="row.last_order && row.last_order.final_total != null" class="order-total">最近订单 ${{ formatOrderMoney(row.last_order.final_total) }}</span>
              <span v-if="row.last_order">{{ formatDateTime(row.last_order.created_at) }}</span>
              <span class="fu-count">反馈记录 {{ row.feedback && row.feedback.count != null ? row.feedback.count : 0 }} 条</span>
            </div>
            <div v-if="row.feedback && row.feedback.records && row.feedback.records.length" class="record-snippet">
              <div
                v-for="rec in row.feedback.records.slice(0, 2)"
                :key="rec.id"
                class="record-line"
              >
                <span class="outcome-tag">{{ outcomeLabel(rec.outcome) }}</span>
                <span v-if="rec.notes">{{ rec.notes }}</span>
                <span class="rec-time">{{ formatDateTime(rec.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add follow-up modal -->
    <div v-if="followUpModal.open" class="modal-overlay" @click.self="closeFollowUpModal">
      <div class="modal-box modal-wide">
        <div class="modal-head">
          <h2>添加回访记录</h2>
          <button type="button" class="close-x" @click="closeFollowUpModal" aria-label="关闭">×</button>
        </div>
        <div v-if="followUpModal.row" class="modal-body">
          <p class="modal-user">
            {{ followUpModal.row.user.nickname || followUpModal.row.user.phone }}
            <template v-if="followUpModal.tab === 'first-time' && followUpModal.row.order">
              · 订单 {{ followUpModal.row.order.order_number }}
            </template>
            <template v-else-if="followUpModal.tab === 'churned' && followUpModal.row.last_order">
              · 最近订单 {{ followUpModal.row.last_order.order_number }}
            </template>
          </p>

          <div v-if="historyRecords.length" class="history-block">
            <div class="history-title">已有记录（{{ historyRecords.length }} 条）</div>
            <div v-for="rec in historyRecords" :key="rec.id" class="history-row">
              <template v-if="editingHistoryId !== rec.id">
                <div class="history-row-main">
                  <span class="outcome-tag">{{ outcomeLabel(rec.outcome) }}</span>
                  <span v-if="rec.notes" class="history-notes">{{ rec.notes }}</span>
                  <span class="rec-time">{{ formatDateTime(rec.created_at) }}</span>
                  <span v-if="rec.created_by && rec.created_by.nickname" class="by-admin">{{ rec.created_by.nickname }}</span>
                </div>
                <div class="history-row-actions">
                  <button
                    type="button"
                    class="history-icon-btn"
                    title="编辑"
                    aria-label="编辑此条记录"
                    @click.stop="startEditHistory(rec)"
                  >
                    <svg class="history-icon-svg" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                    </svg>
                  </button>
                  <button
                    type="button"
                    class="history-icon-btn history-icon-btn--danger"
                    title="删除"
                    aria-label="删除此条记录"
                    @click.stop="deleteHistoryRecord(rec)"
                  >
                    <svg class="history-icon-svg" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                    </svg>
                  </button>
                </div>
              </template>
              <div v-else class="history-edit">
                <label class="history-edit-label">结果</label>
                <select v-model="editHistoryForm.outcome" class="field-input history-edit-field">
                  <option v-for="s in outcomeOptions" :key="s" :value="s">{{ outcomeLabel(s) }}</option>
                </select>
                <label class="history-edit-label">备注</label>
                <textarea v-model="editHistoryForm.notes" class="field-textarea history-edit-field" rows="3" placeholder="可选" />
                <div class="history-edit-actions">
                  <button type="button" class="btn-secondary btn-compact" @click="cancelEditHistory">取消</button>
                  <button type="button" class="btn-primary btn-compact" :disabled="savingHistoryEdit" @click="saveEditHistory">
                    {{ savingHistoryEdit ? '保存中…' : '保存' }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <label class="field-label">本次结果</label>
          <select v-model="followUpForm.outcome" class="field-input">
            <option v-for="s in outcomeOptions" :key="s" :value="s">{{ outcomeLabel(s) }}</option>
          </select>
          <label class="field-label">备注 / 反馈</label>
          <textarea
            v-model="followUpForm.notes"
            class="field-textarea"
            rows="4"
            placeholder="可选"
          />
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="closeFollowUpModal">取消</button>
            <button type="button" class="btn-primary" :disabled="savingFollowUp" @click="saveFollowUp">
              {{ savingFollowUp ? '保存中…' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'
import { formatDateTimeEST_CN } from '../utils/date'

const CONTEXT = {
  'first-time': 'after_sales_first_order',
  churned: 'after_sales_churned',
}

export default {
  name: 'AfterSales',
  data() {
    return {
      activeTab: 'first-time',
      firstTimeDealId: null,
      groupDealOptions: [],
      loadingFirst: false,
      errorFirst: null,
      firstTimeItems: [],
      outcomeOptions: ['不跟进', '再次跟进', '未回复', '未联系'],
      loadingChurned: false,
      errorChurned: null,
      churnedItems: [],
      churnedMeta: { recent_group_deals: [] },
      followUpModal: { open: false, row: null, tab: 'first-time' },
      followUpForm: { outcome: '未联系', notes: '' },
      savingFollowUp: false,
      editingHistoryId: null,
      editHistoryForm: { outcome: '', notes: '' },
      savingHistoryEdit: false,
      searchQuery: '',
    }
  },
  computed: {
    historyRecords() {
      const row = this.followUpModal.row
      if (!row || !row.feedback || !row.feedback.records) return []
      return row.feedback.records
    },
    churnedScopeLine() {
      const deals = this.churnedMeta.recent_group_deals || []
      return deals.map((d) => d.title).join(' · ')
    },
  },
  mounted() {
    this.loadFirstTime()
    this.loadChurned()
  },
  watch: {
    activeTab(tab) {
      if (tab === 'first-time') this.loadFirstTime()
      else this.loadChurned()
    },
  },
  methods: {
    hasFeedback(row) {
      return !!(row.feedback && row.feedback.count > 0)
    },
    cardAriaLabel(row) {
      const name = row.user.nickname || row.user.phone || `用户${row.user.id}`
      return `登记回访，${name}`
    },
    scheduleSearchReload() {
      clearTimeout(this._searchDebounce)
      this._searchDebounce = setTimeout(() => {
        if (this.activeTab === 'first-time') this.loadFirstTime()
        else this.loadChurned()
      }, 350)
    },
    clearSearch() {
      this.searchQuery = ''
      clearTimeout(this._searchDebounce)
      if (this.activeTab === 'first-time') this.loadFirstTime()
      else this.loadChurned()
    },
    formatDateTime(value) {
      return formatDateTimeEST_CN(value)
    },
    formatOrderMoney(n) {
      const v = Number(n)
      if (Number.isNaN(v)) return '0.00'
      return v.toFixed(2)
    },
    outcomeLabel(s) {
      const legacy = {
        pending: '未联系',
        reached: '再次跟进',
        no_answer: '未回复',
        will_not_follow: '不跟进',
      }
      return legacy[s] || s
    },
    dealOptionLabel(d) {
      const title = d.title || `团购 #${d.id}`
      const end = d.order_end_date ? this.formatDateTime(d.order_end_date) : ''
      return end ? `${title} · 截单 ${end}` : title
    },
    async loadFirstTime() {
      this.loadingFirst = true
      this.errorFirst = null
      try {
        const params = {}
        if (this.firstTimeDealId != null) {
          params.group_deal_id = this.firstTimeDealId
        }
        const sq = this.searchQuery.trim()
        if (sq) params.search = sq
        const { data } = await apiClient.get('/admin/after-sales/first-time-buyers', { params })
        this.firstTimeItems = data.items || []
        if (data.group_deal_options && data.group_deal_options.length) {
          this.groupDealOptions = data.group_deal_options
        }
        if (data.selected_group_deal_id != null) {
          this.firstTimeDealId = data.selected_group_deal_id
        }
        if (data.feedback_outcome_options && data.feedback_outcome_options.length) {
          this.outcomeOptions = data.feedback_outcome_options
        }
      } catch (e) {
        this.errorFirst = (e.response && e.response.data && e.response.data.message) || e.message || '加载失败'
      } finally {
        this.loadingFirst = false
      }
    },
    async loadChurned() {
      this.loadingChurned = true
      this.errorChurned = null
      try {
        const params = {}
        const sq = this.searchQuery.trim()
        if (sq) params.search = sq
        const { data } = await apiClient.get('/admin/after-sales/churned-buyers', { params })
        this.churnedItems = data.items || []
        this.churnedMeta = { recent_group_deals: data.recent_group_deals || [] }
        if (data.feedback_outcome_options && data.feedback_outcome_options.length) {
          this.outcomeOptions = data.feedback_outcome_options
        }
      } catch (e) {
        this.errorChurned = (e.response && e.response.data && e.response.data.message) || e.message || '加载失败'
      } finally {
        this.loadingChurned = false
      }
    },
    openFollowUpModal(row, tab) {
      this.editingHistoryId = null
      this.editHistoryForm = { outcome: '', notes: '' }
      this.followUpModal = { open: true, row, tab }
      this.followUpForm = { outcome: '未联系', notes: '' }
    },
    closeFollowUpModal() {
      this.editingHistoryId = null
      this.editHistoryForm = { outcome: '', notes: '' }
      this.followUpModal = { open: false, row: null, tab: 'first-time' }
    },
    startEditHistory(rec) {
      this.editingHistoryId = rec.id
      this.editHistoryForm = {
        outcome: rec.outcome || '未联系',
        notes: rec.notes || '',
      }
    },
    cancelEditHistory() {
      this.editingHistoryId = null
      this.editHistoryForm = { outcome: '', notes: '' }
    },
    async saveEditHistory() {
      if (!this.editingHistoryId) return
      this.savingHistoryEdit = true
      try {
        await apiClient.patch(`/admin/after-sales/customer-feedback/${this.editingHistoryId}`, {
          outcome: this.editHistoryForm.outcome,
          notes: this.editHistoryForm.notes,
        })
        this.cancelEditHistory()
        await this.refreshModalRowAfterFeedbackChange()
      } catch (e) {
        const msg = (e.response && e.response.data && e.response.data.message) || e.message || '保存失败'
        alert(msg)
      } finally {
        this.savingHistoryEdit = false
      }
    },
    async deleteHistoryRecord(rec) {
      if (!confirm('确定删除这条回访记录？')) return
      try {
        await apiClient.delete(`/admin/after-sales/customer-feedback/${rec.id}`)
        await this.refreshModalRowAfterFeedbackChange()
      } catch (e) {
        const msg = (e.response && e.response.data && e.response.data.message) || e.message || '删除失败'
        alert(msg)
      }
    },
    async refreshModalRowAfterFeedbackChange() {
      const tab = this.followUpModal.tab
      const uid = this.followUpModal.row && this.followUpModal.row.user && this.followUpModal.row.user.id
      if (!uid) return
      if (tab === 'first-time') {
        await this.loadFirstTime()
        const row = this.firstTimeItems.find((r) => r.user.id === uid)
        if (row) this.followUpModal = { ...this.followUpModal, row }
      } else {
        await this.loadChurned()
        const row = this.churnedItems.find((r) => r.user.id === uid)
        if (row) this.followUpModal = { ...this.followUpModal, row }
      }
    },
    async saveFollowUp() {
      const row = this.followUpModal.row
      const tab = this.followUpModal.tab
      if (!row || !row.user) return

      const context = CONTEXT[tab]
      let orderId = null
      if (tab === 'first-time' && row.order) orderId = row.order.id
      if (tab === 'churned' && row.last_order) orderId = row.last_order.id

      this.savingFollowUp = true
      try {
        const payload = {
          user_id: row.user.id,
          context,
          outcome: this.followUpForm.outcome,
          notes: this.followUpForm.notes,
        }
        if (orderId != null) payload.order_id = orderId

        await apiClient.post('/admin/after-sales/customer-feedback', payload)
        if (tab === 'first-time') {
          await this.loadFirstTime()
        } else {
          await this.loadChurned()
        }
        this.closeFollowUpModal()
      } catch (e) {
        const msg = (e.response && e.response.data && e.response.data.message) || e.message || '保存失败'
        alert(msg)
      } finally {
        this.savingFollowUp = false
      }
    },
  },
}
</script>

<style scoped>
.after-sales-page {
  --as-teal: rgba(0, 137, 123, 0.1);
  --as-teal-border: rgba(0, 121, 107, 0.35);
  width: 100%;
  min-width: 0;
  max-width: min(960px, 100%);
  box-sizing: border-box;
  padding: 2px 0 8px;
  border-radius: var(--md-radius-md);
  overflow-x: hidden;
}

.tabs {
  display: flex;
  gap: var(--md-spacing-sm);
  margin-bottom: var(--md-spacing-lg);
  border-bottom: 1px solid var(--md-surface-variant);
  padding-bottom: var(--md-spacing-sm);
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.tab {
  flex: 0 0 auto;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  background: transparent;
  border: none;
  border-radius: var(--md-radius-md);
  color: var(--md-on-surface-variant);
  text-align: left;
  cursor: pointer;
  font-size: var(--md-body-size);
}

.tab:hover {
  background: var(--md-surface-variant);
  color: var(--md-on-surface);
}

.tab.active {
  background: rgba(255, 140, 0, 0.14);
  color: #e65100;
  font-weight: 500;
}

.search-toolbar {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 0.5rem;
  margin-bottom: var(--md-spacing-md);
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.filter-row--deal {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 0.5rem;
  margin-bottom: var(--md-spacing-md);
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.filter-label--icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 44px;
  min-width: 44px;
  min-height: 44px;
  margin: 0;
  padding: 0;
  background: none;
  border: none;
  border-radius: 0;
  color: var(--md-primary);
  box-sizing: border-box;
  -webkit-tap-highlight-color: transparent;
}

.filter-label--icon:hover {
  color: #e65100;
}

.filter-icon-svg {
  width: 24px;
  height: 24px;
  display: block;
}

.deal-select {
  flex: 1;
  min-width: 0;
  max-width: 100%;
  padding: 10px 12px;
  font-size: 16px;
  border: 1px solid var(--md-surface-variant);
  border-radius: var(--md-radius-md);
  background: var(--md-surface);
  color: var(--md-on-surface);
  box-sizing: border-box;
  min-height: 44px;
}

.deal-select:focus {
  outline: none;
  border-color: var(--md-primary);
  box-shadow: 0 0 0 2px rgba(255, 140, 0, 0.2);
}

.search-input {
  flex: 1;
  min-width: 0;
  min-height: 44px;
  padding: 10px 12px;
  font-size: 16px;
  border: 1px solid var(--md-surface-variant);
  border-radius: var(--md-radius-md);
  background: var(--md-surface);
  color: var(--md-on-surface);
  box-sizing: border-box;
}

.search-input:focus {
  outline: none;
  border-color: var(--md-primary);
  box-shadow: 0 0 0 2px rgba(255, 140, 0, 0.2);
}

.search-clear {
  flex-shrink: 0;
  padding: 8px 12px;
  font-size: var(--md-label-size);
  border: 1px solid var(--md-surface-variant);
  border-radius: var(--md-radius-md);
  background: var(--md-surface);
  color: var(--md-on-surface-variant);
  cursor: pointer;
}

.search-clear:hover {
  background: var(--md-surface-variant);
  color: var(--md-on-surface);
}

.tab-content {
  padding-top: var(--md-spacing-sm);
  min-width: 0;
  max-width: 100%;
}

.hint-block {
  margin-bottom: var(--md-spacing-lg);
  padding: var(--md-spacing-md) var(--md-spacing-md);
  padding-left: calc(var(--md-spacing-md) + 3px);
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
  background: rgba(255, 140, 0, 0.06);
  border: 1px solid rgba(255, 140, 0, 0.2);
  border-left: 3px solid var(--md-primary);
  border-radius: var(--md-radius-md);
  box-shadow: var(--md-elevation-1);
}

.hint-block--plain {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  padding-left: calc(var(--md-spacing-md) + 3px);
  background: var(--as-teal);
  border-color: var(--as-teal-border);
  border-left-color: #00897b;
}

.hint-main {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem 0.5rem;
  font-size: var(--md-body-size);
  line-height: 1.55;
  color: var(--md-on-surface);
}

.hint-main--single {
  margin: 0;
  color: var(--md-on-surface-variant);
  font-size: var(--md-label-size);
  line-height: 1.6;
}

.hint-lead {
  font-weight: 500;
  color: var(--md-on-surface);
  white-space: nowrap;
}

.hint-text {
  flex: 1 1 12rem;
  min-width: 0;
  color: var(--md-on-surface-variant);
}

.num-field {
  display: inline-flex;
  align-items: center;
  gap: 0.15rem;
  margin: 0 0.1rem;
}

.num-suffix {
  font-size: var(--md-body-size);
  color: var(--md-on-surface);
  font-weight: 500;
  user-select: none;
}

.inline-num {
  width: 2.75rem;
  min-height: 2rem;
  padding: 0.2rem 0.35rem;
  border: 1px solid var(--md-outline-variant, #cac4d0);
  border-radius: var(--md-radius-sm);
  text-align: center;
  font-size: 1rem;
  font-variant-numeric: tabular-nums;
  line-height: 1.25;
  background: var(--md-surface);
  color: var(--md-on-surface);
  vertical-align: middle;
}

.inline-num:focus {
  outline: none;
  border-color: var(--md-primary);
  box-shadow: 0 0 0 2px rgba(255, 140, 0, 0.2);
}

.hint-note {
  margin: var(--md-spacing-sm) 0 0;
  padding-top: var(--md-spacing-sm);
  border-top: 1px solid var(--md-surface-variant);
  font-size: 0.8125rem;
  line-height: 1.5;
  color: var(--md-on-surface-variant);
}

.loading,
.error,
.empty-state {
  padding: var(--md-spacing-xl);
  text-align: center;
  color: var(--md-on-surface-variant);
}

.error {
  color: #c62828;
}

.card-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
  min-width: 0;
  max-width: 100%;
}

.card {
  display: block;
  padding: var(--md-spacing-md);
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
  background: #fff;
  border-radius: var(--md-radius-md);
  border: 1px solid var(--md-surface-variant);
  box-shadow: var(--md-elevation-1);
  cursor: pointer;
  text-align: left;
  transition: box-shadow 0.15s ease, border-color 0.15s ease, background 0.15s ease;
  -webkit-tap-highlight-color: transparent;
}

.card:hover {
  box-shadow: var(--md-elevation-2);
}

.card:focus {
  outline: none;
}

.card:focus-visible {
  outline: 2px solid var(--md-primary);
  outline-offset: 2px;
}

.card--has-feedback {
  padding-left: calc(var(--md-spacing-md) + 3px);
  border-left: 3px solid #2e7d32;
  background: rgba(46, 125, 50, 0.06);
  border-color: rgba(46, 125, 50, 0.2);
}

.card-main {
  flex: 1;
  min-width: 0;
}

.card-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--md-spacing-sm);
  margin-bottom: var(--md-spacing-xs);
}

.card-title {
  font-weight: 500;
  color: var(--md-on-surface);
  margin: 0;
  flex: 1;
  min-width: 0;
}

.status-pill {
  flex-shrink: 0;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  padding: 4px 8px;
  border-radius: 999px;
  line-height: 1.2;
  white-space: nowrap;
}

.status-pill--todo {
  color: #e65100;
  background: rgba(255, 152, 0, 0.2);
}

.status-pill--done {
  color: #1b5e20;
  background: rgba(46, 125, 50, 0.18);
}

.deal-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: var(--md-spacing-xs);
  margin-bottom: 2px;
}

.deal-chip {
  display: inline-block;
  max-width: 100%;
  padding: 4px 10px;
  font-size: 0.7rem;
  font-weight: 500;
  line-height: 1.35;
  border-radius: 999px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  box-sizing: border-box;
}

.deal-chip--ordered {
  color: #e65100;
  background: rgba(255, 140, 0, 0.16);
  border: 1px solid rgba(255, 140, 0, 0.5);
}

.deal-chip--none {
  color: var(--md-on-surface-variant);
  background: rgba(0, 0, 0, 0.05);
  border: 1px solid var(--md-surface-variant);
}

.muted {
  font-weight: 400;
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin-left: var(--md-spacing-sm);
}

.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--md-spacing-sm);
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.fu-count {
  font-weight: 600;
  color: var(--md-on-surface-variant);
}

.card--has-feedback .fu-count {
  color: #2e7d32;
}

.order-total {
  font-weight: 600;
  color: var(--md-on-surface);
}

.record-snippet {
  margin-top: var(--md-spacing-sm);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.record-line {
  font-size: 0.75rem;
  color: var(--md-on-surface-variant);
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: baseline;
}

.outcome-tag {
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 6px;
  font-weight: 500;
  background: rgba(255, 140, 0, 0.15);
  color: #e65100;
}

.rec-time {
  opacity: 0.85;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--md-spacing-md);
}

.modal-box {
  width: 100%;
  max-width: 420px;
  background: var(--md-surface);
  border-radius: var(--md-radius-md);
  box-shadow: var(--md-elevation-2);
}

.modal-wide {
  max-width: 480px;
}

.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--md-spacing-md);
  border-bottom: 1px solid var(--md-surface-variant);
}

.modal-head h2 {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 500;
}

.close-x {
  background: none;
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  color: var(--md-on-surface-variant);
}

.modal-body {
  padding: var(--md-spacing-md);
}

.modal-user {
  margin: 0 0 var(--md-spacing-md);
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.history-block {
  margin-bottom: var(--md-spacing-md);
  max-height: min(320px, 50vh);
  overflow-y: auto;
  padding: var(--md-spacing-sm);
  background: var(--md-surface-variant);
  border-radius: var(--md-radius-sm);
}

.history-title {
  font-size: var(--md-label-size);
  font-weight: 500;
  margin-bottom: var(--md-spacing-sm);
  color: var(--md-on-surface);
}

.history-row {
  font-size: 0.75rem;
  margin-bottom: 10px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.history-row:last-child {
  margin-bottom: 0;
}

.history-row-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: baseline;
}

.history-row-actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 2px;
}

.history-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--md-on-surface-variant);
  border-radius: var(--md-radius-sm);
  -webkit-tap-highlight-color: transparent;
}

.history-icon-btn:hover {
  background: rgba(0, 0, 0, 0.06);
  color: var(--md-primary);
}

.history-icon-btn--danger:hover {
  color: #c62828;
  background: rgba(198, 40, 40, 0.08);
}

.history-icon-svg {
  width: 18px;
  height: 18px;
  display: block;
}

.history-edit {
  width: 100%;
  padding-top: 4px;
}

.history-edit-label {
  display: block;
  font-size: 0.7rem;
  color: var(--md-on-surface-variant);
  margin-bottom: 4px;
}

.history-edit-field {
  margin-bottom: var(--md-spacing-sm);
}

.history-edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--md-spacing-sm);
  margin-top: var(--md-spacing-xs);
}

.btn-compact {
  padding: 6px 14px;
  font-size: var(--md-label-size);
}

.history-notes {
  flex: 1;
  min-width: 120px;
  color: var(--md-on-surface);
}

.by-admin {
  color: var(--md-on-surface-variant);
  font-size: 0.7rem;
}

.field-label {
  display: block;
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin-bottom: var(--md-spacing-xs);
}

.field-input,
.field-textarea {
  width: 100%;
  padding: var(--md-spacing-sm);
  border: 1px solid var(--md-surface-variant);
  border-radius: var(--md-radius-sm);
  font-size: var(--md-body-size);
  margin-bottom: var(--md-spacing-md);
  box-sizing: border-box;
}

.field-textarea {
  resize: vertical;
  font-family: inherit;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--md-spacing-sm);
  margin-top: var(--md-spacing-sm);
}

.btn-secondary {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  background: transparent;
  border: 1px solid var(--md-surface-variant);
  border-radius: var(--md-radius-md);
  cursor: pointer;
}

.btn-primary {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  background: var(--md-primary);
  color: #fff;
  border: none;
  border-radius: var(--md-radius-md);
  cursor: pointer;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Mobile / small screens */
@media (max-width: 767px) {
  .after-sales-page {
    /* Horizontal inset comes from Dashboard .content-area + #app safe-area */
    padding-left: 0;
    padding-right: 0;
    padding-bottom: max(8px, env(safe-area-inset-bottom, 0px));
  }

  .tabs {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    gap: 0;
    margin-bottom: var(--md-spacing-md);
    border-bottom: none;
    border-radius: var(--md-radius-md);
    overflow: hidden;
    border: 1px solid var(--md-surface-variant);
    width: 100%;
    min-width: 0;
  }

  .tab {
    min-height: 48px;
    min-width: 0;
    justify-content: center;
    text-align: center;
    padding: 12px 8px;
    font-size: 0.9375rem;
    border-radius: 0;
    -webkit-tap-highlight-color: transparent;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .tab + .tab {
    border-left: 1px solid var(--md-surface-variant);
  }

  .tab.active {
    background: rgba(255, 140, 0, 0.15);
  }

  .search-toolbar {
    flex-wrap: wrap;
    margin-bottom: var(--md-spacing-sm);
  }

  .search-input {
    min-height: 44px;
  }

  .filter-row--deal {
    gap: 0.5rem;
  }

  .deal-select {
    min-height: 44px;
  }

  .hint-block {
    padding: var(--md-spacing-sm);
    margin-bottom: var(--md-spacing-md);
  }

  .hint-main:not(.hint-main--single) {
    flex-direction: column;
    align-items: stretch;
    gap: 0.5rem;
  }

  .num-field {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    margin: 0;
  }

  .inline-num {
    width: 3.25rem;
    min-height: 44px;
    font-size: 16px; /* iOS: avoid zoom on focus */
  }

  .hint-text {
    flex: none;
    word-break: break-word;
    overflow-wrap: anywhere;
  }

  .hint-main--single {
    word-break: break-word;
    overflow-wrap: anywhere;
  }

  .card {
    padding: var(--md-spacing-sm);
  }

  .card--has-feedback {
    padding-left: calc(var(--md-spacing-sm) + 3px);
  }

  .card-title {
    word-break: break-word;
  }

  .card-meta span {
    display: inline-block;
    max-width: 100%;
  }

  .modal-overlay {
    align-items: flex-end;
    justify-content: center;
    padding: 0;
    padding-bottom: env(safe-area-inset-bottom, 0);
  }

  .modal-box {
    max-width: 100%;
    width: 100%;
    max-height: min(92vh, 92dvh);
    border-radius: var(--md-radius-lg, 12px) var(--md-radius-lg, 12px) 0 0;
    display: flex;
    flex-direction: column;
    margin: 0;
  }

  .modal-wide {
    max-width: 100%;
  }

  .modal-head {
    flex-shrink: 0;
    padding: var(--md-spacing-md);
    padding-top: max(var(--md-spacing-md), env(safe-area-inset-top, 0px));
  }

  .modal-head h2 {
    font-size: 1.0625rem;
    line-height: 1.35;
    padding-right: 8px;
  }

  .close-x {
    min-width: 44px;
    min-height: 44px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin: -8px -8px -8px 0;
  }

  .modal-body {
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
    padding: var(--md-spacing-md);
    padding-bottom: max(var(--md-spacing-md), env(safe-area-inset-bottom, 12px));
    flex: 1;
    min-height: 0;
  }

  .field-input,
  .field-textarea {
    font-size: 16px; /* iOS: avoid zoom on focus */
  }

  .modal-actions {
    flex-wrap: wrap;
    justify-content: stretch;
    gap: var(--md-spacing-sm);
    padding-top: var(--md-spacing-sm);
  }

  .modal-actions .btn-secondary,
  .modal-actions .btn-primary {
    flex: 1;
    min-height: 44px;
    -webkit-tap-highlight-color: transparent;
  }

  .history-block {
    max-height: min(42vh, 280px);
    -webkit-overflow-scrolling: touch;
  }

  .history-row {
    flex-direction: column;
    align-items: stretch;
    gap: 0;
  }

  .history-row-main {
    width: 100%;
  }

  .history-row-actions {
    align-self: flex-end;
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid rgba(0, 0, 0, 0.08);
    width: 100%;
    justify-content: flex-end;
  }

  .history-icon-btn {
    min-width: 44px;
    min-height: 44px;
    width: 44px;
    height: 44px;
  }

  .history-icon-svg {
    width: 20px;
    height: 20px;
  }

  .history-edit-actions {
    flex-direction: row;
    justify-content: stretch;
    gap: 10px;
    margin-top: var(--md-spacing-sm);
  }

  .history-edit-actions .btn-compact {
    flex: 1;
    min-height: 44px;
    padding-top: 10px;
    padding-bottom: 10px;
    -webkit-tap-highlight-color: transparent;
  }

  .history-edit .field-input,
  .history-edit .field-textarea {
    min-height: 44px;
  }

  .history-edit .field-textarea {
    min-height: 88px;
  }

  .history-notes {
    min-width: 0;
    word-break: break-word;
  }

  .deal-chips {
    gap: 8px;
  }

  .deal-chip {
    white-space: normal;
    line-height: 1.35;
    max-width: 100%;
  }
}

@media (max-width: 380px) {
  .tab {
    font-size: 0.8125rem;
    padding: 10px 6px;
  }
}
</style>
