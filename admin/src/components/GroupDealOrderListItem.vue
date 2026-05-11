<template>
  <div class="order-list-item" :class="{ 'expanded': isExpanded }" @click="handleClick">
    <!-- Expand/Collapse Toggle Button -->
    <button class="toggle-expand-btn" @click.stop="toggleExpand" :title="isExpanded ? '收起' : '展开'">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <!-- Collapsed View -->
    <div v-if="!isExpanded" class="collapsed-view">
      <div class="list-item-row">
        <div class="order-number">{{ order.order_number }}</div>
        <div class="status-badges">
          <span v-if="hasMissingFinalWeight" class="missing-weight-badge" title="有按重计价商品未填写有效实际重量">
            缺称重
          </span>
          <span class="status-badge" :class="`status-${order.status}`">
            {{ getStatusText(order.status) }}
          </span>
          <span class="payment-badge" :class="`payment-${order.payment_status}`">
            {{ getPaymentStatusText(order.payment_status) }}
          </span>
        </div>
      </div>

      <div class="list-item-row list-item-row--with-pricing">
        <div class="user-info">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          <span class="user-name">{{ order.user?.nickname || 'N/A' }}</span>
          <span v-if="order.user?.phone" class="user-phone">{{ order.user.phone }}</span>
          <span v-if="order.user?.wechat" class="user-wechat">微信: {{ order.user.wechat }}</span>
        </div>
        <div class="order-pricing">
          <div class="pricing-line">
            <span class="pricing-label">订单金额</span>
            <span class="pricing-value">${{ moneyFinal(order) }}</span>
          </div>
          <div
            v-if="storeCreditApplied(order) > 0"
            class="pricing-line pricing-line--sub"
          >
            <span class="pricing-label">使用代金券</span>
            <span class="pricing-value pricing-value--credit">-${{ moneyCredit(order) }}</span>
          </div>
          <div class="pricing-line pricing-line--due">
            <span class="pricing-label">应付金额</span>
            <span class="pricing-value pricing-value--due">${{ moneyDue(order) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Expanded View -->
    <div v-else class="expanded-view">
      <div class="list-item-row">
        <div class="order-number">{{ order.order_number }}</div>
        <div class="status-badges">
          <span v-if="hasMissingFinalWeight" class="missing-weight-badge" title="有按重计价商品未填写有效实际重量">
            缺称重
          </span>
          <span class="status-badge" :class="`status-${order.status}`">
            {{ getStatusText(order.status) }}
          </span>
          <span class="payment-badge" :class="`payment-${order.payment_status}`">
            {{ getPaymentStatusText(order.payment_status) }}
          </span>
        </div>
      </div>

      <div class="list-item-row list-item-row--with-pricing">
        <div class="user-info">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          <span class="user-name">{{ order.user?.nickname || 'N/A' }}</span>
          <span v-if="order.user?.phone" class="user-phone">{{ order.user.phone }}</span>
          <span v-if="order.user?.wechat" class="user-wechat">微信: {{ order.user.wechat }}</span>
        </div>
        <div class="order-pricing">
          <div class="pricing-line">
            <span class="pricing-label">订单金额</span>
            <span class="pricing-value">${{ moneyFinal(order) }}</span>
          </div>
          <div
            v-if="storeCreditApplied(order) > 0"
            class="pricing-line pricing-line--sub"
          >
            <span class="pricing-label">使用代金券</span>
            <span class="pricing-value pricing-value--credit">-${{ moneyCredit(order) }}</span>
          </div>
          <div class="pricing-line pricing-line--due">
            <span class="pricing-label">应付金额</span>
            <span class="pricing-value pricing-value--due">${{ moneyDue(order) }}</span>
          </div>
        </div>
      </div>

      <div class="list-item-row">
        <div class="delivery-info">
          <svg v-if="order.delivery_method === 'pickup'" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
          </svg>
          <span class="delivery-method">{{ order.delivery_method === 'pickup' ? '自取' : '配送' }}</span>
          <span v-if="order.delivery_method === 'pickup'" class="location-text">
            {{ order.pickup_location || 'N/A' }}
          </span>
          <span v-else-if="order.address" class="location-text">
            {{ formatAddress(order.address) }}
          </span>
        </div>
      </div>

      <div class="list-item-row items-row" v-if="order.items && order.items.length > 0">
        <div class="items-summary">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
          </svg>
          <span class="items-count">{{ order.items.length }} 件商品</span>
        </div>
        <div class="items-list-compact">
          <span 
            v-for="(item, index) in order.items" 
            :key="item.id"
            class="item-compact">
            {{ item.product?.name || 'Unknown' }} x{{ item.quantity }}{{ index < order.items.length - 1 ? ',' : '' }}
          </span>
        </div>
      </div>

      <div class="list-item-row" v-if="order.notes">
        <div class="notes-info">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
          </svg>
          <span class="notes-text">{{ order.notes }}</span>
        </div>
      </div>

      <div class="list-item-actions" @click.stop v-if="order.status === 'preparing'">
        <button 
          @click="handleMarkPackingComplete" 
          class="quick-action-btn"
          title="标记配货完成">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>配货完成</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { orderHasMissingFinalWeight } from '../utils/orderWeightValidation'
import {
  orderFinalTotalNumber,
  orderStoreCreditAppliedNumber,
  orderAmountDueNumber,
  formatOrderMoney2
} from '../utils/orderPricing'

export default {
  name: 'GroupDealOrderListItem',
  props: {
    order: {
      type: Object,
      required: true
    }
  },
  emits: ['click', 'mark-packing-complete'],
  data() {
    return {
      isExpanded: false
    }
  },
  computed: {
    hasMissingFinalWeight() {
      return orderHasMissingFinalWeight(this.order)
    }
  },
  methods: {
    handleClick() {
      // Always emit click to open modal
      this.$emit('click', this.order)
    },
    toggleExpand() {
      // Toggle expand/collapse state
      this.isExpanded = !this.isExpanded
    },
    getStatusText(status) {
      const statusMap = {
        'submitted': '已提交',
        'confirmed': '已确认',
        'preparing': '配货中',
        'packing_complete': '配货完成',
        'ready_for_pickup': '可取货',
        'out_for_delivery': '配送中',
        'delivering': '配送中',
        'completed': '已完成',
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
      if (address.city) parts.push(address.city)
      return parts.join(', ') || 'N/A'
    },
    moneyFinal(o) {
      return formatOrderMoney2(orderFinalTotalNumber(o))
    },
    moneyCredit(o) {
      return formatOrderMoney2(orderStoreCreditAppliedNumber(o))
    },
    moneyDue(o) {
      return formatOrderMoney2(orderAmountDueNumber(o))
    },
    storeCreditApplied(o) {
      return orderStoreCreditAppliedNumber(o)
    },
    handleMarkPackingComplete() {
      this.$emit('mark-packing-complete', this.order)
    }
  }
}
</script>

<style scoped>
.order-list-item {
  position: relative;
  background: #FFFFFF;
  border-radius: 12px;
  padding: 12px 16px 12px 44px;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border-left: 4px solid transparent;
  cursor: pointer;
}

.order-list-item:hover {
  box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.16), 0px 2px 4px rgba(0, 0, 0, 0.23);
  border-left-color: var(--md-primary);
}

.order-list-item.expanded {
  border-left-color: var(--md-primary);
}

.toggle-expand-btn {
  position: absolute;
  left: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.05);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  color: rgba(0, 0, 0, 0.6);
  padding: 0;
  z-index: 10;
}

.toggle-expand-btn:hover {
  background: rgba(0, 0, 0, 0.1);
  color: var(--md-primary);
  transform: translateY(-50%) scale(1.1);
}

.toggle-expand-btn svg {
  width: 18px;
  height: 18px;
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  transform: rotate(-90deg);
}

.order-list-item.expanded .toggle-expand-btn svg {
  transform: rotate(0deg);
}

.collapsed-view,
.expanded-view {
  width: 100%;
}

.list-item-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.list-item-row:last-child {
  margin-bottom: 0;
}

.order-number {
  font-size: 0.875rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.87);
  font-family: 'Courier New', monospace;
}

