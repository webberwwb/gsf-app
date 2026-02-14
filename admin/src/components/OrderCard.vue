<template>
  <div class="order-card" @click="handleCardClick">
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
      <div class="header-right">
        <div class="status-badges">
          <div class="order-status" :class="`status-${order.status}`">
            {{ getStatusText(order.status) }}
          </div>
          <div class="payment-status" :class="`payment-${order.payment_status}`">
            {{ getPaymentStatusText(order.payment_status) }}
          </div>
        </div>
        <!-- Quick Action Button: Mark Packing Complete -->
        <button 
          v-if="order.status === 'preparing'"
          @click.stop="handleMarkPackingComplete" 
          class="quick-action-btn-header packing-complete-btn"
          title="标记配货完成">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span class="quick-action-text">标记配货完成</span>
        </button>
      </div>
    </div>
    
    <div class="order-info-row">
      <div class="order-info-user">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
        <span class="value">{{ order.user?.nickname || 'N/A' }}</span>
        <span v-if="order.user?.phone" class="phone-badge">{{ order.user.phone }}</span>
        <span v-if="order.user?.wechat" class="wechat-badge">微信: {{ order.user.wechat }}</span>
        <button 
          v-if="order.user && !order.user.is_admin" 
          @click.stop="impersonateUser(order.user.id)" 
          class="impersonate-btn-small"
          title="代登录此用户">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="width: 14px; height: 14px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          代登录
        </button>
      </div>
      <div class="order-info-price">
        <span class="value price">${{ parseFloat(order.final_total || order.total || 0).toFixed(2) }}</span>
        <span v-if="order.final_total && order.final_total !== order.total" class="price-note-small">(含调整)</span>
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
        <span class="value">{{ order.pickup_location || 'N/A' }}</span>
      </div>
    </div>
    
    <!-- Order Notes -->
    <div class="order-info-row" v-if="order.notes">
      <div class="order-notes">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
        </svg>
        <span class="value notes-text">备注: {{ order.notes }}</span>
      </div>
    </div>
    
    <!-- Order Items/Products -->
    <div class="order-items-section" :class="{ 'items-expanded': showOrderItems }" v-if="order.items && order.items.length > 0">
      <div class="items-header" @click.stop="toggleOrderItems">
        <div class="items-header-left">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
          </svg>
          <span>商品明细 ({{ order.items.length }})</span>
        </div>
        <button class="toggle-items-btn" @click.stop="toggleOrderItems">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>
      
      <div v-if="showOrderItems">
        <div class="items-list">
        <div 
          v-for="item in order.items" 
          :key="item.id"
          class="item-row">
          <span class="item-name">
            {{ item.product?.name || 'Unknown' }}
            <div v-if="item.product" class="product-info-icon" @click.stop title="查看价格详情">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div class="price-tooltip">
                <div class="tooltip-content">
                  <div class="tooltip-header">{{ item.product.name }}</div>
                  <div class="tooltip-body">
                    <div class="tooltip-row">
                      <span class="tooltip-label">定价类型:</span>
                      <span class="tooltip-value">{{ formatPricingType(item.product.pricing_type) }}</span>
                    </div>
                    <div class="tooltip-divider"></div>
                    <div v-if="item.product.pricing_type === 'per_item'" class="tooltip-row">
                      <span class="tooltip-label">价格:</span>
                      <span class="tooltip-value">${{ item.product.pricing_data?.price?.toFixed(2) }}</span>
                    </div>
                    <div v-else-if="item.product.pricing_type === 'weight_range'" class="tooltip-section">
                      <div class="tooltip-label">价格区间:</div>
                      <div v-for="(range, idx) in item.product.pricing_data?.ranges" :key="idx" class="tooltip-range">
                        <span>{{ range.min }}{{ range.max ? ` - ${range.max}` : '+' }} {{ item.product.pricing_data?.unit || 'lb' }}:</span>
                        <span class="tooltip-price">${{ range.price?.toFixed(2) }}/{{ item.product.pricing_data?.unit || 'lb' }}</span>
                      </div>
                    </div>
                    <div v-else-if="item.product.pricing_type === 'unit_weight'" class="tooltip-row">
                      <span class="tooltip-label">单价:</span>
                      <span class="tooltip-value">${{ item.product.pricing_data?.price_per_unit?.toFixed(2) }}/{{ item.product.pricing_data?.unit || 'lb' }}</span>
                    </div>
                    <div v-else-if="item.product.pricing_type === 'bundled_weight'" class="tooltip-section">
                      <div class="tooltip-row">
                        <span class="tooltip-label">单价:</span>
                        <span class="tooltip-value">${{ item.product.pricing_data?.price_per_unit?.toFixed(2) }}/{{ item.product.pricing_data?.unit || 'lb' }}</span>
                      </div>
                      <div class="tooltip-row">
                        <span class="tooltip-label">重量范围:</span>
                        <span class="tooltip-value">{{ item.product.pricing_data?.min_weight }} - {{ item.product.pricing_data?.max_weight }} {{ item.product.pricing_data?.unit || 'lb' }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </span>
          <span class="item-quantity">x{{ item.quantity }}</span>
          <span class="item-price">${{ parseFloat(item.total_price || item.unit_price * item.quantity || 0).toFixed(2) }}</span>
        </div>
      </div>
      <div class="items-subtotal">
        <span class="subtotal-label">小计:</span>
        <span class="subtotal-amount">${{ calculateSubtotal().toFixed(2) }}</span>
      </div>
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
import apiClient from '../api/client'
import { useModal } from '../composables/useModal'

export default {
  name: 'OrderCard',
  setup() {
    const { confirm, success, error } = useModal()
    return { confirm, success, error }
  },
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
    },
    itemsExpandedByDefault: {
      type: Boolean,
      default: false
    }
  },
  emits: ['click', 'delete', 'update-payment', 'mark-shipped', 'update-status', 'cancel', 'mark-packing-complete'],
  data() {
    return {
      showOrderItems: this.itemsExpandedByDefault
    }
  },
  methods: {
    toggleOrderItems() {
      this.showOrderItems = !this.showOrderItems
    },
    handleCardClick() {
      this.$emit('click', this.order)
    },
    getStatusText(status) {
      const statusMap = {
        'submitted': '已提交订单',
        'confirmed': '已确认订单',
        'preparing': '正在配货',
        'packing_complete': '配货完成',
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
    },
    calculateSubtotal() {
      if (!this.order.items || !Array.isArray(this.order.items) || this.order.items.length === 0) {
        return 0
      }
      
      return this.order.items.reduce((sum, item) => {
        // Use total_price if available, otherwise calculate from unit_price * quantity
        const itemTotal = parseFloat(item.total_price || (item.unit_price * item.quantity) || 0)
        return sum + itemTotal
      }, 0)
    },
    async impersonateUser(userId) {
      const confirmed = await this.confirm('确定要以该用户身份登录吗？您将被重定向到用户端应用，可以直接修改订单。', {
        type: 'warning',
        title: '代登录确认'
      })
      if (!confirmed) {
        return
      }

      try {
        const response = await apiClient.post(`/admin/users/${userId}/impersonate`)
        const { redirect_url } = response.data
        
        // Redirect to app frontend with token
        window.location.href = redirect_url
      } catch (error) {
        await this.error(error.response?.data?.message || error.response?.data?.error || '代登录失败')
        console.error('Impersonate user error:', error)
      }
    },
    handleMarkPackingComplete() {
      this.$emit('mark-packing-complete', this.order)
    },
    formatPricingType(pricingType) {
      const typeMap = {
        'per_item': '按件计价',
        'weight_range': '按重量区间计价',
        'unit_weight': '按单位重量计价',
        'bundled_weight': '按捆绑重量计价'
      }
      return typeMap[pricingType] || pricingType
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
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: none;
  overflow: visible;
  cursor: pointer;
}

/* Laptop screens - more compact */
@media (max-width: 1366px) {
  .order-card {
    padding: var(--md-spacing-sm) var(--md-spacing-md);
    border-radius: 12px;
  }
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

/* Laptop screens - stack header on narrow screens */
@media (max-width: 1366px) {
  .order-header {
    flex-wrap: wrap;
    gap: var(--md-spacing-xs);
    margin-bottom: var(--md-spacing-xs);
    padding-bottom: var(--md-spacing-xs);
  }
  
  .order-id {
    font-size: 0.875rem;
  }
  
  .header-right {
    flex-wrap: wrap;
    gap: var(--md-spacing-xs);
  }
}

.order-id {
  font-size: 0.9375rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.87);
  font-family: 'Courier New', monospace;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
}

.status-badges {
  display: flex;
  gap: var(--md-spacing-sm);
}

/* Laptop screens - smaller badges */
@media (max-width: 1366px) {
  .status-badges {
    gap: 4px;
  }
}

.order-status, .payment-status {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

/* Laptop screens - even smaller badges */
@media (max-width: 1366px) {
  .order-status, .payment-status {
    padding: 3px 8px;
    font-size: 0.6875rem;
    border-radius: 10px;
  }
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

.status-packing_complete {
  background: #E1F5FE;
  color: #01579B;
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
  margin-bottom: 6px;
  gap: var(--md-spacing-md);
}

/* Laptop screens - more compact rows */
@media (max-width: 1366px) {
  .order-info-row {
    margin-bottom: 4px;
    gap: var(--md-spacing-sm);
  }
  
  .order-info-row .value {
    font-size: 0.8125rem;
  }
  
  .order-info-row .value.price {
    font-size: 0.9375rem;
  }
}

.order-info-user,
.order-info-group,
.order-info-delivery,
.order-info-address,
.order-notes {
  display: flex;
  align-items: center;
  gap: 8px;
}

.order-info-user svg,
.order-info-group svg,
.order-info-delivery svg,
.order-info-address svg,
.order-notes svg {
  width: 18px;
  height: 18px;
  color: rgba(0, 0, 0, 0.6);
  flex-shrink: 0;
}

.order-info-address .value {
  flex: 1;
  word-break: break-word;
}

.order-notes {
  align-items: flex-start;
}

.order-notes .notes-text {
  font-style: italic;
  background: #FFF9C4;
  padding: 6px 12px;
  border-radius: 8px;
  border-left: 3px solid #FFC107;
  line-height: 1.4;
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

.price-note-small {
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.5);
  margin-left: 4px;
  font-weight: normal;
}

.phone-badge {
  margin-left: 8px;
  padding: 2px 8px;
  background: #E3F2FD;
  color: #1565C0;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

/* Laptop screens - hide or simplify badges on small screens */
@media (max-width: 1366px) {
  .phone-badge,
  .wechat-badge {
    display: none;
  }
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

.impersonate-btn-small {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: 8px;
  padding: 4px 10px;
  background: rgba(33, 150, 243, 0.1);
  color: #2196F3;
  border: 1px solid rgba(33, 150, 243, 0.3);
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.impersonate-btn-small:hover {
  background: rgba(33, 150, 243, 0.2);
  border-color: rgba(33, 150, 243, 0.5);
  transform: translateY(-1px);
}

.impersonate-btn-small svg {
  width: 14px;
  height: 14px;
}

.order-actions {
  display: flex;
  gap: var(--md-spacing-sm);
  flex-wrap: wrap;
  margin-top: var(--md-spacing-sm);
}

/* Laptop screens - smaller action buttons */
@media (max-width: 1366px) {
  .order-actions {
    gap: 6px;
    margin-top: var(--md-spacing-xs);
  }
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

/* Laptop screens - more compact buttons */
@media (max-width: 1366px) {
  .action-btn {
    padding: 6px 16px;
    font-size: 0.8125rem;
    min-height: 32px;
    border-radius: 16px;
  }
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

.order-items-section {
  margin-top: 0;
  padding-top: 0;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  overflow: visible;
}

.items-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: var(--md-spacing-sm);
  font-size: 0.875rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.7);
  cursor: pointer;
  padding: 0;
  border-radius: 8px;
  transition: background 0.2s;
}

.items-header:hover {
  background: rgba(0, 0, 0, 0.03);
}

.items-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.items-header svg {
  width: 16px;
  height: 16px;
  color: rgba(0, 0, 0, 0.6);
}

.toggle-items-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  background: transparent;
  border: none;
  cursor: pointer;
  color: rgba(0, 0, 0, 0.6);
  transition: all 0.2s;
  flex-shrink: 0;
  border-radius: 4px;
}

.toggle-items-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  color: var(--md-primary);
}

.toggle-items-btn svg {
  width: 18px;
  height: 18px;
  transition: transform 0.2s;
  transform: rotate(-90deg);
}

.order-items-section.items-expanded .toggle-items-btn svg {
  transform: rotate(0deg);
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow: visible;
}

.item-row {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  font-size: 0.875rem;
  position: relative;
  z-index: 1;
}

.item-row:hover {
  z-index: 1001;
}

.item-name {
  flex: 1;
  color: rgba(0, 0, 0, 0.87);
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
}

.item-quantity {
  color: rgba(0, 0, 0, 0.6);
  font-weight: 500;
  min-width: 40px;
  text-align: right;
}

.item-price {
  color: var(--md-primary);
  font-weight: 600;
  min-width: 60px;
  text-align: right;
}

.items-subtotal {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: var(--md-spacing-sm);
  padding-top: var(--md-spacing-sm);
  border-top: 2px solid rgba(0, 0, 0, 0.12);
  font-weight: 600;
}

.subtotal-label {
  color: rgba(0, 0, 0, 0.87);
  font-size: 0.875rem;
}

.subtotal-amount {
  color: var(--md-primary);
  font-size: 0.9375rem;
  font-weight: 600;
}

.quick-action-btn-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 6px 14px;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(1, 87, 155, 0.2);
  background: #E1F5FE;
  color: #01579B;
  flex-shrink: 0;
  box-shadow: 0px 1px 2px rgba(0, 0, 0, 0.1);
  outline: none;
  white-space: nowrap;
  font-size: 0.75rem;
  font-weight: 500;
}

/* Laptop screens - hide text, show icon only */
@media (max-width: 1366px) {
  .quick-action-btn-header {
    padding: 6px 10px;
  }
  
  .quick-action-text {
    display: none;
  }
}

.quick-action-btn-header svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.quick-action-text {
  font-size: 0.75rem;
  font-weight: 500;
}

.quick-action-btn-header:hover {
  background: #B3E5FC;
  border-color: rgba(1, 87, 155, 0.4);
  box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

.quick-action-btn-header:active {
  background: #81D4FA;
  box-shadow: 0px 1px 2px rgba(0, 0, 0, 0.1);
  transform: translateY(0);
}

/* Product Info Icon and Tooltip */
.product-info-icon {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  cursor: help;
  color: rgba(0, 0, 0, 0.4);
  transition: all 0.2s;
}

.product-info-icon svg {
  width: 16px;
  height: 16px;
}

.product-info-icon:hover {
  color: var(--md-primary);
  transform: scale(1.1);
}

.price-tooltip {
  position: absolute;
  left: calc(100% + 8px);
  top: 50%;
  transform: translateY(-50%);
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
  z-index: 1000;
}

.product-info-icon:hover .price-tooltip {
  opacity: 1;
  visibility: visible;
  left: calc(100% + 12px);
}

.tooltip-content {
  background: #FFFFFF;
  border-radius: 12px;
  box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.15), 0px 2px 8px rgba(0, 0, 0, 0.1);
  padding: 12px 16px;
  min-width: 260px;
  max-width: 350px;
  width: max-content;
  border: 1px solid rgba(0, 0, 0, 0.08);
  position: relative;
}

.tooltip-content::after {
  content: '';
  position: absolute;
  left: -6px;
  top: 50%;
  width: 12px;
  height: 12px;
  background: #FFFFFF;
  border-left: 1px solid rgba(0, 0, 0, 0.08);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  transform: translateY(-50%) rotate(45deg);
}

.tooltip-header {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--md-on-surface);
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--md-primary);
}

.tooltip-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tooltip-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  font-size: 0.8125rem;
}

.tooltip-label {
  color: rgba(0, 0, 0, 0.6);
  font-weight: 500;
  white-space: nowrap;
}

.tooltip-value {
  color: var(--md-on-surface);
  font-weight: 600;
  text-align: right;
}

.tooltip-divider {
  height: 1px;
  background: rgba(0, 0, 0, 0.08);
  margin: 4px 0;
}

.tooltip-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tooltip-section .tooltip-label {
  display: block;
  margin-bottom: 4px;
}

.tooltip-range {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 8px;
  background: rgba(255, 140, 0, 0.05);
  border-radius: 6px;
  font-size: 0.75rem;
  gap: 8px;
  white-space: nowrap;
}

.tooltip-range span:first-child {
  color: rgba(0, 0, 0, 0.7);
}

.tooltip-price {
  color: var(--md-primary);
  font-weight: 600;
  white-space: nowrap;
}

/* Laptop Responsive Styles */
@media (max-width: 1366px) {
  .order-header {
    flex-direction: row;
    align-items: center;
  }

  .impersonate-btn-small {
    font-size: 0.6875rem;
    padding: 3px 8px;
  }
}

/* Tablet Responsive Styles */
@media (max-width: 1024px) {
  .order-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .header-right {
    width: 100%;
    justify-content: space-between;
  }
  
  .phone-badge,
  .wechat-badge {
    display: inline-block;
  }
  
  .order-info-user {
    flex-wrap: wrap;
  }
}

</style>

