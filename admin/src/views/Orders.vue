<template>
  <div class="orders-page">
    <div class="page-header-actions">
      <div class="search-group">
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="搜索订单号或电话号码..."
          class="search-input"
          @keyup.enter="handleSearch" />
        <button @click="handleSearch" class="search-btn">搜索</button>
        <button v-if="searchQuery" @click="clearSearch" class="clear-btn">清除</button>
        <button @click="openQRScanner" class="qr-scanner-btn">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="width: 20px; height: 20px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
          </svg>
          扫描取货码
        </button>
      </div>
      
      <div class="filter-group">
        <select v-model="groupDealFilter" class="filter-select">
          <option value="">全部团购</option>
          <option v-for="deal in groupDeals" :key="deal.id" :value="deal.id">
            {{ deal.title }}
          </option>
        </select>
        
        <select v-model="statusFilter" class="filter-select">
          <option value="">全部状态</option>
          <option value="submitted">已提交订单</option>
          <option value="confirmed">已确认订单</option>
          <option value="preparing">正在配货</option>
          <option value="ready_for_pickup">可以取货</option>
          <option value="delivering">正在配送</option>
          <option value="completed">订单完成</option>
          <option value="cancelled">已取消</option>
        </select>
        
        <select v-model="paymentFilter" class="filter-select">
          <option value="">全部支付状态</option>
          <option value="unpaid">未付款</option>
          <option value="paid">已付款</option>
        </select>
        
        <select v-model="paymentMethodFilter" class="filter-select">
          <option value="">全部支付方式</option>
          <option value="cash">现金</option>
          <option value="etransfer">电子转账</option>
        </select>
        
        <select v-model="deliveryMethodFilter" class="filter-select">
          <option value="">全部配送方式</option>
          <option value="pickup">自取</option>
          <option value="delivery">配送</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="orders.length === 0" class="empty-state">
      <p>暂无订单</p>
    </div>
    <div v-else class="orders-list">
      <OrderCard
        v-for="order in orders"
        :key="order.id"
        :order="order"
        :show-delete="true"
        :show-actions="true"
        @click="viewOrderDetail(order)"
        @delete="deleteOrder"
        @update-payment="updatePaymentStatus"
        @mark-shipped="markAsShipped"
        @update-status="updateOrderStatus"
        @cancel="cancelOrder"
      />
    </div>
    
    <!-- Pagination -->
    <div v-if="pagination && pagination.pages > 1" class="pagination">
      <button 
        @click="goToPage(pagination.page - 1)" 
        :disabled="pagination.page <= 1"
        class="page-btn">
        上一页
      </button>
      <span class="page-info">第 {{ pagination.page }} / {{ pagination.pages }} 页</span>
      <button 
        @click="goToPage(pagination.page + 1)" 
        :disabled="pagination.page >= pagination.pages"
        class="page-btn">
        下一页
      </button>
    </div>

    <!-- QR Scanner Modal -->
    <div v-if="showQRScanner" class="modal-overlay" @click="closeQRScanner">
      <div class="modal-content qr-scanner-modal" @click.stop>
        <div class="modal-header">
          <h2>扫描取货码</h2>
          <button @click="closeQRScanner" class="close-btn">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div id="qr-reader" style="width: 100%;"></div>
          <div v-if="scanError" class="error-message">{{ scanError }}</div>
        </div>
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
</template>

<script>
import apiClient from '../api/client'
import { useModal } from '../composables/useModal'
import { Html5Qrcode } from 'html5-qrcode'
import { formatDateEST_CN } from '../utils/date'
import OrderCard from '../components/OrderCard.vue'
import OrderDetailModal from '../components/OrderDetailModal.vue'

