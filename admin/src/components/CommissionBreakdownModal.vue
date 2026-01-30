<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>分红明细 - {{ groupDeal.title }}</h2>
        <button @click="$emit('close')" class="close-btn">×</button>
      </div>

      <div class="modal-body">
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="error" class="error-message">{{ error }}</div>
        <div v-else-if="!commissionData || commissionData.records.length === 0" class="empty-state">
          <p>暂无提成记录</p>
          <button @click="calculateCommission" class="calculate-btn" :disabled="calculating">
            {{ calculating ? '计算中...' : '计算提成' }}
          </button>
        </div>
        <div v-else>
          <!-- Total Commission Summary -->
          <div class="commission-summary">
            <div class="summary-item">
              <span class="summary-label">总提成:</span>
              <span class="summary-value total">${{ commissionData.total_commission.toFixed(2) }}</span>
            </div>
          </div>

          <!-- Commission Records per SDR -->
          <div v-for="record in commissionData.records" :key="record.id" class="sdr-commission-card">
            <div class="sdr-header">
              <div class="sdr-info">
                <h3>{{ record.sdr.name }}</h3>
                <span class="sdr-identifier">{{ record.sdr.source_identifier }}</span>
              </div>
              <div class="sdr-total">
                <span class="total-label">提成总额:</span>
                <span class="total-value">${{ record.total_commission.toFixed(2) }}</span>
              </div>
            </div>

            <div class="commission-breakdown">
              <div class="breakdown-row summary-row">
                <div class="breakdown-item">
                  <span class="breakdown-label">自己客户提成:</span>
                  <span class="breakdown-value own">${{ record.own_customer_commission.toFixed(2) }}</span>
                </div>
                <div class="breakdown-item">
                  <span class="breakdown-label">一般客户提成:</span>
                  <span class="breakdown-value general">${{ record.general_customer_commission.toFixed(2) }}</span>
                </div>
              </div>
            </div>

            <!-- Product Details Table -->
            <div v-if="record.details && record.details.length > 0" class="product-details">
              <h4>产品明细</h4>
              <div class="table-container">
                <table class="details-table">
                  <thead>
                    <tr>
                      <th>产品</th>
                      <th>自己客户</th>
                      <th>一般客户</th>
                      <th>总计</th>
                      <th>提成</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="detail in record.details" :key="detail.product_id">
                      <td class="product-name">{{ detail.product_name }}</td>
                      <td>
                        <div v-if="detail.commission_type === 'per_item'">
                          {{ detail.own_quantity }} 只 × ${{ detail.own_rate.toFixed(2) }}
                        </div>
                        <div v-else>
                          {{ detail.own_weight ? detail.own_weight.toFixed(2) : 0 }} 磅 × ${{ detail.own_rate.toFixed(2) }}
                        </div>
                        <div class="amount">${{ detail.own_commission.toFixed(2) }}</div>
                      </td>
                      <td>
                        <div v-if="detail.commission_type === 'per_item'">
                          {{ detail.general_quantity }} 只 × ${{ detail.general_rate.toFixed(2) }}
                        </div>
                        <div v-else>
                          {{ detail.general_weight ? detail.general_weight.toFixed(2) : 0 }} 磅 × ${{ detail.general_rate.toFixed(2) }}
                        </div>
                        <div class="amount">${{ detail.general_commission.toFixed(2) }}</div>
                      </td>
                      <td>
                        <div v-if="detail.commission_type === 'per_item'">
                          {{ detail.own_quantity + detail.general_quantity }} 只
                        </div>
                        <div v-else>
                          {{ ((detail.own_weight || 0) + (detail.general_weight || 0)).toFixed(2) }} 磅
                        </div>
                      </td>
                      <td class="commission-amount">${{ detail.total_commission.toFixed(2) }}</td>
                    </tr>
                  </tbody>
                  <tfoot>
                    <tr>
                      <td colspan="4" class="total-label">总计</td>
                      <td class="total-amount">${{ record.total_commission.toFixed(2) }}</td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>

            <!-- Order Grouping for Validation -->
            <div v-if="record.order_grouping" class="order-grouping-section">
              <h4>订单分组验证</h4>
              
              <!-- Own Customer Orders -->
              <div v-if="record.order_grouping.own_customer_orders && record.order_grouping.own_customer_orders.length > 0" class="order-group own-customer-group">
                <div class="group-header">
                  <h5>自己客户订单 ({{ record.order_grouping.own_customer_orders.length }})</h5>
                  <span class="group-badge own">提成: ${{ record.own_customer_commission.toFixed(2) }}</span>
                </div>
                <div class="orders-list">
                  <div v-for="order in record.order_grouping.own_customer_orders" :key="order.order_id" class="order-card">
                    <div class="order-header">
                      <span class="order-number">订单: {{ order.order_number }}</span>
                      <span class="order-total">${{ order.total.toFixed(2) }}</span>
                    </div>
                    <div class="order-user">
                      <span class="user-name">{{ order.user_name || 'N/A' }}</span>
                      <span class="user-phone">{{ order.user_phone || 'N/A' }}</span>
                      <span v-if="order.user_source" class="user-source">来源: {{ order.user_source }}</span>
                    </div>
                    <div class="order-items">
                      <div v-for="item in order.items" :key="item.product_id" class="order-item">
                        <span class="item-name">{{ item.product_name }}</span>
                        <span class="item-details">
                          <span v-if="item.quantity">数量: {{ item.quantity }}</span>
                          <span v-if="item.weight">重量: {{ item.weight.toFixed(2) }} 磅</span>
                          <span class="item-subtotal">${{ item.subtotal ? item.subtotal.toFixed(2) : '0.00' }}</span>
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Other Customer Orders -->
              <div v-if="record.order_grouping.other_customer_orders && record.order_grouping.other_customer_orders.length > 0" class="order-group other-customer-group">
                <div class="group-header">
                  <h5>一般客户订单 ({{ record.order_grouping.other_customer_orders.length }})</h5>
                  <span class="group-badge general">提成: ${{ record.general_customer_commission.toFixed(2) }}</span>
                </div>
                <div class="orders-list">
                  <div v-for="order in record.order_grouping.other_customer_orders" :key="order.order_id" class="order-card">
                    <div class="order-header">
                      <span class="order-number">订单: {{ order.order_number }}</span>
                      <span class="order-total">${{ order.total.toFixed(2) }}</span>
                    </div>
                    <div class="order-user">
                      <span class="user-name">{{ order.user_name || 'N/A' }}</span>
                      <span class="user-phone">{{ order.user_phone || 'N/A' }}</span>
                      <span v-if="order.user_source" class="user-source">来源: {{ order.user_source }}</span>
                    </div>
                    <div class="order-items">
                      <div v-for="item in order.items" :key="item.product_id" class="order-item">
                        <span class="item-name">{{ item.product_name }}</span>
                        <span class="item-details">
                          <span v-if="item.quantity">数量: {{ item.quantity }}</span>
                          <span v-if="item.weight">重量: {{ item.weight.toFixed(2) }} 磅</span>
                          <span class="item-subtotal">${{ item.subtotal ? item.subtotal.toFixed(2) : '0.00' }}</span>
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- No Commission Orders -->
              <div v-if="record.order_grouping.no_commission_orders && record.order_grouping.no_commission_orders.length > 0" class="order-group no-commission-group">
                <div class="group-header">
                  <h5>无提成订单 - 谷语农庄 ({{ record.order_grouping.no_commission_orders.length }})</h5>
                  <span class="group-badge no-commission">无提成</span>
                </div>
                <div class="orders-list">
                  <div v-for="order in record.order_grouping.no_commission_orders" :key="order.order_id" class="order-card">
                    <div class="order-header">
                      <span class="order-number">订单: {{ order.order_number }}</span>
                      <span class="order-total">${{ order.total.toFixed(2) }}</span>
                    </div>
                    <div class="order-user">
                      <span class="user-name">{{ order.user_name || 'N/A' }}</span>
                      <span class="user-phone">{{ order.user_phone || 'N/A' }}</span>
                      <span v-if="order.user_source" class="user-source">来源: {{ order.user_source }}</span>
                    </div>
                    <div class="order-items">
                      <div v-for="item in order.items" :key="item.product_id" class="order-item">
                        <span class="item-name">{{ item.product_name }}</span>
                        <span class="item-details">
                          <span v-if="item.quantity">数量: {{ item.quantity }}</span>
                          <span v-if="item.weight">重量: {{ item.weight.toFixed(2) }} 磅</span>
                          <span class="item-subtotal">${{ item.subtotal ? item.subtotal.toFixed(2) : '0.00' }}</span>
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Manual Adjustment Section -->
            <div class="manual-adjustment-section">
              <h4>手动调整</h4>
              <div class="adjustment-form">
                <div class="adjustment-inputs">
                  <div class="adjustment-field">
                    <label>调整金额 ($):</label>
                    <input
                      type="number"
                      step="0.01"
                      v-model.number="getAdjustmentData(record.id).amount"
                      class="adjustment-input"
                      placeholder="可输入正数(奖金)或负数(扣除)"
                    />
                    <span class="adjustment-hint">
                      正数表示增加，负数表示扣除
                    </span>
                  </div>
                  <div class="adjustment-field">
                    <label>调整原因:</label>
                    <textarea
                      v-model="getAdjustmentData(record.id).notes"
                      class="adjustment-textarea"
                      placeholder="例如: 额外奖金、运费扣除等"
                      rows="2"
                    ></textarea>
                  </div>
                </div>
                <button
                  @click="saveAdjustment(record.id)"
                  class="save-adjustment-btn"
                  :disabled="savingAdjustment"
                >
                  {{ savingAdjustment ? '保存中...' : '保存调整' }}
                </button>
              </div>
              
              <!-- Show current adjustment if exists -->
              <div v-if="record.manual_adjustment !== 0" class="current-adjustment">
                <div class="adjustment-display">
                  <span class="adjustment-label">当前调整:</span>
                  <span :class="['adjustment-amount', record.manual_adjustment >= 0 ? 'positive' : 'negative']">
                    {{ record.manual_adjustment >= 0 ? '+' : '' }}${{ record.manual_adjustment.toFixed(2) }}
                  </span>
                </div>
                <div v-if="record.adjustment_notes" class="adjustment-notes">
                  <strong>原因:</strong> {{ record.adjustment_notes }}
                </div>
              </div>
            </div>

            <!-- Final Total with Adjustment -->
            <div class="final-total-section">
              <div class="final-total-row">
                <span class="final-total-label">计算提成:</span>
                <span class="final-total-value">${{ record.total_commission.toFixed(2) }}</span>
              </div>
              <div v-if="record.manual_adjustment !== 0" class="final-total-row adjustment-row">
                <span class="final-total-label">手动调整:</span>
                <span :class="['final-total-value', record.manual_adjustment >= 0 ? 'positive' : 'negative']">
                  {{ record.manual_adjustment >= 0 ? '+' : '' }}${{ record.manual_adjustment.toFixed(2) }}
                </span>
              </div>
              <div class="final-total-row total-row">
                <span class="final-total-label">最终总额:</span>
                <span class="final-total-value-large">${{ record.final_total.toFixed(2) }}</span>
              </div>
            </div>

            <!-- Payment Status -->
            <div class="payment-status">
              <div class="status-info">
                <span class="status-label">付款状态:</span>
                <span :class="['status-badge', record.payment_status]">
                  {{ getPaymentStatusLabel(record.payment_status) }}
                </span>
              </div>
              <button
                v-if="record.payment_status === 'pending'"
                @click="markAsPaid(record.id)"
                class="mark-paid-btn"
                :disabled="markingPaid"
              >
                标记为已付款
              </button>
            </div>
          </div>

          <!-- Actions -->
          <div class="modal-actions">
            <button @click="calculateCommission" class="recalculate-btn" :disabled="calculating">
              {{ calculating ? '重新计算中...' : '重新计算' }}
            </button>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button @click="$emit('close')" class="close-footer-btn">关闭</button>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'
