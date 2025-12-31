<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <img src="/logos/gsf-icon.png" alt="谷语农庄" class="logo" />
        <h1>谷语农庄</h1>
        <p>精品生态农产品团购</p>
      </div>

      <div class="login-options">
        <h2>登录选项</h2>

        <!-- Phone/SMS Login (Primary Method) -->
        <div class="phone-section">
          <input
            v-model="phone"
            type="tel"
            placeholder="手机号码 (例如: 4161234567 或 +14161234567)"
            class="phone-input"
            :disabled="loading"
            @input="formatPhoneInput"
          />
          <div class="phone-hint">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>输入10位号码即可，自动添加 +1 区号</span>
          </div>
          <button 
            @click="sendOTP" 
            class="login-btn sms-btn"
            :disabled="loading || !phone || !isPhoneValid"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="icon">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
            <span>发送验证码</span>
          </button>

          <div v-if="otpSent" class="otp-section">
            <input
              v-model="otp"
              type="text"
              placeholder="请输入6位验证码"
              class="otp-input"
              maxlength="6"
              :disabled="loading"
            />
            <button 
              @click="verifyOTP" 
              class="login-btn verify-btn"
              :disabled="loading || !otp"
            >
              验证码登录
            </button>
          </div>
        </div>

      </div>

      <div v-if="error" class="error-message">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'
import { useModal } from '../composables/useModal'
import { useAuthStore } from '../stores/auth'

export default {
  name: 'Login',
  setup() {
    const { alert } = useModal()
    const authStore = useAuthStore()
    return { $alert: alert, authStore }
  },
  data() {
    return {
      loading: false,
      error: null,
      phone: '',
      otp: '',
      otpSent: false,
      lastPhoneNumber: ''
    }
  },
  computed: {
    isPhoneValid() {
      if (!this.phone) return false
      // Remove all non-digit characters
      const digits = this.phone.replace(/\D/g, '')
      // Valid if 10 digits (Canadian) or 11+ digits with country code
      return digits.length === 10 || (digits.length >= 11 && digits.startsWith('1'))
    }
  },
  async mounted() {
    // Load saved phone number from localStorage (keeping this for UX convenience)
    const savedPhone = localStorage.getItem('last_phone_number')
    if (savedPhone) {
      this.phone = savedPhone
    }
    
    // Check if we have a valid cached token
    if (this.authStore.token || this.authStore.isAuthenticated) {
      const isValid = await this.authStore.checkAuth()
      if (isValid) {
        this.$router.push('/')
        return
      }
    }
  },
  methods: {
    formatPhoneInput() {
      // Optional: Add formatting as user types
      // For now, just trim whitespace
      this.phone = this.phone.trim()
    },
    async sendOTP() {
      this.loading = true
      this.error = null
      
      try {
        const response = await apiClient.post('/auth/phone/send-otp', {
          phone: this.phone,
          channel: 'sms'  // SMS only
        })
        
        // Save phone number for next time (UX convenience)
        if (this.phone) {
          localStorage.setItem('last_phone_number', this.phone)
        }
        
        // Check if dev mode bypass is active
        if (response.data.skip_otp || response.data.dev_mode) {
          // Dev mode: OTP bypassed, show OTP input but allow any code
          this.otpSent = true
          this.error = null
          return
        }
        
        this.otpSent = true
        // In development, show OTP (remove in production!)
        if (response.data.otp) {
          await this.$alert(`验证码: ${response.data.otp}\n\n(开发模式 - 生产环境请检查短信)`, {
            type: 'info',
            title: '验证码已发送'
          })
        } else {
          // OTP sent successfully via Twilio
          this.error = null
        }
      } catch (error) {
        const errorData = error.response?.data || {}
        const errorMessage = errorData.message || errorData.error || error.message || 'Failed to send OTP'
        this.error = errorMessage
        console.error('OTP send error:', error)
        console.error('Error details:', errorData)
      } finally {
        this.loading = false
      }
    },
    
    async verifyOTP() {
      this.loading = true
      this.error = null

      try {
        // Save phone number for next time (UX convenience)
        if (this.phone) {
          localStorage.setItem('last_phone_number', this.phone)
        }

        // Use the auth store login method
        await this.authStore.login(this.phone, this.otp)

        // Redirect to home
        this.$router.push('/')
      } catch (error) {
        const errorData = error.response?.data || {}
        this.error = errorData.message || errorData.error || 'Invalid OTP'
        console.error('OTP verification error:', errorData)
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--md-primary-variant) 0%, var(--md-primary) 100%);
  padding: var(--md-spacing-xl);
}

.login-container {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-xl);
  max-width: 400px;
  width: 100%;
  box-shadow: var(--md-elevation-4);
  border: none;
  backdrop-filter: blur(10px);
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.logo {
  width: 80px;
  height: 80px;
  margin: 0 auto 1rem;
  display: block;
  object-fit: contain;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.2));
}

.login-header h1 {
  font-size: var(--md-headline-size);
  margin-bottom: var(--md-spacing-sm);
  color: var(--md-primary);
  font-weight: 500;
  letter-spacing: -0.5px;
}

.login-header p {
  color: var(--md-on-surface-variant);
  font-size: var(--md-label-size);
  opacity: 0.87;
}

.login-options h2 {
  font-size: var(--md-title-size);
  margin-bottom: var(--md-spacing-lg);
  color: var(--md-primary);
  text-align: center;
  font-weight: 500;
  letter-spacing: 0.15px;
}

.login-btn {
  width: 100%;
  padding: 0.875rem;
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  letter-spacing: 0.5px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--md-spacing-sm);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  margin-bottom: var(--md-spacing-md);
  text-transform: uppercase;
  box-shadow: var(--md-elevation-2);
  position: relative;
  overflow: hidden;
}

.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.sms-btn {
  background: #25D366;
  color: white;
}

.sms-btn:hover:not(:disabled) {
  background: #20ba5a;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(37, 211, 102, 0.4);
}

.sms-btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: var(--md-elevation-2);
}

.verify-btn {
  background: var(--md-primary);
  color: white;
}

.verify-btn:hover:not(:disabled) {
  background: #FF7F00;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 140, 0, 0.4);
}

.verify-btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: var(--md-elevation-2);
}

.phone-input,
.otp-input {
  width: 100%;
  padding: 0.875rem;
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  margin-bottom: var(--md-spacing-sm);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  background: var(--md-surface);
  color: var(--md-on-surface);
  font-family: var(--md-font-family);
}

.phone-hint {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-xs);
  padding: var(--md-spacing-sm);
  background: #E3F2FD;
  border-radius: var(--md-radius-sm);
  margin-bottom: var(--md-spacing-md);
  font-size: 12px;
  color: #1565C0;
  line-height: 1.4;
}

.phone-hint svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  color: #1565C0;
}

.phone-input:focus,
.otp-input:focus {
  outline: none;
  border-color: var(--md-primary);
  border-width: 2px;
  box-shadow: 0 0 0 4px rgba(255, 140, 0, 0.12);
}

.otp-section {
  margin-top: var(--md-spacing-md);
  padding-top: var(--md-spacing-md);
  border-top: 1px solid var(--md-surface-variant);
}

.otp-section .otp-input {
  margin-bottom: var(--md-spacing-md);
}

.error-message {
  background: #FFEBEE;
  color: #C62828;
  padding: var(--md-spacing-md);
  border-radius: var(--md-radius-md);
  margin-top: var(--md-spacing-md);
  font-size: var(--md-label-size);
  font-weight: 500;
  box-shadow: var(--md-elevation-1);
  border-left: 4px solid #C62828;
}

.icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}
</style>

