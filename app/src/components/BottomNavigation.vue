<template>
  <nav class="bottom-nav">
    <router-link
      v-for="item in navItems"
      :key="item.path"
      :to="item.path"
      class="nav-item"
      :class="{ active: isActive(item) }"
    >
      <span class="nav-icon" v-html="item.icon"></span>
      <span class="nav-label">{{ item.label }}</span>
      <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
    </router-link>
  </nav>
</template>

<script>
import { useCartStore } from '../stores/cart'

export default {
  name: 'BottomNavigation',
  setup() {
    const cartStore = useCartStore()
    return { cartStore }
  },
  data() {
    return {
      navItems: [
        {
          path: '/',
          label: '随便逛逛',
          icon: '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>',
          badge: null
        },
        {
          path: '/group-deals',
          label: '团购下单',
          icon: '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" /><path stroke-linecap="round" stroke-linejoin="round" d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z" /></svg>',
          badge: null
        },
        {
          path: '/orders',
          label: '我的订单',
          icon: '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>',
          badge: null
        },
        {
          path: '/me',
          label: '账号管理',
          icon: '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>',
          badge: null
        }
      ]
    }
  },
  mounted() {
    // Load cart from storage on mount
    this.cartStore.loadFromStorage()
  },
  methods: {
    isActive(item) {
      // For "团购" item, highlight when on group-deals routes
      if (item.path === '/group-deals') {
        return this.$route.path === '/group-deals' || this.$route.path.startsWith('/group-deals/')
      }
      // For "订单" item, highlight when on orders routes
      if (item.path === '/orders') {
        return this.$route.path === '/orders' || this.$route.path.startsWith('/orders/')
      }
      // For other items, exact match
      return this.$route.path === item.path
    }
  }
}
</script>

<style scoped>
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-around;
  align-items: center;
  background: var(--md-surface);
  border-top: none;
  padding: 0.75rem 0;
  padding-bottom: max(0.75rem, env(safe-area-inset-bottom));
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.08);
  z-index: 1000;
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.95);
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  color: var(--md-on-surface-variant);
  padding: 0.5rem 1rem;
  position: relative;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 64px;
  border-radius: var(--md-radius-md);
  margin: 0 0.25rem;
}

.nav-item.active {
  color: var(--md-primary);
  background: rgba(255, 140, 0, 0.1);
  border-radius: var(--md-radius-md);
}

.nav-icon {
  width: 24px;
  height: 24px;
  margin-bottom: 0.25rem;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-icon svg {
  width: 100%;
  height: 100%;
  stroke: currentColor;
}

.nav-item.active .nav-icon {
  transform: scale(1.05);
}

.nav-label {
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.nav-badge {
  position: absolute;
  top: 0.25rem;
  right: 0.5rem;
  background: #FF4444;
  color: white;
  border-radius: 10px;
  min-width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0 0.25rem;
  box-shadow: 0 2px 4px rgba(255, 68, 68, 0.3);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

/* Safe area for devices with notches */
@supports (padding: max(0px)) {
  .bottom-nav {
    padding-bottom: max(0.75rem, env(safe-area-inset-bottom));
  }
}
</style>

