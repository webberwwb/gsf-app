<template>
  <div class="sales-management-page">
    <div class="page-header">
      <h2>销售管理</h2>
      <p class="page-description">管理销售代表(SDR)及其产品提成配置</p>
    </div>

    <!-- SDR Management Section -->
    <div class="sdr-section">
      <div class="sdr-header">
        <h3 class="sdr-title">👤 SDR管理 (Sales Development Representative)</h3>
        <button v-if="!sdr" @click="showCreateSdrModal = true" class="create-sdr-btn">
          + 创建SDR
        </button>
      </div>

      <div v-if="loadingSdr" class="sdr-loading">加载中...</div>
      <div v-else-if="sdr" class="sdr-content">
        <div class="sdr-info">
          <div class="sdr-info-row">
            <span class="sdr-label">当前SDR:</span>
            <span class="sdr-value">{{ sdr.name }}</span>
          </div>
          <div class="sdr-info-row">
            <span class="sdr-label">客户来源标识:</span>
            <span class="sdr-value">{{ sdr.source_identifier }}</span>
          </div>
          <div v-if="sdr.email" class="sdr-info-row">
            <span class="sdr-label">邮箱:</span>
            <span class="sdr-value">{{ sdr.email }}</span>
          </div>
          <div v-if="sdr.phone" class="sdr-info-row">
            <span class="sdr-label">电话:</span>
            <span class="sdr-value">{{ sdr.phone }}</span>
          </div>
        </div>
        <div class="sdr-actions">
          <button @click="openCommissionConfig" class="commission-config-btn">
            配置产品提成
          </button>
          <button @click="editSdr" class="edit-sdr-btn">
            编辑SDR
          </button>
        </div>
      </div>
      <div v-else class="sdr-empty">
        <p>暂无SDR信息</p>
        <button @click="createDefaultSdr" class="create-sdr-btn">创建默认SDR (花泽)</button>
      </div>
    </div>

    <!-- Commission Records Summary -->
    <div v-if="sdr" class="commission-summary-section">
      <h3 class="section-title">提成记录汇总</h3>
      <div v-if="loadingRecords" class="loading">加载中...</div>
      <div v-else-if="commissionRecords.length === 0" class="empty-state">
        <p>暂无提成记录</p>
      </div>
      <div v-else class="records-list">
        <div v-for="record in commissionRecords" :key="record.id" class="record-card">
          <div class="record-header">
            <div class="record-info">
              <h4>{{ record.group_deal?.title || `团购 #${record.group_deal_id}` }}</h4>
              <span class="record-date">{{ formatDate(record.created_at) }}</span>
            </div>
            <span :class="['payment-badge', record.payment_status]">
              {{ getPaymentStatusLabel(record.payment_status) }}
            </span>
          </div>
          <div class="record-totals">
            <div class="total-item">
              <span class="total-label">计算提成:</span>
              <span class="total-value">${{ record.total_commission.toFixed(2) }}</span>
            </div>
            <div v-if="record.manual_adjustment !== 0" class="total-item adjustment">
              <span class="total-label">手动调整:</span>
              <span :class="['total-value', record.manual_adjustment >= 0 ? 'positive' : 'negative']">
                {{ record.manual_adjustment >= 0 ? '+' : '' }}${{ record.manual_adjustment.toFixed(2) }}
              </span>
            </div>
            <div class="total-item final">
              <span class="total-label">最终总额:</span>
              <span class="total-value-large">${{ record.final_total.toFixed(2) }}</span>
            </div>
          </div>
          <div class="record-actions">
            <router-link 
              :to="`/group-deals/${record.group_deal_id}`" 
              class="view-deal-btn"
            >
              查看团购详情
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- Create SDR Modal -->
    <div v-if="showCreateSdrModal" class="modal-overlay" @click="showCreateSdrModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>创建SDR</h2>
          <button @click="showCreateSdrModal = false" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>名称 *</label>
            <input v-model="newSdr.name" type="text" class="form-input" placeholder="例如: 花泽" />
          </div>
          <div class="form-group">
            <label>客户来源标识 *</label>
            <input v-model="newSdr.source_identifier" type="text" class="form-input" placeholder="例如: 花泽" />
            <small class="form-hint">此标识将用于匹配用户的user_source字段</small>
          </div>
          <div class="form-group">
            <label>邮箱</label>
            <input v-model="newSdr.email" type="email" class="form-input" placeholder="可选" />
          </div>
          <div class="form-group">
            <label>电话</label>
            <input v-model="newSdr.phone" type="tel" class="form-input" placeholder="可选" />
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showCreateSdrModal = false" class="cancel-btn">取消</button>
          <button @click="saveNewSdr" class="confirm-btn" :disabled="!newSdr.name || !newSdr.source_identifier || savingSdr">
            {{ savingSdr ? '创建中...' : '创建' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Edit SDR Modal -->
    <div v-if="showEditSdrModal && sdr" class="modal-overlay" @click="showEditSdrModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>编辑SDR</h2>
          <button @click="showEditSdrModal = false" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>名称 *</label>
            <input v-model="editSdrData.name" type="text" class="form-input" />
          </div>
          <div class="form-group">
            <label>客户来源标识 *</label>
            <input v-model="editSdrData.source_identifier" type="text" class="form-input" />
          </div>
          <div class="form-group">
            <label>邮箱</label>
            <input v-model="editSdrData.email" type="email" class="form-input" />
          </div>
          <div class="form-group">
            <label>电话</label>
            <input v-model="editSdrData.phone" type="tel" class="form-input" />
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showEditSdrModal = false" class="cancel-btn">取消</button>
          <button @click="saveEditSdr" class="confirm-btn" :disabled="!editSdrData.name || !editSdrData.source_identifier || savingSdr">
            {{ savingSdr ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Commission Config Modal -->
    <CommissionConfigModal
      v-if="showCommissionConfigModal && sdr"
      :sdr="sdr"
      @close="closeCommissionConfig"
      @saved="fetchSdr"
    />
  </div>
</template>

<script>
import apiClient from '../api/client'
import CommissionConfigModal from '../components/CommissionConfigModal.vue'
import { useModal } from '../composables/useModal'
import { formatDateTimeEST_CN } from '../utils/date'

export default {
  name: 'SalesManagement',
  components: {
    CommissionConfigModal
  },
  setup() {
    const { confirm, success, error } = useModal()
    return { confirm, success, error }
  },
  data() {
    return {
      loadingSdr: false,
      sdr: null,
      loadingRecords: false,
      commissionRecords: [],
      showCommissionConfigModal: false,
      showCreateSdrModal: false,
      showEditSdrModal: false,
      savingSdr: false,
      newSdr: {
        name: '',
        source_identifier: '',
        email: '',
        phone: ''
      },
      editSdrData: {
        name: '',
        source_identifier: '',
        email: '',
        phone: ''
      }
    }
  },
  mounted() {
    this.fetchSdr()
    this.fetchCommissionRecords()
  },
  methods: {
    async fetchSdr() {
      try {
        this.loadingSdr = true
        const response = await apiClient.get('/admin/sdrs')
        const sdrs = response.data.sdrs || []
        // For now, just take the first SDR (since you mentioned only having one)
        this.sdr = sdrs.length > 0 ? sdrs[0] : null
      } catch (err) {
        console.error('Failed to fetch SDR:', err)
        // Don't show error to user, just log it
      } finally {
        this.loadingSdr = false
      }
    },
    async fetchCommissionRecords() {
      if (!this.sdr) return
      
      try {
        this.loadingRecords = true
        const response = await apiClient.get('/admin/commission-records', {
          params: { sdr_id: this.sdr.id }
        })
        this.commissionRecords = response.data.records || []
      } catch (err) {
        console.error('Failed to fetch commission records:', err)
      } finally {
        this.loadingRecords = false
      }
    },
    async createDefaultSdr() {
      const confirmed = await this.confirm('创建默认SDR (花泽)?', {
        type: 'info',
        title: '创建SDR'
      })
      if (!confirmed) {
        return
      }

      try {
        const response = await apiClient.post('/admin/sdrs', {
          name: '花泽',
          source_identifier: '花泽',
          is_active: true
        })
        this.sdr = response.data.sdr
        await this.success('SDR创建成功')
        this.fetchCommissionRecords()
      } catch (err) {
        await this.error(err.response?.data?.message || err.response?.data?.error || 'SDR创建失败')
        console.error('Create SDR error:', err)
      }
    },
    async saveNewSdr() {
      if (!this.newSdr.name || !this.newSdr.source_identifier) {
        await this.error('请填写名称和客户来源标识')
        return
      }

      try {
        this.savingSdr = true
        const response = await apiClient.post('/admin/sdrs', {
          name: this.newSdr.name,
          source_identifier: this.newSdr.source_identifier,
          email: this.newSdr.email || null,
          phone: this.newSdr.phone || null,
          is_active: true
        })
        this.sdr = response.data.sdr
        await this.success('SDR创建成功')
        this.showCreateSdrModal = false
        this.newSdr = { name: '', source_identifier: '', email: '', phone: '' }
        this.fetchCommissionRecords()
      } catch (err) {
        await this.error(err.response?.data?.message || err.response?.data?.error || 'SDR创建失败')
        console.error('Create SDR error:', err)
      } finally {
        this.savingSdr = false
      }
    },
    editSdr() {
      this.editSdrData = {
        name: this.sdr.name,
        source_identifier: this.sdr.source_identifier,
        email: this.sdr.email || '',
        phone: this.sdr.phone || ''
      }
      this.showEditSdrModal = true
    },
    async saveEditSdr() {
      if (!this.editSdrData.name || !this.editSdrData.source_identifier) {
        await this.error('请填写名称和客户来源标识')
        return
      }

      try {
        this.savingSdr = true
        const response = await apiClient.put(`/admin/sdrs/${this.sdr.id}`, {
          name: this.editSdrData.name,
          source_identifier: this.editSdrData.source_identifier,
          email: this.editSdrData.email || null,
          phone: this.editSdrData.phone || null
        })
        this.sdr = response.data.sdr
        await this.success('SDR更新成功')
        this.showEditSdrModal = false
        this.fetchCommissionRecords()
      } catch (err) {
        await this.error(err.response?.data?.message || err.response?.data?.error || 'SDR更新失败')
        console.error('Update SDR error:', err)
      } finally {
        this.savingSdr = false
      }
    },
    openCommissionConfig() {
      this.showCommissionConfigModal = true
    },
    closeCommissionConfig() {
      this.showCommissionConfigModal = false
    },
    formatDate(dateString) {
      return formatDateTimeEST_CN(dateString) || 'N/A'
    },
    getPaymentStatusLabel(status) {
      const labels = {
        'pending': '待付款',
        'paid': '已付款',
        'cancelled': '已取消'
      }
      return labels[status] || status
    }
  },
  watch: {
    sdr() {
      if (this.sdr) {
        this.fetchCommissionRecords()
      }
    }
  }
}
</script>

<style scoped>
.sales-management-page {
  max-width: 1200px;
  padding: var(--md-spacing-lg);
}

.page-header {
  margin-bottom: var(--md-spacing-xl);
}

.page-header h2 {
  font-size: var(--md-headline-size);
  font-weight: 600;
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-sm);
}

.page-description {
  font-size: var(--md-body-size);
  color: var(--md-on-surface-variant);
}

/* SDR Section */
.sdr-section {
  background: linear-gradient(135deg, rgba(255, 140, 0, 0.05) 0%, rgba(255, 140, 0, 0.02) 100%);
  border: 2px solid rgba(255, 140, 0, 0.2);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  margin-bottom: var(--md-spacing-xl);
}

.sdr-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--md-spacing-md);
}

.sdr-title {
  font-size: var(--md-title-size);
  font-weight: 600;
  color: var(--md-on-surface);
  margin: 0;
}

.sdr-loading {
  text-align: center;
  padding: var(--md-spacing-md);
  color: var(--md-on-surface-variant);
}

.sdr-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--md-spacing-lg);
  flex-wrap: wrap;
}

