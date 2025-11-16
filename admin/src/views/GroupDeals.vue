<template>
  <div class="group-deals-page">
    <div class="page-header-actions">
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
      <button @click="openAddModal" class="add-first-btn">创建第一个团购</button>
    </div>
    <div v-else class="deals-list">
      <div v-for="deal in groupDeals" :key="deal.id" class="deal-card">
        <div class="deal-header">
          <div class="deal-title-section">
            <h3>{{ deal.title }}</h3>
            <span :class="['status-badge', deal.status]">
              {{ getStatusLabel(deal.status) }}
            </span>
          </div>
          <div class="deal-actions">
            <button @click="editDeal(deal)" class="edit-btn">编辑</button>
            <button @click="deleteDeal(deal.id)" class="delete-btn">删除</button>
          </div>
        </div>
        
        <div v-if="deal.description" class="deal-description">
          {{ deal.description }}
        </div>
        
        <div class="deal-dates">
          <div class="date-item">
            <span class="date-label">下单时间:</span>
            <span class="date-value">
              {{ formatDateTime(deal.order_start_date) }} - {{ formatDateTime(deal.order_end_date) }}
            </span>
          </div>
          <div class="date-item">
            <span class="date-label">取货时间:</span>
            <span class="date-value">{{ formatDateTime(deal.pickup_date) }}</span>
          </div>
        </div>
        
        <div v-if="deal.products && deal.products.length > 0" class="deal-products">
          <div class="products-header">
            <span class="products-count">包含 {{ deal.products.length }} 个商品</span>
          </div>
          <div class="products-grid">
            <div v-for="product in deal.products" :key="product.id" class="product-mini-card">
              <div class="product-mini-image">
                <img v-if="product.image" :src="product.image" :alt="product.name" />
                <div v-else class="image-placeholder">🛒</div>
              </div>
              <div class="product-mini-info">
                <div class="product-mini-name">{{ product.name }}</div>
                <div class="product-mini-price">
                  <span class="deal-price">${{ product.deal_price || product.sale_price }}</span>
                  <span v-if="product.deal_price && product.sale_price && product.deal_price < product.sale_price" class="original-price">
                    ${{ product.sale_price }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Group Deal Form Modal -->
    <GroupDealForm
      :show="showAddModal"
      :deal="editingDeal"
      @close="closeModal"
      @saved="handleDealSaved"
    />
  </div>
</template>

<script>
import apiClient from '../api/client'
import GroupDealForm from '../components/GroupDealForm.vue'

export default {
  name: 'GroupDeals',
  components: {
    GroupDealForm
  },
  data() {
    return {
      loading: true,
      error: null,
      groupDeals: [],
      showAddModal: false,
      editingDeal: null
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
      this.showAddModal = true
    },
    editDeal(deal) {
      this.editingDeal = deal
      this.showAddModal = true
    },
    closeModal() {
      this.showAddModal = false
      this.editingDeal = null
    },
    async handleDealSaved() {
      await this.fetchGroupDeals()
    },
    async deleteDeal(id) {
      if (!confirm('确定要删除这个团购活动吗？')) {
        return
      }

      try {
        await apiClient.delete(`/admin/group-deals/${id}`)
        await this.fetchGroupDeals()
      } catch (error) {
        alert(error.response?.data?.message || error.response?.data?.error || '删除失败')
        console.error('Delete group deal error:', error)
      }
    },
    getStatusLabel(status) {
      const labels = {
        'upcoming': '即将开始',
        'active': '进行中',
        'closed': '已结束',
        'completed': '已完成'
      }
      return labels[status] || status
    },
    formatDateTime(dateString) {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
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
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.deal-card:hover {
  box-shadow: var(--md-elevation-2);
}

.deal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--md-spacing-md);
}

.deal-title-section {
  flex: 1;
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
}

.deal-title-section h3 {
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

.status-badge.completed {
  background: #F3E5F5;
  color: #7B1FA2;
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
  background: var(--md-primary-variant);
  color: var(--md-on-surface);
}

.edit-btn:hover {
  background: var(--md-primary);
  color: white;
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

.deal-products {
  margin-top: var(--md-spacing-md);
  padding-top: var(--md-spacing-md);
  border-top: 1px solid var(--md-surface-variant);
}

.products-header {
  margin-bottom: var(--md-spacing-md);
}

.products-count {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  font-weight: 500;
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: var(--md-spacing-md);
}

.product-mini-card {
  background: var(--md-surface-variant);
  border-radius: var(--md-radius-md);
  overflow: hidden;
}

.product-mini-image {
  width: 100%;
  height: 100px;
  background: var(--md-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.product-mini-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-placeholder {
  font-size: 2rem;
  opacity: 0.3;
}

.product-mini-info {
  padding: var(--md-spacing-sm);
}

.product-mini-name {
  font-size: var(--md-label-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-xs);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-mini-price {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-xs);
}

.deal-price {
  font-size: var(--md-body-size);
  color: #FF4444;
  font-weight: 600;
}

.original-price {
  font-size: var(--md-label-size);
  color: var(--md-outline);
  text-decoration: line-through;
}
</style>