import { useModal } from '../composables/useModal'

export default {
  name: 'CommissionBreakdownModal',
  props: {
    groupDeal: {
      type: Object,
      required: true
    }
  },
  setup() {
    const { success, error } = useModal()
    return { success, error: error }
  },
  data() {
    return {
      loading: true,
      error: null,
      calculating: false,
      markingPaid: false,
      savingAdjustment: false,
      commissionData: null,
      adjustmentData: {} // record_id -> {amount, notes}
    }
  },
  mounted() {
    this.fetchCommission()
  },
  methods: {
    async fetchCommission() {
      try {
        this.loading = true
        this.error = null

        const response = await apiClient.get(`/admin/group-deals/${this.groupDeal.id}/commission`)
        this.commissionData = response.data

        // Initialize adjustment data for each record
        if (this.commissionData && this.commissionData.records) {
          this.commissionData.records.forEach(record => {
            this.adjustmentData[record.id] = {
              amount: record.manual_adjustment || 0,
              notes: record.adjustment_notes || ''
            }
          })
        }

      } catch (err) {
        this.error = err.response?.data?.message || err.response?.data?.error || '加载提成数据失败'
        console.error('Failed to fetch commission:', err)
      } finally {
        this.loading = false
      }
    },
    async calculateCommission() {
      try {
        this.calculating = true
        this.error = null

        await apiClient.post(`/admin/group-deals/${this.groupDeal.id}/commission/calculate`, {
          recalculate: true
        })

        await this.success('提成计算成功')
        await this.fetchCommission()

      } catch (err) {
        this.error = err.response?.data?.message || err.response?.data?.error || '计算提成失败'
        await this.error(this.error)
        console.error('Failed to calculate commission:', err)
      } finally {
        this.calculating = false
      }
    },
    getAdjustmentData(recordId) {
      if (!this.adjustmentData[recordId]) {
        this.adjustmentData[recordId] = {
          amount: 0,
          notes: ''
        }
      }
      return this.adjustmentData[recordId]
    },
    async saveAdjustment(recordId) {
      try {
        this.savingAdjustment = true

        const adjustmentInfo = this.getAdjustmentData(recordId)
        
        await apiClient.put(`/admin/commission-records/${recordId}/adjustment`, {
          manual_adjustment: parseFloat(adjustmentInfo.amount || 0),
          adjustment_notes: adjustmentInfo.notes || ''
        })

        await this.success('调整保存成功')
        await this.fetchCommission()

      } catch (err) {
        await this.error(err.response?.data?.message || err.response?.data?.error || '保存调整失败')
        console.error('Failed to save adjustment:', err)
      } finally {
        this.savingAdjustment = false
      }
    },
    async markAsPaid(recordId) {
      try {
        this.markingPaid = true

        await apiClient.put(`/admin/commission-records/${recordId}/payment`, {
          payment_status: 'paid'
        })

        await this.success('已标记为已付款')
        await this.fetchCommission()

      } catch (err) {
        await this.error(err.response?.data?.message || err.response?.data?.error || '更新付款状态失败')
        console.error('Failed to mark as paid:', err)
      } finally {
        this.markingPaid = false
      }
    },
    getPaymentStatusLabel(status) {
      const labels = {
        'pending': '待付款',
        'paid': '已付款',
        'cancelled': '已取消'
      }
      return labels[status] || status
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
  z-index: 9999;
  padding: 16px;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 1100px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
  flex-shrink: 0;
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
  overflow-y: auto;
  flex: 1;
}

.loading,
.error-message,
.empty-state {
  text-align: center;
  padding: 40px;
  color: #6b7280;
}

.error-message {
  color: #dc2626;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.calculate-btn,
.recalculate-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #ff8c00 0%, #ff7700 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.calculate-btn:hover:not(:disabled),
.recalculate-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 140, 0, 0.3);
}

.calculate-btn:disabled,
.recalculate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.commission-summary {
  background: rgba(255, 140, 0, 0.05);
  border: 2px solid rgba(255, 140, 0, 0.2);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 24px;
  display: flex;
  justify-content: center;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.summary-label {
  font-size: 18px;
  font-weight: 500;
  color: #374151;
}

.summary-value.total {
  font-size: 28px;
  font-weight: 700;
  color: #ff8c00;
}

.sdr-commission-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}

.sdr-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 2px solid #e5e7eb;
}

