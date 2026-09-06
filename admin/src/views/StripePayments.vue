<template>
  <div class="stripe-payments-page">
    <div class="page-header-actions">
      <div class="filter-group">
        <select v-model="groupDealFilter" class="filter-select">
          <option value="">全部团购</option>
          <option v-for="deal in groupDeals" :key="deal.id" :value="String(deal.id)">
            {{ deal.title }}
          </option>
        </select>

        <select v-model="dealStatusFilter" class="filter-select">
          <option value="">全部团购状态</option>
          <option value="draft">草稿</option>
          <option value="upcoming">即将开始</option>
          <option value="active">进行中</option>
          <option value="closed">已截单</option>
          <option value="preparing">正在配货</option>
          <option value="ready_for_pickup">可以取货</option>
          <option value="completed">已完成</option>
        </select>

        <select v-model="stripeStatusFilter" class="filter-select">
          <option value="">全部收款状态</option>
          <option value="ready">待扣款</option>
          <option value="failed">扣款失败</option>
          <option value="no_card">未绑卡</option>
          <option value="paid">已付款</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <template v-else>
      <div class="summary-row">
        <button
          type="button"
          class="summary-chip"
          :class="{ active: stripeStatusFilter === '' }"
          @click="stripeStatusFilter = ''"
        >
          <span class="chip-label">银行卡订单</span>
          <span class="chip-value">{{ totals.card_orders }}</span>
        </button>
        <button
          type="button"
          class="summary-chip ready"
          :class="{ active: stripeStatusFilter === 'ready' }"
          @click="toggleStripeFilter('ready')"
        >
          <span class="chip-label">待扣款</span>
          <span class="chip-value">{{ totals.ready }}</span>
        </button>
        <button
          type="button"
          class="summary-chip failed"
          :class="{ active: stripeStatusFilter === 'failed' }"
          @click="toggleStripeFilter('failed')"
        >
          <span class="chip-label">扣款失败</span>
          <span class="chip-value">{{ totals.failed }}</span>
        </button>
        <button
          type="button"
          class="summary-chip no-card"
          :class="{ active: stripeStatusFilter === 'no_card' }"
          @click="toggleStripeFilter('no_card')"
        >
          <span class="chip-label">未绑卡</span>
          <span class="chip-value">{{ totals.no_card }}</span>
        </button>
        <button
          type="button"
          class="summary-chip paid"
          :class="{ active: stripeStatusFilter === 'paid' }"
          @click="toggleStripeFilter('paid')"
        >
          <span class="chip-label">已付款</span>
          <span class="chip-value">{{ totals.paid }}</span>
        </button>
        <div class="summary-chip amount">
          <span class="chip-label">待收</span>
          <span class="chip-value">${{ formatMoney(totals.amount_due_unpaid) }}</span>
        </div>
        <div class="summary-chip amount charged">
          <span class="chip-label">已扣</span>
          <span class="chip-value">${{ formatMoney(totals.amount_charged) }}</span>
        </div>
      </div>

      <div v-if="deals.length === 0" class="empty-state">
        <p>暂无符合条件的在线支付订单</p>
      </div>
      <div v-else class="deals-list">
        <div v-for="deal in deals" :key="deal.id" class="deal-card">
          <button type="button" class="deal-header" @click="toggleDeal(deal.id)">
            <div class="deal-title-section">
              <h3>{{ deal.title }}</h3>
              <span :class="['status-badge', deal.status]">{{ dealStatusLabel(deal.status) }}</span>
              <span v-if="deal.online_payment_enabled" class="status-badge online-payment">在线支付</span>
            </div>
            <div class="deal-meta">
              <span v-if="deal.pickup_date" class="pickup-date">取货 {{ formatDate(deal.pickup_date) }}</span>
              <span v-if="deal.amount_due_unpaid" class="due-hint">待收 ${{ formatMoney(deal.amount_due_unpaid) }}</span>
              <span class="expand-icon">{{ expandedDealIds.includes(deal.id) ? '收起' : '展开' }}</span>
            </div>
          </button>

          <div class="deal-chips">
            <span class="mini-chip ready">待扣 {{ deal.counts.ready }}</span>
            <span class="mini-chip failed">失败 {{ deal.counts.failed }}</span>
            <span class="mini-chip no-card">未绑 {{ deal.counts.no_card }}</span>
            <span class="mini-chip paid">已付 {{ deal.counts.paid }}</span>
          </div>

          <div v-if="expandedDealIds.includes(deal.id)" class="deal-orders">
            <div v-if="deal.orders.length === 0" class="empty-orders">
              已开通在线支付，暂无银行卡订单
            </div>
            <button
              v-for="order in deal.orders"
              :key="order.id"
              type="button"
              class="order-row"
              @click="viewOrderDetail(order)"
            >
              <div class="order-main">
                <span class="order-number">#{{ order.order_number }}</span>
                <span class="order-user">{{ customerLabel(order) }}</span>
                <span class="order-card">{{ cardLabel(order) }}</span>
              </div>
              <div class="order-side">
                <span :class="['stripe-badge', order.stripe_status]">{{ stripeStatusLabel(order.stripe_status) }}</span>
                <span class="order-amount">${{ formatMoney(order.amount_due) }}</span>
              </div>
              <p v-if="order.stripe_last_error && order.stripe_status === 'failed'" class="order-error">
                {{ order.stripe_last_error }}
              </p>
            </button>
          </div>
        </div>
      </div>
    </template>

    <OrderDetailModal
      ref="orderDetailModal"
      :show="showOrderDetail"
      :order="selectedOrder"
      :available-products="availableProducts"
      :updating-order="updatingOrder"
      :marking-complete="markingComplete"
      :update-error="updateError"
      @close="closeOrderDetail"
      @update="handleUpdateOrder"
      @mark-paid="markOrderAsPaid"
      @mark-unpaid="markOrderAsUnpaid"
      @mark-complete="markOrderComplete"
      @status-change="handleOrderStatusChange"
      @payment-method-change="handlePaymentMethodChange"
      @order-updated="handleOrderUpdated"
      @update-error="(msg) => { this.updateError = msg }"
      @products-loaded="(products) => { this.availableProducts = products }"
    />
  </div>
