<template>
  <div class="me-page">
    <header class="page-header">
      <h1>账号管理</h1>
    </header>
    <main class="page-content">
      <!-- Not Authenticated State -->
      <div v-if="!isAuthenticated" class="not-authenticated-state">
        <div class="empty-icon">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
        <h2>未登录</h2>
        <p>请先登录以查看您的账号信息</p>
        <button @click="goToLogin" class="signup-btn">立即登录</button>
      </div>
      
      <!-- Authenticated Content -->
      <template v-else>
        <div class="profile-section">
          <div class="profile-card">
            <div class="avatar">{{ userInitial }}</div>
            <div class="profile-info">
              <h2>{{ userNickname || '用户' }}</h2>
              <p class="phone">{{ userPhone || '未设置手机号' }}</p>
              <p v-if="userWechat" class="wechat">微信号: {{ userWechat }}</p>
              <p class="points">积分: {{ userPoints || 0 }}</p>
            </div>
          </div>
        </div>

        <div class="credit-referral-panel">
          <div class="panel-block">
            <h3 class="panel-title">代金券余额</h3>
            <p class="panel-emphasis">${{ storeCreditDisplay }}</p>
            <p class="panel-hint">下单支付时可抵扣订单金额（与积分不同）</p>
            <p v-if="user?.referrer_display_name" class="referrer-line">
              我的邀请人：{{ user.referrer_display_name }}
            </p>
            <button type="button" class="ledger-btn" @click="openCreditLedger">
              查看代金券明细
            </button>
          </div>

          <div class="panel-block">
            <h3 class="panel-title">我的推荐码</h3>
            <template v-if="user && user.referral_unlocked && user.referral_code">
              <div class="ref-code-row">
                <span class="ref-code">{{ user.referral_code }}</span>
                <button type="button" class="mini-btn" @click="copyText(user.referral_code)">复制</button>
              </div>
              <button type="button" class="outline-btn" @click="copyInviteLink">复制邀请链接</button>
              <p class="panel-hint">好友用您的链接注册或绑定推荐码后，好友立即获得奖励；好友首单完成后您再获得奖励。</p>
            </template>
            <p v-else class="placeholder-msg">
              完成任意一笔订单后，即可获得专属推荐码。邀请好友加入，双方均可获得代金券。
            </p>
          </div>

          <div v-if="user && user.referral_unlocked && invitees.length" class="panel-block">
            <h3 class="panel-title">我邀请的好友</h3>
            <ul class="invitees-ul">
              <li v-for="row in invitees" :key="row.referral_id" class="invitee-li">
                <span class="invitee-name">{{ row.invitee_nickname || ('用户' + row.invitee_user_id) }}</span>
                <span class="invitee-status">{{ row.status_label }}</span>
              </li>
            </ul>
          </div>

          <div v-if="user && showReferralInviteRow" class="panel-block">
            <h3 class="panel-title">填写好友推荐码</h3>
            <p class="panel-hint">若尚未绑定过推荐人，可在此填写，并获取代金券（仅一次）</p>
            <div class="apply-row apply-row--solo">
              <input
                v-model="referralApplyCode"
                type="text"
                class="apply-input apply-input--full"
                placeholder="推荐码"
                autocapitalize="characters"
                autocomplete="off"
              />
            </div>
            <p v-if="referralFeedback?.kind === 'loading'" class="referral-live-msg referral-live-msg--muted">
              验证中…
            </p>
            <p v-else-if="referralFeedback?.kind === 'err'" class="referral-live-msg referral-live-msg--err">
              {{ referralFeedback.text }}
            </p>
          </div>
        </div>

        <div class="menu-section">
        <div class="menu-item" @click="$router.push('/addresses')">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="menu-icon">
            <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span class="menu-label">配送地址</span>
          <span class="menu-arrow">›</span>
        </div>
        <div class="menu-item" @click="$router.push('/points-mall')">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="menu-icon">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span class="menu-label">积分商城</span>
          <span class="menu-arrow">›</span>
        </div>
        <div class="menu-item version-item" @click="toggleVersionSection">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="menu-icon">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span class="menu-label">版本更新</span>
          <span class="menu-arrow" :class="{ rotated: showVersionSection }">›</span>
        </div>
      </div>

      <div v-if="showVersionSection" class="version-section">
        <div class="version-info">
          <div class="version-row">
            <span class="version-label">当前版本:</span>
            <span class="version-value">{{ currentVersion || '加载中...' }}</span>
          </div>
          <div class="version-row">
            <span class="version-label">最新版本:</span>
            <span class="version-value" :class="{ 'version-new': hasUpdate }">{{ latestVersion || '加载中...' }}</span>
          </div>
        </div>
        <button @click="handleUpdate" class="update-button" :disabled="isUpdating || isVersionMatch">
          {{ getUpdateButtonText() }}
        </button>
      </div>

        <div class="logout-section">
          <button @click="handleLogout" class="logout-btn">退出登录</button>
        </div>
      </template>

      <Teleport to="body">
        <div
          v-if="showCreditLedger"
          class="ledger-overlay"
          @click.self="closeCreditLedger"
        >
          <div class="ledger-sheet" role="dialog" aria-modal="true" aria-labelledby="ledger-title">
            <div class="ledger-sheet-header">
              <h3 id="ledger-title" class="ledger-sheet-title">代金券明细</h3>
              <button type="button" class="ledger-close" aria-label="关闭" @click="closeCreditLedger">
                ×
              </button>
            </div>
            <div class="ledger-sheet-body">
              <p v-if="creditTxLoading" class="ledger-status">加载中…</p>
              <p v-else-if="creditTxError" class="ledger-status ledger-status--err">{{ creditTxError }}</p>
              <ul v-else-if="creditTxList.length" class="ledger-list">
                <li v-for="t in creditTxList" :key="t.id" class="ledger-item">
                  <div class="ledger-item-top">
                    <span class="ledger-type">{{ t.tx_type_label }}</span>
                    <span
                      class="ledger-delta"
                      :class="{ 'ledger-delta--pos': Number(t.delta) > 0, 'ledger-delta--neg': Number(t.delta) < 0 }"
                    >
                      {{ Number(t.delta) > 0 ? '+' : '' }}{{ Number(t.delta).toFixed(2) }}
                    </span>
                  </div>
                  <p v-if="t.reason" class="ledger-reason">{{ t.reason }}</p>
                  <p v-if="t.related_order_number" class="ledger-order">订单：{{ t.related_order_number }}</p>
                  <p class="ledger-footer-line">
                    余额 ${{ Number(t.balance_after).toFixed(2) }} · {{ formatTxTime(t.created_at) }}
                  </p>
                </li>
              </ul>
              <p v-else class="ledger-status">暂无代金券记录</p>
            </div>
          </div>
        </div>
      </Teleport>
    </main>
  </div>
