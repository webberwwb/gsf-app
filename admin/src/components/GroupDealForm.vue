<template>
  <div v-if="show" class="modal-overlay" @click.self="close">
    <div class="modal-container large">
      <div class="modal-header">
        <h2>{{ editingDeal ? '编辑团购' : '创建团购' }}</h2>
        <button @click="close" class="close-btn">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <form @submit.prevent="submitForm" class="group-deal-form">
        <!-- Title -->
        <div class="form-group">
          <label for="title">团购标题 *</label>
          <input
            id="title"
            v-model="formData.title"
            type="text"
            required
            placeholder="请输入团购标题"
            class="form-input"
          />
        </div>

        <!-- Description -->
        <div class="form-group">
          <label for="description">团购描述</label>
          <textarea
            id="description"
            v-model="formData.description"
            rows="3"
            placeholder="请输入团购描述"
            class="form-textarea"
          ></textarea>
        </div>

        <!-- Dates -->
        <div class="form-row">
          <div class="form-group">
            <label for="order_start_date">开团时间 *</label>
            <input
              id="order_start_date"
              v-model="formData.order_start_date"
              type="datetime-local"
              required
              class="form-input"
            />
            <small class="form-hint">团购开始时间</small>
          </div>
          <div class="form-group">
            <label for="order_end_date">截单时间 *</label>
            <input
              id="order_end_date"
              v-model="formData.order_end_date"
              type="datetime-local"
              required
              class="form-input"
            />
            <small class="form-hint">团购截止时间</small>
          </div>
        </div>

        <div class="form-group">
          <label for="pickup_date">取货日期 *</label>
          <input
            id="pickup_date"
            v-model="formData.pickup_date"
            type="date"
            required
            class="form-input"
          />
          <small class="form-hint">取货日期（时间待定）</small>
        </div>

        <!-- Status -->
        <div class="form-group">
          <label for="status">状态</label>
          <select id="status" v-model="formData.status" class="form-input">
            <option value="upcoming">即将开始</option>
            <option value="active">进行中</option>
            <option value="closed">已截单</option>
            <option value="preparing">正在配货</option>
            <option value="ready_for_pickup">可以取货</option>
            <option value="completed">已完成</option>
          </select>
        </div>

        <!-- Products -->
        <div class="form-group">
          <label>选择商品</label>
          <div class="products-section">
            <div v-if="availableProducts.length === 0" class="no-products">
              <p>暂无可用商品，请先创建商品</p>
            </div>
            <div v-else class="products-list">
              <div
                v-for="product in availableProducts"
                :key="product.id"
                class="product-select-item"
                :class="{ selected: isProductSelected(product.id) }"
                @click="toggleProduct(product)"
              >
                <div class="product-select-info">
                  <div class="product-select-name">{{ product.name }}</div>
                  <div class="product-select-price">${{ product.price }}</div>
                </div>
                <div v-if="isProductSelected(product.id)" class="product-select-check">
                  ✓
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Selected Products Details -->
        <div v-if="selectedProducts.length > 0" class="form-group">
          <label>设置商品价格和库存</label>
          <div class="selected-products-details">
            <div
              v-for="(selectedProduct, index) in selectedProducts"
              :key="selectedProduct.id"
              class="product-detail-card"
            >
              <div class="product-detail-header">
                <span class="product-detail-name">{{ selectedProduct.name }}</span>
                <button type="button" @click="removeProduct(index)" class="remove-product-btn">×</button>
              </div>
              <div class="product-detail-fields">
                <div class="form-group-inline">
                  <label>团购价格 ($)</label>
                  <input
                    v-model.number="selectedProduct.deal_price"
                    type="number"
                    step="0.01"
                    min="0"
                    :placeholder="`默认: ${selectedProduct.price}`"
                    class="form-input-small"
                  />
                </div>
                <div class="form-group-inline">
                  <label>库存限制</label>
                  <input
                    v-model.number="selectedProduct.deal_stock_limit"
                    type="number"
                    min="0"
                    placeholder="留空表示无限制"
                    class="form-input-small"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <!-- Form Actions -->
        <div class="form-actions">
          <button type="button" @click="close" class="cancel-btn">取消</button>
          <button type="submit" :disabled="submitting" class="submit-btn">
            <span v-if="submitting">保存中...</span>
            <span v-else>保存</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'