</template>

<script>
import apiClient from '../api/client'
import OrderDetailModal from '../components/OrderDetailModal.vue'
import { useModal } from '../composables/useModal'
import { formatDateEST_CN } from '../utils/date'
import { calculateOrderPoints } from '../utils/orderPoints'
import { formatOrderMoney2, orderAmountDueNumber, orderFinalTotalNumber } from '../utils/orderPricing'

const DEAL_STATUS_LABELS = {
  draft: '草稿',
  upcoming: '即将开始',
  active: '进行中',
  closed: '已截单',
  preparing: '正在配货',
  ready_for_pickup: '可以取货',
  completed: '已完成'
}

const ORDER_STATUS_LABELS = {
  submitted: '已提交订单',
  confirmed: '已确认订单',
  preparing: '正在配货',
  packing_complete: '配货完成',
  ready_for_pickup: '可以取货',
  out_for_delivery: '正在配送',
  delivering: '正在配送',
  completed: '订单完成',
  cancelled: '已取消'
}

const STRIPE_STATUS_LABELS = {
  paid: '已付款',
  ready: '待扣款',
  failed: '扣款失败',
  no_card: '未绑卡'
}

export default {
  name: 'StripePayments',
  components: { OrderDetailModal },
  setup() {
    const { confirm, success, error: showError } = useModal()
    return { confirm, success, showError }
  },
  data() {
    return {
      loading: true,
      error: null,
      groupDeals: [],
      deals: [],
      totals: {
        card_orders: 0,
        paid: 0,
        ready: 0,
        failed: 0,
        no_card: 0,
        amount_due_unpaid: 0,
        amount_charged: 0
      },
      groupDealFilter: '',
      dealStatusFilter: '',
      stripeStatusFilter: '',
      expandedDealIds: [],
      showOrderDetail: false,
      selectedOrder: null,
      availableProducts: [],
      updatingOrder: false,
      markingComplete: false,
      updateError: null
    }
  },
  watch: {
    groupDealFilter() {
      this.fetchPayments({ silent: true })
    },
    dealStatusFilter() {
      this.fetchPayments({ silent: true })
    },
    stripeStatusFilter() {
      this.fetchPayments({ silent: true })
    }
  },
  mounted() {
    this.fetchGroupDeals()
    this.fetchPayments()
  },
  methods: {
    formatMoney(value) {
      return formatOrderMoney2(value || 0)
    },
    formatDate(value) {
      return formatDateEST_CN(value)
    },
    dealStatusLabel(status) {
      return DEAL_STATUS_LABELS[status] || status
    },
    stripeStatusLabel(status) {
      return STRIPE_STATUS_LABELS[status] || status
    },
    customerLabel(order) {
      const user = order.user || {}
      return user.nickname || user.wechat || user.phone || '客户'
    },
    cardLabel(order) {
      if (!order.stripe_card_last4) return '未绑卡'
      const brand = order.stripe_card_brand
        ? order.stripe_card_brand.charAt(0).toUpperCase() + order.stripe_card_brand.slice(1)
        : '卡'
      return `${brand} •••• ${order.stripe_card_last4}`
    },
    toggleStripeFilter(status) {
      this.stripeStatusFilter = this.stripeStatusFilter === status ? '' : status
    },
    toggleDeal(dealId) {
      if (this.expandedDealIds.includes(dealId)) {
        this.expandedDealIds = this.expandedDealIds.filter((id) => id !== dealId)
      } else {
        this.expandedDealIds = [...this.expandedDealIds, dealId]
      }
    },
    defaultExpandedIds(deals) {
      const attention = deals.filter((deal) => (deal.counts.failed || 0) > 0 || (deal.counts.ready || 0) > 0)
      if (attention.length) return attention.map((deal) => deal.id)
      return deals.slice(0, 1).map((deal) => deal.id)
    },
    async fetchGroupDeals() {
      try {
        const response = await apiClient.get('/admin/group-deals')
        this.groupDeals = response.data.group_deals || []
      } catch (error) {
        console.error('Failed to fetch group deals:', error)
      }
    },
    async fetchPayments({ silent = false } = {}) {
      try {
        if (!silent) this.loading = true
        this.error = null
        const params = {}
        if (this.groupDealFilter) params.group_deal_id = this.groupDealFilter
        if (this.dealStatusFilter) params.deal_status = this.dealStatusFilter
        if (this.stripeStatusFilter) params.stripe_status = this.stripeStatusFilter
        const response = await apiClient.get('/admin/stripe-payments', { params })
        this.totals = response.data.totals || this.totals
        this.deals = response.data.deals || []
        const keepOpen = this.expandedDealIds.filter((id) => this.deals.some((deal) => deal.id === id))
        this.expandedDealIds = keepOpen.length ? keepOpen : this.defaultExpandedIds(this.deals)
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || error.message || '加载失败'
        console.error('Failed to fetch Stripe payments:', error)
      } finally {
        this.loading = false
      }
    },
    async viewOrderDetail(order) {
      try {
        const response = await apiClient.get(`/admin/orders/${order.id}`)
        this.selectedOrder = response.data.order
        this.showOrderDetail = true
        this.updateError = null
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Failed to load order details'
        await this.showError(`加载失败: ${errorMsg}`)
      }
    },
    closeOrderDetail() {
      this.showOrderDetail = false
      this.selectedOrder = null
      this.availableProducts = []
      this.updateError = null
    },
    applyUpdatedOrder(updatedOrder) {
      if (this.selectedOrder && this.selectedOrder.id === updatedOrder.id) {
        this.selectedOrder = updatedOrder
      }
      this.fetchPayments({ silent: true })
    },
    async handleUpdateOrder(orderId, updateData) {
      this.updatingOrder = true
      this.updateError = null
      try {
        const response = await apiClient.put(`/admin/orders/${orderId}/update`, updateData)
        this.applyUpdatedOrder(response.data.order)
        await this.success('订单已更新')
      } catch (error) {
        this.updateError = error.response?.data?.message || error.response?.data?.error || '更新失败'
        await this.showError(`更新失败: ${this.updateError}`)
      } finally {
        this.updatingOrder = false
      }
    },
    handleOrderUpdated(order) {
      if (order) this.applyUpdatedOrder(order)
    },
    async handlePaymentMethodChange(paymentMethod) {
      if (
        paymentMethod === 'cash' &&
        this.selectedOrder &&
        this.selectedOrder.payment_status === 'unpaid' &&
        this.selectedOrder.status !== 'cancelled' &&
        this.selectedOrder.status !== 'completed'
      ) {
        try {
          const response = await apiClient.put(`/admin/orders/${this.selectedOrder.id}/payment`, {
            payment_status: 'paid',
            payment_method: 'cash'
          })
          this.applyUpdatedOrder(response.data.order)
          await this.success('订单已自动标记为已付款（现金）')
        } catch (error) {
          const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Failed to update payment status'
          await this.showError(`更新失败: ${errorMsg}`)
        }
      }
    },
    async handleOrderStatusChange(orderId, newStatus) {
      if (!this.selectedOrder || !newStatus || newStatus === this.selectedOrder.status) return
      const statusText = ORDER_STATUS_LABELS[newStatus] || newStatus
      const confirmed = await this.confirm(`确认将订单状态改为 "${statusText}"?`)
      if (!confirmed) return
      try {
        const response = await apiClient.put(`/admin/orders/${orderId}/status`, { status: newStatus })
        this.applyUpdatedOrder(response.data.order)
        await this.success(`订单状态已更新为: ${statusText}`)
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Failed to update status'
        await this.showError(`更新失败: ${errorMsg}`)
      }
    },
    async markOrderAsPaid(data) {
      const orderToMark = this.selectedOrder
      const paymentMethod = data?.paymentMethod || orderToMark?.payment_method || 'card'
      if (!orderToMark || orderToMark.payment_status === 'paid') return
      const amount = formatOrderMoney2(orderAmountDueNumber(orderToMark))
      const pointsToEarn = calculateOrderPoints(orderToMark)
      const confirmed = await this.confirm(
        `确认标记订单 #${orderToMark.order_number} 为已付款?\n\n应付金额: $${amount}\n将获得积分: ${pointsToEarn} 分\n\n支付后订单将自动完成。`
      )
      if (!confirmed) return
      try {
        const response = await apiClient.put(`/admin/orders/${orderToMark.id}/payment`, {
          payment_status: 'paid',
          payment_method: paymentMethod
        })
        this.applyUpdatedOrder(response.data.order)
        await this.success('订单已标记为已付款')
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Failed to update payment status'
        await this.showError(`更新失败: ${errorMsg}`)
      }
    },
    async markOrderAsUnpaid() {
      const orderToMark = this.selectedOrder
      if (!orderToMark || orderToMark.payment_status !== 'paid') return
      const amount = formatOrderMoney2(orderFinalTotalNumber(orderToMark))
      const confirmed = await this.confirm(
        `确认标记订单 #${orderToMark.order_number} 为未付款?\n\n金额: $${amount}\n\n此操作将撤销已发放的积分。`
      )
      if (!confirmed) return
      try {
        const response = await apiClient.put(`/admin/orders/${orderToMark.id}/payment`, {
          payment_status: 'unpaid'
        })
        this.applyUpdatedOrder(response.data.order)
        await this.success('订单已标记为未付款')
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Failed to update payment status'
        await this.showError(`更新失败: ${errorMsg}`)
      }
    },
    async markOrderComplete() {
      if (!this.selectedOrder || this.selectedOrder.status === 'completed') return
      let confirmMsg = `确认标记订单 #${this.selectedOrder.order_number} 为已完成?`
      if (this.selectedOrder.payment_status === 'unpaid') {
        const pts = calculateOrderPoints(this.selectedOrder)
        confirmMsg += `\n\n注意：订单仍为「未付款」，不会发放积分（预计 ${pts} 分）。`
      }
      const confirmed = await this.confirm(confirmMsg, { type: 'warning' })
      if (!confirmed) return
      this.markingComplete = true
      try {
        const response = await apiClient.put(`/admin/orders/${this.selectedOrder.id}/status`, { status: 'completed' })
        this.applyUpdatedOrder(response.data.order)
        await this.success('订单已标记为已完成')
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Failed to update status'
        await this.showError(`更新失败: ${errorMsg}`)
      } finally {
        this.markingComplete = false
      }
    }
  }
}
</script>