export default {
  name: 'Orders',
  components: {
    OrderCard,
    OrderDetailModal
  },
  setup() {
    const { confirm, success, error } = useModal()
    return { confirm, success, error }
  },
  data() {
    return {
      loading: true,
      error: null,
      orders: [],
      groupDeals: [],
      pagination: null,
      searchQuery: '',
      groupDealFilter: '',
      statusFilter: '',
      paymentFilter: '',
      paymentMethodFilter: '',
      deliveryMethodFilter: '',
      currentPage: 1,
      showQRScanner: false,
      qrScanner: null,
      scanError: null,
      showOrderDetail: false,
      selectedOrder: null,
      availableProducts: [],
      updatingOrder: false,
      updateError: null,
      markingComplete: false
    }
  },
  watch: {
    groupDealFilter() {
      this.currentPage = 1
      this.fetchOrders()
    },
    statusFilter() {
      this.currentPage = 1
      this.fetchOrders()
    },
    paymentFilter() {
      this.currentPage = 1
      this.fetchOrders()
    },
    paymentMethodFilter() {
      this.currentPage = 1
      this.fetchOrders()
    },
    deliveryMethodFilter() {
      this.currentPage = 1
      this.fetchOrders()
    }
  },
  mounted() {
    // Check for query params (from "查看订单" button)
    const groupDealId = this.$route.query.group_deal_id
    if (groupDealId) {
      this.groupDealFilter = groupDealId
    }
    
    this.fetchGroupDeals()
    this.fetchOrders()
  },
  methods: {
    async fetchGroupDeals() {
      try {
        const response = await apiClient.get('/admin/group-deals', {
          params: { per_page: 1000 }
        })
        this.groupDeals = response.data.group_deals || []
      } catch (error) {
        console.error('Failed to fetch group deals:', error)
      }
    },
    
    async fetchOrders() {
      try {
        this.loading = true
        this.error = null
        
        // Build query params
        const params = {
          page: this.currentPage,
          per_page: 50
        }
        if (this.searchQuery) {
          params.search = this.searchQuery
        }
        if (this.groupDealFilter) {
          params.group_deal_id = this.groupDealFilter
        }
        if (this.statusFilter) {
          params.status = this.statusFilter
        }
        if (this.paymentFilter) {
          params.payment_status = this.paymentFilter
        }
        if (this.paymentMethodFilter) {
          params.payment_method = this.paymentMethodFilter
        }
        if (this.deliveryMethodFilter) {
          params.delivery_method = this.deliveryMethodFilter
        }
        
        const response = await apiClient.get('/admin/orders', { params })
        this.orders = response.data.orders || []
        this.pagination = response.data.pagination
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || 'Failed to load orders'
        console.error('Failed to fetch orders:', error)
      } finally {
        this.loading = false
      }
    },
    
    handleSearch() {
      this.currentPage = 1
      this.fetchOrders()
    },
    
    clearSearch() {
      this.searchQuery = ''
      this.currentPage = 1
      this.fetchOrders()
    },
    
    goToPage(page) {
      if (page >= 1 && page <= this.pagination.pages) {
        this.currentPage = page
        this.fetchOrders()
      }
    },
    
    async viewOrder(order) {
      // Navigate to order detail or show modal
      const items = order.items_count || 0
      await this.confirm(`订单详情\n\n订单号: ${order.order_number}\n用户: ${order.user?.nickname || order.user?.phone}\n总金额: $${order.total}\n订单状态: ${this.getStatusText(order.status)}\n支付状态: ${this.getPaymentStatusText(order.payment_status)}\n商品数量: ${items} 件`, {
        type: 'info',
        title: '订单详情',
        showCancel: false
      })
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
        await this.fetchOrders()
        
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
      // Refresh the selected order after update from modal
      if (order) {
        this.selectedOrder = order
      }
      this.fetchOrders()
    },
    async openQRScanner() {
      this.showQRScanner = true
      this.scanError = null
      
      await this.$nextTick()
      
      try {
        this.qrScanner = new Html5Qrcode("qr-reader")
        await this.qrScanner.start(
          { facingMode: "environment" },
          {
            fps: 10,
            qrbox: { width: 250, height: 250 }
          },
          (decodedText) => {
            // QR code scanned successfully
            this.handleQRScan(decodedText)
          },
          (errorMessage) => {
            // Ignore scanning errors
          }
        )
      } catch (error) {
        this.scanError = '无法启动摄像头，请检查权限设置'
        console.error('Failed to start QR scanner:', error)
      }
    },
    closeQRScanner() {
      if (this.qrScanner) {
        this.qrScanner.stop().then(() => {
          this.qrScanner = null
        }).catch(() => {
          this.qrScanner = null
        })
      }
      this.showQRScanner = false
      this.scanError = null
    },
    async handleQRScan(pickupCode) {
      // Stop scanner
      if (this.qrScanner) {
        await this.qrScanner.stop()
        this.qrScanner = null
      }
      
      this.showQRScanner = false
      
      try {
        // Fetch order by pickup code
        const response = await apiClient.get(`/admin/orders/by-pickup-code/${pickupCode}`)
        const order = response.data.order
        
        // Show order detail
        this.selectedOrder = order
        
        // Auto-mark as paid if payment method is cash and order is unpaid
        const existingPaymentMethod = this.selectedOrder.payment_method || ''
        if (existingPaymentMethod === 'cash' && this.selectedOrder.payment_status === 'unpaid') {
          // Use nextTick to ensure the order is fully loaded before auto-marking
          await this.$nextTick()
          await this.autoMarkAsPaid()
        }
        
        // Load available products
        await this.loadAvailableProducts()
        
        this.showOrderDetail = true
        this.updateError = null
        
        await this.success(`已找到订单: ${order.order_number}`)
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || '订单未找到'
        await this.error(`扫描失败: ${errorMsg}`)
        console.error('Failed to fetch order by pickup code:', error)
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
        await this.autoMarkAsPaid()
      }
    },
    
    async handleOrderStatusChange(orderId, newStatus) {
      if (!this.selectedOrder || !newStatus) {
        return
      }
      
      // Don't update if status hasn't actually changed
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
        await this.fetchOrders()
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Failed to update status'
        await this.error(`更新失败: ${errorMsg}`)
        console.error('Failed to update order status:', error)
      }
    },
    
    async autoMarkAsPaid() {
      if (!this.selectedOrder || this.selectedOrder.payment_status === 'paid') {
        return
      }
      
      try {
        const response = await apiClient.put(`/admin/orders/${this.selectedOrder.id}/payment`, { 
          payment_status: 'paid',
          payment_method: 'cash'
        })
        
        // Update selected order with new data
        this.selectedOrder = response.data.order
        
        const pointsAwarded = response.data.points_awarded || 0
        await this.success(`订单已自动标记为已付款（现金）\n积分: ${pointsAwarded} 分已发放\n订单状态: 订单完成`)
        
        // Refresh orders list
        await this.fetchOrders()
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Failed to update payment status'
        await this.error(`更新失败: ${errorMsg}`)
        console.error('Failed to auto-mark as paid:', error)
      }
    },
    
    async markOrderAsPaid() {
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
          payment_method: 'etransfer'
        })
        
        // Update selected order with new data
        this.selectedOrder = response.data.order
        
        // Update order status in UI
        this.selectedOrderStatus = this.selectedOrder.status || 'submitted'
        
        const pointsAwarded = response.data.points_awarded || 0
        await this.success(`订单已标记为已付款（电子转账）\n积分: ${pointsAwarded} 分已发放\n订单状态: 订单完成`)
        
        // Refresh orders list
        await this.fetchOrders()
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
        
        // Update order status in UI
        this.selectedOrderStatus = this.selectedOrder.status || 'submitted'
        
        await this.success('订单已标记为已完成')
        await this.fetchOrders()
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Failed to update status'
        await this.error(`更新失败: ${errorMsg}`)
        console.error('Failed to mark order complete:', error)
      } finally {
        this.markingComplete = false
      }
    },
    
    async updateOrderStatus(orderId, newStatus) {
      const statusText = this.getStatusText(newStatus)
      const confirmed = await this.confirm(`确认将订单状态改为 "${statusText}"?`)
      if (!confirmed) {
        return
      }
      
      try {
        await apiClient.put(`/admin/orders/${orderId}/status`, { status: newStatus })
        await this.success(`订单状态已更新为: ${statusText}`)
        await this.fetchOrders()
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Failed to update status'
        await this.error(`更新失败: ${errorMsg}`)
        console.error('Failed to update order status:', error)
      }
    },
    
    async updatePaymentStatus(order) {
      const amount = parseFloat(order.total || 0).toFixed(2)
      const pointsToEarn = Math.floor(parseFloat(order.total) * 100)
      
      const confirmed = await this.confirm(`确认标记订单 #${order.order_number} 为已付款?\n\n金额: $${amount}\n将获得积分: ${pointsToEarn} 分\n\n支付后订单将自动完成。`)
      if (!confirmed) {
        return
      }
      
      // Use existing payment method or default to cash
      const paymentMethod = order.payment_method || 'cash'
      
      try {
        const response = await apiClient.put(`/admin/orders/${order.id}/payment`, { 
          payment_status: 'paid',
          payment_method: paymentMethod
        })
        
        const pointsAwarded = response.data.points_awarded || 0
        await this.success(`订单已标记为已付款\n积分: ${pointsAwarded} 分已发放\n订单状态: 订单完成`)
        await this.fetchOrders()
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Failed to update payment status'
        await this.error(`更新失败: ${errorMsg}`)
        console.error('Failed to update payment status:', error)
      }
    },
    
    async markAsShipped(order) {
      const isDelivery = order.delivery_method === 'delivery'
      const newStatus = isDelivery ? 'out_for_delivery' : 'completed'
      const statusText = isDelivery ? '正在配送' : '订单完成'
      const actionText = isDelivery ? '已发货' : '已取货'
      
      const confirmed = await this.confirm(`确认标记订单 #${order.order_number} 为${actionText}?\n\n订单将更新为"${statusText}"状态。`)
      if (!confirmed) {
        return
      }
      
      try {
        await apiClient.put(`/admin/orders/${order.id}/status`, { status: newStatus })
        await this.success(`订单已标记为${actionText}\n订单状态: ${statusText}`)
        await this.fetchOrders()
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Failed to update status'
        await this.error(`更新失败: ${errorMsg}`)
        console.error('Failed to update status:', error)
      }
    },
    
    async cancelOrder(orderId) {
      const confirmed = await this.confirm('确认取消此订单? 此操作无法撤销。', {
        type: 'warning'
      })
      if (!confirmed) {
        return
      }
      
      try {
        await apiClient.post(`/admin/orders/${orderId}/cancel`)
        await this.success('订单已取消')
        await this.fetchOrders()
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Failed to cancel order'
        await this.error(`取消失败: ${errorMsg}`)
        console.error('Failed to cancel order:', error)
      }
    },
    
    async deleteOrder(orderId) {
      const confirmed = await this.confirm('确认删除此订单? 订单将被软删除，不会在列表中显示，但数据仍保留在数据库中。此操作无法撤销。', {
        type: 'warning',
        title: '确认删除'
      })
      if (!confirmed) {
        return
      }
      
      try {
        await apiClient.delete(`/admin/orders/${orderId}`)
        await this.success('订单已删除')
        await this.fetchOrders()
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Failed to delete order'
        await this.error(`删除失败: ${errorMsg}`)
        console.error('Failed to delete order:', error)
      }
    },
    
    getStatusText(status) {
      const statusMap = {
        'submitted': '已提交订单',
        'confirmed': '已确认订单',
        'preparing': '正在配货',
        'ready_for_pickup': '可以取货',
        'out_for_delivery': '正在配送',
        'delivering': '正在配送', // Legacy fallback
        'completed': '订单完成',
        'cancelled': '已取消'
      }
      return statusMap[status] || status
    },
    
    getPaymentStatusText(paymentStatus) {
      const paymentMap = {
        'unpaid': '未付款',
        'paid': '已付款'
      }
      return paymentMap[paymentStatus] || paymentStatus
    },
    
    formatDate(dateString) {
      return formatDateEST_CN(dateString) || 'N/A'
    },
    formatAddress(address) {
      if (!address) return 'N/A'
      const parts = []
      if (address.address_line1) parts.push(address.address_line1)
      if (address.address_line2) parts.push(address.address_line2)
      if (address.city) parts.push(address.city)
      if (address.postal_code) parts.push(address.postal_code)
      return parts.join(', ') || 'N/A'
    },
    getPickupCode(orderNumber) {
      // Extract last part of order_number (after last dash)
      // e.g., "GSF-20231225123456-CGN7O7" -> "CGN7O7"
      if (!orderNumber) return ''
      const parts = orderNumber.split('-')
      return parts[parts.length - 1] || orderNumber
    }
  }
}
</script>

