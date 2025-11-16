<template>
  <div class="users-page">
    <div class="page-header-actions">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜索用户 (手机号/昵称)"
        class="search-input"
      />
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="filteredUsers.length === 0" class="empty-state">
      <p>暂无用户</p>
    </div>
    <div v-else class="users-list">
      <div v-for="user in filteredUsers" :key="user.id" class="user-card">
        <div class="user-avatar">{{ getUserInitial(user) }}</div>
        <div class="user-info">
          <div class="user-name-row">
            <span class="user-name">{{ user.nickname || user.phone || '未设置' }}</span>
            <span v-if="user.is_admin" class="admin-badge">管理员</span>
          </div>
          <div class="user-phone">{{ user.phone || user.email || 'N/A' }}</div>
          <div class="user-meta">
            <span v-if="!user.is_admin" class="meta-item">积分: {{ user.points || 0 }}</span>
            <span class="meta-item">注册时间: {{ formatDate(user.creation_date) }}</span>
            <span v-if="user.last_login_date" class="meta-item">最后登录: {{ formatDate(user.last_login_date) }}</span>
            <span v-if="!user.is_admin && user.order_count !== undefined" class="meta-item">订单数: {{ user.order_count || 0 }}</span>
          </div>
          <div v-if="user.roles && user.roles.length > 0" class="user-roles">
            <span v-for="role in user.roles.filter(r => r !== 'admin')" :key="role" class="role-badge" :class="role">
              {{ getRoleLabel(role) }}
            </span>
          </div>
        </div>
        <div class="user-actions">
          <button @click="viewUser(user)" class="view-btn">查看</button>
          <button v-if="user.is_admin" @click="manageRoles(user)" class="roles-btn">角色</button>
          <button v-if="user.status === 'active'" @click="banUser(user.id)" class="ban-btn">
            禁用
          </button>
          <button v-else @click="unbanUser(user.id)" class="unban-btn">
            启用
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'

export default {
  name: 'Users',
  data() {
    return {
      loading: true,
      error: null,
      users: [],
      searchQuery: ''
    }
  },
  computed: {
    filteredUsers() {
      if (!this.searchQuery) {
        return this.users
      }
      const query = this.searchQuery.toLowerCase()
      return this.users.filter(user => {
        const phone = (user.phone || '').toLowerCase()
        const nickname = (user.nickname || '').toLowerCase()
        return phone.includes(query) || nickname.includes(query)
      })
    }
  },
  mounted() {
    this.fetchUsers()
  },
  methods: {
    async fetchUsers() {
      try {
        this.loading = true
        this.error = null
        const response = await apiClient.get('/admin/users')
        this.users = response.data.users || []
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || error.message || 'Failed to load users'
        console.error('Failed to fetch users:', error)
      } finally {
        this.loading = false
      }
    },
    getUserInitial(user) {
      const name = user.nickname || user.phone || 'U'
      return name.charAt(0).toUpperCase()
    },
    viewUser(user) {
      // TODO: Implement user detail view
      alert(`View user: ${user.id}`)
    },
    async banUser(userId) {
      if (!confirm('确定要禁用这个用户吗？')) {
        return
      }

      try {
        await apiClient.post(`/admin/users/${userId}/ban`)
        await this.fetchUsers()
      } catch (error) {
        alert(error.response?.data?.message || error.response?.data?.error || '禁用失败')
        console.error('Ban user error:', error)
      }
    },
    async unbanUser(userId) {
      if (!confirm('确定要启用这个用户吗？')) {
        return
      }

      try {
        await apiClient.post(`/admin/users/${userId}/unban`)
        await this.fetchUsers()
      } catch (error) {
        alert(error.response?.data?.message || error.response?.data?.error || '启用失败')
        console.error('Unban user error:', error)
      }
    },
    formatDate(dateString) {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    },
    getRoleLabel(role) {
      const labels = {
        'admin': '管理员',
        'moderator': '版主',
        'user': '用户'
      }
      return labels[role] || role
    },
    async manageRoles(user) {
      const action = prompt(`用户: ${user.nickname || user.phone}\n当前角色: ${user.roles?.join(', ') || '无'}\n\n输入操作:\n1. 添加角色: add admin/moderator/user\n2. 移除角色: remove admin/moderator/user`)
      
      if (!action) return
      
      const parts = action.trim().split(' ')
      if (parts.length !== 2) {
        alert('格式错误，请使用: add/remove role_name')
        return
      }
      
      const [action_type, role_name] = parts
      
      try {
        if (action_type.toLowerCase() === 'add') {
          await apiClient.post(`/admin/users/${user.id}/roles`, { role: role_name })
          alert('角色添加成功')
        } else if (action_type.toLowerCase() === 'remove') {
          await apiClient.delete(`/admin/users/${user.id}/roles/${role_name}`)
          alert('角色移除成功')
        } else {
          alert('无效操作，请使用 add 或 remove')
          return
        }
        await this.fetchUsers()
      } catch (error) {
        alert(error.response?.data?.message || error.response?.data?.error || '操作失败')
        console.error('Role management error:', error)
      }
    }
  }
}
</script>

