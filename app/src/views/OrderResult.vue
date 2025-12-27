<template>
  <div class="order-result-page">
    <div class="result-container">
      <!-- Success State -->
      <div v-if="status === 'success'" class="result-content success">
        <div class="icon-container success-icon">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h1 class="result-title">{{ isNew ? '订单创建成功！' : '订单更新成功！' }}</h1>
        <p class="result-message">{{ isNew ? '您的订单已成功提交，我们会尽快处理' : '您的订单已成功更新，我们会尽快处理' }}</p>
        
        <div v-if="orderNumber" class="order-info">
          <div class="info-label">订单号</div>
          <div class="order-number-container">
            <span class="order-number">{{ orderNumber }}</span>
            <button @click="copyOrderNumber" class="copy-btn" :class="{ copied: copied }">
              <svg v-if="!copied" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </button>
          </div>
        </div>

        <div class="action-buttons">
          <button @click="goToOrders" class="primary-btn">
            查看订单
          </button>
          <button @click="goToHome" class="secondary-btn">
            返回首页
          </button>
        </div>
      </div>

      <!-- Error State -->
      <div v-else class="result-content error">
        <div class="icon-container error-icon">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h1 class="result-title">订单创建失败</h1>
        <p class="result-message">{{ errorMessage || '抱歉，订单创建过程中遇到了问题' }}</p>
        
        <div class="error-details" v-if="errorDetails">
          <p>{{ errorDetails }}</p>
        </div>

        <div class="action-buttons">
          <button @click="goBack" class="primary-btn">
            返回重试
          </button>
          <button @click="goToHome" class="secondary-btn">
            返回首页
          </button>
        </div>
      </div>
    </div>

    <!-- Decorative elements -->
    <div class="decoration-circle circle-1"></div>
    <div class="decoration-circle circle-2"></div>
    <div class="decoration-circle circle-3"></div>
  </div>
</template>

<script>
export default {
  name: 'OrderResult',
  data() {
    return {
      status: 'success', // 'success' or 'error'
      orderNumber: null,
      errorMessage: null,
      errorDetails: null,
      copied: false,
      isNew: true, // Whether it's a new order or update
      message: null // Custom message
    }
  },
  mounted() {
    // Get result data from route query params
    const queryStatus = this.$route.query.status
    const queryOrderNumber = this.$route.query.orderNumber
    const queryError = this.$route.query.error
    const queryErrorDetails = this.$route.query.errorDetails
    const queryIsNew = this.$route.query.isNew
    
    if (queryStatus) {
      this.status = queryStatus
      this.orderNumber = queryOrderNumber || null
      this.errorMessage = queryError || null
      this.errorDetails = queryErrorDetails || null
      this.isNew = queryIsNew !== 'false' // Default to true if not specified
    } else {
      // No query params - redirect to home or orders page
      this.$router.push('/')
    }
  },
  methods: {
    copyOrderNumber() {
      if (this.orderNumber) {
        navigator.clipboard.writeText(this.orderNumber).then(() => {
          this.copied = true
          setTimeout(() => {
            this.copied = false
          }, 2000)
        }).catch(err => {
          console.error('Failed to copy:', err)
        })
      }
    },
    goToOrders() {
      this.$router.push('/orders')
    },
    goToHome() {
      this.$router.push('/')
    },
    goBack() {
      this.$router.back()
    }
  }
}
</script>

<style scoped>
.order-result-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--md-spacing-lg);
  position: relative;
  overflow: hidden;
}

.result-container {
  max-width: 500px;
  width: 100%;
  animation: slideUp 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.result-content {
  background: var(--md-surface);
  border-radius: var(--md-radius-xl);
  padding: var(--md-spacing-xl);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  text-align: center;
}

.icon-container {
  width: 100px;
  height: 100px;
  margin: 0 auto var(--md-spacing-lg);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: scaleIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
  animation-delay: 0.2s;
  animation-fill-mode: both;
}

@keyframes scaleIn {
  from {
    transform: scale(0);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

.success-icon {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  box-shadow: 0 10px 30px rgba(17, 153, 142, 0.3);
}

.success-icon svg {
  width: 60px;
  height: 60px;
  color: white;
  animation: checkmarkDraw 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  animation-delay: 0.4s;
  animation-fill-mode: both;
}

@keyframes checkmarkDraw {
  from {
    stroke-dasharray: 100;
    stroke-dashoffset: 100;
  }
  to {
    stroke-dasharray: 100;
    stroke-dashoffset: 0;
  }
}

.error-icon {
  background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
  box-shadow: 0 10px 30px rgba(235, 51, 73, 0.3);
}

.error-icon svg {
  width: 60px;
  height: 60px;
  color: white;
  animation: shake 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  animation-delay: 0.2s;
}

@keyframes shake {
  0%, 100% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-10px);
  }
  75% {
    transform: translateX(10px);
  }
}

.result-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-sm);
  animation: fadeIn 0.6s ease-out;
  animation-delay: 0.3s;
  animation-fill-mode: both;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.result-message {
  font-size: var(--md-body-size);
  color: var(--md-on-surface-variant);
  margin-bottom: var(--md-spacing-lg);
  line-height: 1.6;
  animation: fadeIn 0.6s ease-out;
  animation-delay: 0.4s;
  animation-fill-mode: both;
}

