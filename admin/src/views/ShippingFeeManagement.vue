<template>
  <div class="shipping-fee-page">
    <div class="page-header">
      <h1>运费管理</h1>
      <p class="page-description">配置订单运费规则。不计入免运的商品价格不会计入免运费门槛计算。</p>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="config-form-container">
      <form @submit.prevent="saveConfig" class="config-form">
        <div class="form-section">
          <h2>基础运费</h2>
          <div class="form-group">
            <label>基础运费 (订单小计 < 58)</label>
            <div class="input-with-unit">
              <input 
                v-model.number="formData.base_fee" 
                type="number" 
                step="0.01" 
                min="0" 
                required 
                placeholder="7.99"
              />
              <span class="unit">$</span>
            </div>
            <small class="form-hint">订单小计低于第一个门槛时使用此运费</small>
          </div>
        </div>

        <div class="form-section">
          <h2>运费门槛 1</h2>
          <div class="form-group">
            <label>订单小计门槛</label>
            <div class="input-with-unit">
              <input 
                v-model.number="formData.threshold_1_amount" 
                type="number" 
                step="0.01" 
                min="0" 
                required 
                placeholder="58.00"
              />
              <span class="unit">$</span>
            </div>
            <small class="form-hint">订单小计达到此金额时使用门槛1的运费</small>
          </div>
          <div class="form-group">
            <label>运费</label>
            <div class="input-with-unit">
              <input 
                v-model.number="formData.threshold_1_fee" 
                type="number" 
                step="0.01" 
                min="0" 
                required 
                placeholder="5.99"
              />
              <span class="unit">$</span>
            </div>
          </div>
        </div>

        <div class="form-section">
          <h2>运费门槛 2</h2>
          <div class="form-group">
            <label>订单小计门槛</label>
            <div class="input-with-unit">
              <input 
                v-model.number="formData.threshold_2_amount" 
                type="number" 
                step="0.01" 
                min="0" 
                required 
                placeholder="128.00"
              />
              <span class="unit">$</span>
            </div>
            <small class="form-hint">订单小计达到此金额时使用门槛2的运费</small>
          </div>
          <div class="form-group">
            <label>运费</label>
            <div class="input-with-unit">
              <input 
                v-model.number="formData.threshold_2_fee" 
                type="number" 
                step="0.01" 
                min="0" 
                required 
                placeholder="3.99"
              />
              <span class="unit">$</span>
            </div>
          </div>
        </div>

        <div class="form-section">
          <h2>免运费门槛</h2>
          <div class="form-group">
            <label>订单小计门槛</label>
            <div class="input-with-unit">
              <input 
                v-model.number="formData.threshold_3_amount" 
                type="number" 
                step="0.01" 
                min="0" 
                required 
                placeholder="150.00"
              />
              <span class="unit">$</span>
            </div>
            <small class="form-hint">订单小计达到此金额时免运费</small>
          </div>
        </div>

        <div class="form-actions">
          <button type="button" @click="resetForm" class="reset-btn">重置</button>
          <button type="submit" :disabled="saving" class="save-btn">
            {{ saving ? '保存中...' : '保存配置' }}
          </button>
        </div>
      </form>

      <div class="rules-preview">
        <h3>运费规则预览</h3>
        <div class="rules-list">
          <div class="rule-item">
            <span class="rule-condition">订单小计 < ${{ formData.threshold_1_amount.toFixed(2) }}</span>
            <span class="rule-fee">运费: ${{ formData.base_fee.toFixed(2) }}</span>
          </div>
          <div class="rule-item">
            <span class="rule-condition">${{ formData.threshold_1_amount.toFixed(2) }} ≤ 订单小计 < ${{ formData.threshold_2_amount.toFixed(2) }}</span>
            <span class="rule-fee">运费: ${{ formData.threshold_1_fee.toFixed(2) }}</span>
          </div>
          <div class="rule-item">
            <span class="rule-condition">${{ formData.threshold_2_amount.toFixed(2) }} ≤ 订单小计 < ${{ formData.threshold_3_amount.toFixed(2) }}</span>
            <span class="rule-fee">运费: ${{ formData.threshold_2_fee.toFixed(2) }}</span>
          </div>
          <div class="rule-item free-shipping">
            <span class="rule-condition">订单小计 ≥ ${{ formData.threshold_3_amount.toFixed(2) }}</span>
            <span class="rule-fee">免运费</span>
          </div>
        </div>
        <p class="note">注意：不计入免运的商品价格不会计入订单小计计算</p>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'
import { useModal } from '../composables/useModal'

