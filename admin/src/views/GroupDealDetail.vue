<template>
  <div class="group-deal-detail-page">
    <div class="page-header">
      <button @click="goBack" class="back-btn">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        返回
      </button>
      
      <div class="header-actions">
        <button @click="exportSupplierOrder" class="export-btn" :disabled="loading || !groupDeal">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          导出供货单
        </button>
        <button @click="exportDeliveryOrder" class="export-btn" :disabled="loading || !groupDeal">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          导出配送单
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="!groupDeal" class="error">团购活动不存在</div>
    <div v-else>
      <!-- Group Deal Info -->
      <div class="deal-info-card">
        <div class="deal-header">
          <h2>{{ groupDeal.title }}</h2>
          <div class="status-control-group">
            <span :class="['status-badge', groupDeal.status]">
              {{ getStatusLabel(groupDeal.status) }}
            </span>
            <select 
              v-model="groupDeal.status" 
              @change="handleGroupDealStatusChange"
              :disabled="updatingGroupDealStatus"
              class="status-select"
            >
              <option value="upcoming">即将开始</option>
              <option value="active">进行中</option>
              <option value="closed">已截单</option>
              <option value="preparing">正在配货</option>
              <option value="ready_for_pickup">可以取货</option>
              <option value="completed">已完成</option>
            </select>
          </div>
        </div>
        
        <div v-if="groupDeal.description" class="deal-description">
          {{ groupDeal.description }}
        </div>
        
        <div class="deal-dates">
          <div class="date-item">
            <span class="date-label">下单时间:</span>
            <span class="date-value">
              {{ formatDateTime(groupDeal.order_start_date) }} - {{ formatDateTime(groupDeal.order_end_date) }}
            </span>
          </div>
          <div class="date-item">
            <span class="date-label">取货时间:</span>
            <span class="date-value">{{ formatDateTime(groupDeal.pickup_date) }}</span>
          </div>
        </div>
      </div>

      <!-- Orders List -->
      <div class="orders-section">
        <h3>订单列表 ({{ orders.length }})</h3>
        
        <div v-if="orders.length === 0" class="empty-state">
          <p>暂无订单</p>
        </div>
        <div v-else class="orders-list">
          <OrderCard
            v-for="order in orders"
            :key="order.id"
            :order="order"
            :show-delete="false"
            :show-actions="false"
            @click="viewOrderDetail(order)"
          />
        </div>
      </div>
      
      <!-- Order Detail Modal -->
      <OrderDetailModal
        :show="showOrderDetail"
        :order="selectedOrder"
        :available-products="availableProducts"
        :updating-order="updatingOrder"
        :marking-complete="markingComplete"
        :update-error="updateError"
        @close="closeOrderDetail"
        @update="handleUpdateOrder"
        @mark-paid="markOrderAsPaid"
        @mark-complete="markOrderComplete"
        @status-change="handleOrderStatusChange"
        @payment-method-change="handlePaymentMethodChange"
        @order-updated="handleOrderUpdated"
      @update-error="(msg) => { this.updateError = msg }"
      />
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'
import { formatDateTimeEST_CN } from '../utils/date'
import { useModal } from '../composables/useModal'
import OrderCard from '../components/OrderCard.vue'
import OrderDetailModal from '../components/OrderDetailModal.vue'

