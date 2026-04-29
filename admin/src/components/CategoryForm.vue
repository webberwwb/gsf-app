<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="show" class="modal-overlay" @click.self="handleClose">
        <div class="modal-content" :class="{ 'wide': false }">
          <div class="modal-header">
            <h2>{{ category ? '编辑分类' : '添加分类' }}</h2>
            <button @click="handleClose" class="close-btn">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <form @submit.prevent="handleSubmit" class="modal-body">
            <div class="form-group">
              <label for="name">分类名称 *</label>
              <input
                id="name"
                v-model="form.name"
                type="text"
                placeholder="例如: 鸡肉类, 猪肉类, 牛肉类"
                required
                maxlength="255"
              />
            </div>

            <div class="form-group">
              <label for="description">分类描述</label>
              <textarea
                id="description"
                v-model="form.description"
                rows="3"
                placeholder="描述这个分类（可选）"
              ></textarea>
            </div>

            <div class="form-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  v-model="form.is_active"
                />
                <span>启用分类</span>
              </label>
              <p class="hint">停用的分类在前端不会显示</p>
            </div>

            <div class="modal-footer">
              <button type="button" @click="handleClose" class="cancel-btn">取消</button>
              <button type="submit" class="submit-btn" :disabled="submitting">
                {{ submitting ? '保存中...' : (category ? '保存更改' : '创建分类') }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import apiClient from '../api/client'
import { useModal } from '../composables/useModal'

export default {
  name: 'CategoryForm',
  props: {
    show: {
      type: Boolean,
      required: true
    },
    category: {
      type: Object,
      default: null
    }
  },
  emits: ['close', 'saved'],
  setup() {
    const { error: showError } = useModal()
    return { showError }
  },
  data() {
    return {
      form: {
        name: '',
        description: '',
        is_active: true
      },
      submitting: false
    }
  },
  watch: {
    show(newVal) {
      if (newVal) {
        this.resetForm()
      }
    },
    category: {
      immediate: true,
      handler(newVal) {
        if (newVal && this.show) {
          this.resetForm()
        }
      }
    }
  },
  methods: {
    resetForm() {
      if (this.category) {
        this.form = {
          name: this.category.name || '',
          description: this.category.description || '',
          is_active: this.category.is_active !== false
        }
      } else {
        this.form = {
          name: '',
          description: '',
          is_active: true
        }
      }
    },
    handleClose() {
      if (!this.submitting) {
        this.$emit('close')
      }
    },
    async handleSubmit() {
      this.submitting = true

      try {
        const data = { ...this.form }

        if (this.category) {
          // Update existing category
          await apiClient.put(`/admin/product-categories/${this.category.id}`, data)
        } else {
          // Create new category
          await apiClient.post('/admin/product-categories', data)
        }

        this.$emit('saved')
        this.$emit('close')
      } catch (error) {
        await this.showError(error.response?.data?.message || error.response?.data?.error || '保存失败')
        console.error('Save category error:', error)
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
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--md-spacing-md);
}

.modal-content {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  box-shadow: var(--md-elevation-5);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--md-spacing-lg);
  border-bottom: 1px solid var(--md-outline-variant);
}

.modal-header h2 {
  font-size: var(--md-title-size);
  font-weight: 500;
  color: var(--md-on-surface);
  margin: 0;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--md-on-surface-variant);
  border-radius: var(--md-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.close-btn:hover {
  background: var(--md-surface-variant);
}

.close-btn svg {
  width: 20px;
  height: 20px;
}

.modal-body {
  padding: var(--md-spacing-lg);
  overflow-y: auto;
  flex: 1;
}

.form-group {
  margin-bottom: var(--md-spacing-lg);
}

.form-group label {
  display: block;
  font-size: var(--md-label-size);
  font-weight: 500;
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-xs);
}

.form-group input[type="text"],
.form-group textarea {
  width: 100%;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: 1px solid var(--md-outline-variant);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-family: inherit;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--md-primary);
  box-shadow: 0 0 0 2px rgba(255, 140, 0, 0.2);
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  cursor: pointer;
  font-weight: normal;
  margin-bottom: var(--md-spacing-xs);
}

.checkbox-group input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
  flex-shrink: 0;
}

.hint {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin: var(--md-spacing-xs) 0 0 0;
}

.modal-footer {
  display: flex;
  gap: var(--md-spacing-md);
  justify-content: flex-end;
  padding-top: var(--md-spacing-lg);
  border-top: 1px solid var(--md-outline-variant);
}

.cancel-btn,
.submit-btn {
  padding: var(--md-spacing-sm) var(--md-spacing-lg);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: none;
}

.cancel-btn {
  background: var(--md-surface-variant);
  color: var(--md-on-surface-variant);
}

.cancel-btn:hover {
  background: var(--md-outline-variant);
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

/* Transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-content,
.modal-leave-active .modal-content {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
  transform: scale(0.95);
  opacity: 0;
}
</style>