<style scoped>
.orders-page {
  max-width: 1400px;
}

.page-header-actions {
  margin-bottom: var(--md-spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.search-group {
  display: flex;
  gap: var(--md-spacing-sm);
  align-items: center;
}

.search-input {
  flex: 1;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  background: var(--md-surface);
  color: var(--md-on-surface);
}

.search-input:focus {
  outline: none;
  border-color: var(--md-primary);
  border-width: 2px;
}

.search-btn, .clear-btn {
  padding: 10px 24px;
  border: none;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.1px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  min-height: 40px;
  position: relative;
  overflow: hidden;
  outline: none;
}

.search-btn {
  background: #FFF3E0;
  color: #E65100;
  border: 1px solid rgba(230, 81, 0, 0.2);
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
}

.search-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(230, 81, 0, 0.1);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s, opacity 0.3s;
  opacity: 0;
}

.search-btn:hover {
  background: #FFE0B2;
  border-color: rgba(230, 81, 0, 0.4);
  box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.16), 0px 3px 6px rgba(0, 0, 0, 0.23);
  transform: translateY(-1px);
}

.search-btn:active {
  background: #FFCC80;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  transform: translateY(0);
}

.search-btn:active::before {
  width: 300px;
  height: 300px;
  opacity: 1;
  transition: width 0s, height 0s, opacity 0.3s;
}