.sdr-info {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
  flex: 1;
}

.sdr-info-row {
  display: flex;
  gap: var(--md-spacing-sm);
  align-items: center;
}

.sdr-label {
  font-size: var(--md-body-size);
  font-weight: 500;
  color: var(--md-on-surface-variant);
}

.sdr-value {
  font-size: var(--md-body-size);
  font-weight: 600;
  color: var(--md-primary);
}

.sdr-actions {
  display: flex;
  gap: var(--md-spacing-sm);
  flex-wrap: wrap;
}

.commission-config-btn,
.edit-sdr-btn,
.create-sdr-btn {
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition-fast);
  white-space: nowrap;
}

.commission-config-btn {
  background: var(--gradient-primary);
  color: white;
}

.commission-config-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 140, 0, 0.3);
}

.edit-sdr-btn {
  background: rgba(33, 150, 243, 0.1);
  color: #2196F3;
  border: 1px solid rgba(33, 150, 243, 0.3);
}

.edit-sdr-btn:hover {
  background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
  color: white;
  border-color: transparent;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
}

.create-sdr-btn {
  background: var(--gradient-primary);
  color: white;
}

.create-sdr-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 140, 0, 0.3);
}

.sdr-empty {
  text-align: center;
  padding: var(--md-spacing-lg);
}

