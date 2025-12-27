<template>
  <div v-if="show" class="modal-overlay" @click="close">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>{{ editingAddress ? '编辑地址' : '添加地址' }}</h2>
        <button @click="close" class="close-btn">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <form @submit.prevent="submitForm" class="address-form">
        <div class="form-group">
          <label for="recipient_name">收货人姓名 *</label>
          <input
            id="recipient_name"
            v-model="formData.recipient_name"
            type="text"
            required
            placeholder="请输入收货人姓名"
            class="form-input"
          />
        </div>

        <div class="form-group">
          <label for="phone">联系电话 *</label>
          <input
            id="phone"
            v-model="formData.phone"
            type="tel"
            required
            placeholder="请输入联系电话"
            class="form-input"
          />
        </div>

        <div class="form-group">
          <label for="address_line1">详细地址 *</label>
          <input
            id="address_line1"
            v-model="formData.address_line1"
            type="text"
            required
            placeholder="街道地址、门牌号等"
            class="form-input"
          />
        </div>

        <div class="form-group">
          <label for="address_line2">地址补充（可选）</label>
          <input
            id="address_line2"
            v-model="formData.address_line2"
            type="text"
            placeholder="单元号、楼层等"
            class="form-input"
          />
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="city">城市 *</label>
            <input
              id="city"
              v-model="formData.city"
              type="text"
              required
              placeholder="城市"
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label for="postal_code">邮编 *</label>
            <input
              id="postal_code"
              v-model="formData.postal_code"
              type="text"
              required
              placeholder="邮编"
              class="form-input"
            />
          </div>
        </div>

        <div class="form-group">
          <label for="delivery_instructions">配送说明（可选）</label>
          <textarea
            id="delivery_instructions"
            v-model="formData.delivery_instructions"
            rows="3"
            placeholder="例如：请放在门口、联系我后再配送等"
            class="form-textarea"
          ></textarea>
        </div>

        <div class="form-group">
          <label class="checkbox-label">
            <input
              type="checkbox"
              v-model="formData.is_default"
              class="checkbox-input"
            />
            <span>设为默认地址</span>
          </label>
        </div>

        <div v-if="error" class="error-message">{{ error }}</div>

        <div class="form-actions">
          <button type="button" @click="close" class="cancel-btn">取消</button>
          <button type="submit" :disabled="submitting" class="submit-btn">
            {{ submitting ? '保存中...' : '保存' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'

export default {
  name: 'AddressForm',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    address: {
      type: Object,
      default: null
    }
  },
  data() {
    return {
      submitting: false,
      error: null,
      formData: {
        recipient_name: '',
        phone: '',
        address_line1: '',
        address_line2: '',
        city: '',
        postal_code: '',
        delivery_instructions: '',
        is_default: false
      }
    }
  },
  watch: {
    show(newVal) {
      if (newVal) {
        this.loadAddressData()
      } else {
        this.resetForm()
      }
    },
    address(newVal) {
      if (newVal) {
        this.loadAddressData()
      }
    }
  },
  methods: {
    loadAddressData() {
      if (this.address) {
        this.formData = {
          recipient_name: this.address.recipient_name || '',
          phone: this.address.phone || '',
          address_line1: this.address.address_line1 || '',
          address_line2: this.address.address_line2 || '',
          city: this.address.city || '',
          postal_code: this.address.postal_code || '',
          delivery_instructions: this.address.delivery_instructions || '',
          is_default: this.address.is_default || false
        }
      } else {
        this.resetForm()
      }
    },
    resetForm() {
      this.formData = {
        recipient_name: '',
        phone: '',
        address_line1: '',
        address_line2: '',
        city: '',
        postal_code: '',
        delivery_instructions: '',
        is_default: false
      }
      this.error = null
    },
    close() {
      this.$emit('close')
    },
    async submitForm() {
      this.submitting = true
      this.error = null

      try {
        if (this.address) {
          // Update existing address
          await apiClient.put(`/addresses/${this.address.id}`, this.formData)
        } else {
          // Create new address
          await apiClient.post('/addresses', this.formData)
        }

        this.$emit('saved')
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || '保存失败'
        console.error('Save address error:', error)
      } finally {
        this.submitting = false
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
  align-items: flex-end;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-content {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg) var(--md-radius-lg) 0 0;
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  animation: slideUp 0.3s ease-out;
  box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.2);
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
  }
  to {
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-lg);
  border-bottom: 1px solid var(--md-outline-variant);
  position: sticky;
  top: 0;
  background: var(--md-surface);
  z-index: 10;
}

.modal-header h2 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  font-weight: 500;
  margin: 0;
}

.close-btn {
  background: transparent;
  border: none;
  padding: var(--md-spacing-xs);
  cursor: pointer;
  color: var(--md-on-surface-variant);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--md-radius-sm);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  width: 32px;
  height: 32px;
}

.close-btn:hover {
  background: var(--md-surface-variant);
  color: var(--md-on-surface);
}

.close-btn svg {
  width: 24px;
  height: 24px;
}

.address-form {
  padding: var(--md-spacing-lg);
}

.form-group {
  margin-bottom: var(--md-spacing-md);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--md-spacing-md);
}

.form-group label {
  display: block;
  font-size: var(--md-label-size);
  color: var(--md-on-surface);
  font-weight: 500;
  margin-bottom: var(--md-spacing-xs);
}

.form-input, .form-textarea {
  width: 100%;
  padding: var(--md-spacing-sm);
  border: 1px solid var(--md-outline-variant);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  color: var(--md-on-surface);
  background: var(--md-surface);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-sizing: border-box;
}

.form-input:focus, .form-textarea:focus {
  outline: none;
  border-color: var(--md-primary);
  box-shadow: 0 0 0 2px rgba(255, 140, 0, 0.2);
}

.form-textarea {
  resize: vertical;
  font-family: inherit;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  cursor: pointer;
  font-weight: normal;
  padding: var(--md-spacing-sm) 0;
  user-select: none;
}

.checkbox-label span {
  line-height: 1.5;
  padding-top: 1px; /* Fine-tune vertical alignment */
}

.checkbox-input {
  width: 20px;
  height: 20px;
  cursor: pointer;
  flex-shrink: 0;
  margin: 0;
  accent-color: var(--md-primary);
}

.error-message {
  padding: var(--md-spacing-sm);
  background: #FFEBEE;
  color: #C62828;
  border-radius: var(--md-radius-md);
  font-size: var(--md-label-size);
  margin-bottom: var(--md-spacing-md);
}

.form-actions {
  display: flex;
  gap: var(--md-spacing-md);
  margin-top: var(--md-spacing-lg);
  padding-top: var(--md-spacing-md);
  border-top: 1px solid var(--md-outline-variant);
}

.cancel-btn, .submit-btn {
  flex: 1;
  padding: var(--md-spacing-md);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: none;
}

.cancel-btn {
  background: var(--md-surface-variant);
  color: var(--md-on-surface);
}

.cancel-btn:hover {
  background: var(--md-outline-variant);
}

.submit-btn {
  background: var(--md-primary);
  color: white;
}

.submit-btn:hover:not(:disabled) {
  background: #FF7F00;
  box-shadow: var(--md-elevation-2);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 480px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>