.clear-btn {
  background: rgba(0, 0, 0, 0.05);
  color: rgba(0, 0, 0, 0.87);
  border: 1px solid rgba(0, 0, 0, 0.12);
}

.clear-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.1);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s, opacity 0.3s;
  opacity: 0;
}

.clear-btn:hover {
  background: rgba(0, 0, 0, 0.08);
  border-color: rgba(0, 0, 0, 0.2);
}

.clear-btn:active::before {
  width: 300px;
  height: 300px;
  opacity: 1;
  transition: width 0s, height 0s, opacity 0.3s;
}

.clear-btn:active {
  background: rgba(0, 0, 0, 0.12);
}

.filter-group {
  display: flex;
  gap: var(--md-spacing-md);
  flex-wrap: wrap;
}

.filter-select {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  background: var(--md-surface);
  color: var(--md-on-surface);
  cursor: pointer;
  min-width: 150px;
}

.filter-select:focus {
  outline: none;
  border-color: var(--md-primary);
  border-width: 2px;
}

.loading, .error, .empty-state {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.error {
  color: #C62828;
}

.orders-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.order-card {
  position: relative;
  background: #FFFFFF;
  border-radius: 16px;
  padding: var(--md-spacing-md);
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: none;
  overflow: hidden;
  cursor: pointer;
}

.order-card:hover {
  background: #FFFFFF;
  box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.16), 0px 2px 4px rgba(0, 0, 0, 0.23);
  transform: translateY(-2px);
}

.delete-icon-btn {
  position: absolute;
  bottom: var(--md-spacing-md);
  right: var(--md-spacing-md);
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(158, 158, 158, 0.1);
  border: 1px solid rgba(158, 158, 158, 0.3);
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  color: #757575;
  padding: 0;
}

.delete-icon-btn:hover {
  background: rgba(244, 67, 54, 0.1);
  border-color: rgba(244, 67, 54, 0.5);
  color: #F44336;
  transform: scale(1.1);
}

.delete-icon-btn:active {
  transform: scale(0.95);
}

.delete-icon-btn svg {
  width: 18px;
  height: 18px;
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--md-spacing-sm);
  padding-bottom: var(--md-spacing-sm);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.order-id {
  font-size: 0.9375rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.87);
  font-family: 'Courier New', monospace;
}

.status-badges {
  display: flex;
  gap: var(--md-spacing-sm);
}

.order-status, .payment-status {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

/* Order Status Colors */
.status-submitted {
  background: #FFF3E0;
  color: #E65100;
}

.status-confirmed {
  background: #E3F2FD;
  color: #1565C0;
}

.status-preparing {
  background: #F3E5F5;
  color: #7B1FA2;
}

.status-ready_for_pickup {
  background: #E8F5E9;
  color: #2E7D32;
}

.status-delivering {
  background: #E1F5FE;
  color: #0277BD;
}

.status-completed {
  background: #E8F5E9;
  color: #1B5E20;
}

.status-cancelled {
  background: #FFEBEE;
  color: #C62828;
}

/* Payment Status Colors */
.payment-unpaid {
  background: #FFF3E0;
  color: #E65100;
}

.payment-paid {
  background: #E8F5E9;
  color: #1B5E20;
}

.order-info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--md-spacing-sm);
  gap: var(--md-spacing-md);
}

