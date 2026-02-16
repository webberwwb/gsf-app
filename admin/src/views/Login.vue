<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <img src="/logos/gsf-icon.png" alt="谷语农庄" class="logo" />
        <h1>管理后台</h1>
        <p>谷语农庄 - 管理员登录</p>
      </div>

      <div class="login-form">
        <button
          @click="loginWithGoogle"
          class="login-btn google-btn"
          :disabled="loading"
        >
          <svg class="google-icon" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          <span v-if="!loading">使用 Google 登录</span>
          <span v-else>登录中...</span>
        </button>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'

export default {
  name: 'Login',
  data() {
    return {
      loading: false,
      error: null
    }
  },
  async mounted() {
    // Check for error message in URL (from backend redirect)
    const urlParams = new URLSearchParams(window.location.search)
    const errorMessage = urlParams.get('error')
    if (errorMessage) {
      this.error = decodeURIComponent(errorMessage)
      // Clean up URL
      window.history.replaceState({}, document.title, '/login')
    }

    // Check if we have a valid cached token
    const token = localStorage.getItem('admin_auth_token')
    if (token) {
      try {
        const response = await apiClient.get('/auth/me')
        if (response.data.user) {
          localStorage.setItem('admin_user', JSON.stringify(response.data.user))
          this.$router.push('/')
          return
        }
      } catch (error) {
        localStorage.removeItem('admin_auth_token')
        localStorage.removeItem('admin_user')
      }
    }

    // Check if we're returning from Google OAuth callback
    const code = urlParams.get('code')
    const hashParams = new URLSearchParams(window.location.hash.substring(1))
    const urlToken = hashParams.get('token')
    
    if (urlToken) {
      // Token received from backend redirect
      this.handleTokenReceived(urlToken)
    } else if (code) {
      // Code received from Google - exchange with backend
      this.handleGoogleCallback(code)
    }
  },
  methods: {
    async loginWithGoogle() {
      this.loading = true
      this.error = null

      try {
        // Backend will handle redirect URI configuration
        // No need to pass redirect_uri - backend uses GOOGLE_OAUTH_REDIRECT_URI from config
        const response = await apiClient.get('/auth/google/login-url')

        if (response.data.auth_url) {
          // Redirect to Google OAuth
          window.location.href = response.data.auth_url
        } else {
          this.error = 'Failed to get Google OAuth URL'
        }
      } catch (error) {
        const errorData = error.response?.data || {}
        this.error = errorData.message || errorData.error || error.message || 'Failed to initiate Google login'
        console.error('Google login error:', error)
        this.loading = false
      }
    },

    async handleGoogleCallback(code) {
      this.loading = true
      this.error = null

      try {
        // Backend handles redirect URI - no need to pass it
        // Exchange code for token via backend
        const response = await apiClient.get('/auth/google/callback', {
          params: {
            code: code
          }
        })

        if (response.data.token) {
          // Store token and user info
          localStorage.setItem('admin_auth_token', response.data.token)
          localStorage.setItem('admin_user', JSON.stringify(response.data.user))

          if (response.data.expires_at) {
            localStorage.setItem('admin_auth_token_expires_at', response.data.expires_at)
          }

          // Clean up URL
          window.history.replaceState({}, document.title, '/login')

          // Redirect to dashboard
          this.$router.push('/')
        } else {
          this.error = 'Failed to complete Google login'
        }
      } catch (error) {
        const errorData = error.response?.data || {}
        this.error = errorData.message || errorData.error || 'Failed to complete Google login'
        console.error('Google callback error:', errorData)
        
        // Clean up URL
        window.history.replaceState({}, document.title, '/login')
      } finally {
        this.loading = false
      }
    },

    async handleTokenReceived(token) {
      this.loading = true
      this.error = null

      try {
        // Token received from backend redirect
        localStorage.setItem('admin_auth_token', token)
        
        // Fetch user info
        const response = await apiClient.get('/auth/me')
        if (response.data.user) {
          localStorage.setItem('admin_user', JSON.stringify(response.data.user))
          if (response.data.token?.expires_at) {
            localStorage.setItem('admin_auth_token_expires_at', response.data.token.expires_at)
          }
        }

        // Clean up URL
        window.history.replaceState({}, document.title, '/login')

        // Redirect to dashboard
        this.$router.push('/')
      } catch (error) {
        this.error = 'Failed to complete login'
        console.error('Token handling error:', error)
        window.history.replaceState({}, document.title, '/login')
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
  width: 100%;
  overflow-x: hidden;
}

/* Mobile responsiveness */
@media (max-width: 767px) {
  .login-page {
    padding: var(--md-spacing-md);
  }
}

.login-container {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-xl);
  max-width: 400px;
  width: 100%;
  box-shadow: var(--md-elevation-4);
  backdrop-filter: blur(10px);
}

/* Mobile responsiveness */
@media (max-width: 767px) {
  .login-container {
    padding: var(--md-spacing-lg);
    max-width: 100%;
    border-radius: var(--md-radius-md);
  }
}

.login-header {
  text-align: center;
  margin-bottom: var(--md-spacing-xl);
}

.logo {
  width: 80px;
  height: 80px;
  margin: 0 auto var(--md-spacing-md);
  display: block;
  object-fit: contain;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.2));
}

/* Mobile responsiveness */
@media (max-width: 767px) {
  .logo {
    width: 64px;
    height: 64px;
  }
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

.login-form {
  display: flex;
  flex-direction: column;
}

.phone-input,
.otp-input {
  width: 100%;
  padding: 0.875rem;
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  margin-bottom: var(--md-spacing-md);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  background: var(--md-surface);
  color: var(--md-on-surface);
  font-family: var(--md-font-family);
}

.phone-input:focus,
.otp-input:focus {
  outline: none;
  border-color: var(--md-primary);
  border-width: 2px;
  box-shadow: 0 0 0 4px rgba(255, 140, 0, 0.12);
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
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  margin-bottom: var(--md-spacing-md);
  text-transform: uppercase;
  box-shadow: var(--md-elevation-2);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--md-spacing-sm);
}

.login-btn:hover:not(:disabled) {
  box-shadow: var(--md-elevation-3);
  transform: translateY(-2px);
}

.login-btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: var(--md-elevation-2);
}

.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.google-btn {
  background: white;
  color: #757575;
  border: 1px solid #dadce0;
}

.google-btn:hover:not(:disabled) {
  background: #f8f9fa;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.google-icon {
  width: 20px;
  height: 20px;
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
</style>