export default {
  name: 'GroupDealDetail',
  components: {
    OrderCard,
    OrderDetailModal
  },
  setup() {
    const { confirm, success, error: showError } = useModal()
    return { confirm, success, showError }
  },
  data() {
    return {
      loading: true,
      error: null,
      groupDeal: null,
      orders: [],
      showOrderDetail: false,
      selectedOrder: null,
      availableProducts: [],
      updatingOrder: false,
      updateError: null,
      markingComplete: false,
      updatingGroupDealStatus: false
    }
  },
  mounted() {
    this.fetchGroupDealDetail()
  },
  methods: {
    async fetchGroupDealDetail() {
      try {
        this.loading = true
        this.error = null
        const dealId = this.$route.params.id
        
        // Fetch group deal
        const dealResponse = await apiClient.get(`/admin/group-deals/${dealId}`)
        this.groupDeal = dealResponse.data.group_deal
        // Store previous status for change detection
        if (this.groupDeal) {
          this.groupDeal._previousStatus = this.groupDeal.status
        }
        // Store previous status for change detection
        if (this.groupDeal) {
          this.groupDeal._previousStatus = this.groupDeal.status
        }
        
        // Fetch orders for this group deal (excluding cancelled orders)
        const ordersResponse = await apiClient.get('/admin/orders', {
          params: {
            group_deal_id: dealId,
            per_page: 1000
          }
        })
        // Filter out cancelled orders
        this.orders = (ordersResponse.data.orders || []).filter(order => order.status !== 'cancelled')
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || error.message || 'Failed to load group deal'
        console.error('Failed to fetch group deal detail:', error)
      } finally {
        this.loading = false
      }
    },
    goBack() {
      this.$router.push('/group-deals')
    },
    async exportSupplierOrder() {
      try {
        const dealId = this.$route.params.id
        const token = localStorage.getItem('admin_auth_token')
        
        const response = await fetch(`${apiClient.defaults.baseURL}/admin/group-deals/${dealId}/export-orders-csv`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        if (!response.ok) {
          throw new Error('Export failed')
        }
        
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `group_deal_${dealId}_supplier_order.csv`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } catch (error) {
        await this.showError('导出供货单失败: ' + (error.message || 'Unknown error'))
        console.error('Export supplier order error:', error)
      }
    },
    async exportDeliveryOrder() {
      try {
        const dealId = this.$route.params.id
        const token = localStorage.getItem('admin_auth_token')
        
        const response = await fetch(`${apiClient.defaults.baseURL}/admin/group-deals/${dealId}/export-delivery-csv`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        if (!response.ok) {
          throw new Error('Export failed')
        }
        
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `group_deal_${dealId}_delivery_order.csv`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } catch (error) {
        await this.showError('导出配送单失败: ' + (error.message || 'Unknown error'))
        console.error('Export delivery order error:', error)
      }
    },
    async handleGroupDealStatusChange() {
      if (!this.groupDeal) return
      
      const newStatus = this.groupDeal.status
      const oldStatus = this.groupDeal._previousStatus || this.groupDeal.status
      
      // Don't update if status hasn't changed
      if (newStatus === oldStatus) {
        return
      }
      
      const statusText = this.getStatusLabel(newStatus)
      const confirmed = await this.confirm(`确认将团购状态改为 "${statusText}"?\n\n此操作将自动更新相关订单状态。`)
      if (!confirmed) {
        // Revert the status change
        this.groupDeal.status = oldStatus
        return
      }
      
      this.updatingGroupDealStatus = true
      try {
        const response = await apiClient.put(`/admin/group-deals/${this.groupDeal.id}/status`, { 
          status: newStatus 
        })
        
        // Update group deal with response data
        this.groupDeal = response.data.group_deal
        // Update previous status
        this.groupDeal._previousStatus = this.groupDeal.status
        
        // Refresh orders list to show updated order statuses
        await this.fetchGroupDealDetail()
        
        const ordersUpdated = response.data.orders_updated || 0
        if (ordersUpdated > 0) {
          await this.success(`团购状态已更新为: ${statusText}\n已更新 ${ordersUpdated} 个订单状态`)
        } else {
          await this.success(`团购状态已更新为: ${statusText}`)
        }
      } catch (error) {
        // Revert the status change on error
        this.groupDeal.status = oldStatus
        const errorMsg = error.response?.data?.message || error.response?.data?.error || '更新失败'
        await this.showError(`更新失败: ${errorMsg}`)
        console.error('Failed to update group deal status:', error)
      } finally {
        this.updatingGroupDealStatus = false
      }
    },
    getStatusLabel(status) {
      const labels = {
        'upcoming': '即将开始',
        'active': '进行中',
        'closed': '已截单',
        'preparing': '准备中',
        'ready_for_pickup': '可以取货',
        'completed': '已完成'
      }
      return labels[status] || status
    },
    getStatusText(status) {
      const labels = {
        'submitted': '已提交',
        'confirmed': '已确认',
        'preparing': '配货中',
        'ready_for_pickup': '可取货',
        'out_for_delivery': '配送中',
        'delivering': '配送中',
        'completed': '已完成',
        'cancelled': '已取消'
      }
      return labels[status] || status
    },
    getPaymentStatusText(status) {
      const labels = {
        'unpaid': '未付款',
        'paid': '已付款',
        'failed': '支付失败',
        'refunded': '已退款'
      }
      return labels[status] || status
    },
    formatDateTime(dateString) {
      return formatDateTimeEST_CN(dateString) || 'N/A'
    },
    formatAddress(address) {
      if (!address) return ''
      const parts = [
        address.address_line1,
        address.address_line2,
        address.city,
        address.postal_code
      ].filter(Boolean)
      return parts.join(', ')
    },
    async viewOrderDetail(order) {
      try {
        // Fetch full order details
        const response = await apiClient.get(`/admin/orders/${order.id}`)
        this.selectedOrder = response.data.order
        
        // Load available products from group deal
        await this.loadAvailableProducts()
        
        this.showOrderDetail = true
        this.updateError = null
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Failed to load order details'
        await this.error(`加载失败: ${errorMsg}`)
        console.error('Failed to load order details:', error)
      }
    },
    async loadAvailableProducts() {
      if (!this.selectedOrder?.group_deal_id) return
      
      try {
        const response = await apiClient.get(`/admin/group-deals/${this.selectedOrder.group_deal_id}`)
        this.availableProducts = response.data.group_deal?.products || []
      } catch (error) {
        console.error('Failed to load products:', error)
        this.availableProducts = []
      }
    },
    closeOrderDetail() {
      this.showOrderDetail = false
      this.selectedOrder = null
      this.availableProducts = []
      this.updateError = null
    },
    async handleUpdateOrder(orderId, updateData) {
      this.updatingOrder = true
      this.updateError = null
      
      try {
        const response = await apiClient.put(`/admin/orders/${orderId}/update`, updateData)
        
        // Update selected order with new data
        this.selectedOrder = response.data.order
        
        // Refresh orders list
        await this.fetchGroupDealDetail()
        
        await this.success('订单已更新')
      } catch (error) {
        this.updateError = error.response?.data?.message || error.response?.data?.error || '更新失败'
        await this.error(`更新失败: ${this.updateError}`)
        console.error('Failed to update order:', error)
      } finally {
        this.updatingOrder = false
      }
    },
    handleOrderUpdated(order) {
      // Refresh the selected order after update
      this.selectedOrder = order
      this.fetchGroupDealDetail()
    },
    async handleOrderStatusChange(orderId, newStatus) {
      if (!this.selectedOrder || !newStatus) {
        return
      }
      
      if (newStatus === this.selectedOrder.status) {
        return
      }
      
      const statusText = this.getStatusText(newStatus)
      const confirmed = await this.confirm(`确认将订单状态改为 "${statusText}"?`)
      if (!confirmed) {
        return
      }
      
      try {
        await apiClient.put(`/admin/orders/${orderId}/status`, { status: newStatus })
        
        // Refresh order details
        const response = await apiClient.get(`/admin/orders/${orderId}`)
        this.selectedOrder = response.data.order
        
        await this.success(`订单状态已更新为: ${statusText}`)
        await this.fetchGroupDealDetail()
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Failed to update status'
        await this.error(`更新失败: ${errorMsg}`)
        console.error('Failed to update order status:', error)
      }
    },
    async handlePaymentMethodChange(paymentMethod) {
      // Auto-mark as paid when cash is selected and order is unpaid
      // Don't trigger for cancelled or completed orders
      if (paymentMethod === 'cash' && 
          this.selectedOrder && 
          this.selectedOrder.payment_status === 'unpaid' &&
          this.selectedOrder.status !== 'cancelled' &&
          this.selectedOrder.status !== 'completed') {
        await this.markOrderAsPaid('cash')
      }
    },
    async markOrderAsPaid(paymentMethod = 'etransfer') {
      if (!this.selectedOrder || this.selectedOrder.payment_status === 'paid') {
        return
      }
      
      const amount = parseFloat(this.selectedOrder.total || 0).toFixed(2)
      const pointsToEarn = Math.floor(parseFloat(this.selectedOrder.total) * 100)
      
      const confirmed = await this.confirm(`确认标记订单 #${this.selectedOrder.order_number} 为已付款?\n\n金额: $${amount}\n将获得积分: ${pointsToEarn} 分\n\n支付后订单将自动完成。`)
      if (!confirmed) {
        return
      }
      
      try {
        const response = await apiClient.put(`/admin/orders/${this.selectedOrder.id}/payment`, { 
          payment_status: 'paid',
          payment_method: paymentMethod
        })
        
        // Update selected order with new data
        this.selectedOrder = response.data.order
        
        const pointsAwarded = response.data.points_awarded || 0
        await this.success(`订单已标记为已付款\n积分: ${pointsAwarded} 分已发放\n订单状态: 订单完成`)
        
        // Refresh orders list
        await this.fetchGroupDealDetail()
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Failed to update payment status'
        await this.error(`更新失败: ${errorMsg}`)
        console.error('Failed to mark as paid:', error)
      }
    },
    async markOrderComplete() {
      if (!this.selectedOrder || this.selectedOrder.status === 'completed') {
        return
      }
      
      const confirmed = await this.confirm(`确认标记订单 #${this.selectedOrder.order_number} 为已完成?`)
      if (!confirmed) {
        return
      }
      
      this.markingComplete = true
      try {
        await apiClient.put(`/admin/orders/${this.selectedOrder.id}/status`, { status: 'completed' })
        
        // Refresh order details
        const response = await apiClient.get(`/admin/orders/${this.selectedOrder.id}`)
        this.selectedOrder = response.data.order
        
        await this.success('订单已标记为已完成')
        await this.fetchGroupDealDetail()
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Failed to update status'
        await this.error(`更新失败: ${errorMsg}`)
        console.error('Failed to mark order complete:', error)
      } finally {
        this.markingComplete = false
      }
    }
  }
}
</script>

<style scoped>
.group-deal-detail-page {
  max-width: 1200px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--md-spacing-lg);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  background: rgba(0, 0, 0, 0.05);
  color: rgba(0, 0, 0, 0.87);
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.back-btn svg {
  width: 20px;
  height: 20px;
}

.back-btn:hover {
  background: rgba(0, 0, 0, 0.08);
  border-color: rgba(0, 0, 0, 0.2);
}

.header-actions {
  display: flex;
  gap: var(--md-spacing-md);
}

.export-btn {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  background: var(--md-primary);
  color: white;
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--md-elevation-2);
}

.export-btn svg {
  width: 20px;
  height: 20px;
}

.export-btn:hover:not(:disabled) {
  background: #FF7F00;
  box-shadow: var(--md-elevation-3);
  transform: translateY(-2px);
}

.export-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading, .error, .empty-state {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.deal-info-card {
  background: #FFFFFF;
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  margin-bottom: var(--md-spacing-lg);
}

.deal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--md-spacing-md);
}