.sdr-info h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
  color: #111827;
}

.sdr-identifier {
  font-size: 14px;
  color: #6b7280;
  padding: 4px 12px;
  background: rgba(156, 39, 176, 0.1);
  color: #9c27b0;
  border-radius: 6px;
  font-weight: 500;
}

.sdr-total {
  text-align: right;
}

.total-label {
  display: block;
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 4px;
}

.total-value {
  font-size: 24px;
  font-weight: 700;
  color: #9c27b0;
}

.commission-breakdown {
  margin-bottom: 20px;
}

.breakdown-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.summary-row {
  background: rgba(156, 39, 176, 0.05);
  padding: 16px;
  border-radius: 8px;
}

.breakdown-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.breakdown-label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.breakdown-value {
  font-size: 18px;
  font-weight: 600;
}

.breakdown-value.own {
  color: #9c27b0;
}

.breakdown-value.general {
  color: #7b1fa2;
}

.product-details {
  margin-top: 20px;
}

.product-details h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.table-container {
  overflow-x: auto;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.details-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.details-table thead {
  background: #f9fafb;
  border-bottom: 2px solid #e5e7eb;
}

.details-table th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #111827;
  white-space: nowrap;
}

.details-table tbody tr {
  border-bottom: 1px solid #e5e7eb;
}