.order-info-user,
.order-info-group,
.order-info-delivery,
.order-info-address {
  display: flex;
  align-items: center;
  gap: 8px;
}

.order-info-user svg,
.order-info-group svg,
.order-info-delivery svg,
.order-info-address svg {
  width: 18px;
  height: 18px;
  color: rgba(0, 0, 0, 0.6);
  flex-shrink: 0;
}

.order-info-address .value {
  flex: 1;
  word-break: break-word;
}

.order-info-price {
  display: flex;
  align-items: center;
}

.order-info-row .value {
  color: rgba(0, 0, 0, 0.87);
  font-size: 0.875rem;
}

.order-info-row .value.price {
  color: var(--md-primary);
  font-weight: 600;
  font-size: 1rem;
}

.order-actions {
  display: flex;
  gap: var(--md-spacing-sm);
  flex-wrap: wrap;
  margin-top: var(--md-spacing-sm);
}

.action-btn {
  padding: 10px 24px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 24px;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.1px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  min-height: 40px;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  text-transform: none;
  outline: none;
}

/* Material Design Ripple Effect */
.action-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.1);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s, opacity 0.3s;
  opacity: 0;
}

.action-btn:active::before {
  width: 300px;
  height: 300px;
  opacity: 1;
  transition: width 0s, height 0s, opacity 0.3s;
}

.action-btn:hover {
  box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.16), 0px 3px 6px rgba(0, 0, 0, 0.23);
  transform: translateY(-1px);
}

.action-btn:active {
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  transform: translateY(0);
}

.view-btn {
  background: rgba(0, 0, 0, 0.05);
  color: rgba(0, 0, 0, 0.87);
  border: 1px solid rgba(0, 0, 0, 0.12);
}

.view-btn:hover {
  background: rgba(0, 0, 0, 0.08);
  border-color: rgba(0, 0, 0, 0.2);
}

.view-btn:active {
  background: rgba(0, 0, 0, 0.12);
}

.payment-btn {
  background: #E8F5E9;
  color: #2E7D32;
  border: 1px solid rgba(46, 125, 50, 0.2);
}

.payment-btn:hover {
  background: #C8E6C9;
  border-color: rgba(46, 125, 50, 0.4);
}

.payment-btn:active {
  background: #A5D6A7;
}

.shipping-btn {
  background: #E1F5FE;
  color: #0277BD;
  border: 1px solid rgba(2, 119, 189, 0.2);
}

.shipping-btn:hover {
  background: #B3E5FC;
  border-color: rgba(2, 119, 189, 0.4);
}

.shipping-btn:active {
  background: #81D4FA;
}

.pickup-btn {
  background: #FFF3E0;
  color: #E65100;
  border: 1px solid rgba(230, 81, 0, 0.2);
}

.pickup-btn:hover {
  background: #FFE0B2;
  border-color: rgba(230, 81, 0, 0.4);
}

.pickup-btn:active {
  background: #FFCC80;
}

.confirm-btn {
  background: #E3F2FD;
  color: #1565C0;
  border: 1px solid rgba(21, 101, 192, 0.2);
}

.confirm-btn:hover {
  background: #BBDEFB;
  border-color: rgba(21, 101, 192, 0.4);
}

.confirm-btn:active {
  background: #90CAF9;
}

.preparing-btn {
  background: #F3E5F5;
  color: #7B1FA2;
  border: 1px solid rgba(123, 31, 162, 0.2);
}

.preparing-btn:hover {
  background: #E1BEE7;
  border-color: rgba(123, 31, 162, 0.4);
}

.preparing-btn:active {
  background: #CE93D8;
}

.ready-btn {
  background: #E8F5E9;
  color: #2E7D32;
  border: 1px solid rgba(46, 125, 50, 0.2);
}

.ready-btn:hover {
  background: #C8E6C9;
  border-color: rgba(46, 125, 50, 0.4);
}

.ready-btn:active {
  background: #A5D6A7;
}

.delivery-btn {
  background: #E1F5FE;
  color: #0277BD;
  border: 1px solid rgba(2, 119, 189, 0.2);
}

.delivery-btn:hover {
  background: #B3E5FC;
  border-color: rgba(2, 119, 189, 0.4);
}

.delivery-btn:active {
  background: #81D4FA;
}

.cancel-btn {
  background: #FFEBEE;
  color: #C62828;
  border: 1px solid rgba(198, 40, 40, 0.2);
}

.cancel-btn:hover {
  background: #FFCDD2;
  border-color: rgba(198, 40, 40, 0.4);
}

.cancel-btn:active {
  background: #EF9A9A;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--md-spacing-md);
  margin-top: var(--md-spacing-lg);
  padding: var(--md-spacing-md);
}

.page-btn {
  padding: 10px 24px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 24px;
  background: #FFFFFF;
  color: rgba(0, 0, 0, 0.87);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.1px;
  min-height: 40px;
  position: relative;
  overflow: hidden;
  outline: none;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
}

