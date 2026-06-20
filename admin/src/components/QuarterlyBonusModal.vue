<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>季度分红 - {{ sdr.name }}</h2>
        <button @click="$emit('close')" class="close-btn">×</button>
      </div>

      <div class="modal-body">
        <!-- Quarter Selection -->
        <div class="quarter-selection">
          <div class="form-group">
            <label>年份</label>
            <select v-model.number="selectedYear" class="form-select" @change="loadQuarterData">
              <option v-for="year in availableYears" :key="year" :value="year">{{ year }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>季度</label>
            <select v-model.number="selectedQuarter" class="form-select" @change="loadQuarterData">
              <option :value="1">Q1 (1-3月)</option>
              <option :value="2">Q2 (4-6月)</option>
              <option :value="3">Q3 (7-9月)</option>
              <option :value="4">Q4 (10-12月)</option>
            </select>
          </div>
          <button @click="calculateQuarterlyBonus" class="calculate-btn" :disabled="calculating">
            {{ calculating ? '计算中...' : '计算季度提成' }}
          </button>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="loading">加载中...</div>

        <!-- Error State -->
        <div v-else-if="error" class="error-message">{{ error }}</div>

        <!-- Empty State -->
        <div v-else-if="!quarterData || (!hasCommissionRecords && !hasExcludedOrders)" class="empty-state">
          <p>该季度暂无提成记录</p>
        </div>

        <!-- Quarter Data -->
        <div v-else>
          <!-- Excluded Orders Section -->
          <div v-if="hasExcludedOrders" class="excluded-orders-section">
            <div class="excluded-section-header">
              <h3>不计入提成的订单 ({{ quarterData.excluded_orders.total_excluded_orders }}笔)</h3>
              <span class="excluded-badge">排除列表</span>
            </div>
            <p class="excluded-section-description">
              以下订单来自提成排除用户，已从季度提成计算中忽略。
              计入提成金额合计 ${{ formatMoney(quarterData.excluded_orders.total_excluded_order_value) }}（商品小计 - 手动调整 - 积分抵扣，不计运费）。
            </p>

            <div class="excluded-deals-list">
              <div
                v-for="deal in quarterData.excluded_orders.group_deals"
                :key="deal.group_deal_id"
                class="excluded-deal-card"
              >
                <div class="excluded-deal-header">
                  <div>
                    <h4>{{ deal.group_deal_title }}</h4>
                    <span class="excluded-deal-meta">
                      {{ deal.order_count }} 笔排除订单 · 计入提成金额 ${{ formatMoney(deal.total_order_value) }}
                    </span>
                  </div>
                </div>

                <div class="excluded-orders-list">
                  <div
                    v-for="order in deal.orders"
                    :key="order.order_id"
                    class="excluded-order-card"
                  >
                    <div class="excluded-order-header">
                      <span class="order-number">订单: {{ order.order_number }}</span>
                      <span class="order-total">${{ formatMoney(order.order_amount ?? order.total) }}</span>
                    </div>
                    <div class="excluded-order-user">
                      <span class="user-name">{{ order.user_name || 'N/A' }}</span>
                      <span v-if="order.user_phone" class="user-phone">{{ order.user_phone }}</span>
                      <span v-if="order.user_source" class="user-source">来源: {{ order.user_source }}</span>
                      <span v-if="order.exclusion_note" class="exclusion-note">{{ order.exclusion_note }}</span>
                      <span v-if="order.adjustment_discount > 0" class="deduction-tag">
                        手动调整 -${{ formatMoney(order.adjustment_discount) }}
                      </span>
                      <span v-if="order.store_credit_applied > 0" class="deduction-tag">
                        积分 -${{ formatMoney(order.store_credit_applied) }}
                      </span>
                      <span v-if="order.commission_ratio < 1" class="deduction-tag">
                        提成 {{ formatCommissionRatio(order.commission_ratio) }}
                      </span>
                    </div>
                    <div class="excluded-order-items">
                      <div v-for="item in order.items" :key="`${order.order_id}-${item.product_id}`" class="order-item">
                        <span class="item-name">{{ item.product_name }}</span>
                        <span class="item-details">
                          <span v-if="item.quantity">数量: {{ item.quantity }}</span>
                          <span v-if="item.weight">重量: {{ item.weight.toFixed(2) }} 磅</span>
                          <span class="item-subtotal">${{ formatMoney(item.subtotal || 0) }}</span>
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Commission Records List -->
          <div v-if="hasCommissionRecords" class="commission-records-section">
            <h3>本季度提成记录 ({{ quarterData.commission_records.length }}个团购)</h3>
            <p class="commission-records-hint">
              提成金额已按各订单「商品小计 - 手动调整 - 积分抵扣」后的比例计算（不计运费）。
            </p>
            
            <div class="records-table-container">
              <table class="records-table">
                <thead>
                  <tr>
                    <th>团购标题</th>
                    <th>计算提成</th>
                    <th>手动调整 <span class="not-included-hint">(不计入)</span></th>
                    <th>最终总额</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="record in quarterData.commission_records" :key="record.commission_record_id">
                    <td class="deal-title">{{ record.group_deal_title }}</td>
                    <td class="commission-amount">${{ formatMoney(record.total_commission) }}</td>
                    <td :class="['adjustment-amount', 'not-included', record.manual_adjustment >= 0 ? 'positive' : 'negative']">
                      <span class="adjustment-value">
                        {{ record.manual_adjustment >= 0 ? '+' : '' }}${{ formatMoney(record.manual_adjustment) }}
                      </span>
                    </td>
                    <td class="final-amount">${{ formatMoney(record.final_total) }}</td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr>
                    <td colspan="3" class="total-label">季度总提成</td>
                    <td class="total-amount">${{ formatMoney(quarterData.total_commission) }}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>

          <!-- Bonus Calculation -->
          <div v-if="hasCommissionRecords" class="bonus-calculation-section">
            <h3>季度分红计算</h3>
            
            <div class="bonus-form">
              <div class="bonus-summary">
                <div class="summary-row">
                  <span class="summary-label">季度总提成:</span>
                  <span class="summary-value">${{ formatMoney(quarterData.total_commission) }}</span>
                </div>
              </div>

              <div class="percentage-input-group">
                <label>分红比例 (%)</label>
                <div class="input-with-result">
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="100"
                    v-model.number="bonusPercentage"
                    class="percentage-input"
                    placeholder="例如: 10 表示 10%"
                    @input="calculateBonusAmount"
                  />
                  <span class="percentage-symbol">%</span>
                </div>
                <span class="input-hint">输入分红比例，将根据季度总提成计算分红金额</span>
              </div>

              <div class="bonus-result">
                <div class="result-row">
                  <span class="result-label">分红金额:</span>
                  <span class="result-value">${{ formatMoney(calculatedBonusAmount) }}</span>
                </div>
                <div class="calculation-formula">
                  ${{ formatMoney(quarterData.total_commission) }} × {{ bonusPercentage }}% = ${{ formatMoney(calculatedBonusAmount) }}
                </div>
              </div>

              <button
                @click="saveQuarterlyBonus"
                class="save-bonus-btn"
                :disabled="!bonusPercentage || bonusPercentage <= 0 || saving"
              >
                {{ saving ? '保存中...' : '保存季度分红' }}
              </button>
            </div>
          </div>

          <!-- Existing Bonuses -->
          <div v-if="existingBonuses.length > 0" class="existing-bonuses-section">
            <h3>历史季度分红</h3>
            <div class="bonuses-list">
              <div v-for="bonus in existingBonuses" :key="bonus.id" class="bonus-card">
                <div class="bonus-header">
                  <div class="bonus-period">
                    <span class="bonus-year">{{ bonus.year }}</span>
                    <span class="bonus-quarter">Q{{ bonus.quarter }}</span>
                  </div>
                  <span :class="['payment-badge', bonus.payment_status]">
                    {{ getPaymentStatusLabel(bonus.payment_status) }}
                  </span>
                </div>
                <div class="bonus-details">
                  <div class="detail-row">
                    <span class="detail-label">季度总提成:</span>
                    <span class="detail-value">${{ formatMoney(bonus.total_commission) }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="detail-label">分红比例:</span>
                    <span class="detail-value">{{ bonus.bonus_percentage }}%</span>
                  </div>
                  <div class="detail-row highlight">
                    <span class="detail-label">分红金额:</span>
                    <span class="detail-value-large">${{ formatMoney(bonus.bonus_amount) }}</span>
                  </div>
                </div>
                <div v-if="bonus.payment_status === 'pending'" class="bonus-actions">
                  <button @click="markBonusAsPaid(bonus.id)" class="mark-paid-btn" :disabled="markingPaid">
                    标记为已付款
                  </button>
                  <button @click="deleteBonus(bonus.id)" class="delete-bonus-btn" :disabled="markingPaid">
                    删除
                  </button>
                </div>
              </div>
            </div>
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
import { formatOrderMoney2 } from '../utils/orderPricing'

export default {
  name: 'QuarterlyBonusModal',
  props: {
    sdr: {
      type: Object,
      required: true
    }
  },
  setup() {
    const { success, error } = useModal()
    return { success, error }
  },
  data() {
    const currentYear = new Date().getFullYear()
    const currentQuarter = Math.floor(new Date().getMonth() / 3) + 1
    
    return {
      selectedYear: currentYear,
      selectedQuarter: currentQuarter,
      availableYears: this.generateAvailableYears(),
      loading: false,
      calculating: false,
      saving: false,
      markingPaid: false,
      error: null,
      quarterData: null,
      bonusPercentage: 0,
      calculatedBonusAmount: 0,
      existingBonuses: []
    }
  },
  mounted() {
    this.loadExistingBonuses()
  },
  methods: {
    formatMoney(value) {
      return formatOrderMoney2(value)
    },
    formatCommissionRatio(ratio) {
      const pct = (Number(ratio) || 0) * 100
      return `${pct.toFixed(1)}%`
    },
    generateAvailableYears() {
      const currentYear = new Date().getFullYear()
      const years = []
      for (let i = currentYear; i >= currentYear - 5; i--) {
        years.push(i)
      }
      return years
    },
    async calculateQuarterlyBonus() {
      try {
        this.calculating = true
        this.loading = true
        this.error = null

        const response = await apiClient.post(`/admin/sdrs/${this.sdr.id}/quarterly-bonus/calculate`, {
          year: this.selectedYear,
          quarter: this.selectedQuarter
        })

        this.quarterData = response.data
        if (!this.quarterData.commission_records) {
          this.quarterData.commission_records = []
        }
        if (!this.quarterData.excluded_orders) {
          this.quarterData.excluded_orders = {
            group_deals: [],
            total_excluded_orders: 0,
            total_excluded_order_value: 0
          }
        }

        if (!this.hasCommissionRecords && !this.hasExcludedOrders) {
          this.error = '该季度暂无提成记录'
        }

      } catch (err) {
        this.error = err.response?.data?.message || err.response?.data?.error || '计算季度提成失败'
        await this.error(this.error)
        console.error('Failed to calculate quarterly bonus:', err)
      } finally {
        this.calculating = false
        this.loading = false
      }
    },
    async loadQuarterData() {
      await this.calculateQuarterlyBonus()
    },
    calculateBonusAmount() {
      if (!this.quarterData || !this.bonusPercentage) {
        this.calculatedBonusAmount = 0
        return
      }
      this.calculatedBonusAmount = this.quarterData.total_commission * (this.bonusPercentage / 100)
    },
    async saveQuarterlyBonus() {
      if (!this.bonusPercentage || this.bonusPercentage <= 0) {
        await this.error('请输入有效的分红比例')
        return
      }

      try {
        this.saving = true

        await apiClient.post(`/admin/sdrs/${this.sdr.id}/quarterly-bonus`, {
          year: this.selectedYear,
          quarter: this.selectedQuarter,
          bonus_percentage: this.bonusPercentage,
          commission_records: this.quarterData.commission_records
        })

        await this.success('季度分红保存成功')
        
        await this.loadExistingBonuses()
        this.bonusPercentage = 0
        this.calculatedBonusAmount = 0

      } catch (err) {
        await this.error(err.response?.data?.message || err.response?.data?.error || '保存季度分红失败')
        console.error('Failed to save quarterly bonus:', err)
      } finally {
        this.saving = false
      }
    },
    async loadExistingBonuses() {
      try {
        const response = await apiClient.get(`/admin/sdrs/${this.sdr.id}/quarterly-bonuses`)
        this.existingBonuses = response.data.bonuses || []
      } catch (err) {
        console.error('Failed to load existing bonuses:', err)
      }
    },
    async markBonusAsPaid(bonusId) {
      try {
        this.markingPaid = true

        await apiClient.put(`/admin/quarterly-bonuses/${bonusId}/payment`, {
          payment_status: 'paid'
        })

        await this.success('已标记为已付款')
        await this.loadExistingBonuses()

      } catch (err) {
        await this.error(err.response?.data?.message || err.response?.data?.error || '更新付款状态失败')
        console.error('Failed to mark bonus as paid:', err)
      } finally {
        this.markingPaid = false
      }
    },
    async deleteBonus(bonusId) {
      try {
        if (!confirm('确定要删除这条季度分红记录吗？')) {
          return
        }

        this.markingPaid = true

        await apiClient.delete(`/admin/quarterly-bonuses/${bonusId}`)

        await this.success('季度分红记录已删除')
        await this.loadExistingBonuses()

      } catch (err) {
        await this.error(err.response?.data?.message || err.response?.data?.error || '删除失败')
        console.error('Failed to delete bonus:', err)
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
  },
  computed: {
    hasCommissionRecords() {
      return this.quarterData?.commission_records?.length > 0
    },
    hasExcludedOrders() {
      return (this.quarterData?.excluded_orders?.total_excluded_orders || 0) > 0
    }
  },
  watch: {
    bonusPercentage() {
      this.calculateBonusAmount()
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
  max-width: 1000px;
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
  padding-top: calc(20px + env(safe-area-inset-top));
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

/* Quarter Selection */
.quarter-selection {
  display: flex;
  gap: 16px;
  align-items: flex-end;
  margin-bottom: 24px;
  padding: 20px;
  background: rgba(255, 140, 0, 0.05);
  border: 1px solid rgba(255, 140, 0, 0.2);
  border-radius: 8px;
}

.form-group {
  flex: 1;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}

.form-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  color: #111827;
  background: white;
  cursor: pointer;
  transition: border-color 0.2s;
}

.form-select:focus {
  outline: none;
  border-color: #ff8c00;
  box-shadow: 0 0 0 3px rgba(255, 140, 0, 0.1);
}

.calculate-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #ff8c00 0%, #ff7700 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.calculate-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 140, 0, 0.3);
}

.calculate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Excluded Orders Section */
.excluded-orders-section {
  background: rgba(239, 68, 68, 0.04);
  border: 2px solid rgba(239, 68, 68, 0.2);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 32px;
}

.excluded-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.excluded-section-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #991b1b;
}

.excluded-badge {
  padding: 4px 10px;
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
  border: 1px solid rgba(239, 68, 68, 0.25);
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.excluded-section-description {
  margin: 0 0 20px 0;
  font-size: 14px;
  color: #6b7280;
  line-height: 1.5;
}

.excluded-deals-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.excluded-deal-card {
  background: white;
  border: 1px solid rgba(239, 68, 68, 0.15);
  border-radius: 8px;
  overflow: hidden;
}

.excluded-deal-header {
  padding: 14px 16px;
  background: rgba(239, 68, 68, 0.05);
  border-bottom: 1px solid rgba(239, 68, 68, 0.12);
}

.excluded-deal-header h4 {
  margin: 0 0 4px 0;
  font-size: 15px;
  font-weight: 600;
  color: #111827;
}

.excluded-deal-meta {
  font-size: 13px;
  color: #6b7280;
}

.excluded-orders-list {
  display: flex;
  flex-direction: column;
}

.excluded-order-card {
  padding: 14px 16px;
  border-bottom: 1px solid #f3f4f6;
}

.excluded-order-card:last-child {
  border-bottom: none;
}

.excluded-order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.order-number {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.order-total {
  font-size: 14px;
  font-weight: 600;
  color: #dc2626;
}

.excluded-order-user {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 13px;
}

.user-name {
  font-weight: 600;
  color: #374151;
}

.user-phone,
.user-source {
  color: #6b7280;
}

.exclusion-note {
  color: #dc2626;
  font-style: italic;
}

.excluded-order-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.order-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
  color: #4b5563;
}

.item-name {
  font-weight: 500;
}

.item-details {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.item-subtotal {
  font-weight: 600;
  color: #374151;
}

/* Commission Records Section */
.commission-records-section {
  margin-bottom: 32px;
}

.commission-records-section h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.commission-records-hint {
  margin: 0 0 16px 0;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
}

.deduction-tag {
  font-size: 12px;
  color: #b45309;
  padding: 2px 8px;
  background: rgba(245, 158, 11, 0.1);
  border-radius: 4px;
}

.records-table-container {
  overflow-x: auto;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.records-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.records-table thead {
  background: #f9fafb;
  border-bottom: 2px solid #e5e7eb;
}

.records-table th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #111827;
  white-space: nowrap;
}

.records-table tbody tr {
  border-bottom: 1px solid #e5e7eb;
}

.records-table tbody tr:hover {
  background: #f9fafb;
}

.records-table td {
  padding: 12px;
  color: #374151;
}

.deal-title {
  font-weight: 500;
  color: #111827;
}

.commission-amount {
  font-weight: 600;
  color: #9c27b0;
}

.adjustment-amount {
  font-weight: 600;
}

.adjustment-amount.positive {
  color: #16a34a;
}

.adjustment-amount.negative {
  color: #dc2626;
}

.adjustment-amount.not-included .adjustment-value {
  text-decoration: line-through;
  opacity: 0.6;
}

.not-included-hint {
  font-size: 11px;
  color: #6b7280;
  font-weight: 400;
  font-style: italic;
}

.final-amount {
  font-weight: 700;
  color: #9c27b0;
  font-size: 15px;
}

.records-table tfoot {
  background: #f9fafb;
  border-top: 2px solid #e5e7eb;
}

.records-table tfoot td {
  padding: 12px;
  font-weight: 600;
}

.total-label {
  text-align: right;
  color: #374151;
}

.total-amount {
  font-size: 18px;
  font-weight: 700;
  color: #ff8c00;
}

/* Bonus Calculation Section */
.bonus-calculation-section {
  background: rgba(255, 140, 0, 0.05);
  border: 2px solid rgba(255, 140, 0, 0.2);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 32px;
}

.bonus-calculation-section h3 {
  margin: 0 0 20px 0;
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.bonus-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.bonus-summary {
  background: white;
  border: 1px solid rgba(255, 140, 0, 0.2);
  border-radius: 8px;
  padding: 16px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.summary-label {
  font-size: 16px;
  font-weight: 500;
  color: #374151;
}

.summary-value {
  font-size: 24px;
  font-weight: 700;
  color: #ff8c00;
}

.percentage-input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.percentage-input-group label {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.input-with-result {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
}

.percentage-input {
  flex: 1;
  padding: 12px 16px;
  padding-right: 40px;
  border: 2px solid #d1d5db;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  background: white;
  transition: border-color 0.2s;
}

.percentage-input:focus {
  outline: none;
  border-color: #ff8c00;
  box-shadow: 0 0 0 3px rgba(255, 140, 0, 0.1);
}

.percentage-symbol {
  position: absolute;
  right: 16px;
  font-size: 16px;
  font-weight: 600;
  color: #6b7280;
  pointer-events: none;
}

.input-hint {
  font-size: 12px;
  color: #6b7280;
  font-style: italic;
}

.bonus-result {
  background: white;
  border: 2px solid rgba(255, 140, 0, 0.3);
  border-radius: 8px;
  padding: 20px;
}

.result-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.result-label {
  font-size: 18px;
  font-weight: 600;
  color: #374151;
}

.result-value {
  font-size: 32px;
  font-weight: 700;
  color: #ff8c00;
}

.calculation-formula {
  text-align: center;
  font-size: 14px;
  color: #6b7280;
  font-family: 'Courier New', monospace;
  padding: 12px;
  background: rgba(255, 140, 0, 0.05);
  border-radius: 6px;
}

.save-bonus-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #ff8c00 0%, #ff7700 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.save-bonus-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 140, 0, 0.3);
}

.save-bonus-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Existing Bonuses Section */
.existing-bonuses-section {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 2px solid #e5e7eb;
}

.existing-bonuses-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.bonuses-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.bonus-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.bonus-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.bonus-period {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bonus-year {
  font-size: 18px;
  font-weight: 700;
  color: #111827;
}

.bonus-quarter {
  font-size: 16px;
  font-weight: 600;
  color: #ff8c00;
  padding: 4px 12px;
  background: rgba(255, 140, 0, 0.1);
  border-radius: 6px;
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

.bonus-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-row.highlight {
  padding: 12px;
  background: rgba(255, 140, 0, 0.05);
  border: 1px solid rgba(255, 140, 0, 0.2);
  border-radius: 6px;
  margin-top: 8px;
}

.detail-label {
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
}

.detail-value {
  font-size: 15px;
  font-weight: 600;
  color: #374151;
}

.detail-value-large {
  font-size: 20px;
  font-weight: 700;
  color: #ff8c00;
}

.bonus-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.mark-paid-btn {
  padding: 8px 16px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(16, 185, 129, 0.2);
}

.mark-paid-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
}

.mark-paid-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.delete-bonus-btn {
  padding: 8px 16px;
  background: #6b7280;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(107, 114, 128, 0.2);
}

.delete-bonus-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  background: #dc2626;
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
}

.delete-bonus-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

  .quarter-selection {
    flex-direction: column;
  }

  .calculate-btn {
    width: 100%;
  }

  .bonus-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .records-table {
    font-size: 12px;
  }

  .records-table th,
  .records-table td {
    padding: 8px;
  }

  .summary-value {
    font-size: 20px;
  }

  .result-value {
    font-size: 24px;
  }

  .save-bonus-btn {
    width: 100%;
  }

  .mark-paid-btn,
  .delete-bonus-btn {
    width: 100%;
  }

  .bonus-actions {
    justify-content: stretch;
  }
}
</style>