</template>

<script>
import apiClient from '../api/client'
import { getAppPublicOrigin } from '@/config/api'
import { formatDateTimeEST_CN } from '../utils/date'
import { useModal } from '../composables/useModal'
import { useAuthStore } from '../stores/auth'
import { REFERRAL_BIND_DEBOUNCE_MS } from '../utils/referralLiveBind'
import { getUserHasCompletedOrderCached } from '../utils/referralInviteUi'

export default {
  name: 'Me',
  setup() {
    const { confirm, error: showError, success, alert: showAlert } = useModal()
    const authStore = useAuthStore()
    return { confirm, showError, success, showAlert, authStore }
  },
  data() {
    return {
      showVersionSection: false,
      currentVersion: null,
      latestVersion: null,
      isUpdating: false,
      invitees: [],
      referralApplyCode: '',
      referralFeedback: null,
      referralBindTimer: null,
      showCreditLedger: false,
      creditTxLoading: false,
      creditTxList: [],
      creditTxError: null,
      referralUiHadCompletedOrder: null
    }
  },
  computed: {
    isAuthenticated() {
      return this.authStore.isAuthenticated
    },
    user() {
      return this.authStore.currentUser
    },
    userNickname() {
      return this.user?.nickname || this.user?.phone
    },
    userPhone() {
      return this.user?.phone
    },
    userWechat() {
      return this.user?.wechat
    },
    userPoints() {
      return this.user?.points || 0
    },
    userInitial() {
      if (this.userNickname) {
        return this.userNickname.charAt(0).toUpperCase()
      }
      return '👤'
    },
    hasUpdate() {
      return this.currentVersion && this.latestVersion && this.currentVersion !== this.latestVersion
    },
    isVersionMatch() {
      return this.currentVersion && this.latestVersion && this.currentVersion === this.latestVersion
    },
    isStandalone() {
      return window.matchMedia('(display-mode: standalone)').matches || 
             window.navigator.standalone === true
    },
    isIOS() {
      return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream
    },
    storeCreditDisplay() {
      return Number(this.user?.store_credit_balance || 0).toFixed(2)
    },
    inviteShareOrigin() {
      return getAppPublicOrigin()
    },
    showReferralInviteRow() {
      const u = this.user
      if (!u || u.referred_by_user_id) return false
      return this.referralUiHadCompletedOrder === false
    }
  },
  watch: {
    referralApplyCode() {
      this.scheduleReferralApplyLive()
    },
    'user.id'(id) {
      if (id) this.refreshReferralInviteUiGate()
    }
  },
  beforeUnmount() {
    if (this.referralBindTimer) {
      clearTimeout(this.referralBindTimer)
      this.referralBindTimer = null
    }
  },
  mounted() {
    // Load auth from storage if not already loaded
    if (!this.authStore.token) {
      this.authStore.loadFromStorage()
    }
    
    // Only load user data if authenticated
    if (this.authStore.isAuthenticated) {
      this.loadUser()
      this.loadVersions()
      this.fetchInvitees()
      this.refreshReferralInviteUiGate()
    }
  },
  methods: {
    loadUser() {
      if (!this.user) {
        // Try to fetch from API
        this.fetchUser()
      }
    },
    async fetchUser() {
      try {
        const response = await apiClient.get('/auth/me')
        if (response?.data?.user) {
          this.authStore.setUser(response.data.user)
          await this.fetchInvitees()
          await this.refreshReferralInviteUiGate()
        }
      } catch (error) {
        console.error('Failed to fetch user:', error)
      }
    },
    async fetchInvitees() {
      if (!this.authStore.isAuthenticated) return
      try {
        const r = await apiClient.get('/referrals/invitees')
        this.invitees = r.data?.invitees || []
      } catch (e) {
        console.warn('invitees', e)
        this.invitees = []
      }
    },
    async refreshReferralInviteUiGate() {
      const u = this.user
      if (!u?.id) {
        this.referralUiHadCompletedOrder = null
        return
      }
      this.referralUiHadCompletedOrder = await getUserHasCompletedOrderCached(u.id)
    },
    async copyText(text) {
      try {
        await navigator.clipboard.writeText(text)
        await this.success('已复制到剪贴板', { title: '完成' })
      } catch (_) {
        await this.showError('复制失败，请手动复制')
      }
    },
    async copyInviteLink() {
      if (!this.user?.referral_code) return
      const url = `${this.inviteShareOrigin}/login?ref=${encodeURIComponent(this.user.referral_code)}`
      await this.copyText(url)
    },
    formatTxTime(iso) {
      return formatDateTimeEST_CN(iso)
    },
    openCreditLedger() {
      this.showCreditLedger = true
      this.loadCreditTransactions()
    },
    closeCreditLedger() {
      this.showCreditLedger = false
    },
    async loadCreditTransactions() {
      this.creditTxLoading = true
      this.creditTxError = null
      try {
        const r = await apiClient.get('/referrals/credit-transactions')
        this.creditTxList = r.data?.transactions || []
      } catch (e) {
        this.creditTxError = e.response?.data?.error || e.response?.data?.message || '加载失败'
        this.creditTxList = []
      } finally {
        this.creditTxLoading = false
      }
    },
    scheduleReferralApplyLive() {
      if (this.referralBindTimer) {
        clearTimeout(this.referralBindTimer)
        this.referralBindTimer = null
      }
      const raw = (this.referralApplyCode || '').trim()
      if (!raw) {
        this.referralFeedback = null
        return
      }
      if (!this.user || this.user.referred_by_user_id || !this.showReferralInviteRow) {
        this.referralFeedback = null
        return
      }
      this.referralBindTimer = setTimeout(() => {
        this.referralBindTimer = null
        this.runReferralApplyLive(raw)
      }, REFERRAL_BIND_DEBOUNCE_MS)
    },
    async runReferralApplyLive(raw) {
      if (!this.user || this.user.referred_by_user_id || !this.showReferralInviteRow) return
      if ((this.referralApplyCode || '').trim() !== raw) return
      this.referralFeedback = { kind: 'loading' }
      try {
        const v = await apiClient.get('/referrals/validate-code', { params: { code: raw } })
        const d = v.data || {}
        if (!d.valid) {
          this.referralFeedback = { kind: 'err', text: d.message || '邀请码无效' }
          return
        }
        if ((this.referralApplyCode || '').trim() !== raw) return
        const r = await apiClient.post('/referrals/apply', { code: raw })
        if (r.data?.user) {
          this.authStore.setUser(r.data.user)
        } else {
          await this.fetchUser()
        }
        const nick = d.inviter_nickname || '好友'
        this.referralApplyCode = ''
        this.referralFeedback = null
        await this.fetchInvitees()
        await this.success(`已绑定邀请人《${nick}》`, { title: '成功' })
      } catch (e) {
        const msg = e.response?.data?.error || e.response?.data?.message || '绑定失败'
        this.referralFeedback = { kind: 'err', text: msg }
      }
    },
    goToLogin() {
      this.$router.push('/login')
    },
    async handleLogout() {
      const confirmed = await this.confirm('确定要退出登录吗？')
      if (confirmed) {
        this.authStore.logout()
        this.$router.push('/login')
      }
    },
    async loadVersions() {
      // Get current version from service worker
      this.getCurrentVersion()
      // Get latest version from backend
      this.getLatestVersion()
    },
    toggleVersionSection() {
      this.showVersionSection = !this.showVersionSection
      // Reload versions when section is opened
      if (this.showVersionSection) {
        this.loadVersions()
        // In standalone mode, also force service worker update check
        if (this.isStandalone && 'serviceWorker' in navigator) {
          navigator.serviceWorker.ready.then((registration) => {
            registration.update()
            // Also send check update message to service worker
            if (navigator.serviceWorker.controller) {
              navigator.serviceWorker.controller.postMessage({ type: 'CHECK_UPDATE' })
            }
          })
        }
      }
    },
    async getCurrentVersion() {
      try {
        // First try: Read directly from sw.js (most reliable)
        try {
          const response = await fetch('/sw.js?t=' + Date.now(), { cache: 'no-store' })
          const text = await response.text()
          const match = text.match(/const VERSION = ['"]([^'"]+)['"]/)
          if (match && match[1]) {
            this.currentVersion = match[1]
            return
          }
        } catch (e) {
          console.warn('Failed to get version from sw.js:', e)
        }

        // Second try: Get from service worker via message channel
        if ('serviceWorker' in navigator) {
          try {
            const registration = await navigator.serviceWorker.ready
            if (registration.active) {
              const gotVersion = await new Promise((resolve) => {
                const channel = new MessageChannel()
                let resolved = false
                const timeout = setTimeout(() => {
                  if (!resolved) {
                    resolved = true
                    channel.port1.close()
                    resolve(false) // Indicate we didn't get version from SW
                  }
                }, 1000) // 1 second timeout

                channel.port1.onmessage = (event) => {
                  if (!resolved) {
                    resolved = true
                    clearTimeout(timeout)
                    if (event.data && event.data.version) {
                      this.currentVersion = event.data.version
                      resolve(true) // Got version from SW
                    } else {
                      resolve(false)
                    }
                    channel.port1.close()
                  }
                }
                
                registration.active.postMessage({ type: 'GET_VERSION' }, [channel.port2])
              })
              
              if (gotVersion) {
                return // Successfully got version from service worker
              }
            }
          } catch (error) {
            console.warn('Failed to get version from service worker:', error)
          }
        }
        
        // Final fallback: read from sw.js
        await this.getCurrentVersionFromSwJs()
      } catch (error) {
        console.error('Failed to get current version:', error)
        this.currentVersion = '未知'
      }
    },
    async getCurrentVersionFromSwJs() {
      // Fallback method to read from sw.js
      try {
        const response = await fetch('/sw.js?t=' + Date.now(), { cache: 'no-store' })
        const text = await response.text()
        const match = text.match(/const VERSION = ['"]([^'"]+)['"]/)
        if (match && match[1]) {
          this.currentVersion = match[1]
        } else {
          this.currentVersion = '未知'
        }
      } catch (e) {
        console.error('Failed to get version from sw.js:', e)
        this.currentVersion = '未知'
      }
    },
    async getLatestVersion() {
      try {
        const response = await apiClient.get('/version')
        if (response.data) {
          // Try app_version first (new format)
          if (response.data.app_version && response.data.app_version !== 'unknown') {
            this.latestVersion = response.data.app_version
            return
          }
          // Fallback to version (old format)
          if (response.data.version && response.data.version !== 'unknown') {
            this.latestVersion = response.data.version
            return
          }
        }
        // If API returns unknown or no version, try to get from sw.js as fallback
        this.getLatestVersionFromSwJs()
      } catch (error) {
        console.error('Failed to get latest version from API:', error)
        // Fallback: try to get from sw.js directly
        this.getLatestVersionFromSwJs()
      }
    },
    async getLatestVersionFromSwJs() {
      // Fallback method to read latest version from sw.js
      try {
        const response = await fetch('/sw.js?t=' + Date.now(), { cache: 'no-store' })
        const text = await response.text()
        const match = text.match(/const VERSION = ['"]([^'"]+)['"]/)
        if (match && match[1]) {
          this.latestVersion = match[1]
        } else {
          this.latestVersion = '未知'
        }
      } catch (e) {
        console.error('Failed to get latest version from sw.js:', e)
        this.latestVersion = '获取失败'
      }
    },
    getUpdateButtonText() {
      if (this.isUpdating) {
        return '更新中...'
      }
      if (this.isVersionMatch) {
        return '您已在使用最新版本'
      }
      if (!this.currentVersion || !this.latestVersion || this.currentVersion === '未知' || this.latestVersion === '未知' || this.latestVersion === '获取失败') {
        return '立即更新'
      }
      return '立即更新'
    },
    async handleUpdate() {
      if (this.isUpdating) {
        console.log('Update already in progress')
        return
      }
      
      // Detect if we're in PWA standalone mode
      const isStandalone = window.matchMedia('(display-mode: standalone)').matches || 
                           window.navigator.standalone === true
      const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream
      
      console.log('Update button clicked, current version:', this.currentVersion, 'latest version:', this.latestVersion)
      console.log('PWA standalone mode:', isStandalone, 'iOS:', isIOS)
      
      const confirmed = await this.confirm('确定要更新应用吗？这将清除所有缓存并重新加载。')
      if (!confirmed) {
        console.log('Update cancelled by user')
        return
      }
      
      console.log('Starting update process...')
      this.isUpdating = true
      
      try {
        // First, tell any waiting service worker to skip waiting
        if ('serviceWorker' in navigator) {
          console.log('Checking for service workers...')
          const registrations = await navigator.serviceWorker.getRegistrations()
          console.log('Found', registrations.length, 'service worker registrations')
          
          for (const registration of registrations) {
            if (registration.waiting) {
              console.log('Sending SKIP_WAITING to waiting service worker')
              registration.waiting.postMessage({ type: 'SKIP_WAITING' })
            }
            if (registration.installing) {
              console.log('Sending SKIP_WAITING to installing service worker')
              registration.installing.postMessage({ type: 'SKIP_WAITING' })
            }
            if (navigator.serviceWorker.controller) {
              console.log('Sending SKIP_WAITING to active service worker')
              navigator.serviceWorker.controller.postMessage({ type: 'SKIP_WAITING' })
            }
          }
          
          // Wait a bit for the message to be processed
          await new Promise(resolve => setTimeout(resolve, 500))
        }
        
        // Clear all caches
        if ('caches' in window) {
          console.log('Clearing all caches...')
          const cacheNames = await caches.keys()
          console.log('Found', cacheNames.length, 'caches to clear')
          await Promise.all(
            cacheNames.map(cacheName => caches.delete(cacheName))
          )
          console.log('All caches cleared')
        }
        
        // Unregister all service workers
        if ('serviceWorker' in navigator) {
          console.log('Unregistering service workers...')
          const registrations = await navigator.serviceWorker.getRegistrations()
          await Promise.all(
            registrations.map(registration => registration.unregister())
          )
          console.log('All service workers unregistered')
        }
        
        // Clear localStorage and sessionStorage (optional, but helps ensure clean state)
        // We'll keep auth token to avoid logging user out
        const authToken = localStorage.getItem('auth_token')
        localStorage.clear()
        if (authToken) {
          localStorage.setItem('auth_token', authToken)
        }
        sessionStorage.clear()
        console.log('Storage cleared (auth token preserved)')
        
        // Force hard reload with cache bypass
        // For PWA standalone mode, especially iOS, we need more aggressive cache bypass
        const url = new URL(window.location.href)
        // Remove existing cache-busting parameters if any
        url.searchParams.delete('_update')
        url.searchParams.delete('_nocache')
        url.searchParams.delete('_sw')
        // Add new cache-busting parameters
        const timestamp = Date.now()
        url.searchParams.set('_update', timestamp.toString())
        url.searchParams.set('_nocache', '1')
        url.searchParams.set('_sw', timestamp.toString())
        const reloadUrl = url.toString()
        
        console.log('Reloading page with cache bypass:', reloadUrl)
        console.log('Standalone mode:', isStandalone, 'iOS:', isIOS)
        
        // For iOS standalone mode, use a more aggressive approach
        if (isIOS && isStandalone) {
          // iOS Safari standalone has very aggressive caching
          // Use window.location.href assignment (not replace) to ensure navigation happens
          // The href assignment forces a full page navigation which bypasses more cache layers
          setTimeout(() => {
            window.location.href = reloadUrl
          }, 200)
        } else if (isStandalone) {
          // For other standalone browsers (Android Chrome, etc.)
          // Use replace to avoid adding to history, but still force reload
          setTimeout(() => {
            window.location.replace(reloadUrl)
          }, 100)
        } else {
          // For regular browser mode
          // Use replace to avoid adding to history
          setTimeout(() => {
            window.location.replace(reloadUrl)
          }, 100)
        }
      } catch (error) {
        console.error('Update error:', error)
        this.isUpdating = false
        await this.showError('更新失败，请手动刷新页面')
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
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-2);
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--md-spacing-md);
  padding-top: calc(var(--md-spacing-lg) + env(safe-area-inset-top));
}

.header-logo {
  width: 40px;
  height: 40px;
  object-fit: contain;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.15));
}

