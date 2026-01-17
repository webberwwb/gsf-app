<template>
  <div class="admin-layout">
    <!-- Mobile overlay -->
    <div v-if="sidebarOpen" class="sidebar-overlay" @click="toggleSidebar"></div>
    
    <aside class="sidebar" :class="{ 'sidebar-open': sidebarOpen }">
      <div class="sidebar-header">
        <img src="/logos/gsf-icon.png" alt="谷语农庄" class="logo" />
        <div class="sidebar-title-container">
          <h2>管理后台</h2>
          <span class="version-text">v{{ version }}</span>
        </div>
        <button class="sidebar-close-btn" @click="toggleSidebar" aria-label="Close sidebar">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <nav class="sidebar-nav">
        <router-link to="/" class="nav-item" :class="{ active: $route.path === '/' }">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          <span>仪表盘</span>
        </router-link>
        <router-link to="/products" class="nav-item" :class="{ active: $route.path === '/products' }">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
          </svg>
          <span>商品管理</span>
        </router-link>
        <router-link to="/group-deals" class="nav-item" :class="{ active: $route.path === '/group-deals' }">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <span>团购管理</span>
        </router-link>
        <router-link to="/orders" class="nav-item" :class="{ active: $route.path === '/orders' }">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <span>订单管理</span>
        </router-link>
        <router-link to="/users" class="nav-item" :class="{ active: $route.path.startsWith('/users') }">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <span>用户管理</span>
        </router-link>
        <router-link to="/suppliers" class="nav-item" :class="{ active: $route.path === '/suppliers' }">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
          <span>供应商管理</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <div class="user-info">
          <div class="user-avatar">{{ userInitial }}</div>
          <div class="user-details">
            <div class="user-name">{{ userNickname }}</div>
            <div class="user-phone">{{ userPhone }}</div>
          </div>
        </div>
        <button @click="handleLogout" class="logout-btn">退出登录</button>
      </div>
    </aside>

    <main class="main-content">
      <header class="top-header">
        <button class="hamburger-btn" @click="toggleSidebar" aria-label="Toggle sidebar">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <h1>{{ pageTitle }}</h1>
      </header>
      <div class="content-area">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script>
import { getCurrentUser, clearAuth } from '../utils/auth'
import { useModal } from '../composables/useModal'

export default {
  name: 'Dashboard',
  setup() {
    const { confirm } = useModal()
    return { confirm }
  },
  data() {
    return {
      user: null,
      sidebarOpen: false,
      version: '加载中...'
    }
  },
  computed: {
    pageTitle() {
      const titles = {
        '/': '仪表盘',
        '/products': '商品管理',
        '/group-deals': '团购管理',
        '/orders': '订单管理',
        '/users': '用户管理',
        '/suppliers': '供应商管理'
      }
      return titles[this.$route.path] || '管理后台'
    },
    userNickname() {
      return this.user?.nickname || this.user?.phone || '管理员'
    },
    userPhone() {
      return this.user?.phone || ''
    },
    userInitial() {
      if (this.userNickname) {
        return this.userNickname.charAt(0).toUpperCase()
      }
      return 'A'
    }
  },
  mounted() {
    this.loadUser()
    this.loadVersion()
    // Close sidebar when route changes on mobile
    this.$watch('$route', () => {
      if (window.innerWidth < 768) {
        this.sidebarOpen = false
      }
    })
  },
  methods: {
    async loadVersion() {
      // First try: Read directly from sw.js (most reliable and fastest)
      try {
        const response = await fetch('/sw.js?t=' + Date.now(), { 
          cache: 'no-store',
          headers: {
            'Cache-Control': 'no-cache'
          }
        })
        if (response.ok) {
          const text = await response.text()
          const match = text.match(/const VERSION = ['"]([^'"]+)['"]/)
          if (match && match[1]) {
            this.version = match[1]
            return
          }
        }
      } catch (e) {
        console.warn('Failed to get version from sw.js:', e)
      }

      // Second try: Get from service worker via message channel (if available)
      if ('serviceWorker' in navigator) {
        try {
          // Use Promise.race to timeout after 2 seconds
          const registration = await Promise.race([
            navigator.serviceWorker.ready,
            new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 2000))
          ]).catch(() => null)
          
          if (registration && registration.active) {
            const gotVersion = await new Promise((resolve) => {
              const channel = new MessageChannel()
              let resolved = false
              const timeout = setTimeout(() => {
                if (!resolved) {
                  resolved = true
                  channel.port1.close()
                  resolve(false)
                }
              }, 1000)

              channel.port1.onmessage = (event) => {
                if (!resolved) {
                  resolved = true
                  clearTimeout(timeout)
                  if (event.data && event.data.version) {
                    this.version = event.data.version
                    resolve(true)
                  } else {
                    resolve(false)
                  }
                  channel.port1.close()
                }
              }
              
              registration.active.postMessage({ type: 'GET_VERSION' }, [channel.port2])
            })
            
            if (gotVersion) {
              return
            }
          }
        } catch (error) {
          console.warn('Failed to get version from service worker:', error)
        }
      }
      
      // Final fallback: show unknown if we couldn't get version
      this.version = '未知'
    },
    loadUser() {
      this.user = getCurrentUser()
    },
    toggleSidebar() {
      this.sidebarOpen = !this.sidebarOpen
    },
    async handleLogout() {
      const confirmed = await this.confirm('确定要退出登录吗？', {
        type: 'warning'
      })
      if (confirmed) {
        clearAuth()
        this.$router.push('/login')
      }
    }
  }
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
  background: var(--md-background);
}

