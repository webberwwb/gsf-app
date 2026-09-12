<template>
  <div class="group-deals-page">
    <div v-if="!isFulfillmentOnly" class="page-header-actions">
      <button @click="openAddModal" class="add-btn">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
        </svg>
        创建团购
      </button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="groupDeals.length === 0" class="empty-state">
      <p>暂无团购活动</p>
      <button v-if="!isFulfillmentOnly" @click="openAddModal" class="add-first-btn">创建第一个团购</button>
    </div>
    <div v-else class="deals-list">
      <div v-for="deal in groupDeals" :key="deal.id" class="deal-card" @click="viewDealDetail(deal.id)">
        <div class="deal-header">
          <h3 class="deal-title">{{ deal.title }}</h3>
          <span class="products-count">包含 {{ deal.products?.length || 0 }} 个产品</span>
        </div>
        <div class="deal-meta">
          <div class="deal-title-section">
            <span :class="['status-badge', deal.status]">
              {{ getStatusLabel(deal.status) }}
            </span>
            <span v-if="deal.online_payment_enabled" class="status-badge online-payment">在线支付</span>
          </div>
          <div v-if="!isFulfillmentOnly" class="deal-actions">
            <button @click.stop="editDeal(deal)" class="edit-btn">编辑</button>
            <button @click.stop="deleteDeal(deal.id)" class="delete-btn">删除</button>
          </div>
        </div>
        
        <div v-if="deal.description" class="deal-description">
          {{ deal.description }}
        </div>
        
            <div class="deal-dates">
              <div class="date-item">
                <span class="date-label">开团时间:</span>
                <span class="date-value">{{ formatDateTime(deal.order_start_date) }}</span>
              </div>
              <div class="date-item">
                <span class="date-label">截单时间:</span>
                <span class="date-value">{{ formatDateTime(deal.order_end_date) }}</span>
              </div>
              <div class="date-item">
                <span class="date-label">取货时间:</span>
                <span class="date-value">{{ formatPickupDate(deal.pickup_date) }}</span>
              </div>
            </div>
      </div>
    </div>

    <!-- Copy From Previous Deal Modal -->
    <CopyGroupDealModal
      :show="showCopyModal"
      :deals="groupDeals"
      @close="closeCopyModal"
      @select="handleCopySelect"
      @blank="handleBlankCreate"
    />

    <!-- Group Deal Form Modal -->
    <GroupDealForm
      :show="showAddModal"
      :deal="editingDeal"
      :copy-from="copyFromDeal"
      @close="closeModal"
      @saved="handleDealSaved"
    />
  </div>
</template>

<script>
import apiClient from '../api/client'
import GroupDealForm from '../components/GroupDealForm.vue'
import CopyGroupDealModal from '../components/CopyGroupDealModal.vue'
import { formatDateTimeEST_CN, formatPickupDateTime_CN } from '../utils/date'
import { useModal } from '../composables/useModal'
import { isFulfillmentOnly } from '../utils/auth'
export default {
  name: 'GroupDeals',
  components: {
    GroupDealForm,
    CopyGroupDealModal
  },
  setup() {
    const { confirm, error: showError } = useModal()
    return { confirm, showError }
  },
  computed: {
    isFulfillmentOnly() {
      return isFulfillmentOnly()
    }
  },
  data() {
    return {
      loading: true,
      error: null,
      groupDeals: [],
      showAddModal: false,
      showCopyModal: false,
      editingDeal: null,
      copyFromDeal: null
    }
  },
  mounted() {
    this.fetchGroupDeals()
  },
  methods: {
    async fetchGroupDeals() {
      try {
        this.loading = true
        this.error = null
        const response = await apiClient.get('/admin/group-deals')
        this.groupDeals = response.data.group_deals || []
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || error.message || 'Failed to load group deals'
        console.error('Failed to fetch group deals:', error)
      } finally {
        this.loading = false
      }
    },
    openAddModal() {
      this.editingDeal = null
      this.copyFromDeal = null
      if (this.groupDeals.length > 0) {
        this.showCopyModal = true
      } else {
        this.showAddModal = true
      }
    },
    closeCopyModal() {
      this.showCopyModal = false
    },
    handleCopySelect(deal) {
      this.copyFromDeal = deal
      this.showCopyModal = false
      this.showAddModal = true
    },
    handleBlankCreate() {
      this.copyFromDeal = null
      this.showCopyModal = false
      this.showAddModal = true
    },
    editDeal(deal) {
      this.editingDeal = deal
      this.copyFromDeal = null
      this.showAddModal = true
    },
    closeModal() {
      this.showAddModal = false
      this.editingDeal = null
      this.copyFromDeal = null
    },
    async handleDealSaved() {
      await this.fetchGroupDeals()
    },
    async deleteDeal(id) {
      const confirmed = await this.confirm('确定要删除这个团购活动吗？', {
        type: 'warning'
      })
      if (!confirmed) {
        return
      }

      try {
        await apiClient.delete(`/admin/group-deals/${id}`)
        await this.fetchGroupDeals()
      } catch (error) {
        await this.showError(error.response?.data?.message || error.response?.data?.error || '删除失败')
        console.error('Delete group deal error:', error)
      }
    },
    getStatusLabel(status) {
      const labels = {
        'draft': '草稿',
        'upcoming': '即将开始',
        'active': '进行中',
        'closed': '已截单',
        'preparing': '正在配货',
        'ready_for_pickup': '可以取货',
        'completed': '已完成'
      }
      return labels[status] || status
    },
    formatDateTime(dateString) {
      return formatDateTimeEST_CN(dateString) || 'N/A'
    },
    formatPickupDate(dateString) {
      return formatPickupDateTime_CN(dateString) || 'N/A'
    },
    viewDealDetail(dealId) {
      this.$router.push(`/group-deals/${dealId}`)
    }
  }
}
</script>