.page-header h1 {
  font-size: var(--md-headline-size);
  color: white;
  font-weight: 500;
  letter-spacing: -0.5px;
  text-align: center;
}

.page-content {
  padding: 1rem;
}

.profile-section {
  margin-bottom: 1rem;
}

.profile-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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

.profile-info .wechat {
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
  width: 20px;
  height: 20px;
  margin-right: 1rem;
  flex-shrink: 0;
  color: var(--md-on-surface-variant);
}

.menu-label {
  flex: 1;
  font-size: 1rem;
  color: #333;
}

.menu-arrow {
  font-size: 1.5rem;
  color: #999;
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.menu-arrow.rotated {
  transform: rotate(90deg);
}

.version-item {
  cursor: pointer;
}

.version-section {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-md);
  margin-bottom: var(--md-spacing-md);
  box-shadow: var(--md-elevation-1);
  animation: slideDown 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.version-info {
  margin-bottom: var(--md-spacing-md);
}

.version-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-sm) 0;
  border-bottom: 1px solid var(--md-surface-variant);
}

.version-row:last-child {
  border-bottom: none;
}

.version-label {
  font-size: var(--md-body-size);
  color: var(--md-on-surface-variant);
  font-weight: 500;
}

.version-value {
  font-size: var(--md-body-size);
  color: var(--md-on-surface);
  font-weight: 600;
  font-family: monospace;
}

