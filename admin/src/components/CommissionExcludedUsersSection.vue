<template>
  <div class="excluded-users-section">
    <div class="section-header">
      <div>
        <h3 class="section-title">提成排除用户</h3>
        <p class="section-description">
          列表中的用户订单将不计入任何提成（无论自己客户或一般客户）。
        </p>
      </div>
    </div>

    <div class="search-wrapper">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜索用户 (手机号/昵称/微信号/用户ID)"
        class="search-input"
      />
      <span v-if="searching" class="search-status">搜索中...</span>
    </div>

    <div v-if="searchQuery.trim() && !searching && searchResults.length === 0" class="no-search-results">
      未找到匹配用户
    </div>

    <div v-if="searchResults.length > 0" class="search-results">
      <div
        v-for="user in searchResults"
        :key="user.id"
        class="search-result-item"
      >
        <div class="user-info">
          <span class="user-name">{{ getUserDisplayName(user) }}</span>
          <span v-if="user.phone" class="user-detail">{{ user.phone }}</span>
          <span v-if="user.user_source" class="user-source">来源: {{ user.user_source }}</span>
        </div>
        <button
          v-if="!isExcluded(user.id)"
          @click="addExcludedUser(user)"
          class="add-btn"
          :disabled="addingUserId === user.id"
        >
          {{ addingUserId === user.id ? '添加中...' : '添加' }}
        </button>
        <span v-else class="already-excluded">已排除</span>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="excludedUsers.length === 0" class="empty-state">
      <p>暂无排除用户</p>
    </div>
    <div v-else class="excluded-list">
      <div
        v-for="entry in excludedUsers"
        :key="entry.id"
        class="excluded-item"
      >
        <div class="user-info">
          <span class="user-name">{{ getUserDisplayName(entry.user) }}</span>
          <span v-if="entry.user?.phone" class="user-detail">{{ entry.user.phone }}</span>
          <span v-if="entry.user?.user_source" class="user-source">来源: {{ entry.user.user_source }}</span>
          <span v-if="entry.notes" class="user-notes">{{ entry.notes }}</span>
        </div>
        <button
          @click="removeExcludedUser(entry)"
          class="remove-btn"
          :disabled="removingUserId === entry.user_id"
        >
          {{ removingUserId === entry.user_id ? '移除中...' : '移除' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'
import { useModal } from '../composables/useModal'

export default {
  name: 'CommissionExcludedUsersSection',
  setup() {
    const { success, error, confirm } = useModal()
    return { success, error, confirm }
  },
  data() {
    return {
      loading: false,
      searching: false,
      excludedUsers: [],
      searchQuery: '',
      searchResults: [],
      addingUserId: null,
      removingUserId: null,
      searchDebounceTimer: null,
      activeSearchRequest: 0
    }
  },
  watch: {
    searchQuery() {
      if (this.searchDebounceTimer) {
        clearTimeout(this.searchDebounceTimer)
      }

      const query = this.searchQuery.trim()
      if (!query) {
        this.searchResults = []
        this.searching = false
        return
      }

      this.searchDebounceTimer = setTimeout(() => {
        this.searchUsers(query)
      }, 300)
    }
  },
  mounted() {
    this.fetchExcludedUsers()
  },
  beforeUnmount() {
    if (this.searchDebounceTimer) {
      clearTimeout(this.searchDebounceTimer)
    }
  },
  methods: {
    getUserDisplayName(user) {
      if (!user) return '未知用户'
      return user.nickname || user.phone || user.wechat || `用户 #${user.id}`
    },
    isExcluded(userId) {
      return this.excludedUsers.some(entry => entry.user_id === userId)
    },
    async fetchExcludedUsers() {
      try {
        this.loading = true
        const response = await apiClient.get('/admin/commission-excluded-users')
        this.excludedUsers = response.data.excluded_users || []
      } catch (err) {
        console.error('Failed to fetch excluded users:', err)
      } finally {
        this.loading = false
      }
    },
    async searchUsers(query) {
      const requestId = ++this.activeSearchRequest

      try {
        this.searching = true
        const response = await apiClient.get('/admin/users', {
          params: { search: query, per_page: 10 }
        })
        if (requestId !== this.activeSearchRequest || query !== this.searchQuery.trim()) {
          return
        }
        this.searchResults = response.data.users || []
      } catch (err) {
        if (requestId !== this.activeSearchRequest) {
          return
        }
        await this.error(err.response?.data?.message || err.response?.data?.error || '搜索失败')
        console.error('Failed to search users:', err)
      } finally {
        if (requestId === this.activeSearchRequest) {
          this.searching = false
        }
      }
    },
    async addExcludedUser(user) {
      try {
        this.addingUserId = user.id
        const response = await apiClient.post('/admin/commission-excluded-users', {
          user_id: user.id
        })
        const entry = response.data.excluded_user
        if (!this.isExcluded(entry.user_id)) {
          this.excludedUsers.unshift(entry)
        }
        await this.success('已添加到提成排除列表')
      } catch (err) {
        await this.error(err.response?.data?.message || err.response?.data?.error || '添加失败')
        console.error('Failed to add excluded user:', err)
      } finally {
        this.addingUserId = null
      }
    },
    async removeExcludedUser(entry) {
      const displayName = this.getUserDisplayName(entry.user)
      const confirmed = await this.confirm(`确定将 ${displayName} 从提成排除列表移除？`, {
        type: 'warning',
        title: '移除排除用户'
      })
      if (!confirmed) return

      try {
        this.removingUserId = entry.user_id
        await apiClient.delete(`/admin/commission-excluded-users/${entry.user_id}`)
        this.excludedUsers = this.excludedUsers.filter(e => e.user_id !== entry.user_id)
        await this.success('已从提成排除列表移除')
      } catch (err) {
        await this.error(err.response?.data?.message || err.response?.data?.error || '移除失败')
        console.error('Failed to remove excluded user:', err)
      } finally {
        this.removingUserId = null
      }
    }
  }
}
</script>

<style scoped>
.excluded-users-section {
  background: white;
  border: 1px solid var(--md-outline-variant);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  margin-bottom: var(--md-spacing-xl);
}

.section-header {
  margin-bottom: var(--md-spacing-md);
}

.section-title {
  font-size: var(--md-title-size);
  font-weight: 600;
  color: var(--md-on-surface);
  margin: 0 0 var(--md-spacing-xs) 0;
}

.section-description {
  font-size: var(--md-body-size);
  color: var(--md-on-surface-variant);
  margin: 0;
}

.search-wrapper {
  position: relative;
  margin-bottom: var(--md-spacing-md);
}

.search-input {
  width: 100%;
  padding: 10px 12px;
  padding-right: 88px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
}

.search-input:focus {
  outline: none;
  border-color: #ff8c00;
  box-shadow: 0 0 0 3px rgba(255, 140, 0, 0.1);
}

.search-status {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 13px;
  color: var(--md-on-surface-variant);
  pointer-events: none;
}

.no-search-results {
  padding: 12px 16px;
  margin-bottom: var(--md-spacing-md);
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  color: var(--md-on-surface-variant);
  text-align: center;
}

.search-results {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: var(--md-spacing-md);
  overflow: hidden;
}

.search-result-item,
.excluded-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--md-spacing-md);
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
}

.search-result-item:last-child,
.excluded-item:last-child {
  border-bottom: none;
}

.user-info {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  flex: 1;
}

.user-name {
  font-weight: 600;
  color: var(--md-on-surface);
}

.user-detail,
.user-source,
.user-notes {
  font-size: 13px;
  color: var(--md-on-surface-variant);
}

.user-notes {
  font-style: italic;
}

.add-btn,
.remove-btn {
  padding: 6px 14px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
}

.add-btn {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.add-btn:hover:not(:disabled) {
  background: #10b981;
  color: white;
}

.remove-btn {
  background: rgba(220, 38, 38, 0.1);
  color: #dc2626;
  border: 1px solid rgba(220, 38, 38, 0.2);
}

.remove-btn:hover:not(:disabled) {
  background: #dc2626;
  color: white;
}

.add-btn:disabled,
.remove-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.already-excluded {
  font-size: 13px;
  color: var(--md-on-surface-variant);
}

.loading,
.empty-state {
  text-align: center;
  padding: var(--md-spacing-lg);
  color: var(--md-on-surface-variant);
}

.excluded-list {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

@media (max-width: 767px) {
  .search-result-item,
  .excluded-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .add-btn,
  .remove-btn {
    width: 100%;
  }
}
</style>
