<template>
  <div v-if="show" class="modal-overlay" @click.self="close">
    <div class="modal-container">
      <div class="modal-header">
        <h2>复制团购</h2>
        <button @click="close" class="close-btn">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="modal-body">
        <p class="modal-hint">选择要复制的团购，描述和商品将自动填入新团购</p>

        <div class="search-box">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索团购标题..."
            class="search-input"
          />
        </div>

        <div v-if="filteredDeals.length === 0" class="empty-state">
          <p>{{ searchQuery ? '未找到匹配的团购' : '暂无历史团购可复制' }}</p>
        </div>

        <div v-else class="deals-list">
          <button
            v-for="deal in filteredDeals"
            :key="deal.id"
            type="button"
            class="deal-item"
            @click="selectDeal(deal)"
          >
            <div class="deal-item-header">
              <span class="deal-title">{{ deal.title }}</span>
              <span :class="['status-badge', deal.status]">{{ getStatusLabel(deal.status) }}</span>
            </div>
            <p v-if="deal.description" class="deal-description">{{ deal.description }}</p>
            <div class="deal-meta">
              <span>{{ formatDateTime(deal.order_start_date) }}</span>
              <span class="meta-separator">·</span>
              <span>{{ deal.products?.length || 0 }} 个商品</span>
            </div>
          </button>
        </div>
      </div>

      <div class="modal-footer">
        <button type="button" @click="close" class="cancel-btn">取消</button>
        <button type="button" @click="startBlank" class="blank-btn">空白创建</button>
      </div>
    </div>
  </div>
</template>

<script>
import { formatDateTimeEST_CN } from '../utils/date'

export default {
  name: 'CopyGroupDealModal',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    deals: {
      type: Array,
      default: () => []
    }
  },
  emits: ['close', 'select', 'blank'],
  data() {
    return {
      searchQuery: ''
    }
  },
  computed: {
    filteredDeals() {
      const query = this.searchQuery.trim().toLowerCase()
      if (!query) return this.deals
      return this.deals.filter(deal =>
        deal.title?.toLowerCase().includes(query) ||
        deal.description?.toLowerCase().includes(query)
      )
    }
  },
  watch: {
    show(newVal) {
      if (newVal) {
        this.searchQuery = ''
      }
    }
  },
  methods: {
    getStatusLabel(status) {
      const labels = {
        draft: '草稿',
        upcoming: '即将开始',
        active: '进行中',
        closed: '已截单',
        preparing: '正在配货',
        ready_for_pickup: '可以取货',
        completed: '已完成'
      }
      return labels[status] || status
    },
    formatDateTime(dateString) {
      return formatDateTimeEST_CN(dateString) || 'N/A'
    },
    selectDeal(deal) {
      this.$emit('select', deal)
    },
    startBlank() {
      this.$emit('blank')
    },
    close() {
      this.$emit('close')
    }
  }
}
</script>

<style scoped>
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

.modal-container {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  max-width: 560px;
  width: 100%;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--md-elevation-4);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  padding-top: calc(var(--md-spacing-md) + env(safe-area-inset-top));
  background: rgb(255, 140, 0);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: var(--md-radius-lg) var(--md-radius-lg) 0 0;
  flex-shrink: 0;
  position: relative;
}

.modal-header::before {
  content: '';
  position: absolute;
  top: calc(-1 * env(safe-area-inset-top));
  left: 0;
  right: 0;
  height: env(safe-area-inset-top);
  background: rgb(255, 140, 0);
}

.modal-header h2 {
  font-size: var(--md-title-size);
  color: #fff;
  font-weight: 600;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: var(--md-spacing-xs);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--md-radius-sm);
}

.close-btn svg {
  width: 24px;
  height: 24px;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.modal-body {
  padding: var(--md-spacing-lg);
  overflow-y: auto;
  flex: 1;
}

.modal-hint {
  margin: 0 0 var(--md-spacing-md);
  color: var(--md-on-surface-variant);
  font-size: var(--md-label-size);
}

.search-box {
  margin-bottom: var(--md-spacing-md);
}

.search-input {
  width: 100%;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  background: var(--md-surface);
  color: var(--md-on-surface);
  box-sizing: border-box;
}

.search-input:focus {
  outline: none;
  border-color: var(--md-primary);
  box-shadow: 0 0 0 4px rgba(255, 140, 0, 0.12);
}

.empty-state {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.deals-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
}

.deal-item {
  display: block;
  width: 100%;
  text-align: left;
  padding: var(--md-spacing-md);
  background: var(--md-surface-variant);
  border: 1.5px solid transparent;
  border-radius: var(--md-radius-md);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.deal-item:hover {
  border-color: var(--md-primary);
  background: rgba(255, 140, 0, 0.05);
}

.deal-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--md-spacing-sm);
  margin-bottom: var(--md-spacing-xs);
}

.deal-title {
  font-weight: 500;
  color: var(--md-on-surface);
  font-size: var(--md-body-size);
}

.status-badge {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: var(--md-radius-xl);
  font-size: 0.7rem;
  font-weight: 500;
  flex-shrink: 0;
}

.status-badge.draft { background: #F5F5F5; color: #757575; }
.status-badge.upcoming { background: #E3F2FD; color: #1976D2; }
.status-badge.active { background: #E8F5E9; color: #2E7D32; }
.status-badge.closed { background: #FFF3E0; color: #F57C00; }
.status-badge.preparing { background: #F3E5F5; color: #7B1FA2; }
.status-badge.ready_for_pickup { background: #E8F5E9; color: #2E7D32; }
.status-badge.completed { background: #F3E5F5; color: #7B1FA2; }

.deal-description {
  margin: 0 0 var(--md-spacing-xs);
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.4;
}

.deal-meta {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.meta-separator {
  margin: 0 0.25rem;
}

.modal-footer {
  display: flex;
  gap: var(--md-spacing-md);
  justify-content: flex-end;
  padding: var(--md-spacing-lg);
  border-top: 1px solid var(--md-surface-variant);
  flex-shrink: 0;
}

.cancel-btn,
.blank-btn {
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.cancel-btn {
  background: var(--md-surface-variant);
  color: var(--md-on-surface);
}

.cancel-btn:hover {
  background: var(--md-outline);
  color: white;
}

.blank-btn {
  background: var(--md-primary);
  color: white;
  box-shadow: var(--md-elevation-2);
}

.blank-btn:hover {
  background: #FF7F00;
  box-shadow: var(--md-elevation-3);
}

@media (max-width: 768px) {
  .modal-overlay {
    padding: 0;
    align-items: flex-start;
  }

  .modal-container {
    max-width: 100%;
    max-height: 100vh;
    border-radius: 0;
    min-height: 100vh;
  }

  .modal-header {
    border-radius: 0;
  }

  .modal-footer {
    flex-direction: column-reverse;
  }

  .cancel-btn,
  .blank-btn {
    width: 100%;
  }
}
</style>
