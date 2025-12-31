<template>
  <div class="order-card" @click="$emit('click', order)">
    <!-- Delete Icon - Bottom Right -->
    <button 
      v-if="showDelete"
      @click.stop="$emit('delete', order.id)" 
      class="delete-icon-btn"
      title="删除订单">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
      </svg>
    </button>
    
    <div class="order-header">
      <div class="order-id">{{ order.order_number }}</div>
      <div class="status-badges">
        <div class="order-status" :class="`status-${order.status}`">
          {{ getStatusText(order.status) }}
        </div>
        <div class="payment-status" :class="`payment-${order.payment_status}`">
          {{ getPaymentStatusText(order.payment_status) }}
        </div>
      </div>
    </div>
    
    <div class="order-info-row">
      <div class="order-info-user">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
        <span class="value">{{ order.user?.nickname || order.user?.phone || 'N/A' }}</span>
        <span v-if="order.user?.wechat" class="wechat-badge">微信: {{ order.user.wechat }}</span>
      </div>
      <div class="order-info-price">
        <span class="value price">${{ parseFloat(order.total || 0).toFixed(2) }}</span>
      </div>
    </div>
    
    <div class="order-info-row" v-if="order.group_deal">
      <div class="order-info-group">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <span class="value">{{ order.group_deal.title }}</span>
      </div>
    </div>
    
    <div class="order-info-row">
      <div class="order-info-delivery">
        <svg v-if="order.delivery_method === 'pickup'" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span class="value">{{ order.delivery_method === 'pickup' ? '自取' : '配送' }}</span>
      </div>
    </div>
    
    <!-- Address/Location Info -->
    <div class="order-info-row" v-if="order.delivery_method === 'delivery' && order.address">
      <div class="order-info-address">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <span class="value">{{ formatAddress(order.address) }}</span>
      </div>
    </div>
    
    <div class="order-info-row" v-if="order.delivery_method === 'pickup'">
      <div class="order-info-address">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <span class="value">自取点: Markham / North York</span>
      </div>
    </div>
    
    <div class="order-actions" @click.stop v-if="showActions">
      <!-- Payment Status Toggle -->
      <button 
        v-if="order.status !== 'cancelled' && order.payment_status === 'unpaid'"
        @click="$emit('update-payment', order)" 
        class="action-btn payment-btn">
        标记为已付款
      </button>
      
      <!-- Shipping Status Toggle for Delivery Orders -->
      <button 
        v-if="order.status !== 'cancelled' && order.status !== 'completed' && order.delivery_method === 'delivery' && order.status === 'preparing'"
        @click="$emit('mark-shipped', order)" 
        class="action-btn shipping-btn">
        标记为已发货
      </button>
      
      <!-- Pickup Status Toggle for Pickup Orders -->
      <button 
        v-if="order.status !== 'cancelled' && order.status !== 'completed' && order.delivery_method === 'pickup' && (order.status === 'preparing' || order.status === 'ready_for_pickup')"
        @click="$emit('mark-shipped', order)" 
        class="action-btn pickup-btn">
        标记为已取货
      </button>
      
      <!-- Order Status Updates -->
      <button 
        v-if="order.status === 'confirmed'"
        @click="$emit('update-status', order.id, 'preparing')" 
        class="action-btn preparing-btn">
        开始配货
      </button>
      
      <button 
        v-if="order.status === 'preparing' && order.delivery_method === 'pickup'"
        @click="$emit('update-status', order.id, 'ready_for_pickup')" 
        class="action-btn ready-btn">
        通知取货
      </button>
      
      <button 
        v-if="order.status === 'preparing' && order.delivery_method === 'delivery'"
        @click="$emit('update-status', order.id, 'out_for_delivery')" 
        class="action-btn delivery-btn">
        开始配送
      </button>
      
      <!-- Cancel Order -->
      <button 
        v-if="order.status !== 'completed' && order.status !== 'cancelled'"
        @click="$emit('cancel', order.id)" 
        class="action-btn cancel-btn">
        取消订单
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'OrderCard',
  props: {
    order: {
      type: Object,
      required: true
    },
    showDelete: {
      type: Boolean,
      default: true
    },
    showActions: {
      type: Boolean,
      default: true
    }
  },
  emits: ['click', 'delete', 'update-payment', 'mark-shipped', 'update-status', 'cancel'],
  methods: {
    getStatusText(status) {
      const statusMap = {
        'submitted': '已提交订单',
        'confirmed': '已确认订单',
        'preparing': '正在配货',
        'ready_for_pickup': '可以取货',
        'out_for_delivery': '正在配送',
        'delivering': '正在配送',
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
    formatAddress(address) {
      if (!address) return 'N/A'
      const parts = []
      if (address.address_line1) parts.push(address.address_line1)
      if (address.address_line2) parts.push(address.address_line2)
      if (address.city) parts.push(address.city)
      if (address.postal_code) parts.push(address.postal_code)
      return parts.join(', ') || 'N/A'
    }
  }
}
</script>

<style scoped>
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

.wechat-badge {
  margin-left: 8px;
  padding: 2px 8px;
  background: #E8F5E9;
  color: #2E7D32;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
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

.action-btn:hover {
  box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.16), 0px 3px 6px rgba(0, 0, 0, 0.23);
  transform: translateY(-1px);
}

.action-btn:active {
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  transform: translateY(0);
}

.action-btn:active::before {
  width: 300px;
  height: 300px;
  opacity: 1;
  transition: width 0s, height 0s, opacity 0.3s;
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

.shipping-btn {
  background: #E1F5FE;
  color: #0277BD;
  border: 1px solid rgba(2, 119, 189, 0.2);
}

.shipping-btn:hover {
  background: #B3E5FC;
  border-color: rgba(2, 119, 189, 0.4);
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

.preparing-btn {
  background: #F3E5F5;
  color: #7B1FA2;
  border: 1px solid rgba(123, 31, 162, 0.2);
}

.preparing-btn:hover {
  background: #E1BEE7;
  border-color: rgba(123, 31, 162, 0.4);
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

.delivery-btn {
  background: #E1F5FE;
  color: #0277BD;
  border: 1px solid rgba(2, 119, 189, 0.2);
}

.delivery-btn:hover {
  background: #B3E5FC;
  border-color: rgba(2, 119, 189, 0.4);
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
</style>

