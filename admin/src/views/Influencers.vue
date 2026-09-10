<template>
  <div class="promo-page">
    <p class="page-description">
      在此指定或移除推荐官，管理其客户，并配置邀请奖励与商品收益。
    </p>

    <div class="tabs">
      <button type="button" :class="['tab', { active: tab === 'people' }]" @click="tab = 'people'">
        推荐官
        <span v-if="activeCount" class="tab-count">{{ activeCount }}</span>
      </button>
      <button type="button" :class="['tab', { active: tab === 'customers' }]" @click="tab = 'customers'">
        客户
        <span v-if="customerTabCount" class="tab-count">{{ customerTabCount }}</span>
      </button>
      <button type="button" :class="['tab', { active: tab === 'rates' }]" @click="tab = 'rates'">商品费率</button>
      <button type="button" :class="['tab', { active: tab === 'config' }]" @click="tab = 'config'">邀请奖励</button>
    </div>

    <div v-show="tab === 'people'">
      <div class="panel-card assign-card">
        <h2 class="panel-heading">指定推荐官</h2>
        <p class="hint">搜索用户并设为推荐官。移除后历史收益仍保留，账号不再以推荐官身份登录。</p>
        <div class="user-picker">
          <div class="user-picker__input-wrap">
            <input
              v-model.trim="assignQuery"
              type="text"
              class="form-input"
              placeholder="搜索手机号、昵称、微信号或用户 ID"
              autocomplete="off"
              @focus="onAssignFocus"
              @input="onAssignInput"
              @blur="onAssignBlur"
              @keydown.escape.prevent="assignOpen = false"
            />
            <div v-show="assignOpen && assignResults.length" class="user-picker__dropdown" role="listbox">
              <div v-for="u in assignResults" :key="u.id" class="user-picker__option-row">
                <div class="user-picker__option-info">
                  <span class="user-picker__opt-main">{{ u.nickname || '（无昵称）' }}</span>
                  <span class="user-picker__opt-sub">
                    {{ u.phone || u.wechat || u.email || '—' }} · ID {{ u.id }}
                  </span>
                </div>
                <span v-if="isActiveInfluencer(u.id)" class="chip">已是推荐官</span>
                <button
                  v-else
                  type="button"
                  class="btn-primary btn-sm"
                  :disabled="assigningId === u.id"
                  @mousedown.prevent="assignUser(u)"
                >
                  {{ assigningId === u.id ? '指定中…' : (isInactiveInfluencer(u.id) ? '重新启用' : '设为推荐官') }}
                </button>
              </div>
            </div>
          </div>
          <p v-if="assignSearchLoading" class="user-picker__hint">搜索中…</p>
          <p
            v-else-if="assignOpen && assignQuery.length && !assignResults.length"
            class="user-picker__hint"
          >
            无匹配用户
          </p>
        </div>
      </div>

      <div class="people-layout">
        <div class="panel-card people-list-card">
          <div class="panel-heading-row">
            <h2 class="panel-heading">推荐官列表</h2>
            <label class="checkbox-label compact">
              <input v-model="showInactive" type="checkbox" class="checkbox-input" />
              <span>显示已停用</span>
            </label>
          </div>
          <input
            v-model.trim="listQuery"
            type="text"
            class="form-input list-filter"
            placeholder="筛选姓名、手机号或邀请码"
          />
          <div v-if="listLoading" class="muted">加载中...</div>
          <p v-else-if="!visibleInfluencers.length" class="empty-hint">
            {{ influencers.length ? '没有匹配的推荐官' : '还没有推荐官。请在上方搜索用户并指定。' }}
          </p>
          <div v-else class="people-list">
            <div
              v-for="row in visibleInfluencers"
              :key="row.user_id"
              class="person-card"
              :class="{ active: selectedId === row.user_id, inactive: !row.is_active }"
            >
              <button type="button" class="person-main" @click="selectInfluencer(row.user_id)">
                <div class="person-avatar">{{ initial(row) }}</div>
                <div class="person-body">
                  <div class="person-top">
                    <strong>{{ displayName(row) }}</strong>
                    <span class="chip">{{ payoutLabel(row.payout_type) }}</span>
                    <span v-if="!row.is_active" class="chip chip--muted">已停用</span>
                  </div>
                  <div class="person-meta">
                    {{ row.phone || '—' }} · 码 {{ row.referral_code || '—' }}
                  </div>
                  <div class="person-stats">
                    <span>客户 {{ row.customer_count }}</span>
                    <span>代金券 ${{ money(row.credited) }}</span>
                    <span>待付 ${{ money(row.payable) }}</span>
                  </div>
                </div>
              </button>
              <div class="person-actions">
                <button
                  v-if="row.is_active"
                  type="button"
                  class="btn-danger btn-sm"
                  :disabled="removingId === row.user_id"
                  @click.stop="unassignUser(row)"
                >
                  {{ removingId === row.user_id ? '移除中…' : '移除' }}
                </button>
                <button
                  v-else
                  type="button"
                  class="btn-primary btn-sm"
                  :disabled="assigningId === row.user_id"
                  @click.stop="assignUser({ id: row.user_id, nickname: row.nickname })"
                >
                  {{ assigningId === row.user_id ? '启用中…' : '重新启用' }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="panel-card detail-card">
          <div v-if="detailLoading" class="muted">加载中...</div>
          <div v-else-if="!detail" class="empty-detail">
            <p class="empty-hint">选择左侧一位推荐官，查看客户、费率覆盖与待付现金。</p>
          </div>
          <div v-else class="detail">
            <div class="detail-header">
              <div>
                <h3 class="panel-heading">{{ displayName(detail) }}</h3>
                <p class="person-meta">
                  {{ detail.phone || '—' }} · 邀请码 {{ detail.referral_code || '—' }}
                </p>
              </div>
              <button
                v-if="detail.is_active"
                type="button"
                class="btn-danger"
                :disabled="removingId === detail.user_id"
                @click="unassignUser(detail)"
              >
                {{ removingId === detail.user_id ? '移除中…' : '移除推荐官' }}
              </button>
              <button
                v-else
                type="button"
                class="btn-primary"
                :disabled="assigningId === detail.user_id"
                @click="assignUser({ id: detail.user_id, nickname: detail.nickname })"
              >
                {{ assigningId === detail.user_id ? '启用中…' : '重新启用' }}
              </button>
            </div>

            <div class="form-row">
              <label>结算方式</label>
              <select v-model="detail.payout_type" class="form-input form-input--sm" @change="savePayout">
                <option value="credit">代金券</option>
                <option value="cash">现金</option>
              </select>
            </div>

            <h4 class="section-heading">专属费率覆盖</h4>
            <p class="hint">未覆盖的商品使用全局费率。覆盖只影响这位推荐官。</p>
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
            <p v-if="!(detail.overrides || []).length" class="empty-hint">暂无专属覆盖</p>
            <div v-else class="table-wrap">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>商品</th>
                    <th>方式</th>
                    <th>金额</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="ov in detail.overrides" :key="ov.product_id">
                    <td>{{ ov.product?.name || ov.product_id }}</td>
                    <td>{{ typeLabel(ov.commission_type) }}</td>
                    <td>${{ money(ov.amount) }}</td>
                    <td>
                      <button type="button" class="link-btn" @click="removeOverride(ov.product_id)">删除</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="section-heading-row">
              <h4 class="section-heading">客户</h4>
              <button type="button" class="btn-secondary" @click="openCustomersTab">管理客户</button>
            </div>
            <p class="hint">{{ (detail.customers || []).length }} 位客户。添加、改绑或移除请到「客户」页。</p>

            <h4 class="section-heading">待付现金</h4>
            <p v-if="!(detail.payable_entries || []).length" class="empty-hint">无待付记录</p>
            <div v-else>
              <div class="table-wrap">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>订单</th>
                      <th>金额</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="e in detail.payable_entries" :key="e.id">
                      <td>{{ e.order_id }}</td>
                      <td>${{ money(e.amount) }}</td>
                      <td>
                        <button type="button" class="btn-secondary btn-sm" @click="markPaid([e.id])">标记已付</button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <button
                v-if="detail.payable_entries.length > 1"
                type="button"
                class="btn-primary mark-all-btn"
                @click="markPaid(detail.payable_entries.map(e => e.id))"
              >
                全部标记已付
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-show="tab === 'customers'">
      <div class="panel-card">
        <div class="panel-heading-row">
          <h2 class="panel-heading">客户管理</h2>
          <select
            :value="selectedId == null ? '' : selectedId"
            class="form-input form-input--select"
            @change="onCustomerInfluencerChange"
          >
            <option value="">选择推荐官</option>
            <option v-for="row in influencers" :key="row.user_id" :value="row.user_id">
              {{ displayName(row) }}{{ row.is_active ? '' : '（已停用）' }} · {{ row.customer_count }} 位客户
            </option>
          </select>
        </div>
        <p class="hint">管理员手动绑定不发放邀请奖励。移除后历史收益保留，之后订单不再向该推荐官计提。</p>

        <template v-if="!selectedId">
          <p class="empty-hint">请先选择一位推荐官。</p>
        </template>
        <template v-else>
          <h3 class="section-heading">添加客户</h3>
          <div class="user-picker">
            <div class="user-picker__input-wrap">
              <input
                v-model.trim="customerAssignQuery"
                type="text"
                class="form-input"
                placeholder="搜索手机号、昵称、微信号或用户 ID"
                autocomplete="off"
                @focus="onCustomerAssignFocus"
                @input="onCustomerAssignInput"
                @blur="onCustomerAssignBlur"
                @keydown.escape.prevent="customerAssignOpen = false"
              />
              <div
                v-show="customerAssignOpen && customerAssignResults.length"
                class="user-picker__dropdown"
                role="listbox"
              >
                <div v-for="u in customerAssignResults" :key="u.id" class="user-picker__option-row">
                  <div class="user-picker__option-info">
                    <span class="user-picker__opt-main">{{ u.nickname || '（无昵称）' }}</span>
                    <span class="user-picker__opt-sub">
                      {{ u.phone || u.wechat || u.email || '—' }} · ID {{ u.id }}
                      <template v-if="u.referred_by_user_id">
                        · 已绑定 {{ u.referrer_display_name || ('用户' + u.referred_by_user_id) }}
                      </template>
                    </span>
                  </div>
                  <span v-if="u.id === selectedId" class="chip chip--muted">本人</span>
                  <span v-else-if="isCustomerOfSelected(u.id)" class="chip">已是客户</span>
                  <button
                    v-else
                    type="button"
                    class="btn-primary btn-sm"
                    :disabled="bindingCustomerId === u.id"
                    @mousedown.prevent="bindCustomer(u)"
                  >
                    {{ bindingCustomerId === u.id ? '处理中…' : (u.referred_by_user_id ? '改绑' : '添加') }}
                  </button>
                </div>
              </div>
            </div>
            <p v-if="customerAssignSearchLoading" class="user-picker__hint">搜索中…</p>
            <p
              v-else-if="customerAssignOpen && customerAssignQuery.length && !customerAssignResults.length"
              class="user-picker__hint"
            >
              无匹配用户
            </p>
          </div>

          <div class="panel-heading-row customer-list-head">
            <h3 class="section-heading">客户列表</h3>
            <input
              v-model.trim="customerListQuery"
              type="text"
              class="form-input list-filter list-filter--inline"
              placeholder="筛选姓名、手机号或微信号"
            />
          </div>
          <div v-if="detailLoading" class="muted">加载中...</div>
          <p v-else-if="!visibleCustomers.length" class="empty-hint">
            {{ (detail?.customers || []).length ? '没有匹配的客户' : '还没有客户。请在上方搜索用户并添加。' }}
          </p>
          <div v-else class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>客户</th>
                  <th>手机</th>
                  <th>微信</th>
                  <th>进行中</th>
                  <th>已结束</th>
                  <th>消费</th>
                  <th>收益</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="c in visibleCustomers" :key="c.id">
                  <td>
                    <div class="tx-user-line tx-user-line--name">{{ c.nickname || ('用户' + c.id) }}</div>
                    <div class="tx-user-line tx-user-line--id">ID {{ c.id }}</div>
                  </td>
                  <td>{{ c.phone || '—' }}</td>
                  <td>{{ c.wechat || '—' }}</td>
                  <td>{{ c.in_progress_order_count || 0 }}</td>
                  <td>{{ c.closed_order_count || 0 }}</td>
                  <td>${{ money(c.spend) }}</td>
                  <td>${{ money(c.commission) }}</td>
                  <td>
                    <button
                      type="button"
                      class="btn-danger btn-sm"
                      :disabled="unbindingCustomerId === c.id"
                      @click="unbindCustomer(c)"
                    >
                      {{ unbindingCustomerId === c.id ? '移除中…' : '移除' }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
      </div>
    </div>

    <div v-show="tab === 'rates'" class="panel-card">
      <div class="panel-heading-row">
        <h2 class="panel-heading">全局商品收益</h2>
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
      <p class="hint">所有推荐官默认使用此表。未设专属覆盖的推荐官按此费率计提。0 表示不计提。</p>
      <div v-if="ratesLoading" class="muted">加载中...</div>
      <p v-else-if="!rates.length" class="empty-hint">暂无商品</p>
      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>商品</th>
              <th>方式</th>
              <th>金额</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="rate in rates" :key="rate.product_id">
              <td>
                {{ rate.product_name }}
                <span v-if="!rate.is_active" class="muted">（下架）</span>
              </td>
              <td>
                <select v-model="rate.commission_type" class="form-input form-input--sm">
                  <option value="per_item">按件</option>
                  <option value="per_weight">按磅</option>
                </select>
              </td>
              <td>
                <input v-model.number="rate.amount" type="number" step="0.01" min="0" class="form-input form-input--sm" />
              </td>
              <td>
                <button type="button" class="btn-secondary btn-sm" @click="saveRate(rate)">保存</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-show="tab === 'config'" class="panel-card">
      <h2 class="panel-heading">客户绑定奖励</h2>
      <p class="hint">客户通过推荐官邀请码绑定时立即获得代金券。管理员手动改推荐人不发奖。</p>
      <div class="form-stack">
        <div class="form-row">
          <label>奖励金额（$）</label>
          <input v-model.number="configForm.lead_bonus_amount" type="number" step="0.01" min="0" class="form-input" />
        </div>
        <label class="checkbox-label">
          <input v-model="configForm.is_active" type="checkbox" class="checkbox-input" />
          <span>启用邀请奖励</span>
        </label>
        <div class="form-actions">
          <button type="button" class="btn-primary" :disabled="saving" @click="saveConfig">
            {{ saving ? '保存中…' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'
import { useModal } from '../composables/useModal'
import { formatOrderMoney2 } from '../utils/orderPricing'

export default {
  name: 'Influencers',
  setup() {
    const { success, confirm, error: showError } = useModal()
    return { success, confirm, showError }
  },
  data() {
    return {
      tab: 'people',
      saving: false,
      listLoading: false,
      ratesLoading: false,
      detailLoading: false,
      influencers: [],
      rates: [],
      configForm: { lead_bonus_amount: 5, is_active: true },
      selectedId: null,
      detail: null,
      overrideForm: { product_id: null, commission_type: 'per_item', amount: 0 },
      listQuery: '',
      showInactive: false,
      assignQuery: '',
      assignResults: [],
      assignOpen: false,
      assignSearchLoading: false,
      assignSearchTimer: null,
      assigningId: null,
      removingId: null,
      customerAssignQuery: '',
      customerAssignResults: [],
      customerAssignOpen: false,
      customerAssignSearchLoading: false,
      customerAssignSearchTimer: null,
      customerListQuery: '',
      bindingCustomerId: null,
      unbindingCustomerId: null
    }
  },
  computed: {
    activeCount() {
      return this.influencers.filter(row => row.is_active).length
    },
    customerTabCount() {
      if (this.detail && this.detail.user_id === this.selectedId) {
        return (this.detail.customers || []).length
      }
      const row = this.influencers.find(item => item.user_id === this.selectedId)
      return row ? row.customer_count : 0
    },
    visibleCustomers() {
      const rows = this.detail && this.detail.user_id === this.selectedId
        ? (this.detail.customers || [])
        : []
      const q = this.customerListQuery.toLowerCase()
      if (!q) return rows
      return rows.filter(c => {
        const hay = [c.nickname, c.phone, c.wechat, c.email, String(c.id)]
          .filter(Boolean)
          .join(' ')
          .toLowerCase()
        return hay.includes(q)
      })
    },
    visibleInfluencers() {
      const q = this.listQuery.toLowerCase()
      return this.influencers.filter(row => {
        if (!this.showInactive && !row.is_active) return false
        if (!q) return true
        const hay = [row.nickname, row.phone, row.referral_code, String(row.user_id)]
          .filter(Boolean)
          .join(' ')
          .toLowerCase()
        return hay.includes(q)
      })
    }
  },
  watch: {
    tab(val) {
      if (val === 'customers' && this.selectedId && this.detail?.user_id !== this.selectedId) {
        this.selectInfluencer(this.selectedId)
      }
    }
  },
  async mounted() {
    await Promise.all([this.loadList(), this.loadRates(), this.loadConfig()])
  },
  beforeUnmount() {
    if (this.assignSearchTimer) clearTimeout(this.assignSearchTimer)
    if (this.customerAssignSearchTimer) clearTimeout(this.customerAssignSearchTimer)
  },
  methods: {
    money(v) {
      if (v === null || v === undefined || Number.isNaN(Number(v))) return '0.00'
      return formatOrderMoney2(v)
    },
    displayName(row) {
      return row.nickname || row.phone || (`用户${row.user_id}`)
    },
    initial(row) {
      return String(this.displayName(row)).charAt(0)
    },
    payoutLabel(type) {
      return type === 'cash' ? '现金' : '代金券'
    },
    typeLabel(type) {
      return type === 'per_weight' ? '按磅' : '按件'
    },
    isActiveInfluencer(userId) {
      return this.influencers.some(row => row.user_id === userId && row.is_active)
    },
    isInactiveInfluencer(userId) {
      return this.influencers.some(row => row.user_id === userId && !row.is_active)
    },
    isCustomerOfSelected(userId) {
      return (this.detail?.customers || []).some(c => c.id === userId)
    },
    openCustomersTab() {
      this.tab = 'customers'
    },
    async onCustomerInfluencerChange(event) {
      const raw = event.target.value
      const nextId = raw === '' ? null : Number(raw)
      this.selectedId = Number.isNaN(nextId) ? null : nextId
      this.customerAssignQuery = ''
      this.customerAssignResults = []
      this.customerAssignOpen = false
      this.customerListQuery = ''
      if (this.selectedId) {
        await this.selectInfluencer(this.selectedId)
      } else {
        this.detail = null
      }
    },
    onCustomerAssignFocus() {
      if (this.customerAssignQuery.length) this.scheduleCustomerAssignSearch()
    },
    onCustomerAssignInput() {
      this.customerAssignOpen = true
      this.scheduleCustomerAssignSearch()
    },
    onCustomerAssignBlur() {
      setTimeout(() => {
        this.customerAssignOpen = false
      }, 180)
    },
    scheduleCustomerAssignSearch() {
      if (this.customerAssignSearchTimer) clearTimeout(this.customerAssignSearchTimer)
      const q = this.customerAssignQuery.trim()
      if (!q.length) {
        this.customerAssignResults = []
        this.customerAssignOpen = false
        return
      }
      this.customerAssignSearchTimer = setTimeout(() => this.runCustomerAssignSearch(q), 320)
    },
    async runCustomerAssignSearch(q) {
      this.customerAssignSearchLoading = true
      try {
        const r = await apiClient.get('/admin/users', {
          params: { search: q, page: 1, per_page: 30 }
        })
        this.customerAssignResults = r.data.users || []
        this.customerAssignOpen = true
      } catch (e) {
        this.customerAssignResults = []
        await this.showError(this.apiError(e, '搜索用户失败'))
      } finally {
        this.customerAssignSearchLoading = false
      }
    },
    async bindCustomer(user) {
      if (!this.selectedId || !user?.id) return
      if (user.id === this.selectedId) {
        await this.showError('不能将推荐官绑定为自己的客户')
        return
      }
      if (user.referred_by_user_id && user.referred_by_user_id !== this.selectedId) {
        const current = user.referrer_display_name || (`用户${user.referred_by_user_id}`)
        const ok = await this.confirm(
          `该用户已绑定「${current}」。确定改绑到当前推荐官？不会发放邀请奖励。`,
          { title: '改绑客户', confirmText: '改绑' }
        )
        if (!ok) return
      }
      this.bindingCustomerId = user.id
      try {
        await apiClient.post(`/admin/influencers/${this.selectedId}/customers`, {
          customer_user_id: user.id
        })
        this.customerAssignQuery = ''
        this.customerAssignResults = []
        this.customerAssignOpen = false
        await this.selectInfluencer(this.selectedId)
        await this.loadList()
        await this.success(`已将「${user.nickname || ('用户' + user.id)}」绑定为客户`)
      } catch (e) {
        await this.showError(this.apiError(e, '绑定客户失败'))
      } finally {
        this.bindingCustomerId = null
      }
    },
    async unbindCustomer(row) {
      if (!this.selectedId || !row?.id) return
      const name = row.nickname || (`用户${row.id}`)
      const ok = await this.confirm(
        `确定将「${name}」从该推荐官下移除？历史收益会保留，之后订单不再计提。`,
        { title: '移除客户', confirmText: '移除' }
      )
      if (!ok) return
      this.unbindingCustomerId = row.id
      try {
        await apiClient.delete(`/admin/influencers/${this.selectedId}/customers/${row.id}`)
        await this.selectInfluencer(this.selectedId)
        await this.loadList()
        await this.success(`已移除客户「${name}」`)
      } catch (e) {
        await this.showError(this.apiError(e, '移除客户失败'))
      } finally {
        this.unbindingCustomerId = null
      }
    },
    apiError(e, fallback) {
      return e.response?.data?.message || e.response?.data?.error || fallback
    },
    async loadList() {
      this.listLoading = true
      try {
        const res = await apiClient.get('/admin/influencers')
        this.influencers = res.data.influencers || []
      } catch (e) {
        await this.showError(this.apiError(e, '加载推荐官失败'))
      } finally {
        this.listLoading = false
      }
    },
    async loadRates() {
      this.ratesLoading = true
      try {
        const res = await apiClient.get('/admin/influencers/rates')
        this.rates = res.data.rates || []
      } catch (e) {
        await this.showError(this.apiError(e, '加载费率失败'))
      } finally {
        this.ratesLoading = false
      }
    },
    async loadConfig() {
      try {
        const res = await apiClient.get('/admin/influencers/config')
        const cfg = res.data.config || {}
        this.configForm = {
          lead_bonus_amount: cfg.lead_bonus_amount ?? 5,
          is_active: cfg.is_active !== false
        }
      } catch (e) {
        await this.showError(this.apiError(e, '加载邀请奖励失败'))
      }
    },
    onAssignFocus() {
      if (this.assignQuery.length) this.scheduleAssignSearch()
    },
    onAssignInput() {
      this.assignOpen = true
      this.scheduleAssignSearch()
    },
    onAssignBlur() {
      setTimeout(() => {
        this.assignOpen = false
      }, 180)
    },
    scheduleAssignSearch() {
      if (this.assignSearchTimer) clearTimeout(this.assignSearchTimer)
      const q = this.assignQuery.trim()
      if (!q.length) {
        this.assignResults = []
        this.assignOpen = false
        return
      }
      this.assignSearchTimer = setTimeout(() => this.runAssignSearch(q), 320)
    },
    async runAssignSearch(q) {
      this.assignSearchLoading = true
      try {
        const r = await apiClient.get('/admin/users', {
          params: { search: q, page: 1, per_page: 30 }
        })
        this.assignResults = r.data.users || []
        this.assignOpen = true
      } catch (e) {
        this.assignResults = []
        await this.showError(this.apiError(e, '搜索用户失败'))
      } finally {
        this.assignSearchLoading = false
      }
    },
    async assignUser(user) {
      if (!user?.id) return
      this.assigningId = user.id
      try {
        await apiClient.post('/admin/influencers', { user_id: user.id })
        this.assignQuery = ''
        this.assignResults = []
        this.assignOpen = false
        await this.loadList()
        await this.selectInfluencer(user.id)
        await this.success(`已将「${user.nickname || ('用户' + user.id)}」设为推荐官`)
      } catch (e) {
        await this.showError(this.apiError(e, '指定推荐官失败'))
      } finally {
        this.assigningId = null
      }
    },
    async unassignUser(row) {
      const name = this.displayName(row)
      const ok = await this.confirm(`确定移除「${name}」的推荐官身份？历史客户与收益记录会保留。`, {
        title: '移除推荐官',
        confirmText: '移除'
      })
      if (!ok) return
      this.removingId = row.user_id
      try {
        await apiClient.delete(`/admin/influencers/${row.user_id}`)
        if (this.selectedId === row.user_id) {
          this.selectedId = null
          this.detail = null
        }
        await this.loadList()
        await this.success(`已移除「${name}」的推荐官身份`)
      } catch (e) {
        await this.showError(this.apiError(e, '移除推荐官失败'))
      } finally {
        this.removingId = null
      }
    },
    async saveConfig() {
      this.saving = true
      try {
        await apiClient.put('/admin/influencers/config', this.configForm)
        await this.success('邀请奖励已保存')
      } catch (e) {
        await this.showError(this.apiError(e, '保存失败'))
      } finally {
        this.saving = false
      }
    },
    async saveRate(rate) {
      try {
        await apiClient.put('/admin/influencers/rates', {
          product_id: rate.product_id,
          commission_type: rate.commission_type,
          amount: rate.amount || 0
        })
        await this.success(`${rate.product_name} 费率已保存`)
      } catch (e) {
        await this.showError(this.apiError(e, '保存费率失败'))
      }
    },
    async saveAllRates() {
      this.saving = true
      try {
        for (const rate of this.rates) {
          await apiClient.put('/admin/influencers/rates', {
            product_id: rate.product_id,
            commission_type: rate.commission_type,
            amount: rate.amount || 0
          })
        }
        await this.success('全部费率已保存')
      } catch (e) {
        await this.showError(this.apiError(e, '保存费率失败'))
      } finally {
        this.saving = false
      }
    },
    async selectInfluencer(userId) {
      this.selectedId = userId
      this.detailLoading = true
      try {
        const res = await apiClient.get(`/admin/influencers/${userId}`)
        this.detail = res.data.influencer
      } catch (e) {
        this.detail = null
        await this.showError(this.apiError(e, '加载推荐官详情失败'))
      } finally {
        this.detailLoading = false
      }
    },
    async savePayout() {
      if (!this.detail) return
      try {
        await apiClient.patch(`/admin/influencers/${this.detail.user_id}`, {
          payout_type: this.detail.payout_type
        })
        await this.loadList()
        await this.success('结算方式已更新')
      } catch (e) {
        await this.showError(this.apiError(e, '更新结算方式失败'))
      }
    },
    async saveOverride() {
      if (!this.detail || !this.overrideForm.product_id) {
        await this.showError('请选择商品')
        return
      }
      try {
        await apiClient.put(`/admin/influencers/${this.detail.user_id}/overrides`, this.overrideForm)
        await this.selectInfluencer(this.detail.user_id)
        this.overrideForm = { product_id: null, commission_type: 'per_item', amount: 0 }
        await this.success('专属覆盖已保存')
      } catch (e) {
        await this.showError(this.apiError(e, '保存覆盖失败'))
      }
    },
    async removeOverride(productId) {
      try {
        await apiClient.delete(`/admin/influencers/${this.detail.user_id}/overrides/${productId}`)
        await this.selectInfluencer(this.detail.user_id)
      } catch (e) {
        await this.showError(this.apiError(e, '删除覆盖失败'))
      }
    },
    async markPaid(ids) {
      try {
        await apiClient.post('/admin/influencers/cash-payouts', { entry_ids: ids })
        await this.selectInfluencer(this.detail.user_id)
        await this.loadList()
        await this.success('已标记为已付')
      } catch (e) {
        await this.showError(this.apiError(e, '标记失败'))
      }
    }
  }
}
</script>

<style scoped>
.promo-page {
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
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

.tab:hover:not(.active) {
  color: var(--md-primary);
  background: rgba(255, 140, 0, 0.14);
}

.tab.active {
  color: var(--md-primary);
  border-bottom-color: var(--md-primary);
  background: rgba(255, 140, 0, 0.09);
}

.tab-count {
  min-width: 1.25rem;
  padding: 0 0.35rem;
  border-radius: 999px;
  background: rgba(255, 140, 0, 0.2);
  color: var(--md-primary);
  font-size: 0.75rem;
  font-weight: 600;
  line-height: 1.4;
}

.panel-card {
  background: var(--md-surface);
  border-radius: var(--md-radius-md);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
  margin-bottom: var(--md-spacing-lg);
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

.section-heading {
  margin: var(--md-spacing-lg) 0 var(--md-spacing-sm);
  font-size: 1rem;
}

.section-heading-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--md-spacing-md);
}

.section-heading-row .section-heading {
  margin: var(--md-spacing-lg) 0 var(--md-spacing-sm);
}

.hint,
.muted {
  color: var(--md-on-surface-variant);
  font-size: 0.85rem;
}

.empty-hint {
  margin: var(--md-spacing-md) 0 0;
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.form-stack {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
  max-width: 28rem;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin: var(--md-spacing-sm) 0;
  max-width: 16rem;
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
}

.form-input:focus {
  outline: none;
  border-color: var(--md-primary);
  box-shadow: 0 0 0 3px var(--overlay-primary, rgba(255, 140, 0, 0.15));
}

.form-input--sm {
  max-width: 8rem;
  width: auto;
}

.list-filter {
  margin-bottom: var(--md-spacing-md);
}

.list-filter--inline {
  margin: 0;
  max-width: 18rem;
}

.form-input--select {
  width: auto;
  min-width: 16rem;
  max-width: 28rem;
}

.customer-list-head {
  margin-top: var(--md-spacing-lg);
  align-items: flex-end;
}

.customer-list-head .section-heading {
  margin: 0;
}

.tx-user-line {
  line-height: 1.35;
}

.tx-user-line--name {
  font-weight: 600;
}

.tx-user-line--id {
  font-size: 11px;
  color: var(--md-on-surface-variant);
  margin-top: 2px;
}

.checkbox-label {
  display: inline-flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  cursor: pointer;
  font-weight: 500;
}

.checkbox-label.compact {
  margin: 0;
  font-size: var(--md-label-size);
}

.checkbox-input {
  width: 1.125rem;
  height: 1.125rem;
  accent-color: var(--md-primary);
}

.form-actions {
  display: flex;
  gap: var(--md-spacing-sm);
  padding-top: var(--md-spacing-sm);
}

.btn-primary,
.btn-secondary,
.btn-danger {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border-radius: var(--md-radius-sm);
  border: none;
  font-weight: 600;
  cursor: pointer;
  font-size: var(--md-label-size);
  font-family: inherit;
}

.btn-primary {
  background: var(--md-primary);
  color: #fff;
}

.btn-primary:disabled,
.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--md-surface);
  border: 1px solid var(--md-outline-variant, #cac4d0);
  color: var(--md-on-surface);
}

.btn-secondary:hover {
  background: var(--md-surface-variant);
}

.btn-danger {
  background: #fff;
  color: #c62828;
  border: 1px solid #ef9a9a;
}

.btn-danger:hover:not(:disabled) {
  background: #ffebee;
}

.btn-sm {
  padding: var(--md-spacing-xs) var(--md-spacing-md);
}

.user-picker {
  width: 100%;
  max-width: 36rem;
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
  max-height: 280px;
  overflow-y: auto;
  z-index: 20;
  background: var(--md-surface);
  border: 1px solid var(--md-outline-variant, #cac4d0);
  border-radius: var(--md-radius-sm);
  box-shadow: var(--md-elevation-2, 0 4px 12px rgba(0, 0, 0, 0.12));
}

.user-picker__option-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--md-spacing-md);
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border-bottom: 1px solid var(--md-outline-variant, #cac4d0);
}

.user-picker__option-row:last-child {
  border-bottom: none;
}

.user-picker__option-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.user-picker__opt-main {
  font-weight: 600;
}

.user-picker__opt-sub,
.user-picker__hint {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.user-picker__hint {
  margin: var(--md-spacing-xs) 0 0;
}

.people-layout {
  display: grid;
  grid-template-columns: minmax(280px, 1fr) minmax(320px, 1.2fr);
  gap: var(--md-spacing-lg);
  align-items: start;
}

.people-list-card,
.detail-card {
  margin-bottom: 0;
}

.people-list {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.person-card {
  display: flex;
  align-items: stretch;
  gap: 0.5rem;
  border: 1px solid var(--md-outline-variant, #cac4d0);
  background: var(--md-surface);
  border-radius: var(--md-radius-md);
  padding: var(--md-spacing-sm);
}

.person-card.active {
  border-color: var(--md-primary);
  background: rgba(255, 140, 0, 0.06);
}

.person-card.inactive {
  opacity: 0.72;
}

.person-main {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  flex: 1;
  min-width: 0;
  text-align: left;
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 0.25rem;
  font-family: inherit;
  color: inherit;
}

.person-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(255, 140, 0, 0.12);
  color: var(--md-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  flex-shrink: 0;
}

.person-body {
  min-width: 0;
}

.person-top {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.person-meta {
  font-size: 0.8rem;
  color: var(--md-on-surface-variant);
  margin-top: 0.2rem;
}

.person-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  margin-top: 0.4rem;
  font-size: 0.78rem;
  color: var(--md-on-surface-variant);
}

.person-actions {
  display: flex;
  align-items: center;
  padding: 0.25rem;
}

.chip {
  padding: 0.125rem 0.5rem;
  border-radius: var(--md-radius-sm);
  background: rgba(255, 140, 0, 0.2);
  color: var(--md-primary);
  font-size: var(--md-label-size);
  font-weight: 500;
}

.chip--muted {
  background: rgba(0, 0, 0, 0.08);
  color: var(--md-on-surface-variant);
}

.empty-detail {
  min-height: 12rem;
  display: flex;
  align-items: center;
}

.detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--md-spacing-md);
  flex-wrap: wrap;
}

.detail-header .panel-heading {
  margin-bottom: 0.25rem;
}

.override-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.table-wrap {
  overflow-x: auto;
  border-radius: var(--md-radius-sm);
  border: 1px solid var(--md-outline-variant, #cac4d0);
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
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.link-btn {
  border: none;
  background: none;
  color: var(--md-primary);
  cursor: pointer;
  font-weight: 600;
}

.mark-all-btn {
  margin-top: var(--md-spacing-md);
}

@media (max-width: 900px) {
  .people-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 767px) {
  .promo-page {
    max-width: none;
  }

  .tabs {
    flex-wrap: nowrap;
    overflow-x: auto;
  }

  .tab {
    flex-shrink: 0;
    min-height: 44px;
  }

  .user-picker {
    max-width: none;
  }

  .form-stack {
    max-width: none;
  }

  .form-input--sm {
    max-width: none;
    width: 100%;
  }

  .override-row .form-input,
  .override-row .btn-secondary {
    width: 100%;
  }

  .person-card {
    flex-direction: column;
  }

  .person-actions {
    justify-content: flex-end;
  }

  .data-table {
    min-width: 28rem;
  }

  .form-input--select,
  .list-filter--inline {
    max-width: none;
    width: 100%;
    min-width: 0;
  }

  .customer-list-head {
    align-items: stretch;
  }
}
</style>