.status-badges {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.missing-weight-badge,
.status-badge,
.payment-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  padding: 3px 8px;
  border-radius: 10px;
  font-size: 0.6875rem;
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
}

.missing-weight-badge {
  background: #FFEBEE;
  color: #B71C1C;
  border: 1px solid rgba(183, 28, 28, 0.25);
}

.status-badge,
.payment-badge {
  border: 1px solid color-mix(in srgb, currentColor 26%, transparent);
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

.status-delivering,
.status-out_for_delivery {
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

.user-info,
.delivery-info,
.items-summary,
.notes-info {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.user-info svg,
.delivery-info svg,
.items-summary svg,
.notes-info svg {
  width: 16px;
  height: 16px;
  color: rgba(0, 0, 0, 0.5);
  flex-shrink: 0;
}

.user-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.87);
}

.user-phone {
  font-size: 0.75rem;
  color: #1565C0;
  padding: 2px 6px;
  background: #E3F2FD;
  border-radius: 8px;
  font-weight: 500;
}

.user-wechat {
  font-size: 0.75rem;
  color: #2E7D32;
  padding: 2px 6px;
  background: #E8F5E9;
  border-radius: 8px;
  font-weight: 500;
}

.list-item-row--with-pricing {
  align-items: flex-start;
}

.order-pricing {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 4px;
  min-width: 148px;
  text-align: right;
}

.pricing-line {
  display: flex;
  justify-content: flex-end;
  align-items: baseline;
  gap: 10px;
  flex-wrap: wrap;
}

.pricing-line--sub .pricing-label,
.pricing-line--sub .pricing-value {
  font-size: 0.75rem;
}

.pricing-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.55);
}