export default {
  name: 'GroupDealForm',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    deal: {
      type: Object,
      default: null
    }
  },
  emits: ['close', 'saved'],
  data() {
    return {
      formData: {
        title: '',
        description: '',
        order_start_date: '',
        order_end_date: '',
        pickup_date: '',
        status: 'upcoming'
      },
      availableProducts: [],
      selectedProducts: [],
      submitting: false,
      error: null
    }
  },
  computed: {
    editingDeal() {
      return this.deal !== null
    }
  },
  watch: {
    show(newVal) {
      if (newVal) {
        this.resetForm()
        this.fetchProducts()
        if (this.deal) {
          this.loadDealData()
        }
      }
    }
  },
  methods: {
    resetForm() {
      this.formData = {
        title: '',
        description: '',
        order_start_date: '',
        order_end_date: '',
        pickup_date: '',
        status: 'upcoming'
      }
      this.selectedProducts = []
      this.error = null
    },
    async fetchProducts() {
      try {
        const response = await apiClient.get('/products')
        this.availableProducts = response.data.products || []
      } catch (error) {
        console.error('Failed to fetch products:', error)
      }
    },
    loadDealData() {
      if (this.deal) {
        this.formData = {
          title: this.deal.title || '',
          description: this.deal.description || '',
          order_start_date: this.formatDateTimeLocal(this.deal.order_start_date),
          order_end_date: this.formatDateTimeLocal(this.deal.order_end_date),
          pickup_date: this.formatDateOnly(this.deal.pickup_date),
          status: this.deal.status || 'upcoming'
        }
        
        // Load selected products
        if (this.deal.products && this.deal.products.length > 0) {
          this.selectedProducts = this.deal.products.map(product => ({
            id: product.id,
            name: product.name,
            price: product.price,
            deal_price: product.deal_price || product.price,
            deal_stock_limit: typeof product.deal_stock_limit === 'number' ? product.deal_stock_limit : null
          }))
        }
      }
    },
    formatDateTimeLocal(dateString) {
      if (!dateString) return ''
      // Convert ISO string to datetime-local format (YYYY-MM-DDTHH:mm)
      // Remove seconds and timezone info
      const date = new Date(dateString)
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      return `${year}-${month}-${day}T${hours}:${minutes}`
    },
    formatDateOnly(dateString) {
      if (!dateString) return ''
      // Convert ISO string to date format (YYYY-MM-DD)
      const date = new Date(dateString)
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    },
    toggleProduct(product) {
      const index = this.selectedProducts.findIndex(p => p.id === product.id)
      if (index >= 0) {
        this.selectedProducts.splice(index, 1)
      } else {
        this.selectedProducts.push({
          id: product.id,
          name: product.name,
          price: product.price,
          deal_price: product.price,
          deal_stock_limit: null
        })
      }
    },
    isProductSelected(productId) {
      return this.selectedProducts.some(p => p.id === productId)
    },
    removeProduct(index) {
      this.selectedProducts.splice(index, 1)
    },
    async submitForm() {
      this.submitting = true
      this.error = null

      try {
        // Prepare data
        // For order start/end dates: send datetime in EST with HH:mm:ss format
        // For pickup date: send date only (YYYY-MM-DD), backend will set time as TBD (00:00:00)
        const data = {
          title: this.formData.title,
          description: this.formData.description,
          order_start_date: this.formData.order_start_date ? this.formData.order_start_date + ':00' : null,
          order_end_date: this.formData.order_end_date ? this.formData.order_end_date + ':00' : null,
          pickup_date: this.formData.pickup_date || null,
          status: this.formData.status,
          products: this.selectedProducts.map(p => ({
            product_id: p.id,
            deal_price: p.deal_price || null,
            deal_stock_limit: p.deal_stock_limit !== undefined && p.deal_stock_limit !== null ? p.deal_stock_limit : null
          }))
        }

        if (this.editingDeal) {
          // Update deal
          await apiClient.put(`/admin/group-deals/${this.deal.id}`, data)
        } else {
          // Create deal
          await apiClient.post('/admin/group-deals', data)
        }

        this.$emit('saved')
        this.close()
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || '保存失败'
        console.error('Save group deal error:', error)
      } finally {
        this.submitting = false
      }
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
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--md-elevation-4);
}

.modal-container.large {
  max-width: 900px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-lg);
  border-bottom: 1px solid var(--md-surface-variant);
}