.order-info {
  background: var(--md-surface-variant);
  border-radius: var(--md-radius-md);
  padding: var(--md-spacing-md);
  margin-bottom: var(--md-spacing-lg);
  animation: fadeIn 0.6s ease-out;
  animation-delay: 0.5s;
  animation-fill-mode: both;
}

.info-label {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin-bottom: var(--md-spacing-xs);
  text-align: center;
}

.order-number-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--md-spacing-sm);
  padding: var(--md-spacing-sm);
  background: white;
  border-radius: var(--md-radius-sm);
  border: 1px solid var(--md-outline-variant);
}

.order-number {
  font-size: 14px;
  font-weight: 600;
  color: var(--md-primary);
  font-family: 'Courier New', monospace;
  letter-spacing: 0.5px;
  word-break: break-all;
  flex: 1;
  text-align: center;
  line-height: 1.4;
}

.copy-btn {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: var(--md-radius-sm);
  border: none;
  background: var(--md-primary);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 0;
}

.copy-btn svg {
  width: 20px;
  height: 20px;
}

.copy-btn:hover {
  background: #FF7F00;
  transform: scale(1.05);
}

.copy-btn:active {
  transform: scale(0.95);
}

.copy-btn.copied {
  background: #11998e;
}

.info-item {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--md-spacing-xs);
}

.info-item .label {
  font-size: var(--md-body-size);
  color: var(--md-on-surface-variant);
}

.info-item .value {
  font-size: var(--md-body-size);
  font-weight: 600;
  color: var(--md-primary);
  font-family: monospace;
}

.error-details {
  background: #FFF3E0;
  border-left: 4px solid #FF6F00;
  padding: var(--md-spacing-md);
  border-radius: var(--md-radius-sm);
  margin-bottom: var(--md-spacing-lg);
  text-align: left;
}

.error-details p {
  font-size: var(--md-label-size);
  color: #E65100;
  margin: 0;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
  animation: fadeIn 0.6s ease-out;
  animation-delay: 0.6s;
  animation-fill-mode: both;
}

.primary-btn,
.secondary-btn {
  width: 100%;
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: none;
  position: relative;
  overflow: hidden;
}

.primary-btn::before,
.secondary-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s;
}

.primary-btn:hover::before,
.secondary-btn:hover::before {
  width: 300px;
  height: 300px;
}

.primary-btn {
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(255, 140, 0, 0.3);
}

.primary-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 140, 0, 0.4);
}

.primary-btn:active {
  transform: translateY(0);
}

.secondary-btn {
  background: transparent;
  color: var(--md-on-surface);
  border: 2px solid var(--md-outline);
}

.secondary-btn:hover {
  background: var(--md-surface-variant);
  border-color: var(--md-outline-variant);
}

/* Decorative circles */
.decoration-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float 20s infinite ease-in-out;
}

.circle-1 {
  width: 200px;
  height: 200px;
  top: -100px;
  left: -100px;
  animation-delay: 0s;
}

.circle-2 {
  width: 300px;
  height: 300px;
  bottom: -150px;
  right: -150px;
  animation-delay: 5s;
}

.circle-3 {
  width: 150px;
  height: 150px;
  top: 50%;
  right: -75px;
  animation-delay: 10s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
  }
}

@media (max-width: 480px) {
  .result-container {
    padding: var(--md-spacing-md);
  }

  .result-content {
    padding: var(--md-spacing-lg);
  }

  .result-title {
    font-size: 24px;
  }

  .icon-container {
    width: 80px;
    height: 80px;
  }

  .success-icon svg,
  .error-icon svg {
    width: 48px;
    height: 48px;
  }

  .order-number {
    font-size: 12px;
    letter-spacing: 0.3px;
  }

  .copy-btn {
    width: 32px;
    height: 32px;
  }

  .copy-btn svg {
    width: 18px;
    height: 18px;
  }
}
</style>

