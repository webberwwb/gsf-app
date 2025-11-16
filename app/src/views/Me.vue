<template>
  <div class="me-page">
    <header class="page-header">
      <h1>我的</h1>
    </header>
    <main class="page-content">
      <div class="profile-section">
        <div class="profile-card">
          <div class="avatar">{{ userInitial }}</div>
          <div class="profile-info">
            <h2>{{ userNickname || '用户' }}</h2>
            <p class="phone">{{ userPhone || '未设置手机号' }}</p>
            <p class="points">积分: {{ userPoints || 0 }}</p>
          </div>
        </div>
      </div>

      <div class="menu-section">
        <div class="menu-item" @click="$router.push('/orders')">
          <span class="menu-icon">📦</span>
          <span class="menu-label">我的订单</span>
          <span class="menu-arrow">›</span>
        </div>
        <div class="menu-item" @click="$router.push('/addresses')">
          <span class="menu-icon">📍</span>
          <span class="menu-label">收货地址</span>
          <span class="menu-arrow">›</span>
        </div>
        <div class="menu-item" @click="$router.push('/points')">
          <span class="menu-icon">⭐</span>
          <span class="menu-label">积分中心</span>
          <span class="menu-arrow">›</span>
        </div>
        <div class="menu-item" @click="$router.push('/settings')">
          <span class="menu-icon">⚙️</span>
          <span class="menu-label">设置</span>
          <span class="menu-arrow">›</span>
        </div>
      </div>

      <div class="logout-section">
        <button @click="handleLogout" class="logout-btn">退出登录</button>
      </div>
    </main>
  </div>
</template>

<script>
import { getCurrentUser, clearAuth } from '../utils/auth'
import apiClient from '../api/client'

export default {
  name: 'Me',
  data() {
    return {
      user: null
    }
  },
  computed: {
    userNickname() {
      return this.user?.nickname || this.user?.phone
    },
    userPhone() {
      return this.user?.phone
    },
    userPoints() {
      return this.user?.points || 0
    },
    userInitial() {
      if (this.userNickname) {
        return this.userNickname.charAt(0).toUpperCase()
      }
      return '👤'
    }
  },
  mounted() {
    this.loadUser()
  },
  methods: {
    loadUser() {
      this.user = getCurrentUser()
      if (!this.user) {
        // Try to fetch from API
        this.fetchUser()
      }
    },
    async fetchUser() {
      try {
        const response = await apiClient.get('/auth/me')
        if (response?.data?.user) {
          this.user = response.data.user
          localStorage.setItem('user', JSON.stringify(this.user))
        }
      } catch (error) {
        console.error('Failed to fetch user:', error)
      }
    },
    handleLogout() {
      if (confirm('确定要退出登录吗？')) {
        clearAuth()
        this.$router.push('/login')
      }
    }
  }
}
</script>

<style scoped>
.me-page {
  min-height: 100vh;
  background: var(--md-background);
  padding-bottom: 80px; /* Space for bottom nav */
}

.page-header {
  background: var(--md-surface);
  padding: var(--md-spacing-md);
  border-bottom: none;
  box-shadow: var(--md-elevation-1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.page-header h1 {
  font-size: var(--md-headline-size);
  color: var(--md-on-surface);
  font-weight: 500;
  letter-spacing: -0.5px;
}

.page-content {
  padding: 1rem;
}

.profile-section {
  margin-bottom: 1rem;
}

.profile-card {
  background: linear-gradient(135deg, var(--md-primary-variant) 0%, var(--md-primary) 100%);
  padding: var(--md-spacing-xl);
  border-radius: var(--md-radius-lg);
  display: flex;
  align-items: center;
  gap: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-3);
  position: relative;
  overflow: hidden;
}

.profile-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at top right, rgba(255, 255, 255, 0.2), transparent);
  pointer-events: none;
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: var(--md-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: 500;
  color: var(--md-primary);
  box-shadow: var(--md-elevation-2);
  position: relative;
  z-index: 1;
}

.profile-info h2 {
  font-size: 1.5rem;
  color: white;
  margin-bottom: 0.5rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.profile-info .phone {
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.9rem;
  margin-bottom: 0.25rem;
}

.profile-info .points {
  color: white;
  font-size: 1rem;
  font-weight: 600;
}

.menu-section {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  overflow: hidden;
  margin-bottom: var(--md-spacing-md);
  box-shadow: var(--md-elevation-1);
}

.menu-item {
  display: flex;
  align-items: center;
  padding: var(--md-spacing-md);
  border-bottom: 1px solid var(--md-surface-variant);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.menu-item:last-child {
  border-bottom: none;
}

.menu-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 0;
  background: var(--md-primary);
  transition: width 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.menu-item:hover {
  background: var(--md-surface-variant);
}

.menu-item:hover::before {
  width: 4px;
}

.menu-icon {
  font-size: 1.5rem;
  margin-right: 1rem;
}

.menu-label {
  flex: 1;
  font-size: 1rem;
  color: #333;
}

.menu-arrow {
  font-size: 1.5rem;
  color: #999;
}

.logout-section {
  padding: 1rem 0;
}

.logout-btn {
  width: 100%;
  background: var(--md-surface);
  color: #ff4444;
  border: 1px solid #ff4444;
  padding: var(--md-spacing-md);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  text-transform: uppercase;
  box-shadow: var(--md-elevation-1);
}

.logout-btn:hover {
  background: #ff4444;
  color: white;
  box-shadow: 0 4px 8px rgba(255, 68, 68, 0.3);
  transform: translateY(-1px);
}

.logout-btn:active {
  transform: translateY(0);
  box-shadow: var(--md-elevation-1);
}
</style>