.modal-header h2 {
  font-size: var(--md-headline-size);
  color: var(--md-on-surface);
  font-weight: 500;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: var(--md-spacing-xs);
  color: var(--md-on-surface-variant);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--md-radius-sm);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.close-btn svg {
  width: 24px;
  height: 24px;
}

.close-btn:hover {
  background: var(--md-surface-variant);
  color: var(--md-on-surface);
}

.group-deal-form {
  padding: var(--md-spacing-lg);
}

.form-group {
  margin-bottom: var(--md-spacing-lg);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--md-spacing-md);
  margin-bottom: var(--md-spacing-lg);
}

label {
  display: block;
  margin-bottom: var(--md-spacing-sm);
  font-size: var(--md-body-size);
  font-weight: 500;
  color: var(--md-on-surface);
}

.form-input,
.form-textarea,
select.form-input {
  width: 100%;
  padding: var(--md-spacing-md);
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-family: var(--md-font-family);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  background: var(--md-surface);
  color: var(--md-on-surface);
}

.form-input:focus,
.form-textarea:focus,
select.form-input:focus {
  outline: none;
  border-color: var(--md-primary);
  border-width: 2px;
  box-shadow: 0 0 0 4px rgba(255, 140, 0, 0.12);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.products-section {
  margin-top: var(--md-spacing-sm);
}

.no-products {
  padding: var(--md-spacing-lg);
  text-align: center;
  color: var(--md-on-surface-variant);
  background: var(--md-surface-variant);
  border-radius: var(--md-radius-md);
}

.products-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--md-spacing-sm);
  max-height: 300px;
  overflow-y: auto;
  padding: var(--md-spacing-sm);
  background: var(--md-surface-variant);
  border-radius: var(--md-radius-md);
}

.product-select-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  background: var(--md-surface);
  border: 2px solid transparent;
  border-radius: var(--md-radius-md);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.product-select-item:hover {
  border-color: var(--md-primary);
  background: rgba(255, 140, 0, 0.05);
}

.product-select-item.selected {
  border-color: var(--md-primary);
  background: rgba(255, 140, 0, 0.1);
}

.product-select-info {
  flex: 1;
}

.product-select-name {
  font-size: var(--md-body-size);
  font-weight: 500;
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-xs);
}

.product-select-price {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.product-select-check {
  color: var(--md-primary);
  font-weight: bold;
  font-size: 1.2rem;
}

.selected-products-details {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
  margin-top: var(--md-spacing-sm);
}

.product-detail-card {
  background: var(--md-surface-variant);
  border-radius: var(--md-radius-md);
  padding: var(--md-spacing-md);
}

.product-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--md-spacing-md);
}

.product-detail-name {
  font-size: var(--md-body-size);
  font-weight: 500;
  color: var(--md-on-surface);
}

.remove-product-btn {
  background: #FFEBEE;
  color: #C62828;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.remove-product-btn:hover {
  background: #C62828;
  color: white;
}

.product-detail-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--md-spacing-md);
}

.form-group-inline {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-xs);
}

.form-group-inline label {
  font-size: var(--md-label-size);
  margin-bottom: 0;
}

.form-input-small {
  padding: var(--md-spacing-sm);
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-sm);
  font-size: var(--md-body-size);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  background: var(--md-surface);
  color: var(--md-on-surface);
}

.form-input-small:focus {
  outline: none;
  border-color: var(--md-primary);
  border-width: 2px;
}

.error-message {
  background: #FFEBEE;
  color: #C62828;
  padding: var(--md-spacing-md);
  border-radius: var(--md-radius-md);
  margin-bottom: var(--md-spacing-md);
  font-size: var(--md-label-size);
  font-weight: 500;
  border-left: 4px solid #C62828;
}

.form-actions {
  display: flex;
  gap: var(--md-spacing-md);
  justify-content: flex-end;
  margin-top: var(--md-spacing-xl);
  padding-top: var(--md-spacing-lg);
  border-top: 1px solid var(--md-surface-variant);
}

.cancel-btn,
.submit-btn {
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

.submit-btn {
  background: var(--md-primary);
  color: white;
  box-shadow: var(--md-elevation-2);
}

.submit-btn:hover:not(:disabled) {
  background: #FF7F00;
  box-shadow: var(--md-elevation-3);
  transform: translateY(-2px);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>

