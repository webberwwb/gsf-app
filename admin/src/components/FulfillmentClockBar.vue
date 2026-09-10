<template>
  <div v-if="!collapsed" class="clock-bar" :class="{ 'is-open': Boolean(openSession) }">
    <div class="clock-copy">
      <strong v-if="openSession">已打卡 {{ openSession.start_time }}</strong>
      <strong v-else>还没打卡</strong>
      <span>{{ openSession ? '配货结束后点下班' : '配货前先打卡，避免漏记' }}</span>
    </div>
    <div class="clock-actions">
      <button
        type="button"
        class="clock-btn"
        :disabled="saving"
        @click="openSession ? clockOut() : clockIn()"
      >
        {{ saving ? '提交中...' : (openSession ? '下班打卡' : '上班打卡') }}
      </button>
      <button
        type="button"
        class="clock-dismiss"
        aria-label="收起打卡栏"
        @click="collapse"
      >
        ×
      </button>
    </div>
  </div>
  <button
    v-else
    type="button"
    class="clock-chip"
    :class="{ 'is-open': Boolean(openSession) }"
    @click="expand"
  >
    {{ openSession ? `已打卡 ${openSession.start_time || ''}` : '打卡' }}
  </button>
</template>

<script>
import apiClient from '../api/client'
import { useModal } from '../composables/useModal'

const COLLAPSE_KEY = 'gsf_fulfillment_clock_bar_collapsed'

export default {
  name: 'FulfillmentClockBar',
  emits: ['collapsed-change'],
  setup() {
    const { success, error: showError } = useModal()
    return { success, showError }
  },
  data() {
    return {
      openSession: null,
      saving: false,
      collapsed: sessionStorage.getItem(COLLAPSE_KEY) === '1'
    }
  },
  mounted() {
    this.$emit('collapsed-change', this.collapsed)
    this.refresh()
  },
  methods: {
    collapse() {
      this.collapsed = true
      sessionStorage.setItem(COLLAPSE_KEY, '1')
      this.$emit('collapsed-change', true)
    },
    expand() {
      this.collapsed = false
      sessionStorage.removeItem(COLLAPSE_KEY)
      this.$emit('collapsed-change', false)
    },
    async refresh() {
      try {
        const res = await apiClient.get('/admin/fulfillment/clock-status')
        this.openSession = res.data.open_session || null
      } catch (e) {
        this.openSession = null
      }
    },
    async clockIn() {
      this.saving = true
      try {
        const res = await apiClient.post('/admin/fulfillment/work-sessions/clock-in', {})
        this.openSession = res.data.session || null
        await this.success('已上班打卡')
      } catch (e) {
        await this.showError(e.response?.data?.error || '打卡失败')
        await this.refresh()
      } finally {
        this.saving = false
      }
    },
    async clockOut() {
      this.saving = true
      try {
        await apiClient.post('/admin/fulfillment/work-sessions/clock-out', {})
        this.openSession = null
        await this.success('已下班打卡')
      } catch (e) {
        await this.showError(e.response?.data?.error || '打卡失败')
        await this.refresh()
      } finally {
        this.saving = false
      }
    }
  }
}
</script>

<style scoped>
.clock-bar {
  flex-shrink: 0;
  z-index: 80;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.7rem 0.9rem;
  padding-bottom: calc(0.7rem + env(safe-area-inset-bottom));
  background: #FFF3E0;
  border-top: 1px solid rgba(255, 140, 0, 0.35);
  box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.08);
}
.clock-bar.is-open {
  background: #E8F5E9;
  border-top-color: rgba(46, 125, 50, 0.28);
}
.clock-copy {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  min-width: 0;
}
.clock-copy strong {
  font-size: 0.95rem;
}
.clock-copy span {
  color: var(--md-on-surface-variant);
  font-size: 12px;
}
.clock-actions {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  flex-shrink: 0;
}
.clock-btn {
  min-height: 44px;
  min-width: 108px;
  border: none;
  border-radius: var(--md-radius-md);
  background: var(--md-primary);
  color: #fff;
  font-weight: 600;
  font-size: 15px;
  cursor: pointer;
}
.clock-bar.is-open .clock-btn {
  background: #2E7D32;
}
.clock-btn:disabled {
  opacity: 0.65;
}
.clock-dismiss {
  width: 36px;
  min-width: 36px;
  min-height: 44px;
  padding: 0;
  border: none;
  border-radius: var(--md-radius-md);
  background: transparent;
  color: var(--md-on-surface-variant);
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
}
.clock-chip {
  position: fixed;
  right: 12px;
  bottom: calc(12px + env(safe-area-inset-bottom));
  z-index: 80;
  min-height: 40px;
  padding: 0 0.9rem;
  border: none;
  border-radius: 999px;
  background: #FFF3E0;
  color: #E65100;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.16);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}
.clock-chip.is-open {
  background: #E8F5E9;
  color: #2E7D32;
}
</style>