.version-value.version-new {
  color: var(--md-primary);
}

.update-button {
  width: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: var(--md-spacing-md);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--md-elevation-2);
}

.update-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--md-elevation-4);
}

.update-button:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: var(--md-elevation-2);
}

.update-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  background: var(--md-surface-variant);
  color: var(--md-on-surface-variant);
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

.not-authenticated-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--md-spacing-xl);
  text-align: center;
  min-height: 50vh;
}

.not-authenticated-state .empty-icon {
  width: 80px;
  height: 80px;
  color: var(--md-on-surface-variant);
  opacity: 0.5;
  margin-bottom: var(--md-spacing-md);
}

.not-authenticated-state .empty-icon svg {
  width: 100%;
  height: 100%;
}

.not-authenticated-state h2 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-sm);
}

.not-authenticated-state p {
  font-size: var(--md-body-size);
  color: var(--md-on-surface-variant);
  margin-bottom: var(--md-spacing-xl);
}

.signup-btn {
  padding: var(--md-spacing-md) var(--md-spacing-xl);
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  color: white;
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--md-elevation-2);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.signup-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--md-elevation-4);
}

.signup-btn:active {
  transform: translateY(0);
  box-shadow: var(--md-elevation-2);
}

.credit-referral-panel {
  margin: 0 0 var(--md-spacing-md);
  padding: var(--md-spacing-md);
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  box-shadow: var(--md-elevation-1);
  box-sizing: border-box;
  width: 100%;
}