<style scoped>
.users-page {
  max-width: 1200px;
}

.page-header-actions {
  margin-bottom: var(--md-spacing-lg);
}

.search-input {
  width: 100%;
  max-width: 400px;
  padding: var(--md-spacing-md);
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  background: var(--md-surface);
  color: var(--md-on-surface);
}

.search-input:focus {
  outline: none;
  border-color: var(--md-primary);
  border-width: 2px;
  box-shadow: 0 0 0 4px rgba(255, 140, 0, 0.12);
}

.loading, .error, .empty-state {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.users-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.user-card {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
  display: flex;
  align-items: center;
  gap: var(--md-spacing-lg);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.user-card:hover {
  box-shadow: var(--md-elevation-2);
}

.user-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: var(--md-primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--md-title-size);
  font-weight: 500;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
}

.user-name-row {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  margin-bottom: var(--md-spacing-xs);
}

.user-name {
  font-size: var(--md-title-size);
  font-weight: 500;
  color: var(--md-on-surface);
}

.admin-badge {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  background: var(--md-primary);
  color: white;
  border-radius: var(--md-radius-sm);
  font-size: var(--md-label-size);
  font-weight: 500;
}

.user-roles {
  display: flex;
  gap: var(--md-spacing-xs);
  margin-top: var(--md-spacing-sm);
  flex-wrap: wrap;
}

.role-badge {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  border-radius: var(--md-radius-sm);
  font-size: var(--md-label-size);
  font-weight: 500;
}

.role-badge.admin {
  background: rgba(255, 140, 0, 0.2);
  color: var(--md-primary);
}

.role-badge.moderator {
  background: rgba(33, 150, 243, 0.2);
  color: #2196F3;
}

.role-badge.user {
  background: var(--md-surface-variant);
  color: var(--md-on-surface-variant);
}

.user-phone {
  font-size: var(--md-body-size);
  color: var(--md-on-surface-variant);
  margin-bottom: var(--md-spacing-sm);
}

.user-meta {
  display: flex;
  gap: var(--md-spacing-md);
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.meta-item {
  display: flex;
  align-items: center;
}

.user-actions {
  display: flex;
  gap: var(--md-spacing-sm);
}

.view-btn, .ban-btn, .unban-btn, .roles-btn {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-label-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.roles-btn {
  background: rgba(255, 140, 0, 0.1);
  color: var(--md-primary);
}

.roles-btn:hover {
  background: rgba(255, 140, 0, 0.2);
}

.view-btn {
  background: var(--md-surface-variant);
  color: var(--md-on-surface);
}

.view-btn:hover {
  background: var(--md-outline);
  color: white;
}

.ban-btn {
  background: #FFEBEE;
  color: #C62828;
}

.ban-btn:hover {
  background: #C62828;
  color: white;
}

.unban-btn {
  background: #E8F5E9;
  color: #2E7D32;
}

.unban-btn:hover {
  background: #2E7D32;
  color: white;
}
</style>

