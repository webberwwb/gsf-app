<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>产品提成配置 - {{ sdr.name }}</h2>
        <button @click="$emit('close')" class="close-btn">×</button>
      </div>

      <div class="modal-body">
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="error" class="error-message">{{ error }}</div>
        <div v-else>
          <div class="commission-info">
            <p class="info-text">
              <strong>说明:</strong> 设置每个产品的提成金额。
              <span class="info-highlight">自己客户</span> 指用户来源为 "{{ sdr.source_identifier }}" 的客户，
              <span class="info-highlight">一般客户</span> 指其他来源的客户。
            </p>
            <p class="info-text">
              • 按件产品: 提成按数量计算 (例如: 水鸭 $6/只)<br>
              • 按重量产品: 提成按重量计算 (例如: 羊肉 $3/磅)
            </p>
          </div>

          <div class="table-container">
            <table class="commission-table">
              <thead>
                <tr>
                  <th>产品名称</th>
                  <th>产品计价方式</th>
                  <th>提成计算方式</th>
                  <th>自己客户 ($)</th>
                  <th>一般客户 ($)</th>
                  <th>单位</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="product in products" :key="product.id" :class="{ 'has-rule': hasRule(product.id) }">
                  <td class="product-name">{{ product.name }}</td>
                  <td>{{ getPricingTypeLabel(product.pricing_type) }}</td>
                  <td>
                    <select
                      v-model="getRuleData(product.id).commission_type"
                      class="commission-type-select"
                    >
                      <option value="per_item">按件</option>
                      <option value="per_weight">按重量</option>
                    </select>
                  </td>
                  <td>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      v-model.number="getRuleData(product.id).own_customer_amount"
                      class="amount-input"
                      placeholder="0.00"
                    />
                  </td>
                  <td>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      v-model.number="getRuleData(product.id).general_customer_amount"
                      class="amount-input"
                      placeholder="0.00"
                    />
                  </td>
                  <td>{{ getUnitLabel(getRuleData(product.id).commission_type) }}</td>
                  <td>
                    <button
                      v-if="hasRule(product.id)"
                      @click="clearRule(product.id)"
                      class="clear-btn"
                      title="清除"
                    >
                      清除
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button @click="$emit('close')" class="cancel-btn">取消</button>
        <button @click="saveRules" class="save-btn" :disabled="saving">
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'
import { useModal } from '../composables/useModal'