.sdr-empty p {
  color: var(--md-on-surface-variant);
  margin-bottom: var(--md-spacing-md);
}

/* Commission Summary Section */
.commission-summary-section {
  margin-top: var(--md-spacing-xl);
}

.section-title {
  font-size: var(--md-title-size);
  font-weight: 600;
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-lg);
}

.loading,
.empty-state {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.record-card {
  background: white;
  border: 1px solid var(--md-outline-variant);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
  transition: var(--transition-normal);
}

.record-card:hover {
  box-shadow: var(--md-elevation-2);
  transform: translateY(-2px);
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--md-spacing-md);
  padding-bottom: var(--md-spacing-md);
  border-bottom: 1px solid var(--md-outline-variant);
}

.record-info h4 {
  margin: 0 0 var(--md-spacing-xs) 0;
  font-size: var(--md-body-size);
  font-weight: 600;
  color: var(--md-on-surface);
}

.record-date {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.payment-badge {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
}

.payment-badge.pending {
  background: rgba(251, 191, 36, 0.1);
  color: #f59e0b;
}

.payment-badge.paid {
  background: rgba(34, 197, 94, 0.1);
  color: #16a34a;
}

.payment-badge.cancelled {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}

.record-totals {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
  margin-bottom: var(--md-spacing-md);
}

.total-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.total-item.adjustment {
  padding: var(--md-spacing-xs) 0;
  border-top: 1px solid var(--md-outline-variant);
  border-bottom: 1px solid var(--md-outline-variant);
}

.total-item.final {
  padding-top: var(--md-spacing-sm);
  border-top: 2px solid var(--md-primary);
  margin-top: var(--md-spacing-xs);
}

.total-label {
  font-size: var(--md-body-size);
  font-weight: 500;
  color: var(--md-on-surface-variant);
}

.total-value {
  font-size: var(--md-body-size);
  font-weight: 600;
  color: var(--md-on-surface);
}

.total-value.positive {
  color: #16a34a;
}

.total-value.negative {
  color: #dc2626;
}

.total-value-large {
  font-size: var(--md-title-size);
  font-weight: 700;
  color: var(--md-primary);
}

.record-actions {
  display: flex;
  gap: var(--md-spacing-sm);
}

.view-deal-btn {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  background: rgba(156, 39, 176, 0.1);
  color: #9c27b0;
  border: 1px solid rgba(156, 39, 176, 0.3);
  border-radius: var(--md-radius-md);
  font-size: var(--md-label-size);
  font-weight: 500;
  text-decoration: none;
  transition: var(--transition-fast);
  display: inline-block;
}

.view-deal-btn:hover {
  background: linear-gradient(135deg, #9c27b0 0%, #7b1fa2 100%);
  color: white;
  border-color: transparent;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(156, 39, 176, 0.3);
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
  z-index: 9999;
  padding: 16px;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 500px;
  width: 100%;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  padding-top: calc(20px + env(safe-area-inset-top));
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  color: #6b7280;
  font-size: 24px;
  line-height: 1;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #111827;
}

.modal-body {
  padding: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  color: #111827;
  background: white;
  transition: border-color 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #ff8c00;
  box-shadow: 0 0 0 3px rgba(255, 140, 0, 0.1);
}

.form-hint {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}

.modal-footer {
  padding: 16px 24px;
  background: #f9fafb;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  border-top: 1px solid #e5e7eb;
}

.cancel-btn,
.confirm-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.cancel-btn:hover {
  background: #f3f4f6;
}

.confirm-btn {
  background: linear-gradient(135deg, #ff8c00 0%, #ff7700 100%);
  color: white;
}

.confirm-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 140, 0, 0.3);
}

.confirm-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 1366px) {
  .sales-management-page {
    padding: var(--md-spacing-md);
  }
  
  .sdr-card {
    padding: var(--md-spacing-md);
  }
  
  .sdr-name {
    font-size: 1.125rem;
  }
  
  .commission-config-btn,
  .edit-sdr-btn,
  .create-sdr-btn {
    padding: 8px 16px;
    font-size: 0.875rem;
  }
  
  .sdr-actions {
    gap: 6px;
  }
}

@media (max-width: 767px) {
  .sales-management-page {
    padding: var(--md-spacing-md);
  }

  .sdr-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .sdr-actions {
    width: 100%;
  }

  .commission-config-btn,
  .edit-sdr-btn,
  .create-sdr-btn {
    width: 100%;
  }
}
</style>