.panel-block + .panel-block {
  margin-top: var(--md-spacing-lg);
  padding-top: var(--md-spacing-md);
  border-top: 1px solid var(--md-surface-variant);
}

.panel-title {
  font-size: 0.95rem;
  font-weight: 600;
  margin: 0 0 var(--md-spacing-sm);
  color: var(--md-on-surface);
}

.panel-emphasis {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
  color: var(--md-primary);
}

.panel-hint {
  font-size: 0.8rem;
  color: var(--md-on-surface-variant);
  margin: var(--md-spacing-xs) 0 0;
  line-height: 1.4;
}

.referrer-line {
  font-size: 0.85rem;
  color: var(--md-on-surface);
  margin: var(--md-spacing-md) 0 0;
  font-weight: 500;
}

.ledger-btn {
  margin-top: var(--md-spacing-md);
  width: 100%;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border-radius: var(--md-radius-sm);
  border: 1px solid var(--md-outline);
  background: var(--md-surface);
  color: var(--md-primary);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
}

.ledger-btn:active {
  opacity: 0.9;
}

.ledger-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 0;
}

.ledger-sheet {
  width: 100%;
  max-width: 480px;
  max-height: 85vh;
  background: var(--md-surface);
  border-radius: var(--md-radius-lg) var(--md-radius-lg) 0 0;
  box-shadow: var(--md-elevation-3);
  display: flex;
  flex-direction: column;
  animation: ledger-slide-up 0.25s ease-out;
}