<style scoped>
.stripe-payments-page {
  max-width: 1100px;
}

.page-header-actions {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--md-spacing-lg);
  gap: var(--md-spacing-md);
}

.filter-group {
  display: flex;
  gap: var(--md-spacing-md);
  flex-wrap: wrap;
}

.filter-select {
  padding: 10px 12px;
  border: none;
  border-bottom: 2px solid transparent;
  border-radius: 4px 4px 0 0;
  font-size: var(--md-body-size);
  background: var(--md-surface-variant);
  color: var(--md-on-surface);
  cursor: pointer;
  min-width: 160px;
}

.filter-select:focus {
  outline: none;
  background: #EBEBEB;
  border-bottom-color: var(--md-primary);
}

.loading,
.error,
.empty-state {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.error {
  color: #C62828;
}

.summary-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: var(--md-spacing-lg);
  padding: 12px;
  background: #FFFFFF;
  border-radius: var(--md-radius-md);
  box-shadow: var(--md-elevation-1);
}

.summary-chip {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  min-width: 88px;
  padding: 8px 16px;
  border: none;
  border-radius: var(--md-radius-sm);
  background: var(--md-surface-variant);
  color: var(--md-on-surface);
  cursor: pointer;
  text-align: left;
  transition: var(--transition-fast);
}