.page-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.1);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s, opacity 0.3s;
  opacity: 0;
}

.page-btn:hover:not(:disabled) {
  background: #FFF3E0;
  color: #E65100;
  border-color: rgba(230, 81, 0, 0.4);
  box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.16), 0px 3px 6px rgba(0, 0, 0, 0.23);
  transform: translateY(-1px);
}

.page-btn:active:not(:disabled) {
  box-shadow: 0px 1px 3px rgba(255, 140, 0, 0.3), 0px 1px 2px rgba(255, 140, 0, 0.2);
  transform: translateY(0);
}

.page-btn:active:not(:disabled)::before {
  width: 300px;
  height: 300px;
  opacity: 1;
  transition: width 0s, height 0s, opacity 0.3s;
}

.page-btn:disabled {
  opacity: 0.38;
  cursor: not-allowed;
  box-shadow: none;
}

.page-info {
  color: var(--md-on-surface-variant);
  font-size: var(--md-body-size);
}

.qr-scanner-btn {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-xs);
  padding: 10px 24px;
  border: 1px solid rgba(17, 153, 142, 0.2);
  border-radius: 24px;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.1px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  background: #E0F2F1;
  color: #00695C;
  min-height: 40px;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  position: relative;
  overflow: hidden;
  outline: none;
}

.qr-scanner-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(0, 105, 92, 0.1);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s, opacity 0.3s;
  opacity: 0;
}

.qr-scanner-btn:hover {
  background: #B2DFDB;
  border-color: rgba(0, 105, 92, 0.4);
  box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.16), 0px 3px 6px rgba(0, 0, 0, 0.23);
  transform: translateY(-1px);
}

.qr-scanner-btn:active {
  background: #80CBC4;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  transform: translateY(0);
}

.qr-scanner-btn:active::before {
  width: 300px;
  height: 300px;
  opacity: 1;
  transition: width 0s, height 0s, opacity 0.3s;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--md-spacing-md);
}

.modal-content {
  background: #FFFFFF;
  border-radius: 24px;
  max-width: 800px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0px 11px 15px -7px rgba(0, 0, 0, 0.2), 0px 24px 38px 3px rgba(0, 0, 0, 0.14), 0px 9px 46px 8px rgba(0, 0, 0, 0.12);
  overflow: hidden;
}

.qr-scanner-modal {
  max-width: 500px;
}

.order-detail-modal {
  max-width: 900px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  background: var(--gradient-primary);
  border-bottom: 1px solid rgba(255, 165, 0, 0.2);
  border-radius: 24px 24px 0 0;
}

.header-content {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
  width: 100%;
}

.header-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 10px;
  color: #FF8C00;
}

.header-icon svg {
  width: 20px;
  height: 20px;
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.header-status-badges {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  margin-left: auto;
}

.payment-status-badge-header {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.modal-header h2 {
  font-size: 1.125rem;
  color: rgba(0, 0, 0, 0.9);
  font-weight: 600;
  margin: 0;
}

.order-number {
  font-size: 0.8125rem;
  color: rgba(0, 0, 0, 0.7);
  font-family: 'Courier New', monospace;
  margin: 0;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: rgba(0, 0, 0, 0.7);
  cursor: pointer;
  border-radius: var(--md-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn svg {
  width: 20px;
  height: 20px;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  color: rgba(0, 0, 0, 0.9);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--md-spacing-md);
  background: #FAFAFA;
}

.modal-footer {
  display: flex;
  gap: var(--md-spacing-md);
  padding: var(--md-spacing-md);
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  background: #FFFFFF;
  border-radius: 0 0 24px 24px;
}

.cancel-btn-secondary {
  flex: 1;
  padding: 10px 24px;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.1px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(0, 0, 0, 0.12);
  background: transparent;
  color: rgba(0, 0, 0, 0.87);
  min-height: 40px;
  position: relative;
  overflow: hidden;
  outline: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.cancel-btn-secondary::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.1);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s, opacity 0.3s;
  opacity: 0;
}

.cancel-btn-secondary:hover {
  background: rgba(0, 0, 0, 0.04);
  border-color: rgba(0, 0, 0, 0.2);
}

.cancel-btn-secondary:active::before {
  width: 300px;
  height: 300px;
  opacity: 1;
  transition: width 0s, height 0s, opacity 0.3s;
}

.cancel-btn-secondary:active {
  background: rgba(0, 0, 0, 0.08);
}

.update-order-btn {
  flex: 1;
  padding: 10px 24px;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.1px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(230, 81, 0, 0.2);
  background: #FFF3E0;
  color: #E65100;
  min-height: 40px;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  position: relative;
  overflow: hidden;
  outline: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.update-order-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(230, 81, 0, 0.1);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s, opacity 0.3s;
  opacity: 0;
}

.update-order-btn:hover:not(:disabled) {
  background: #FFE0B2;
  border-color: rgba(230, 81, 0, 0.4);
  box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.16), 0px 3px 6px rgba(0, 0, 0, 0.23);
  transform: translateY(-1px);
}

.update-order-btn:active:not(:disabled) {
  background: #FFCC80;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  transform: translateY(0);
}

.update-order-btn:active:not(:disabled)::before {
  width: 300px;
  height: 300px;
  opacity: 1;
  transition: width 0s, height 0s, opacity 0.3s;
}

.update-order-btn:disabled {
  opacity: 0.38;
  cursor: not-allowed;
  box-shadow: none;
}

/* Add Product Modal Styles */
.modal-overlay-inner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: var(--md-spacing-md);
}