.pricing-line--due {
  margin-top: 2px;
  padding: 6px 10px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(255, 140, 0, 0.14) 0%, rgba(255, 165, 0, 0.22) 100%);
  border: 1px solid rgba(255, 140, 0, 0.45);
  box-shadow: 0 1px 3px rgba(255, 140, 0, 0.2);
  justify-content: space-between;
}

.pricing-line--due .pricing-label {
  font-size: 0.8125rem;
  font-weight: 700;
  color: #e65100;
}

.pricing-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.87);
  font-variant-numeric: tabular-nums;
}

.pricing-value--credit {
  color: #2e7d32;
  font-weight: 600;
}

.pricing-value--due {
  font-size: 1.0625rem;
  font-weight: 800;
  color: #bf360c;
  font-variant-numeric: tabular-nums;
}

.delivery-method {
  font-size: 0.8125rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.87);
}

.location-text {
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.6);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.items-row {
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
}

.items-count {
  font-size: 0.8125rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.7);
}

.items-list-compact {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding-left: 22px;
  width: 100%;
}

.item-compact {
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.6);
  background: rgba(0, 0, 0, 0.03);
  padding: 2px 6px;
  border-radius: 6px;
}

.notes-info {
  align-items: flex-start;
}

.notes-text {
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.7);
  font-style: italic;
  background: #FFF9C4;
  padding: 4px 8px;
  border-radius: 6px;
  border-left: 2px solid #FFC107;
  flex: 1;
  word-break: break-word;
}

.list-item-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
  padding-top: 8px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.quick-action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: #E1F5FE;
  color: #01579B;
  border: 1px solid rgba(1, 87, 155, 0.2);
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  outline: none;
}

.quick-action-btn svg {
  width: 14px;
  height: 14px;
}

.quick-action-btn:hover {
  background: #B3E5FC;
  border-color: rgba(1, 87, 155, 0.4);
  transform: translateY(-1px);
  box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
}

.quick-action-btn:active {
  background: #81D4FA;
  transform: translateY(0);
}

/* Mobile Responsive Styles */
@media (max-width: 767px) {
  .order-list-item {
    padding: 12px 12px 12px 40px;
    border-radius: 10px;
  }
  
  .toggle-expand-btn {
    width: 28px;
    height: 28px;
    left: 8px;
    top: 14px;
    transform: none;
  }

  .toggle-expand-btn:hover {
    transform: scale(1.08);
  }
  
  .toggle-expand-btn svg {
    width: 16px;
    height: 16px;
  }
  
  .list-item-row {
    gap: 8px;
    margin-bottom: 6px;
    flex-wrap: wrap;
  }

  /* Stack user + pricing vertically so amounts are not cramped */
  .list-item-row--with-pricing {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .list-item-row--with-pricing .user-info {
    width: 100%;
    min-width: 0;
    align-items: flex-start;
  }

  .list-item-row--with-pricing .order-pricing {
    width: 100%;
    min-width: 0;
    max-width: 100%;
    box-sizing: border-box;
  }
  
  .order-number {
    font-size: 0.8125rem;
  }
  
  .status-badges {
    gap: 4px;
    width: 100%;
  }
  
  .status-badge,
  .payment-badge {
    font-size: 0.625rem;
    padding: 2px 6px;
  }
  
  .user-info,
  .delivery-info {
    flex-wrap: wrap;
  }
  
  .user-name {
    font-size: 0.8125rem;
  }
  
  .user-phone,
  .user-wechat {
    font-size: 0.6875rem;
    padding: 1px 5px;
  }
  
  .order-pricing {
    text-align: left;
  }

  .pricing-line {
    justify-content: space-between;
    width: 100%;
    box-sizing: border-box;
  }

  .pricing-line--due {
    padding: 8px 10px;
  }

  .pricing-line--due .pricing-label {
    flex: 1;
    min-width: 0;
  }

  .pricing-value--due {
    font-size: 1rem;
    flex-shrink: 0;
  }

  .delivery-method {
    font-size: 0.75rem;
  }
  
  .location-text {
    font-size: 0.6875rem;
    width: 100%;
  }
  
  .items-count {
    font-size: 0.75rem;
  }
  
  .items-list-compact {
    padding-left: 18px;
  }
  
  .item-compact {
    font-size: 0.6875rem;
    padding: 1px 4px;
  }
  
  .notes-text {
    font-size: 0.6875rem;
    padding: 3px 6px;
  }
  
  .quick-action-btn {
    font-size: 0.6875rem;
    padding: 5px 10px;
  }
  
  .quick-action-btn svg {
    width: 12px;
    height: 12px;
  }
}
</style>