@keyframes ledger-slide-up {
  from {
    transform: translateY(100%);
  }
  to {
    transform: translateY(0);
  }
}

.ledger-sheet-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  border-bottom: 1px solid var(--md-surface-variant);
  flex-shrink: 0;
}

.ledger-sheet-title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--md-on-surface);
}

.ledger-close {
  border: none;
  background: transparent;
  font-size: 1.5rem;
  line-height: 1;
  padding: 0 0.25rem;
  cursor: pointer;
  color: var(--md-on-surface-variant);
}

.ledger-sheet-body {
  overflow-y: auto;
  padding: var(--md-spacing-md);
  -webkit-overflow-scrolling: touch;
}

.ledger-status {
  text-align: center;
  color: var(--md-on-surface-variant);
  font-size: 0.9rem;
  margin: var(--md-spacing-xl) 0;
}

.ledger-status--err {
  color: #c62828;
}

.ledger-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.ledger-item {
  padding: var(--md-spacing-md) 0;
  border-bottom: 1px solid var(--md-surface-variant);
}

.ledger-item:last-child {
  border-bottom: none;
}

.ledger-item-top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: var(--md-spacing-sm);
}

.ledger-type {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--md-on-surface);
}

.ledger-delta {
  font-size: 0.95rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.ledger-delta--pos {
  color: #2e7d32;
}

.ledger-delta--neg {
  color: #c62828;
}

.ledger-reason {
  font-size: 0.8rem;
  color: var(--md-on-surface-variant);
  margin: var(--md-spacing-xs) 0 0;
  line-height: 1.35;
}

.ledger-order {
  font-size: 0.8rem;
  color: var(--md-on-surface);
  margin: var(--md-spacing-xs) 0 0;
}

.ledger-footer-line {
  font-size: 0.75rem;
  color: var(--md-on-surface-variant);
  margin: var(--md-spacing-xs) 0 0;
}

.placeholder-msg {
  font-size: 0.85rem;
  color: var(--md-on-surface-variant);
  line-height: 1.5;
  margin: 0;
  padding: var(--md-spacing-sm);
  background: rgba(255, 215, 0, 0.12);
  border-radius: var(--md-radius-sm);
}

.ref-code-row {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  margin-bottom: var(--md-spacing-sm);
}

.ref-code {
  font-family: ui-monospace, monospace;
  font-weight: 700;
  letter-spacing: 0.06em;
  font-size: 1.05rem;
}

.mini-btn,
.outline-btn,
.primary-mini {
  border-radius: var(--md-radius-sm);
  padding: 0.4rem 0.75rem;
  font-size: 0.8rem;
  cursor: pointer;
  border: none;
}

.mini-btn {
  background: var(--md-primary);
  color: white;
}

.outline-btn {
  width: 100%;
  margin-top: var(--md-spacing-sm);
  background: transparent;
  border: 1px solid var(--md-outline);
  color: var(--md-primary);
}

.invitees-ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.invitee-li {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--md-surface-variant);
}

.invitee-status {
  color: var(--md-on-surface-variant);
}

.apply-row {
  display: flex;
  gap: var(--md-spacing-sm);
  margin-top: var(--md-spacing-sm);
}

.apply-input {
  flex: 1;
  padding: 0.5rem 0.75rem;
  border-radius: var(--md-radius-sm);
  border: 1px solid var(--md-outline);
  font-size: 0.9rem;
}

.apply-row--solo {
  flex-direction: column;
}

.apply-input--full {
  width: 100%;
  box-sizing: border-box;
}

.referral-live-msg {
  margin: var(--md-spacing-sm) 0 0;
  font-size: 0.85rem;
  line-height: 1.4;
}

.referral-live-msg--muted {
  color: var(--md-on-surface-variant);
}

.referral-live-msg--err {
  color: #c62828;
  font-weight: 500;
}

.primary-mini {
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  color: white;
  font-weight: 600;
  white-space: nowrap;
}

.primary-mini:disabled {
  opacity: 0.6;
}
</style>