.modal-content-inner {
  background: #FFFFFF;
  border-radius: 16px;
  max-width: 500px;
  width: 100%;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0px 11px 15px -7px rgba(0, 0, 0, 0.2), 0px 24px 38px 3px rgba(0, 0, 0, 0.14), 0px 9px 46px 8px rgba(0, 0, 0, 0.12);
  overflow: hidden;
}

.modal-header-inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.modal-header-inner h3 {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
}

.close-btn-small {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: rgba(0, 0, 0, 0.7);
  cursor: pointer;
  border-radius: 50%;
  font-size: 24px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn-small:hover {
  background: rgba(0, 0, 0, 0.05);
}

.modal-body-inner {
  flex: 1;
  overflow-y: auto;
  padding: var(--md-spacing-md);
}

.products-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
}

.product-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  background: #F5F5F5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.product-item:hover {
  background: #EEEEEE;
  transform: translateX(4px);
}

.product-name {
  font-weight: 500;
  color: rgba(0, 0, 0, 0.87);
}

.product-price {
  font-weight: 600;
  color: #E65100;
}

.empty-products {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.order-detail-content {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.order-info-section,
.order-items-section {
  background: #FFFFFF;
  border-radius: 12px;
  padding: var(--md-spacing-md);
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.08), 0px 1px 2px rgba(0, 0, 0, 0.06);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--md-spacing-xs);
  margin-bottom: var(--md-spacing-sm);
  padding-bottom: var(--md-spacing-xs);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.add-item-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #E8F5E9;
  color: #2E7D32;
  border: 1px solid rgba(46, 125, 50, 0.2);
  border-radius: 16px;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.add-item-btn:hover {
  background: #C8E6C9;
  border-color: rgba(46, 125, 50, 0.4);
}

.section-header svg {
  width: 20px;
  height: 20px;
  color: #E65100;
}

.order-info-section h3,
.order-items-section h3 {
  font-size: 1rem;
  color: rgba(0, 0, 0, 0.87);
  margin: 0;
  font-weight: 600;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--md-spacing-sm);
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--md-spacing-md);
}

.info-item-user {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-item-user svg {
  width: 18px;
  height: 18px;
  color: rgba(0, 0, 0, 0.6);
}

.info-item-price {
  display: flex;
  align-items: center;
}

.info-item-payment-method {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  width: 100%;
}

.payment-method-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.7);
  white-space: nowrap;
}

.payment-method-select {
  flex: 1;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  background: var(--md-surface);
  color: var(--md-on-surface);
  cursor: pointer;
  max-width: 200px;
}

.payment-method-select:focus {
  outline: none;
  border-color: var(--md-primary);
  border-width: 2px;
}

.info-item-order-status {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  width: 100%;
}

.order-status-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.7);
  white-space: nowrap;
}

.order-status-select {
  flex: 1;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  background: var(--md-surface);
  color: var(--md-on-surface);
  cursor: pointer;
  max-width: 200px;
}

.order-status-select:focus {
  outline: none;
  border-color: var(--md-primary);
  border-width: 2px;
}

.mark-paid-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 24px;
  border: 1px solid rgba(46, 125, 50, 0.2);
  border-radius: 24px;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.1px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  background: #E8F5E9;
  color: #2E7D32;
  min-height: 40px;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  position: relative;
  overflow: hidden;
  outline: none;
  width: 100%;
  justify-content: center;
}

.mark-paid-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(46, 125, 50, 0.1);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s, opacity 0.3s;
  opacity: 0;
}

.mark-paid-btn:hover {
  background: #C8E6C9;
  border-color: rgba(46, 125, 50, 0.4);
  box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.16), 0px 3px 6px rgba(0, 0, 0, 0.23);
  transform: translateY(-1px);
}

.mark-paid-btn:active {
  background: #A5D6A7;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  transform: translateY(0);
}

.mark-paid-btn:active::before {
  width: 300px;
  height: 300px;
  opacity: 1;
  transition: width 0s, height 0s, opacity 0.3s;
}

.complete-order-btn {
  padding: 10px 24px;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.1px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(46, 125, 50, 0.2);
  background: #E8F5E9;
  color: #2E7D32;
  min-height: 40px;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  position: relative;
  overflow: hidden;
  outline: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.complete-order-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(46, 125, 50, 0.1);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s, opacity 0.3s;
  opacity: 0;
}

.complete-order-btn:hover:not(:disabled) {
  background: #C8E6C9;
  border-color: rgba(46, 125, 50, 0.4);
  box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.16), 0px 3px 6px rgba(0, 0, 0, 0.23);
  transform: translateY(-1px);
}

.complete-order-btn:active:not(:disabled) {
  background: #A5D6A7;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  transform: translateY(0);
}

.complete-order-btn:active:not(:disabled)::before {
  width: 300px;
  height: 300px;
  opacity: 1;
  transition: width 0s, height 0s, opacity 0.3s;
}

.complete-order-btn:disabled {
  opacity: 0.38;
  cursor: not-allowed;
  box-shadow: none;
}