export default {
  name: 'ShippingFeeManagement',
  setup() {
    const { confirm, error: showError } = useModal()
    return { confirm, showError }
  },
  data() {
    return {
      loading: true,
      error: null,
      saving: false,
      formData: {
        base_fee: 7.99,
        threshold_1_amount: 58.00,
        threshold_1_fee: 5.99,
        threshold_2_amount: 128.00,
        threshold_2_fee: 3.99,
        threshold_3_amount: 150.00
      },
      originalData: null
    }
  },
  async mounted() {
    await this.fetchConfig()
  },
  methods: {
    async fetchConfig() {
      this.loading = true
      this.error = null
      try {
        const response = await apiClient.get('/admin/delivery-fee-config')
        if (response.data.config) {
          this.formData = {
            base_fee: response.data.config.base_fee || 7.99,
            threshold_1_amount: response.data.config.threshold_1_amount || 58.00,
            threshold_1_fee: response.data.config.threshold_1_fee || 5.99,
            threshold_2_amount: response.data.config.threshold_2_amount || 128.00,
            threshold_2_fee: response.data.config.threshold_2_fee || 3.99,
            threshold_3_amount: response.data.config.threshold_3_amount || 150.00
          }
          this.originalData = JSON.parse(JSON.stringify(this.formData))
        }
      } catch (error) {
        console.error('Error fetching delivery fee config:', error)
        this.error = error.response?.data?.error || '加载配置失败'
      } finally {
        this.loading = false
      }
    },
    async saveConfig() {
      // Validate thresholds are in ascending order
      if (this.formData.threshold_1_amount >= this.formData.threshold_2_amount ||
          this.formData.threshold_2_amount >= this.formData.threshold_3_amount) {
        this.showError('门槛金额必须按升序排列')
        return
      }

      this.saving = true
      this.error = null
      try {
        const response = await apiClient.put('/admin/delivery-fee-config', this.formData)
        this.originalData = JSON.parse(JSON.stringify(this.formData))
        await this.confirm('运费配置已成功更新')
        // Optionally refresh the config
        await this.fetchConfig()
      } catch (error) {
        console.error('Error saving delivery fee config:', error)
        this.error = error.response?.data?.error || '保存配置失败'
        this.showError(this.error)
      } finally {
        this.saving = false
      }
    },
    resetForm() {
      if (this.originalData) {
        this.formData = JSON.parse(JSON.stringify(this.originalData))
      } else {
        this.formData = {
          base_fee: 7.99,
          threshold_1_amount: 58.00,
          threshold_1_fee: 5.99,
          threshold_2_amount: 128.00,
          threshold_2_fee: 3.99,
          threshold_3_amount: 150.00
        }
      }
    }
  }
}
</script>

<style scoped>
.shipping-fee-page {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 8px;
}

.page-description {
  color: #666;
  font-size: 14px;
}

.loading, .error {
  text-align: center;
  padding: 40px;
  font-size: 16px;
}

.error {
  color: #d32f2f;
}

.config-form-container {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 32px;
}

.config-form {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.form-section {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid #e0e0e0;
}

.form-section:last-of-type {
  border-bottom: none;
}

.form-section h2 {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 16px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
  font-size: 14px;
}

.input-with-unit {
  position: relative;
  display: flex;
  align-items: center;
}

.input-with-unit input {
  flex: 1;
  padding: 10px 40px 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.input-with-unit input:focus {
  outline: none;
  border-color: #2196f3;
}

.unit {
  position: absolute;
  right: 12px;
  color: #666;
  font-size: 14px;
  pointer-events: none;
}

.form-hint {
  display: block;
  margin-top: 4px;
  color: #999;
  font-size: 12px;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e0e0e0;
}

.reset-btn, .save-btn {
  padding: 10px 24px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.reset-btn {
  background: #f5f5f5;
  color: #666;
}

.reset-btn:hover {
  background: #e0e0e0;
}

.save-btn {
  background: #2196f3;
  color: white;
}

.save-btn:hover:not(:disabled) {
  background: #1976d2;
}

.save-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.rules-preview {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  height: fit-content;
  position: sticky;
  top: 24px;
}

.rules-preview h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 16px;
}

.rules-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rule-item {
  padding: 12px;
  background: #f9f9f9;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.rule-item.free-shipping {
  background: #e8f5e9;
  border: 1px solid #4caf50;
}

.rule-condition {
  font-size: 13px;
  color: #666;
}

.rule-fee {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a1a;
}

.rule-item.free-shipping .rule-fee {
  color: #2e7d32;
}

.note {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e0e0e0;
  font-size: 12px;
  color: #999;
  line-height: 1.5;
}

@media (max-width: 1024px) {
  .config-form-container {
    grid-template-columns: 1fr;
  }

  .rules-preview {
    position: static;
  }
}
</style>