export default {
  name: 'CommissionConfigModal',
  props: {
    sdr: {
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
      saving: false,
      products: [],
      rules: {}, // product_id -> {own_customer_amount, general_customer_amount}
      existingRules: {} // Store original rules
    }
  },
  mounted() {
    this.fetchData()
  },
  methods: {
    async fetchData() {
      try {
        this.loading = true
        this.error = null

        // Fetch products and existing commission rules
        const [productsResponse, rulesResponse] = await Promise.all([
          apiClient.get('/admin/products'),
          apiClient.get(`/admin/sdrs/${this.sdr.id}/commission-rules`)
        ])

        this.products = productsResponse.data.products || []
        const existingRules = rulesResponse.data.rules || []

        // Build rules map
        this.rules = {}
        this.existingRules = {}
        
        existingRules.forEach(rule => {
          this.rules[rule.product_id] = {
            commission_type: rule.commission_type || 'per_item',
            own_customer_amount: parseFloat(rule.own_customer_amount || 0),
            general_customer_amount: parseFloat(rule.general_customer_amount || 0)
          }
          this.existingRules[rule.product_id] = { ...this.rules[rule.product_id] }
        })

      } catch (err) {
        this.error = err.response?.data?.message || err.response?.data?.error || '加载失败'
        console.error('Failed to fetch commission data:', err)
      } finally {
        this.loading = false
      }
    },
    hasRule(productId) {
      return this.rules[productId] &&
        (this.rules[productId].own_customer_amount > 0 || this.rules[productId].general_customer_amount > 0)
    },
    getRuleData(productId) {
      if (!this.rules[productId]) {
        this.rules[productId] = {
          commission_type: 'per_item',
          own_customer_amount: 0,
          general_customer_amount: 0
        }
      }
      return this.rules[productId]
    },
    clearRule(productId) {
      this.rules[productId] = {
        commission_type: 'per_item',
        own_customer_amount: 0,
        general_customer_amount: 0
      }
    },
    getPricingTypeLabel(pricingType) {
      const labels = {
        'per_item': '按件',
        'unit_weight': '按重量',
        'bundled_weight': '按重量(捆绑)',
        'weight_range': '重量范围'
      }
      return labels[pricingType] || pricingType
    },
    getUnitLabel(commissionType) {
      // Use commission_type instead of product pricing_type
      if (commissionType === 'per_weight') {
        return '每磅'
      }
      return '每只'
    },
        async saveRules() {
          try {
            this.saving = true

            // Prepare rules to save (only non-zero amounts)
            const rulesToSave = []
            Object.keys(this.rules).forEach(productId => {
              const rule = this.rules[productId]

              // Handle empty/NaN values - treat as 0
              const safeOwnAmount = parseFloat(rule.own_customer_amount) || 0
              const safeGeneralAmount = parseFloat(rule.general_customer_amount) || 0

              if (safeOwnAmount > 0 || safeGeneralAmount > 0) {
                rulesToSave.push({
                  product_id: parseInt(productId),
                  commission_type: rule.commission_type || 'per_item',
                  own_customer_amount: safeOwnAmount,
                  general_customer_amount: safeGeneralAmount,
                  is_active: true
                })
              }
            })

            // Batch update
            await apiClient.post(`/admin/sdrs/${this.sdr.id}/commission-rules/batch`, {
              rules: rulesToSave
            })

            await this.success('提成配置保存成功')
            this.$emit('saved')
            this.$emit('close')

          } catch (err) {
            await this.error(err.response?.data?.message || err.response?.data?.error || '保存失败')
            console.error('Failed to save commission rules:', err)
          } finally {
            this.saving = false
          }
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
.error-message {
  text-align: center;
  padding: 40px;
  color: #6b7280;
}

.error-message {
  color: #dc2626;
}

.commission-info {
  background: rgba(255, 140, 0, 0.05);
  border: 1px solid rgba(255, 140, 0, 0.2);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 24px;
}

.info-text {
  margin: 8px 0;
  font-size: 14px;
  color: #374151;
  line-height: 1.6;
}

.info-highlight {
  font-weight: 600;
  color: #ff8c00;
}

.table-container {
  overflow-x: auto;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.commission-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.commission-table thead {
  background: #f9fafb;
  border-bottom: 2px solid #e5e7eb;
}

.commission-table th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #111827;
  white-space: nowrap;
}

.commission-table tbody tr {
  border-bottom: 1px solid #e5e7eb;
  transition: background 0.2s;
}

.commission-table tbody tr:hover {
  background: #f9fafb;
}

.commission-table tbody tr.has-rule {
  background: rgba(255, 140, 0, 0.03);
}

.commission-table tbody tr.has-rule:hover {
  background: rgba(255, 140, 0, 0.08);
}

.commission-table td {
  padding: 12px;
  color: #374151;
}

.product-name {
  font-weight: 500;
  color: #111827;
}

.amount-input {
  width: 100px;
  padding: 8px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.amount-input:focus {
  outline: none;
  border-color: #ff8c00;
  box-shadow: 0 0 0 3px rgba(255, 140, 0, 0.1);
}

.commission-type-select {
  width: 100px;
  padding: 8px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  background: white;
  color: #111827;
  cursor: pointer;
  transition: border-color 0.2s;
}

.commission-type-select:hover {
  border-color: #9ca3af;
}

.commission-type-select:focus {
  outline: none;
  border-color: #ff8c00;
  box-shadow: 0 0 0 3px rgba(255, 140, 0, 0.1);
}

.clear-btn {
  padding: 6px 12px;
  background: rgba(220, 38, 38, 0.1);
  color: #dc2626;
  border: 1px solid rgba(220, 38, 38, 0.2);
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.clear-btn:hover {
  background: #dc2626;
  color: white;
  border-color: transparent;
}

.modal-footer {
  padding: 16px 24px;
  background: #f9fafb;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  border-top: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.cancel-btn,
.save-btn {
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

.save-btn {
  background: linear-gradient(135deg, #ff8c00 0%, #ff7700 100%);
  color: white;
}

.save-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 140, 0, 0.3);
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 767px) {
  .modal-content {
    max-width: 100%;
    max-height: 100vh;
    border-radius: 0;
  }

  .table-container {
    border-radius: 0;
    margin: 0 -24px;
  }

  .commission-table {
    font-size: 12px;
  }

  .commission-table th,
  .commission-table td {
    padding: 8px;
  }

  .amount-input {
    width: 80px;
    padding: 6px;
    font-size: 12px;
  }

  .commission-type-select {
    width: 90px;
    padding: 6px;
    font-size: 12px;
  }
}
</style>