.details-table tbody tr:hover {
  background: #f9fafb;
}

.details-table td {
  padding: 12px;
  color: #374151;
}

.product-name {
  font-weight: 500;
  color: #111827;
}

.amount {
  font-weight: 600;
  color: #9c27b0;
  margin-top: 4px;
}

.commission-amount {
  font-weight: 700;
  color: #9c27b0;
  font-size: 15px;
}

.details-table tfoot {
  background: #f9fafb;
  border-top: 2px solid #e5e7eb;
}

.details-table tfoot td {
  padding: 12px;
  font-weight: 600;
}

.details-table tfoot .total-amount {
  font-size: 16px;
  font-weight: 700;
  color: #9c27b0;
}

.payment-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

.status-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.status-badge {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
}

.status-badge.pending {
  background: rgba(251, 191, 36, 0.1);
  color: #f59e0b;
}

.status-badge.paid {
  background: rgba(34, 197, 94, 0.1);
  color: #16a34a;
}

.status-badge.cancelled {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}

.mark-paid-btn {
  padding: 8px 16px;
  background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.mark-paid-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
}

.mark-paid-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Manual Adjustment Section */
.manual-adjustment-section {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 2px solid #e5e7eb;
}

.manual-adjustment-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.adjustment-form {
  background: rgba(255, 193, 7, 0.05);
  border: 1px solid rgba(255, 193, 7, 0.2);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.adjustment-inputs {
  display: grid;
  gap: 16px;
  margin-bottom: 16px;
}

.adjustment-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.adjustment-field label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.adjustment-input {
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  color: #111827;
  background: white;
  transition: border-color 0.2s;
}

.adjustment-input:focus {
  outline: none;
  border-color: #fbbf24;
  box-shadow: 0 0 0 3px rgba(251, 191, 36, 0.1);
}

.adjustment-textarea {
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  color: #111827;
  background: white;
  font-family: inherit;
  resize: vertical;
  transition: border-color 0.2s;
}

.adjustment-textarea:focus {
  outline: none;
  border-color: #fbbf24;
  box-shadow: 0 0 0 3px rgba(251, 191, 36, 0.1);
}

.adjustment-hint {
  font-size: 12px;
  color: #6b7280;
  font-style: italic;
}

.save-adjustment-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.save-adjustment-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(251, 191, 36, 0.3);
}

