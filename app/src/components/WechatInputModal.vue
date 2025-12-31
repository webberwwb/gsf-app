<template>
  <Transition name="modal">
    <div v-if="show" class="wechat-modal-overlay">
      <div class="wechat-modal-container">
        <div class="wechat-modal-header">
          <h3 class="wechat-modal-title">完善个人信息</h3>
        </div>
        
        <div class="wechat-modal-body">
          <p class="wechat-modal-description">
            为了更好的团购服务，请完善您的个人信息。
          </p>
          
          <div class="input-group">
            <label class="input-label">姓名/昵称 <span class="required">*</span></label>
            <input
              v-model="nickname"
              type="text"
              placeholder="请输入姓名或昵称"
              class="wechat-input"
              :disabled="loading"
              ref="nicknameRef"
            />
          </div>
          
          <div class="input-group">
            <label class="input-label">微信号 <span class="required">*</span></label>
            <input
              v-model="wechatId"
              type="text"
              placeholder="请输入微信号"
              class="wechat-input"
              :disabled="loading"
              @keyup.enter="handleSubmit"
              ref="inputRef"
            />
            <div v-if="error" class="wechat-error">{{ error }}</div>
          </div>
          
          <div class="wechat-guide-image" v-if="!imageError">
            <img 
              src="/images/WechatID.png" 
              alt="如何查找微信号"
              @error="handleImageError"
              class="guide-img"
            />
            <p class="guide-hint">打开微信 → "我" → 头像右侧 微信号</p>
          </div>
          <div class="wechat-guide-text" v-else>
            <p class="guide-hint-large">如何查找微信号：</p>
            <p class="guide-steps">1. 打开微信应用</p>
            <p class="guide-steps">2. 点击底部"我"</p>
            <p class="guide-steps">3. 在头像右侧找到"微信号"</p>
          </div>
        </div>
        
        <div class="wechat-modal-footer">
          <button 
            @click="handleSubmit" 
            class="wechat-submit-btn"
            :disabled="loading || !wechatId || wechatId.trim().length === 0 || !nickname || nickname.trim().length === 0">
            <span v-if="!loading">提交</span>
            <span v-else>提交中...</span>
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script>
import apiClient from '../api/client'
import { useAuthStore } from '../stores/auth'

export default {
  name: 'WechatInputModal',
  props: {
    show: {
      type: Boolean,
      default: false
    }
  },
  emits: ['success', 'close'],
  setup() {
    const authStore = useAuthStore()
    return { authStore }
  },
  data() {
    return {
      wechatId: '',
      nickname: '',
      loading: false,
      error: null,
      imageError: false
    }
  },
  watch: {
    show(newVal) {
      if (newVal) {
        // Pre-fill nickname if user already has one
        if (this.authStore.currentUser?.nickname) {
          this.nickname = this.authStore.currentUser.nickname
        }
        // Focus nickname input when modal opens
        this.$nextTick(() => {
          if (this.$refs.nicknameRef) {
            this.$refs.nicknameRef.focus()
          }
        })
        // Reset wechat ID (required field)
        this.wechatId = ''
        this.error = null
      }
    }
  },
  methods: {
    handleImageError() {
      this.imageError = true
    },
    async handleSubmit() {
      if (!this.nickname || this.nickname.trim().length === 0) {
        this.error = '请输入姓名/昵称'
        return
      }
      
      if (!this.wechatId || this.wechatId.trim().length === 0) {
        this.error = '请输入微信号'
        return
      }
      
      this.loading = true
      this.error = null
      
      try {
        const response = await apiClient.put('/auth/me/wechat', {
          wechat: this.wechatId.trim(),
          nickname: this.nickname.trim()
        })
        
        if (response.data.user) {
          this.$emit('success', response.data.user)
        }
      } catch (error) {
        const errorData = error.response?.data || {}
        this.error = errorData.message || errorData.error || '提交失败，请重试'
        console.error('Profile update error:', error)
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.wechat-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  padding: 16px;
}

.wechat-modal-container {
  background: white;
  border-radius: 16px;
  max-width: 400px;
  width: 100%;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.wechat-modal-header {
  padding: 24px 24px 16px;
  text-align: center;
  border-bottom: 1px solid #e5e7eb;
}

.wechat-modal-title {
  font-size: 20px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.wechat-modal-body {
  padding: 24px;
}

.wechat-modal-description {
  font-size: 14px;
  color: #6b7280;
  text-align: left;
  margin: 0 0 20px;
  line-height: 1.6;
}

.wechat-guide-image {
  margin: 0 0 20px;
  text-align: center;
}

.guide-img {
  max-height: 125px;
  width: 100%;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  margin: 0 auto 8px;
  display: block;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  object-fit: contain;
}

.guide-hint {
  font-size: 12px;
  color: #9ca3af;
  margin: 8px 0 0;
  text-align: center;
}

.wechat-guide-text {
  background: #f9fafb;
  border-radius: 8px;
  padding: 16px;
  margin: 0 0 20px;
  border: 1px solid #e5e7eb;
}

.guide-hint-large {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 12px;
  text-align: center;
}

.guide-steps {
  font-size: 13px;
  color: #6b7280;
  margin: 8px 0;
  line-height: 1.6;
  padding-left: 8px;
}

.input-group {
  margin-bottom: 16px;
}

.input-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}

.input-label .required {
  color: #ef4444;
}

.wechat-input-wrapper {
  margin-bottom: 8px;
}

.wechat-input {
  width: 100%;
  padding: 14px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 16px;
  transition: all 0.2s;
  background: white;
  color: #111827;
  font-family: var(--md-font-family);
}

.wechat-input:focus {
  outline: none;
  border-color: var(--md-primary);
  box-shadow: 0 0 0 4px rgba(255, 140, 0, 0.12);
}

.wechat-input:disabled {
  background: #f3f4f6;
  cursor: not-allowed;
  opacity: 0.6;
}

.wechat-input::placeholder {
  color: #9ca3af;
}

.wechat-error {
  margin-top: 8px;
  font-size: 13px;
  color: #ef4444;
  text-align: left;
}

.wechat-modal-footer {
  padding: 16px 24px 24px;
  background: #f9fafb;
}

.wechat-submit-btn {
  width: 100%;
  padding: 14px;
  background: var(--md-primary);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.wechat-submit-btn:hover:not(:disabled) {
  background: #FF7F00;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(255, 140, 0, 0.4);
}

.wechat-submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.wechat-submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* Transitions */
.modal-enter-active, .modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-active .wechat-modal-container,
.modal-leave-active .wechat-modal-container {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.modal-enter-from, .modal-leave-to {
  opacity: 0;
}

.modal-enter-from .wechat-modal-container,
.modal-leave-to .wechat-modal-container {
  transform: scale(0.9);
  opacity: 0;
}
</style>