.sidebar {
  width: 260px;
  background: var(--md-surface);
  box-shadow: none;
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
  z-index: 100;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@media (max-width: 767px) {
  .sidebar {
    transform: translateX(-100%);
  }
  
  .sidebar.sidebar-open {
    transform: translateX(0);
  }
}

.sidebar-overlay {
  display: none;
}

@media (max-width: 767px) {
  .sidebar-overlay {
    display: block;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 99;
  }
}

.sidebar-header {
  padding: var(--md-spacing-lg);
  border-bottom: 1px solid var(--md-surface-variant);
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
  position: relative;
}

.sidebar-close-btn {
  display: none;
  position: absolute;
  right: var(--md-spacing-md);
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: none;
  color: var(--md-on-surface-variant);
  cursor: pointer;
  padding: var(--md-spacing-xs);
  border-radius: var(--md-radius-sm);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar-close-btn:hover {
  background: var(--md-surface-variant);
  color: var(--md-on-surface);
}

.sidebar-close-btn svg {
  width: 20px;
  height: 20px;
}

@media (max-width: 767px) {
  .sidebar-close-btn {
    display: block;
  }
}

.logo {
  width: 40px;
  height: 40px;
  object-fit: contain;
}

.sidebar-title-container {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sidebar-header h2 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  font-weight: 500;
  margin: 0;
}

.version-text {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  font-weight: 400;
}

.sidebar-nav {
  flex: 1;
  padding: var(--md-spacing-md);
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
  padding: var(--md-spacing-md);
  color: var(--md-on-surface-variant);
  text-decoration: none;
  border-radius: var(--md-radius-md);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  margin-bottom: var(--md-spacing-xs);
}

.nav-item svg {
  width: 20px;
  height: 20px;
  stroke: currentColor;
}

.nav-item:hover {
  background: var(--md-surface-variant);
  color: var(--md-on-surface);
}

.nav-item.active {
  background: rgba(255, 140, 0, 0.1);
  color: var(--md-primary);
}

.sidebar-footer {
  padding: var(--md-spacing-md);
  border-top: 1px solid var(--md-surface-variant);
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
  margin-bottom: var(--md-spacing-md);
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--md-primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
  font-size: var(--md-body-size);
}

.user-details {
  flex: 1;
}

.user-name {
  font-size: var(--md-body-size);
  font-weight: 500;
  color: var(--md-on-surface);
}

.user-phone {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.logout-btn {
  width: 100%;
  padding: var(--md-spacing-sm);
  background: var(--md-surface);
  color: #ff4444;
  border: 1px solid #ff4444;
  border-radius: var(--md-radius-md);
  font-size: var(--md-label-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  text-transform: uppercase;
}

.logout-btn:hover {
  background: #ff4444;
  color: white;
}

.main-content {
  flex: 1;
  margin-left: 260px;
  display: flex;
  flex-direction: column;
}

@media (max-width: 767px) {
  .main-content {
    margin-left: 0;
  }
}

.top-header {
  background: var(--md-surface);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
}

.hamburger-btn {
  display: none;
  background: transparent;
  border: none;
  color: var(--md-on-surface);
  cursor: pointer;
  padding: var(--md-spacing-xs);
  border-radius: var(--md-radius-sm);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.hamburger-btn:hover {
  background: var(--md-surface-variant);
}

.hamburger-btn svg {
  width: 24px;
  height: 24px;
}

@media (max-width: 767px) {
  .hamburger-btn {
    display: block;
  }
}

.top-header h1 {
  font-size: var(--md-headline-size);
  color: var(--md-on-surface);
  font-weight: 500;
  letter-spacing: -0.5px;
  flex: 1;
}

.content-area {
  flex: 1;
  padding: var(--md-spacing-lg);
}
</style>

