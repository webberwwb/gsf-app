<template>
  <div v-if="show" class="modal-overlay" @click.self="close">
    <div class="modal-container">
      <div class="modal-header">
        <h2>{{ editingProduct ? '编辑商品' : '添加商品' }}</h2>
        <button @click="close" class="close-btn">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <form @submit.prevent="submitForm" class="product-form">
        <!-- Image Upload -->
        <div class="form-group">
          <label>商品图片</label>
          <div class="image-upload-section">
            <div v-if="imagePreview" class="image-preview">
              <img :src="imagePreview" alt="Preview" />
              <button type="button" @click="removeImage" class="remove-image-btn">×</button>
            </div>
            <div v-else class="image-upload-placeholder">
              <input
                ref="fileInput"
                type="file"
                accept="image/*"
                @change="handleImageSelect"
                class="file-input"
                id="image-upload"
              />
              <label for="image-upload" class="upload-label">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <span>点击上传图片</span>
              </label>
            </div>
            <div v-if="uploading" class="upload-progress">
              <span>上传中... {{ uploadProgress }}%</span>
            </div>
          </div>
        </div>

        <!-- Product Name -->
        <div class="form-group">
          <label for="name">商品名称 *</label>
          <input
            id="name"
            v-model="formData.name"
            type="text"
            required
            placeholder="请输入商品名称"
            class="form-input"
          />
        </div>

        <!-- Description -->
        <div class="form-group">
          <label for="description">商品描述</label>
          <textarea
            id="description"
            v-model="formData.description"
            rows="4"
            placeholder="请输入商品描述"
            class="form-textarea"
          ></textarea>
        </div>

        <!-- Pricing Type -->
        <div class="form-group">
          <label for="pricing_type">定价方式 *</label>
          <select
            id="pricing_type"
            v-model="formData.pricing_type"
            @change="onPricingTypeChange"
            class="form-input"
            required
          >
            <option value="per_item">按件计价</option>
            <option value="weight_range">按重量区间计价</option>
            <option value="unit_weight">按单位重量计价</option>
          </select>
        </div>

        <!-- Per Item Pricing -->
        <div v-if="formData.pricing_type === 'per_item'">
          <div class="form-group">
            <label for="price">价格 ($) *</label>
            <input
              id="price"
              v-model.number="formData.pricing_data.price"
              type="number"
              step="0.01"
              min="0"
              required
              placeholder="0.00"
              class="form-input"
            />
            <small class="form-hint">商品的标准价格</small>
          </div>
        </div>

        <!-- Weight Range Pricing -->
        <div v-if="formData.pricing_type === 'weight_range'" class="form-group">
          <label>重量区间价格 (磅)</label>
          <div v-for="(range, index) in formData.pricing_data.ranges" :key="index" class="weight-range-item">
            <div class="range-inputs">
              <input
                v-model.number="range.min"
                type="number"
                step="0.1"
                min="0"
                placeholder="最小重量"
                class="form-input"
              />
              <span>至</span>
              <input
                v-model.number="range.max"
                type="number"
                step="0.1"
                min="0"
                placeholder="最大重量 (留空表示以上)"
                class="form-input"
              />
              <span>磅:</span>
              <input
                v-model.number="range.price"
                type="number"
                step="0.01"
                min="0"
                placeholder="价格"
                class="form-input"
                required
              />
              <span>$</span>
              <button
                v-if="formData.pricing_data.ranges.length > 1"
                type="button"
                @click="removeWeightRange(index)"
                class="remove-range-btn"
              >
                删除
              </button>
            </div>
          </div>
          <button
            type="button"
            @click="addWeightRange"
            class="add-range-btn"
          >
            + 添加区间
          </button>
        </div>

        <!-- Unit Weight Pricing -->
        <div v-if="formData.pricing_type === 'unit_weight'" class="form-row">
          <div class="form-group">
            <label for="price_per_unit">单价 ($) *</label>
            <input
              id="price_per_unit"
              v-model.number="formData.pricing_data.price_per_unit"
              type="number"
              step="0.01"
              min="0"
              required
              placeholder="0.00"
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label for="unit">单位 *</label>
            <select
              id="unit"
              v-model="formData.pricing_data.unit"
              class="form-input"
              required
            >
              <option value="kg">千克 (kg)</option>
              <option value="lb">磅 (lb)</option>
            </select>
          </div>
        </div>

        <!-- Supplier -->
        <div class="form-group">
          <label for="supplier_id">供应商</label>
          <select
            id="supplier_id"
            v-model.number="formData.supplier_id"
            class="form-input"
          >
            <option :value="null">-- 无供应商 --</option>
            <option
              v-for="supplier in suppliers"
              :key="supplier.id"
              :value="supplier.id"
            >
              {{ supplier.name }}
            </option>
          </select>
          <small class="form-hint">选择产品的供应商（可选）</small>
        </div>

        <!-- Stock Limit -->
        <div class="form-group">
          <label for="stock_limit">库存限制</label>
          <input
            id="stock_limit"
            v-model.number="formData.stock_limit"
            type="number"
            min="0"
            placeholder="留空表示无限制"
            class="form-input"
          />
          <small class="form-hint">留空表示库存无限制</small>
        </div>

        <!-- Active Status -->
        <div class="form-group">
          <label class="checkbox-label">
            <input
              type="checkbox"
              v-model="formData.is_active"
              class="checkbox-input"
            />
            <span>商品上架</span>
          </label>
        </div>

        <!-- Error Message -->
        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <!-- Form Actions -->
        <div class="form-actions">
          <button type="button" @click="close" class="cancel-btn">取消</button>
          <button type="submit" :disabled="submitting || uploading" class="submit-btn">
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
  name: 'ProductForm',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    product: {
      type: Object,
      default: null
    }
  },
  emits: ['close', 'saved'],
  data() {
    return {
      formData: {
        name: '',
        image: '',
        description: '',
        pricing_type: 'per_item',
        pricing_data: {
          price: null,
          ranges: [{ min: 0, max: null, price: null }],
          price_per_unit: null,
          unit: 'kg'
        },
        supplier_id: null,
        stock_limit: null,
        is_active: true
      },
      suppliers: [],
      imagePreview: '',
      uploading: false,
      uploadProgress: 0,
      submitting: false,
      error: null
    }
  },
  computed: {
    editingProduct() {
      return this.product !== null
    }
  },
  watch: {
    show(newVal) {
      if (newVal) {
        this.resetForm()
        this.fetchSuppliers()
        if (this.product) {
          this.loadProductData()
        }
      }
    }
  },
  mounted() {
    this.fetchSuppliers()
  },
  methods: {
    resetForm() {
      this.formData = {
        name: '',
        image: '',
        description: '',
        pricing_type: 'per_item',
        pricing_data: {
          price: null,
          ranges: [{ min: 0, max: null, price: null }],
          price_per_unit: null,
          unit: 'kg'
        },
        supplier_id: null,
        stock_limit: null,
        is_active: true
      }
      this.imagePreview = ''
      this.error = null
      this.uploading = false
      this.uploadProgress = 0
    },
    async fetchSuppliers() {
      try {
        const response = await apiClient.get('/admin/suppliers', {
          params: { per_page: 1000 } // Get all suppliers
        })
        this.suppliers = (response.data.suppliers || []).filter(s => s.is_active)
      } catch (error) {
        console.error('Failed to fetch suppliers:', error)
        this.suppliers = []
      }
    },
    loadProductData() {
      if (this.product) {
        const pricingType = this.product.pricing_type || 'per_item'
        let pricingData = this.product.pricing_data || {}
        
        this.formData = {
          name: this.product.name || '',
          image: this.product.image || '',
          description: this.product.description || '',
          pricing_type: pricingType,
          pricing_data: {
            price: pricingData.price || null,
            ranges: pricingData.ranges || [{ min: 0, max: null, price: null }],
            price_per_unit: pricingData.price_per_unit || null,
            unit: pricingData.unit || 'kg'
          },
          supplier_id: this.product.supplier_id || null,
          stock_limit: this.product.stock_limit || null,
          is_active: this.product.is_active !== undefined ? this.product.is_active : true
        }
        this.imagePreview = this.product.image || ''
      }
    },
    onPricingTypeChange() {
      // Reset pricing_data when type changes
      if (this.formData.pricing_type === 'per_item') {
        this.formData.pricing_data = {
          price: null
        }
      } else if (this.formData.pricing_type === 'weight_range') {
        this.formData.pricing_data = {
          ranges: [{ min: 0, max: null, price: null }]
        }
      } else if (this.formData.pricing_type === 'unit_weight') {
        this.formData.pricing_data = {
          price_per_unit: null,
          unit: 'kg'
        }
      }
    },
    addWeightRange() {
      if (!this.formData.pricing_data.ranges) {
        this.formData.pricing_data.ranges = []
      }
      const lastRange = this.formData.pricing_data.ranges[this.formData.pricing_data.ranges.length - 1]
      const newMin = lastRange && lastRange.max ? lastRange.max : 0
      this.formData.pricing_data.ranges.push({
        min: newMin,
        max: null,
        price: null
      })
    },
    removeWeightRange(index) {
      this.formData.pricing_data.ranges.splice(index, 1)
    },
    async handleImageSelect(event) {
      const file = event.target.files[0]
      if (!file) return

      // Validate file type
      if (!file.type.startsWith('image/')) {
        this.error = '请选择图片文件'
        return
      }

      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        this.error = '图片大小不能超过 5MB'
        return
      }

      // Show preview
      const reader = new FileReader()
      reader.onload = (e) => {
        this.imagePreview = e.target.result
      }
      reader.readAsDataURL(file)

      // Upload to server
      await this.uploadImage(file)
    },
    async uploadImage(file) {
      this.uploading = true
      this.uploadProgress = 0
      this.error = null

      try {
        const formData = new FormData()
        formData.append('image', file)

        const response = await apiClient.post('/admin/upload-image', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              this.uploadProgress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            }
          }
        })

        this.formData.image = response.data.url
        this.imagePreview = response.data.url
        console.log('Image uploaded:', response.data.url)
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || '图片上传失败'
        this.imagePreview = ''
        console.error('Image upload error:', error)
      } finally {
        this.uploading = false
        this.uploadProgress = 0
      }
    },
    removeImage() {
      this.imagePreview = ''
      this.formData.image = ''
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = ''
      }
    },
    async submitForm() {
      this.submitting = true
      this.error = null

      try {
        // Validate per_item pricing
        if (this.formData.pricing_type === 'per_item') {
          if (!this.formData.pricing_data.price) {
            this.error = '请输入价格'
            this.submitting = false
            return
          }
        }

        // Prepare data
        const data = {
          name: this.formData.name,
          pricing_type: this.formData.pricing_type,
          pricing_data: { ...this.formData.pricing_data },
          is_active: this.formData.is_active
        }

        // Clean up pricing_data based on type
        if (this.formData.pricing_type === 'per_item') {
          data.pricing_data = {
            price: parseFloat(this.formData.pricing_data.price)
          }
        } else if (this.formData.pricing_type === 'weight_range') {
          // Filter out empty ranges and ensure all have prices
          data.pricing_data.ranges = this.formData.pricing_data.ranges.filter(r => r.price !== null && r.price !== '')
        } else if (this.formData.pricing_type === 'unit_weight') {
          data.pricing_data.price_per_unit = parseFloat(this.formData.pricing_data.price_per_unit)
          data.pricing_data.unit = this.formData.pricing_data.unit
        }

        if (this.formData.image) {
          data.image = this.formData.image
        }
        if (this.formData.description) {
          data.description = this.formData.description
        }
        if (this.formData.stock_limit !== null && this.formData.stock_limit !== '') {
          data.stock_limit = parseInt(this.formData.stock_limit)
        }
        if (this.formData.supplier_id !== null && this.formData.supplier_id !== '') {
          data.supplier_id = parseInt(this.formData.supplier_id)
        } else {
          data.supplier_id = null
        }

        if (this.editingProduct) {
          // Update product
          await apiClient.put(`/admin/products/${this.product.id}`, data)
        } else {
          // Create product
          await apiClient.post('/admin/products', data)
        }

        this.$emit('saved')
        this.close()
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || '保存失败'
        console.error('Save product error:', error)
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

.product-form {
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
.form-textarea {
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
.form-textarea:focus {
  outline: none;
  border-color: var(--md-primary);
  border-width: 2px;
  box-shadow: 0 0 0 4px rgba(255, 140, 0, 0.12);
}

.form-textarea {
  resize: vertical;
  min-height: 100px;
}

.form-hint {
  display: block;
  margin-top: var(--md-spacing-xs);
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.image-upload-section {
  margin-top: var(--md-spacing-sm);
}

.image-preview {
  position: relative;
  width: 100%;
  max-width: 300px;
  margin-bottom: var(--md-spacing-md);
}

.image-preview img {
  width: 100%;
  height: auto;
  border-radius: var(--md-radius-md);
  box-shadow: var(--md-elevation-1);
}

.remove-image-btn {
  position: absolute;
  top: -10px;
  right: -10px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #ff4444;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--md-elevation-2);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.remove-image-btn:hover {
  background: #cc0000;
  transform: scale(1.1);
}

.image-upload-placeholder {
  border: 2px dashed var(--md-outline);
  border-radius: var(--md-radius-md);
  padding: var(--md-spacing-xl);
  text-align: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.image-upload-placeholder:hover {
  border-color: var(--md-primary);
  background: var(--md-surface-variant);
}

.file-input {
  display: none;
}

.upload-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--md-spacing-sm);
  cursor: pointer;
  color: var(--md-on-surface-variant);
}

.upload-label svg {
  width: 48px;
  height: 48px;
}

.upload-progress {
  margin-top: var(--md-spacing-sm);
  font-size: var(--md-label-size);
  color: var(--md-primary);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  cursor: pointer;
}

.checkbox-input {
  width: 20px;
  height: 20px;
  cursor: pointer;
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

.weight-range-item {
  margin-bottom: var(--md-spacing-md);
  padding: var(--md-spacing-md);
  background: var(--md-surface-variant);
  border-radius: var(--md-radius-md);
}

.range-inputs {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  flex-wrap: wrap;
}

.range-inputs .form-input {
  flex: 1;
  min-width: 100px;
}

.range-inputs span {
  color: var(--md-on-surface-variant);
  font-size: var(--md-body-size);
}

.add-range-btn,
.remove-range-btn {
  padding: var(--md-spacing-xs) var(--md-spacing-sm);
  border: none;
  border-radius: var(--md-radius-sm);
  font-size: var(--md-label-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.add-range-btn {
  background: var(--md-primary);
  color: white;
  margin-top: var(--md-spacing-sm);
}

.add-range-btn:hover {
  background: #FF7F00;
}

.remove-range-btn {
  background: #FFEBEE;
  color: #C62828;
}

.remove-range-btn:hover {
  background: #C62828;
  color: white;
}
</style>