.save-adjustment-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.current-adjustment {
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.3);
  border-radius: 8px;
  padding: 12px;
}

.adjustment-display {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.adjustment-label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.adjustment-amount {
  font-size: 18px;
  font-weight: 700;
}

.adjustment-amount.positive {
  color: #16a34a;
}

.adjustment-amount.negative {
  color: #dc2626;
}

.adjustment-notes {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
}

/* Final Total Section */
.final-total-section {
  background: rgba(156, 39, 176, 0.05);
  border: 2px solid rgba(156, 39, 176, 0.2);
  border-radius: 8px;
  padding: 16px;
  margin-top: 20px;
  margin-bottom: 20px;
}

.final-total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.final-total-row.adjustment-row {
  border-top: 1px solid rgba(156, 39, 176, 0.1);
  border-bottom: 1px solid rgba(156, 39, 176, 0.1);
  margin: 8px 0;
}

.final-total-row.total-row {
  padding-top: 12px;
  border-top: 2px solid rgba(156, 39, 176, 0.3);
  margin-top: 8px;
}

.final-total-label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.final-total-value {
  font-size: 16px;
  font-weight: 600;
  color: #6b7280;
}

.final-total-value.positive {
  color: #16a34a;
}

.final-total-value.negative {
  color: #dc2626;
}

.final-total-value-large {
  font-size: 24px;
  font-weight: 700;
  color: #9c27b0;
}

.modal-actions {
  margin-top: 20px;
  text-align: center;
}

.modal-footer {
  padding: 16px 24px;
  background: #f9fafb;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.close-footer-btn {
  padding: 10px 20px;
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.close-footer-btn:hover {
  background: #f3f4f6;
}

@media (max-width: 767px) {
  .modal-content {
    max-width: 100%;
    max-height: 100vh;
    border-radius: 0;
  }

  .sdr-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .breakdown-row {
    grid-template-columns: 1fr;
  }

  .table-container {
    border-radius: 0;
    margin: 0 -20px;
  }

  .details-table {
    font-size: 12px;
  }

  .details-table th,
  .details-table td {
    padding: 8px;
  }

  .payment-status {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .mark-paid-btn {
    width: 100%;
  }

  .adjustment-form {
    padding: 12px;
  }

  .save-adjustment-btn {
    width: 100%;
  }

  .final-total-section {
    padding: 12px;
  }

  .final-total-value-large {
    font-size: 20px;
  }
}

/* Order Grouping Section */
.order-grouping-section {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 2px solid #e5e7eb;
}

.order-grouping-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.order-group {
  margin-bottom: 24px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.own-customer-group {
  border-color: rgba(156, 39, 176, 0.3);
  background: rgba(156, 39, 176, 0.02);
}

.other-customer-group {
  border-color: rgba(123, 31, 162, 0.3);
  background: rgba(123, 31, 162, 0.02);
}

.no-commission-group {
  border-color: rgba(107, 114, 128, 0.3);
  background: rgba(107, 114, 128, 0.02);
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.5);
  border-bottom: 1px solid #e5e7eb;
}

.group-header h5 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #111827;
}

.group-badge {
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
}

.group-badge.own {
  background: rgba(156, 39, 176, 0.1);
  color: #9c27b0;
}

.group-badge.general {
  background: rgba(123, 31, 162, 0.1);
  color: #7b1fa2;
}

.group-badge.no-commission {
  background: rgba(107, 114, 128, 0.1);
  color: #6b7280;
}

.orders-list {
  padding: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.order-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 12px;
}

.order-card:last-child {
  margin-bottom: 0;
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f3f4f6;
}

.order-number {
  font-weight: 600;
  color: #111827;
  font-size: 14px;
}

.order-total {
  font-weight: 600;
  color: #9c27b0;
  font-size: 14px;
}

.order-user {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.user-name {
  font-weight: 500;
  color: #374151;
  font-size: 13px;
}

.user-phone {
  color: #6b7280;
  font-size: 13px;
}

.user-source {
  color: #6b7280;
  font-size: 12px;
  padding: 2px 8px;
  background: rgba(156, 39, 176, 0.1);
  border-radius: 4px;
}

.order-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.order-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  background: #f9fafb;
  border-radius: 4px;
  font-size: 13px;
}

.item-name {
  font-weight: 500;
  color: #111827;
}

.item-details {
  display: flex;
  gap: 12px;
  color: #6b7280;
}

.item-subtotal {
  font-weight: 600;
  color: #374151;
  min-width: 60px;
  text-align: right;
}

@media (max-width: 767px) {
  .order-grouping-section {
    margin-top: 16px;
    padding-top: 16px;
  }

  .group-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .order-user {
    flex-direction: column;
    gap: 4px;
  }

  .item-details {
    flex-direction: column;
    gap: 4px;
    align-items: flex-end;
  }
}
</style>
