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
        <!-- Dashboard hidden for now -->
        <!-- <router-link to="/" class="nav-item" :class="{ active: $route.path === '/' }">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          <span>仪表盘</span>
        </router-link> -->
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
        <router-link to="/stripe-payments" class="nav-item" :class="{ active: $route.path === '/stripe-payments' }">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
          </svg>
          <span>在线支付</span>
        </router-link>
        <router-link to="/users" class="nav-item" :class="{ active: $route.path.startsWith('/users') }">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <span>用户管理</span>
        </router-link>
        <router-link to="/credit-referrals" class="nav-item" :class="{ active: $route.path === '/credit-referrals' }">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v13m0-13V6a2 2 0 112-2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7" />
          </svg>
          <span>用户推广</span>
        </router-link>
        <router-link to="/sales-management" class="nav-item" :class="{ active: $route.path === '/sales-management' }">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>销售管理</span>
        </router-link>
        <router-link to="/suppliers" class="nav-item" :class="{ active: $route.path === '/suppliers' }">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
          <span>供应商管理</span>
        </router-link>
        <router-link to="/shipping-fee" class="nav-item" :class="{ active: $route.path === '/shipping-fee' }">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
          </svg>
          <span>运费管理</span>
        </router-link>
        <router-link to="/after-sales" class="nav-item" :class="{ active: $route.path === '/after-sales' }">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
          </svg>
          <span>售后分析</span>
        </router-link>
        <router-link to="/work-arrangement" class="nav-item" :class="{ active: $route.path === '/work-arrangement' }">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span>工作安排</span>
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
      <header class="top-header" :class="{ 'top-header--detail-nav': isGroupDealDetail }">
        <button
          v-if="isGroupDealDetail"
          type="button"
          class="header-icon-btn header-back-btn"
          aria-label="返回"
          @click="handleDetailBack"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <button
          v-if="!isGroupDealDetail"
          class="hamburger-btn"
          @click="toggleSidebar"
          aria-label="Toggle sidebar"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <button
          v-if="isGroupDealDetail"
          class="hamburger-btn header-detail-desktop-menu"
          @click="toggleSidebar"
          aria-label="Toggle sidebar"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <h1>{{ pageTitle }}</h1>
        <button
          v-if="isGroupDealDetail"
          class="hamburger-btn header-detail-mobile-menu"
          @click="toggleSidebar"
          aria-label="Toggle sidebar"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
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
import { usePageHeader } from '../stores/pageHeader'

