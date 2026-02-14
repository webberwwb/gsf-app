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
        <div class="tiers-header">
          <h2>运费档次</h2>
          <button type="button" @click="addTier" class="add-tier-btn">
            + 添加档次
          </button>
        </div>

        <div class="tiers-list">
          <div v-for="(tier, index) in formData.tiers" :key="index" class="tier-item">
            <div class="tier-header">
              <h3>{{ getTierTitle(index) }}</h3>
              <button 
                v-if="canRemoveTier(index)" 
                type="button" 
                @click="removeTier(index)" 
                class="remove-tier-btn"
                title="删除此档次"
              >
                ✕
              </button>
            </div>
            
            <div class="tier-fields">
              <div class="form-group">
                <label>订单小计门槛</label>
                <div class="input-with-unit">
                  <input 
                    v-model.number="tier.threshold" 
                    type="number" 
                    step="0.01" 
                    min="0" 
                    required
                    :disabled="index === 0"
                    placeholder="0.00"
                  />
                  <span class="unit">$</span>
                </div>
                <small v-if="index === 0" class="form-hint">基础运费 (门槛固定为 $0)</small>
                <small v-else class="form-hint">订单小计达到此金额时使用此档次的运费</small>
              </div>
              
              <div class="form-group">
                <label>运费</label>
                <div class="input-with-unit">
                  <input 
                    v-model.number="tier.fee" 
                    type="number" 
                    step="0.01" 
                    min="0" 
                    required 
                    placeholder="0.00"
                  />
                  <span class="unit">$</span>
                </div>
                <small v-if="tier.fee === 0 && index > 0" class="form-hint">设为 $0 即免运费</small>
              </div>
            </div>
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
        <h2>规则预览</h2>
        <div class="preview-content">
          <div v-for="(tier, index) in sortedTiers" :key="index" class="preview-item">
            <div class="preview-condition">
              <span v-if="index === 0">订单小计 &lt; {{ formatPrice(getNextThreshold(index)) }}</span>
              <span v-else-if="index === sortedTiers.length - 1">
                订单小计 ≥ {{ formatPrice(tier.threshold) }}
              </span>
              <span v-else>
                {{ formatPrice(tier.threshold) }} ≤ 订单小计 &lt; {{ formatPrice(getNextThreshold(index)) }}
              </span>
            </div>
            <div class="preview-fee">
              <span v-if="tier.fee === 0" class="free-fee">免运费</span>
              <span v-else>运费: ${{ formatPrice(tier.fee) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '@/api/client'
import { useModal } from '@/composables/useModal'

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
        tiers: [
          { threshold: 0, fee: 7.99 },
          { threshold: 58.00, fee: 5.99 },
          { threshold: 128.00, fee: 3.99 },
          { threshold: 150.00, fee: 0 }
        ]
      },
      originalData: null
    }
  },
  computed: {
    sortedTiers() {
      // Return a sorted copy of tiers for preview, ensuring values are valid numbers
      return [...this.formData.tiers].map(tier => ({
        threshold: parseFloat(tier.threshold) || 0,
        fee: parseFloat(tier.fee) || 0
      })).sort((a, b) => a.threshold - b.threshold)
    }
  },
  async mounted() {
    await this.fetchConfig()
  },
  methods: {
    getTierTitle(index) {
      if (index === 0) {
        return '基础运费'
      }
      return `运费档次 ${index}`
    },
    canRemoveTier(index) {
      // Can't remove the base tier (index 0), and need at least 1 tier
      return index > 0 && this.formData.tiers.length > 1
    },
    addTier() {
      // Add a new tier with threshold higher than the last one
      const lastTier = this.sortedTiers[this.sortedTiers.length - 1]
      const newThreshold = lastTier ? lastTier.threshold + 10 : 0
      
      this.formData.tiers.push({
        threshold: newThreshold,
        fee: 0
      })
    },
    removeTier(index) {
      if (this.canRemoveTier(index)) {
        this.formData.tiers.splice(index, 1)
      }
    },
    getNextThreshold(index) {
      if (index < this.sortedTiers.length - 1) {
        return this.sortedTiers[index + 1].threshold
      }
      return null
    },
    formatPrice(value) {
      // Handle empty or invalid values gracefully
      if (value === null || value === undefined || value === '' || isNaN(value)) {
        return '0.00'
      }
      return Number(value).toFixed(2)
    },
    async fetchConfig() {
      this.loading = true
      this.error = null
      try {
        const response = await apiClient.get('/admin/delivery-fee-config')
        if (response.data.config && response.data.config.tiers) {
          this.formData.tiers = response.data.config.tiers.map(tier => ({
            threshold: tier.threshold || 0,
            fee: tier.fee || 0
          }))
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
      // Sanitize tier values first - handle empty/NaN inputs
      this.formData.tiers = this.formData.tiers.map(tier => ({
        threshold: parseFloat(tier.threshold) || 0,
        fee: parseFloat(tier.fee) || 0
      }))
      
      // Validate tiers are in ascending order
      const sortedTiers = [...this.formData.tiers].sort((a, b) => a.threshold - b.threshold)
      
      // Check for duplicate thresholds
      const thresholds = sortedTiers.map(t => t.threshold)
      const uniqueThresholds = new Set(thresholds)
      if (thresholds.length !== uniqueThresholds.size) {
        this.showError('门槛金额不能重复')
        return
      }
      
      // Check if first tier has threshold 0
      if (sortedTiers[0].threshold !== 0) {
        this.showError('第一个档次必须是基础运费(门槛为 $0)')
        return
      }

      // Validate ascending order
      for (let i = 1; i < sortedTiers.length; i++) {
        if (sortedTiers[i].threshold <= sortedTiers[i-1].threshold) {
          this.showError('门槛金额必须按升序排列')
          return
        }
      }

      this.saving = true
      this.error = null
      try {
        // Send sorted tiers to backend
        const response = await apiClient.put('/admin/delivery-fee-config', {
          tiers: sortedTiers
        })
        
        // Update form with sorted tiers
        this.formData.tiers = sortedTiers
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
          tiers: [
            { threshold: 0, fee: 7.99 },
            { threshold: 58.00, fee: 5.99 },
            { threshold: 128.00, fee: 3.99 },
            { threshold: 150.00, fee: 0 }
          ]
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

.tiers-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.tiers-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

.add-tier-btn {
  padding: 8px 16px;
  background: #ff9800;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.2s;
}

.add-tier-btn:hover {
  background: #f57c00;
}

.tiers-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 24px;
}

.tier-item {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  background: #fafafa;
}

.tier-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.tier-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.remove-tier-btn {
  padding: 4px 8px;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  transition: background 0.2s;
}

.remove-tier-btn:hover {
  background: #d32f2f;
}

.tier-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.input-with-unit {
  position: relative;
  display: flex;
  align-items: center;
}

.input-with-unit input {
  flex: 1;
  padding: 10px 32px 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.input-with-unit input:focus {
  outline: none;
  border-color: #ff9800;
}

.input-with-unit input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.input-with-unit .unit {
  position: absolute;
  right: 12px;
  color: #666;
  font-size: 14px;
  pointer-events: none;
}

.form-hint {
  margin-top: 4px;
  font-size: 12px;
  color: #666;
  font-style: italic;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.reset-btn, .save-btn {
  padding: 10px 24px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.reset-btn {
  background: white;
  color: #666;
  border: 1px solid #ddd;
}

.reset-btn:hover {
  background: #f5f5f5;
}

.save-btn {
  background: #ff9800;
  color: white;
}

.save-btn:hover {
  background: #f57c00;
}

.save-btn:disabled {
  background: #ccc;
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

.rules-preview h2 {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 16px;
}

.preview-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.preview-item {
  padding: 12px;
  background: #f5f5f5;
  border-radius: 6px;
  border-left: 4px solid #ff9800;
}

.preview-condition {
  font-size: 14px;
  color: #333;
  margin-bottom: 4px;
  font-weight: 500;
}

.preview-fee {
  font-size: 16px;
  color: #f57c00;
  font-weight: 600;
}

.free-fee {
  color: #ff9800;
}

@media (max-width: 968px) {
  .config-form-container {
    grid-template-columns: 1fr;
  }
  
  .rules-preview {
    position: static;
  }
  
  .tier-fields {
    grid-template-columns: 1fr;
  }
}
</style>
