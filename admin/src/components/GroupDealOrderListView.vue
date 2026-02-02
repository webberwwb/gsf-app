<template>
  <div class="order-list-view">
    <div v-if="loading" class="list-loading">
      <div class="loading-spinner">
        <svg class="spinner" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span>加载订单中...</span>
      </div>
    </div>

    <div v-else-if="orders.length === 0" class="empty-state">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
      </svg>
      <p>暂无订单</p>
    </div>

    <div v-else class="list-container">
      <GroupDealOrderListItem
        v-for="order in orders"
        :key="order.id"
        :order="order"
        @click="handleOrderClick"
        @mark-packing-complete="handleMarkPackingComplete"
      />
    </div>
  </div>
</template>

<script>
import GroupDealOrderListItem from './GroupDealOrderListItem.vue'

export default {
  name: 'GroupDealOrderListView',
  components: {
    GroupDealOrderListItem
  },
  props: {
    orders: {
      type: Array,
      required: true,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['order-click', 'mark-packing-complete'],
  methods: {
    handleOrderClick(order) {
      this.$emit('order-click', order)
    },
    handleMarkPackingComplete(order) {
      this.$emit('mark-packing-complete', order)
    }
  }
}
</script>

<style scoped>
.order-list-view {
  width: 100%;
}

.list-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 60px 20px;
  background: linear-gradient(135deg, rgba(255, 140, 0, 0.03) 0%, rgba(255, 165, 0, 0.05) 100%);
  border-radius: 12px;
  min-height: 200px;
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.spinner {
  width: 48px;
  height: 48px;
  color: var(--md-primary);
  animation: spin 1s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg) scale(1);
  }
  50% {
    transform: rotate(180deg) scale(1.1);
  }
  100% {
    transform: rotate(360deg) scale(1);
  }
}

.loading-spinner span {
  font-size: 0.875rem;
  color: var(--md-primary);
  font-weight: 600;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 12px;
  min-height: 200px;
}

.empty-state svg {
  width: 64px;
  height: 64px;
  color: rgba(0, 0, 0, 0.3);
  margin-bottom: 16px;
}

.empty-state p {
  font-size: 1rem;
  color: rgba(0, 0, 0, 0.5);
  margin: 0;
}

.list-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