<style scoped>
.group-deals-page {
  max-width: 1200px;
}

.page-header-actions {
  margin-bottom: var(--md-spacing-lg);
  display: flex;
  justify-content: flex-end;
}

.add-btn {
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

.add-btn svg {
  width: 20px;
  height: 20px;
}

.add-btn:hover {
  background: #FF7F00;
  box-shadow: var(--md-elevation-3);
  transform: translateY(-2px);
}

.loading, .error, .empty-state {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.add-first-btn {
  margin-top: var(--md-spacing-md);
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

.add-first-btn:hover {
  background: #FF7F00;
  box-shadow: var(--md-elevation-3);
  transform: translateY(-2px);
}

.deals-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-lg);
}

.deal-card {
  background: #FFFFFF;
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: none;
  cursor: pointer;
}

.deal-card:hover {
  box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.16), 0px 2px 4px rgba(0, 0, 0, 0.23);
  transform: translateY(-2px);
}

.deal-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: var(--md-spacing-md);
  margin-bottom: var(--md-spacing-sm);
}

.deal-title {
  font-size: var(--md-headline-size);
  color: var(--md-on-surface);
  font-weight: 500;
  margin: 0;
  min-width: 0;
}

.products-count {
  flex-shrink: 0;
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  font-weight: 500;
  white-space: nowrap;
}

.deal-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--md-spacing-md);
  margin-bottom: var(--md-spacing-md);
}

.deal-title-section {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--md-spacing-sm);
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: var(--md-radius-xl);
  font-size: var(--md-label-size);
  font-weight: 500;
}

.status-badge.draft {
  background: #F5F5F5;
  color: #757575;
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

.status-badge.online-payment {
  background: rgba(255, 140, 0, 0.12);
  color: #E65100;
}

.deal-actions {
  display: flex;
  gap: var(--md-spacing-sm);
}

.edit-btn, .delete-btn {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: none;
  border-radius: var(--md-radius-sm);
  font-size: var(--md-label-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.edit-btn {
  background: rgba(0, 0, 0, 0.05);
  color: rgba(0, 0, 0, 0.87);
  border: 1px solid rgba(0, 0, 0, 0.12);
}

.edit-btn:hover {
  background: rgba(0, 0, 0, 0.08);
  border-color: rgba(0, 0, 0, 0.2);
}

.delete-btn {
  background: #FFEBEE;
  color: #C62828;
}

.delete-btn:hover {
  background: #C62828;
  color: white;
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
  margin-bottom: var(--md-spacing-md);
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

/* Laptop Responsive Styles */
@media (max-width: 1366px) {
  .page-header-actions {
    gap: var(--md-spacing-sm);
  }
  
  .add-btn {
    padding: var(--md-spacing-sm) var(--md-spacing-md);
    font-size: 0.875rem;
  }
  
  .deal-card {
    padding: var(--md-spacing-sm) var(--md-spacing-md);
  }
  
  .deal-title {
    font-size: 1.125rem;
  }
  
  .deal-actions {
    flex-wrap: wrap;
    gap: 6px;
  }
  
  .view-orders-btn, .view-products-btn, .edit-btn, .delete-btn {
    padding: 6px 12px;
    font-size: 0.8125rem;
  }
}

/* Mobile Responsive Styles */
@media (max-width: 767px) {
  .group-deals-page {
    max-width: 100%;
  }
  
  .page-header-actions {
    margin-bottom: var(--md-spacing-md);
  }
  
  .add-btn {
    width: 100%;
    justify-content: center;
    padding: var(--md-spacing-md);
  }
  
  .deals-list {
    gap: var(--md-spacing-md);
  }
  
  .deal-card {
    padding: var(--md-spacing-md);
  }
  
  .deal-title {
    font-size: 1.125rem;
  }

  .deal-meta {
    flex-wrap: wrap;
  }
  
  .deal-actions {
    width: 100%;
    justify-content: stretch;
  }
  
  .edit-btn, .delete-btn {
    flex: 1;
    justify-content: center;
  }
  
  .deal-dates {
    padding: var(--md-spacing-sm);
  }
  
  .date-item {
    flex-direction: column;
    gap: var(--md-spacing-xs);
  }
  
  .date-label {
    min-width: 0;
    font-size: 0.75rem;
  }
  
  .date-value {
    font-size: 0.875rem;
  }
}

/* Extra small mobile */
@media (max-width: 360px) {
  .deal-title {
    font-size: 1rem;
  }
}

</style>