.summary-chip:hover {
  background: #EBEBEB;
}

.summary-chip.amount {
  cursor: default;
  background: transparent;
  margin-left: 4px;
}

.summary-chip.amount:hover {
  background: transparent;
}

.summary-chip.active {
  background: var(--overlay-primary);
}

.chip-label {
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.02em;
  color: var(--md-on-surface-variant);
}

.summary-chip.active .chip-label,
.summary-chip.active .chip-value {
  color: #E65100;
}

.chip-value {
  font-size: 1.125rem;
  font-weight: 500;
}

.summary-chip.amount .chip-value {
  color: var(--md-on-surface);
}

.deals-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.deal-card {
  background: #FFFFFF;
  border: none;
  border-radius: var(--md-radius-md);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
}

.deal-header {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--md-spacing-md);
  margin-bottom: var(--md-spacing-md);
  background: none;
  border: 0;
  padding: 0;
  cursor: pointer;
  text-align: left;
}

.deal-title-section {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--md-spacing-md);
}

.deal-title-section h3 {
  margin: 0;
  font-size: var(--md-headline-size);
  font-weight: 500;
  color: var(--md-on-surface);
}

.deal-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--md-spacing-sm);
  color: var(--md-on-surface-variant);
  font-size: var(--md-label-size);
  flex-shrink: 0;
}