.info-item .label {
  font-weight: 500;
  color: rgba(0, 0, 0, 0.6);
  font-size: 0.6875rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-item .value {
  color: rgba(0, 0, 0, 0.87);
  font-size: 0.875rem;
  line-height: 1.2;
}

.info-item .value.pickup-code {
  font-family: 'Courier New', monospace;
  font-weight: 700;
  font-size: 1.1rem;
  color: #2E7D32;
}

.info-item .value.price {
  color: var(--md-primary);
  font-weight: 600;
  font-size: 1.1rem;
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.order-item-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--md-spacing-sm);
  background: #F5F5F5;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  transition: all 0.2s;
  gap: var(--md-spacing-sm);
}

.order-item-row:hover {
  background: #EEEEEE;
  border-color: rgba(0, 0, 0, 0.1);
}

.item-info {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
}

.item-name {
  font-size: var(--md-body-size);
  font-weight: 500;
  color: var(--md-on-surface);
}

.item-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin-top: var(--md-spacing-xs);
  gap: var(--md-spacing-md);
}

.quantity-controls {
  display: flex;
  align-items: center;
  gap: 4px;
}

.qty-btn {
  width: 28px;
  height: 28px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 4px;
  background: #FFFFFF;
  color: rgba(0, 0, 0, 0.87);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 500;
  transition: all 0.2s;
}

.qty-btn:hover:not(:disabled) {
  background: #F5F5F5;
  border-color: rgba(0, 0, 0, 0.2);
}

.qty-btn:disabled {
  opacity: 0.38;
  cursor: not-allowed;
}

.quantity-input {
  width: 50px;
  padding: 4px 8px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 4px;
  text-align: center;
  font-size: 0.875rem;
}

.remove-item-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid rgba(244, 67, 54, 0.3);
  border-radius: 50%;
  color: #F44336;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.remove-item-btn:hover {
  background: rgba(244, 67, 54, 0.2);
  border-color: rgba(244, 67, 54, 0.5);
}

.remove-item-btn svg {
  width: 18px;
  height: 18px;
}

.quantity-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: rgba(230, 81, 0, 0.1);
  border-radius: 12px;
  color: #E65100;
  font-weight: 500;
  font-size: 0.8125rem;
}

.item-price {
  font-weight: 600;
  color: var(--md-primary);
}

.weight-input-group {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  margin-top: var(--md-spacing-sm);
  padding-top: var(--md-spacing-sm);
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.weight-input-group label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--md-label-size);
  color: rgba(0, 0, 0, 0.7);
  font-weight: 500;
  min-width: 120px;
}

.weight-input-group label svg {
  color: #E65100;
}

.weight-input {
  flex: 1;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  background: var(--md-surface);
  color: var(--md-on-surface);
  max-width: 200px;
}

.weight-input:focus {
  outline: none;
  border-color: var(--md-primary);
  border-width: 2px;
}

.error-message {
  padding: var(--md-spacing-md);
  background: #FFEBEE;
  color: #C62828;
  border-radius: var(--md-radius-md);
  font-size: var(--md-label-size);
  margin-top: var(--md-spacing-md);
}

/* Mobile Responsive Styles */
@media (max-width: 767px) {
  .page-header-actions {
    gap: var(--md-spacing-sm);
  }

  .search-group {
    flex-wrap: wrap;
  }

  .search-input {
    min-width: 0;
    flex: 1 1 100%;
  }

  .search-btn,
  .clear-btn,
  .qr-scanner-btn {
    flex: 1 1 auto;
    min-width: 80px;
  }

  .filter-group {
    flex-direction: column;
  }

  .filter-select {
    width: 100%;
    min-width: 0;
  }

  .order-card {
    padding: var(--md-spacing-md);
  }

  .order-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--md-spacing-sm);
  }

  .status-badges {
    width: 100%;
    flex-wrap: wrap;
  }

  .order-info {
    grid-template-columns: 1fr;
    gap: var(--md-spacing-sm);
  }

  .info-item {
    flex-direction: column;
    gap: var(--md-spacing-xs);
  }

  .info-item .label {
    min-width: 0;
    font-size: var(--md-label-size);
  }

  .order-actions {
    flex-direction: column;
    gap: var(--md-spacing-sm);
  }

  .action-btn {
    width: 100%;
  }

  .delete-icon-btn {
    display: none;
  }

  .modal-overlay {
    padding: var(--md-spacing-sm);
  }

  .modal-content {
    max-height: 95vh;
  }

  .modal-header,
  .modal-body,
  .modal-footer {
    padding: var(--md-spacing-md);
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .pagination {
    flex-wrap: wrap;
    gap: var(--md-spacing-sm);
  }

  .page-btn {
    padding: var(--md-spacing-xs) var(--md-spacing-sm);
    font-size: var(--md-label-size);
  }
}

@media (max-width: 480px) {
  .order-card {
    padding: var(--md-spacing-sm);
  }

  .order-id {
    font-size: var(--md-body-size);
  }

  .order-status,
  .payment-status {
    font-size: 0.75rem;
    padding: 0.25rem 0.5rem;
  }

  .info-item .value {
    font-size: var(--md-label-size);
  }

  .action-btn {
    font-size: var(--md-label-size);
    padding: var(--md-spacing-sm);
  }
}
</style>