export default {
  name: 'Dashboard',
  setup() {
    const { confirm } = useModal()
    const { state: pageHeaderState } = usePageHeader()
    return { confirm, pageHeaderState }
  },
  data() {
    return {
      user: null,
      sidebarOpen: false,
      version: '加载中...'
    }
  },
  computed: {
    isGroupDealDetail() {
      return this.$route.name === 'GroupDealDetail'
    },
    pageTitle() {
      if (this.isGroupDealDetail) {
        return this.pageHeaderState.title || '团购详情'
      }
      const titles = {
        // '/': '仪表盘', // Hidden for now
        '/products': '商品管理',
        '/group-deals': '团购管理',
        '/orders': '订单管理',
        '/stripe-payments': '在线支付',
        '/users': '用户管理',
        '/credit-referrals': '用户推广',
        '/sales-management': '销售管理',
        '/suppliers': '供应商管理',
        '/shipping-fee': '运费管理',
        '/after-sales': '售后分析',
        '/work-arrangement': '工作安排'
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
    // Close sidebar when route changes on tablets and smaller laptops
    this.$watch('$route', (to, from) => {
      if (from.name === 'GroupDealDetail' && to.name !== 'GroupDealDetail') {
        const { reset } = usePageHeader()
        reset()
      }
      if (window.innerWidth < 1024) {
        this.sidebarOpen = false
      }
    })
  },
  methods: {
    handleDetailBack() {
      if (this.pageHeaderState.onBack) {
        this.pageHeaderState.onBack()
        return
      }
      this.$router.push('/group-deals')
    },
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
  width: 100%;
  max-width: 100%;
  /* Single scroll: lock shell to viewport; only .content-area scrolls */
  height: 100vh;
  max-height: 100vh;
  min-height: 0;
  overflow: hidden;
  background: var(--md-background);
}

@supports (height: 100dvh) {
  .admin-layout {
    height: 100dvh;
    max-height: 100dvh;
  }
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

/* Laptop screens - smaller sidebar */
@media (max-width: 1366px) {
  .sidebar {
    width: 220px;
  }
}

/* Tablet and below - hidden by default */
@media (max-width: 1024px) {
  .sidebar {
    width: 260px;
    transform: translateX(-100%);
  }
  
  .sidebar.sidebar-open {
    transform: translateX(0);
  }
}

/* Mobile - full width when open */
@media (max-width: 767px) {
  .sidebar {
    width: 100%;
    max-width: 300px;
  }
}

.sidebar-overlay {
  display: none;
}

/* Show overlay on tablets and below when sidebar is open */
@media (max-width: 1024px) {
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
  padding-top: calc(var(--md-spacing-lg) + env(safe-area-inset-top));
  border-bottom: 1px solid var(--md-surface-variant);
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
  position: relative;
}

/* Laptop screens - compact header */
@media (max-width: 1366px) {
  .sidebar-header {
    padding: var(--md-spacing-md);
    padding-top: calc(var(--md-spacing-md) + env(safe-area-inset-top));
    gap: var(--md-spacing-sm);
  }
  
  .logo {
    width: 36px;
    height: 36px;
  }
  
  .sidebar-header h2 {
    font-size: 1.125rem;
  }
  
  .version-text {
    font-size: 0.75rem;
  }
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

/* Laptop screens - more compact nav items */
@media (max-width: 1366px) {
  .nav-item {
    padding: var(--md-spacing-sm) var(--md-spacing-md);
    gap: var(--md-spacing-sm);
    font-size: 0.875rem;
  }
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
  padding-bottom: calc(var(--md-spacing-md) + env(safe-area-inset-bottom));
  border-top: 1px solid var(--md-surface-variant);
}

/* Laptop screens - compact footer */
@media (max-width: 1366px) {
  .sidebar-footer {
    padding: var(--md-spacing-sm) var(--md-spacing-md);
    padding-bottom: calc(var(--md-spacing-sm) + env(safe-area-inset-bottom));
  }
  
  .user-avatar {
    width: 36px;
    height: 36px;
    font-size: 0.875rem;
  }
  
  .user-name {
    font-size: 0.875rem;
  }
  
  .user-phone {
    font-size: 0.75rem;
  }
  
  .logout-btn {
    padding: var(--md-spacing-xs);
    font-size: 0.75rem;
  }
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
  min-width: 0;
  min-height: 0;
  max-width: 100%;
  margin-left: 260px;
  display: flex;
  flex-direction: column;
  overflow-x: clip;
  overflow-y: hidden;
}

/* Laptop screens - adjust for smaller sidebar */
@media (max-width: 1366px) {
  .main-content {
    margin-left: 220px;
  }
}

/* Tablet and below - full width */
@media (max-width: 1024px) {
  .main-content {
    margin-left: 0;
  }
}

.top-header {
  background: var(--md-surface);
  padding: var(--md-spacing-lg);
  padding-top: calc(var(--md-spacing-lg) + env(safe-area-inset-top));
  box-shadow: var(--md-elevation-1);
  z-index: 50;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
  min-width: 0;
  max-width: 100%;
}

/* Laptop screens - compact header */
@media (max-width: 1366px) {
  .top-header {
    padding: var(--md-spacing-md);
    padding-top: calc(var(--md-spacing-md) + env(safe-area-inset-top));
  }
  
  .top-header h1 {
    font-size: 1.25rem;
  }
}

.hamburger-btn {
  display: none;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--md-on-surface);
  cursor: pointer;
  padding: 0;
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

.header-back-btn,
.header-detail-mobile-menu,
.header-detail-desktop-menu {
  display: none;
}

.header-icon-btn {
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--md-radius-sm);
  color: var(--md-on-surface);
  cursor: pointer;
  transition: background 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  -webkit-tap-highlight-color: transparent;
}

.header-icon-btn svg {
  width: 24px;
  height: 24px;
}

.header-icon-btn:active {
  background: rgba(0, 0, 0, 0.06);
}

/* Show hamburger on tablets and below (standard pages only) */
@media (max-width: 1024px) {
  .hamburger-btn:not(.header-detail-desktop-menu):not(.header-detail-mobile-menu) {
    display: flex;
    width: 44px;
    height: 44px;
    min-width: 44px;
    min-height: 44px;
  }
}

.top-header h1 {
  font-size: var(--md-headline-size);
  color: var(--md-on-surface);
  font-weight: 500;
  letter-spacing: -0.5px;
  flex: 1;
  min-width: 0;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Mobile - smaller title */
@media (max-width: 767px) {
  .top-header {
    gap: var(--md-spacing-sm);
    padding-left: var(--md-spacing-sm);
    padding-right: var(--md-spacing-sm);
    padding-bottom: var(--md-spacing-sm);
    padding-top: calc(var(--md-spacing-sm) + env(safe-area-inset-top));
  }

  .top-header:not(.top-header--detail-nav) h1 {
    font-size: 1.0625rem;
    text-align: left;
  }

  .top-header--detail-nav {
    display: grid;
    grid-template-columns: 44px minmax(0, 1fr) 44px;
    align-items: center;
    gap: 0;
    padding-left: var(--md-spacing-xs);
    padding-right: var(--md-spacing-xs);
    padding-bottom: var(--md-spacing-sm);
    padding-top: calc(var(--md-spacing-sm) + env(safe-area-inset-top));
  }

  .top-header--detail-nav .header-detail-desktop-menu {
    display: none;
  }

  .top-header--detail-nav .header-back-btn {
    grid-column: 1;
    grid-row: 1;
  }

  .top-header--detail-nav h1 {
    grid-column: 2;
    grid-row: 1;
    font-size: 1.0625rem;
    text-align: center;
    justify-self: stretch;
    height: 44px;
    min-height: 44px;
    line-height: 44px;
  }

  .top-header--detail-nav .header-detail-mobile-menu {
    grid-column: 3;
    grid-row: 1;
  }

  .top-header--detail-nav .header-back-btn,
  .top-header--detail-nav .header-detail-mobile-menu {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    min-width: 44px;
    height: 44px;
    min-height: 44px;
    padding: 0;
    margin: 0;
  }
}

@media (min-width: 768px) and (max-width: 1024px) {
  .top-header--detail-nav .header-detail-desktop-menu {
    display: flex;
    width: 44px;
    height: 44px;
    min-width: 44px;
    min-height: 44px;
  }
}

.content-area {
  flex: 1;
  min-width: 0;
  min-height: 0;
  max-width: 100%;
  overflow-x: clip;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding: var(--md-spacing-lg);
  padding-bottom: calc(var(--md-spacing-lg) + env(safe-area-inset-bottom));
}

/* Reduce padding on smaller laptops */
@media (max-width: 1366px) {
  .content-area {
    padding: var(--md-spacing-md);
    padding-bottom: calc(var(--md-spacing-md) + env(safe-area-inset-bottom));
  }
}

/* Mobile - reduce padding further */
@media (max-width: 767px) {
  .content-area {
    padding: var(--md-spacing-sm);
    padding-bottom: calc(var(--md-spacing-sm) + env(safe-area-inset-bottom));
  }
}
</style>