.due-hint {
  color: #E65100;
  font-weight: 500;
}

.expand-icon {
  color: var(--md-primary);
  font-weight: 500;
}

.status-badge {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
  font-size: var(--md-label-size);
  font-weight: 500;
}

.status-badge.draft { background: #F5F5F5; color: #757575; }
.status-badge.upcoming { background: #E3F2FD; color: #1976D2; }
.status-badge.active { background: #E8F5E9; color: #2E7D32; }
.status-badge.closed { background: #FFF3E0; color: #F57C00; }
.status-badge.preparing { background: #F3E5F5; color: #7B1FA2; }
.status-badge.ready_for_pickup { background: #E8F5E9; color: #2E7D32; }
.status-badge.completed { background: #F3E5F5; color: #7B1FA2; }
.status-badge.online-payment {
  background: rgba(255, 140, 0, 0.12);
  color: #E65100;
}

.deal-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.mini-chip,
.stripe-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border: none;
  border-radius: var(--md-radius-sm);
  font-size: 0.75rem;
  font-weight: 500;
  background: var(--md-surface-variant);
  color: var(--md-on-surface-variant);
}

.mini-chip.ready,
.stripe-badge.ready {
  background: var(--overlay-primary);
  color: #E65100;
}

.mini-chip.failed,
.stripe-badge.failed {
  background: var(--overlay-accent);
  color: #C62828;
}

.mini-chip.paid,
.stripe-badge.paid {
  background: #E8F5E9;
  color: #1B5E20;
}

.deal-orders {
  margin-top: var(--md-spacing-md);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.empty-orders {
  padding: var(--md-spacing-md);
  color: var(--md-on-surface-variant);
  background: var(--md-surface-variant);
  border-radius: var(--md-radius-sm);
}

.order-row {
  width: 100%;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border: none;
  border-radius: var(--md-radius-sm);
  background: var(--md-surface-variant);
  cursor: pointer;
  text-align: left;
  transition: var(--transition-fast);
}

.order-row:hover {
  background: var(--overlay-primary);
}

.order-main,
.order-side {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.order-number {
  font-weight: 600;
  color: var(--md-on-surface);
}

.order-user,
.order-card {
  color: var(--md-on-surface-variant);
  font-size: var(--md-label-size);
}

.order-amount {
  font-weight: 600;
  color: var(--md-on-surface);
}

.order-error {
  width: 100%;
  margin: 0;
  color: #C62828;
  font-size: var(--md-label-size);
}

@media (max-width: 767px) {
  .deal-header {
    flex-direction: column;
  }

  .deal-title-section h3 {
    font-size: var(--md-title-size);
  }

  .filter-select {
    min-width: 100%;
  }

  .order-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