.deal-header h2 {
  font-size: var(--md-headline-size);
  color: var(--md-on-surface);
  font-weight: 500;
  margin: 0;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: var(--md-radius-xl);
  font-size: var(--md-label-size);
  font-weight: 500;
}

.status-badge.upcoming {
  background: #E3F2FD;
  color: #1976D2;
}

.status-badge.active {
  background: #E8F5E9;
  color: #2E7D32;
}

.status-badge.closed {
  background: #FFF3E0;
  color: #F57C00;
}

.status-badge.preparing {
  background: #F3E5F5;
  color: #7B1FA2;
}

.status-badge.ready_for_pickup {
  background: #E8F5E9;
  color: #2E7D32;
}

.status-badge.completed {
  background: #F3E5F5;
  color: #7B1FA2;
}

.status-control-group {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
}

.status-select {
  padding: var(--md-spacing-xs) var(--md-spacing-sm);
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-sm);
  font-size: var(--md-label-size);
  background: var(--md-surface);
  color: var(--md-on-surface);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.status-select:focus {
  outline: none;
  border-color: var(--md-primary);
  border-width: 2px;
}

.status-select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.status-select:hover:not(:disabled) {
  border-color: var(--md-primary);
  background: rgba(255, 140, 0, 0.05);
}

.deal-description {
  color: var(--md-on-surface-variant);
  margin-bottom: var(--md-spacing-md);
  line-height: 1.5;
}

.deal-dates {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
  padding: var(--md-spacing-md);
  background: var(--md-surface-variant);
  border-radius: var(--md-radius-md);
}

.date-item {
  display: flex;
  gap: var(--md-spacing-sm);
}

.date-label {
  font-weight: 500;
  color: var(--md-on-surface-variant);
  min-width: 80px;
}

.date-value {
  color: var(--md-on-surface);
}

.orders-section {
  margin-top: var(--md-spacing-lg);
}

.orders-section h3 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-md);
}

.orders-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

</style>

