<template>
  <div class="users-page">
    <!-- Tabs -->
    <div class="tabs">
      <button 
        @click="activeTab = 'users'" 
        :class="['tab', { active: activeTab === 'users' }]"
      >
        用户列表
      </button>
      <button 
        @click="activeTab = 'otp-stats'" 
        :class="['tab', { active: activeTab === 'otp-stats' }]"
      >
        OTP使用统计
      </button>
    </div>

    <!-- User List Tab -->
    <div v-if="activeTab === 'users'" class="tab-content">
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
          <div v-if="user.wechat" class="user-wechat">微信号: {{ user.wechat }}</div>
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
          <button v-if="!user.is_admin" @click="impersonateUser(user.id)" class="impersonate-btn">代登录</button>
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

    <!-- OTP Stats Tab -->
    <div v-if="activeTab === 'otp-stats'" class="tab-content">
      <OTPStats />
    </div>

    <!-- Role Management Modal -->
    <div v-if="showRoleModal" class="modal-overlay" @click="closeRoleModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>管理角色</h2>
          <button @click="closeRoleModal" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="role-info">
            <p><strong>用户:</strong> {{ roleModalUser?.nickname || roleModalUser?.phone }}</p>
            <p><strong>当前角色:</strong> {{ roleModalUser?.roles?.join(', ') || '无' }}</p>
          </div>
          <div class="role-form">
            <label>操作:</label>
            <select v-model="roleAction" class="role-select">
              <option value="">请选择操作</option>
              <option value="add">添加角色</option>
              <option value="remove">移除角色</option>
            </select>
            <label>角色:</label>
            <select v-model="roleName" class="role-select">
              <option value="">请选择角色</option>
              <option value="admin">管理员</option>
              <option value="moderator">版主</option>
              <option value="user">用户</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeRoleModal" class="cancel-btn">取消</button>
          <button @click="executeRoleAction" class="confirm-btn" :disabled="!roleAction || !roleName">确定</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'
import OTPStats from './OTPStats.vue'
import { useModal } from '../composables/useModal'
import { formatDateTimeEST_CN } from '../utils/date'

export default {
  name: 'Users',
  components: {
    OTPStats
  },
  setup() {
    const { confirm, success, error, alert } = useModal()
    return { confirm, success, error, $alert: alert }
  },
  data() {
    return {
      activeTab: 'users',
      loading: true,
      error: null,
      users: [],
      searchQuery: '',
      showRoleModal: false,
      roleModalUser: null,
      roleAction: '',
      roleName: ''
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
    async viewUser(user) {
      await this.$alert(`User ID: ${user.id}\nPhone: ${user.phone}\nNickname: ${user.nickname || 'N/A'}`, {
        title: '用户详情',
        type: 'info'
      })
    },
    async banUser(userId) {
      const confirmed = await this.confirm('确定要禁用这个用户吗？', {
        type: 'warning'
      })
      if (!confirmed) {
        return
      }

      try {
        await apiClient.post(`/admin/users/${userId}/ban`)
        await this.success('用户已禁用')
        await this.fetchUsers()
      } catch (error) {
        await this.error(error.response?.data?.message || error.response?.data?.error || '禁用失败')
        console.error('Ban user error:', error)
      }
    },
    async unbanUser(userId) {
      const confirmed = await this.confirm('确定要启用这个用户吗？')
      if (!confirmed) {
        return
      }

      try {
        await apiClient.post(`/admin/users/${userId}/unban`)
        await this.success('用户已启用')
        await this.fetchUsers()
      } catch (error) {
        await this.error(error.response?.data?.message || error.response?.data?.error || '启用失败')
        console.error('Unban user error:', error)
      }
    },
    formatDate(dateString) {
      return formatDateTimeEST_CN(dateString) || 'N/A'
    },
    getRoleLabel(role) {
      const labels = {
        'admin': '管理员',
        'moderator': '版主',
        'user': '用户'
      }
      return labels[role] || role
    },
    manageRoles(user) {
      this.roleModalUser = user
      this.roleAction = ''
      this.roleName = ''
      this.showRoleModal = true
    },
    closeRoleModal() {
      this.showRoleModal = false
      this.roleModalUser = null
      this.roleAction = ''
      this.roleName = ''
    },
    async executeRoleAction() {
      if (!this.roleAction || !this.roleName || !this.roleModalUser) {
        await this.$alert('请选择操作和角色', {
          type: 'warning',
          title: '输入错误'
        })
        return
      }
      
      try {
        if (this.roleAction === 'add') {
          await apiClient.post(`/admin/users/${this.roleModalUser.id}/roles`, { role: this.roleName })
          await this.success('角色添加成功')
        } else if (this.roleAction === 'remove') {
          await apiClient.delete(`/admin/users/${this.roleModalUser.id}/roles/${this.roleName}`)
          await this.success('角色移除成功')
        }
        await this.fetchUsers()
        this.closeRoleModal()
      } catch (error) {
        await this.error(error.response?.data?.message || error.response?.data?.error || '操作失败')
        console.error('Role management error:', error)
      }
    },
    async impersonateUser(userId) {
      const confirmed = await this.confirm('确定要以该用户身份登录吗？您将被重定向到用户端应用。', {
        type: 'warning',
        title: '代登录确认'
      })
      if (!confirmed) {
        return
      }

      try {
        const response = await apiClient.post(`/admin/users/${userId}/impersonate`)
        const { redirect_url } = response.data
        
        // Redirect to app frontend with token
        window.location.href = redirect_url
      } catch (error) {
        await this.error(error.response?.data?.message || error.response?.data?.error || '代登录失败')
        console.error('Impersonate user error:', error)
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
  background: #FFFFFF;
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  display: flex;
  align-items: center;
  gap: var(--md-spacing-lg);
  transition: var(--transition-normal);
  border: none;
  position: relative;
  overflow: hidden;
}

.user-card:hover {
  background: #FFFFFF;
  box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.16), 0px 2px 4px rgba(0, 0, 0, 0.23);
  transform: translateY(-2px);
}

.user-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.04);
  color: var(--md-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--md-title-size);
  font-weight: 500;
  flex-shrink: 0;
  transition: var(--transition-normal);
}

.user-card:hover .user-avatar {
  transform: scale(1.05);
  background: rgba(0, 0, 0, 0.06);
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

.user-wechat {
  font-size: var(--md-body-size);
  color: #2E7D32;
  margin-bottom: var(--md-spacing-sm);
  font-weight: 500;
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

.view-btn, .ban-btn, .unban-btn, .roles-btn, .impersonate-btn {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-label-size);
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition-fast);
  position: relative;
  overflow: hidden;
}

.roles-btn {
  background: rgba(255, 140, 0, 0.1);
  color: var(--md-primary);
  border: 1px solid rgba(255, 140, 0, 0.3);
}

.roles-btn:hover {
  background: var(--gradient-primary);
  color: white;
  border-color: transparent;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 140, 0, 0.3);
}

.impersonate-btn {
  background: rgba(33, 150, 243, 0.1);
  color: #2196F3;
  border: 1px solid rgba(33, 150, 243, 0.3);
}

.impersonate-btn:hover {
  background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
  color: white;
  border-color: transparent;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
}

.view-btn {
  background: rgba(0, 0, 0, 0.05);
  color: rgba(0, 0, 0, 0.87);
  border: 1px solid rgba(0, 0, 0, 0.12);
}

.view-btn:hover {
  background: rgba(0, 0, 0, 0.08);
  border-color: rgba(0, 0, 0, 0.2);
}

.ban-btn {
  background: rgba(255, 68, 68, 0.1);
  color: #C62828;
  border: 1px solid rgba(255, 68, 68, 0.3);
}

.ban-btn:hover {
  background: var(--gradient-accent);
  color: white;
  border-color: transparent;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 68, 68, 0.3);
}

.unban-btn {
  background: rgba(17, 153, 142, 0.1);
  color: #2E7D32;
  border: 1px solid rgba(17, 153, 142, 0.3);
}

.unban-btn:hover {
  background: var(--gradient-success);
  color: white;
  border-color: transparent;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(17, 153, 142, 0.3);
}

/* Tabs */
.tabs {
  display: flex;
  gap: var(--md-spacing-xs);
  margin-bottom: var(--md-spacing-lg);
  border-bottom: 2px solid var(--md-outline-variant);
}

.tab {
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  font-size: var(--md-body-size);
  font-weight: 500;
  color: var(--md-on-surface-variant);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  margin-bottom: -2px;
}

.tab:hover {
  color: var(--md-on-surface);
  background: var(--md-surface-variant);
}

.tab.active {
  color: var(--md-primary);
  border-bottom-color: var(--md-primary);
}

.tab-content {
  /* Tab content wrapper - styles applied via scoped styles */
  display: block;
}

/* Mobile Responsive Styles */
@media (max-width: 767px) {
  .search-input {
    max-width: 100%;
  }

  .user-card {
    flex-direction: column;
    align-items: flex-start;
    padding: var(--md-spacing-md);
  }

  .user-avatar {
    width: 50px;
    height: 50px;
    font-size: var(--md-body-size);
  }

  .user-info {
    width: 100%;
  }

  .user-name {
    font-size: var(--md-body-size);
  }

  .user-meta {
    flex-direction: column;
    gap: var(--md-spacing-xs);
  }

  .user-actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .view-btn,
  .ban-btn,
  .unban-btn,
  .roles-btn,
  .impersonate-btn {
    flex: 1 1 auto;
    min-width: 80px;
  }

  .tabs {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .tab {
    padding: var(--md-spacing-sm) var(--md-spacing-md);
    white-space: nowrap;
    font-size: var(--md-label-size);
  }
}

@media (max-width: 480px) {
  .user-card {
    padding: var(--md-spacing-sm);
  }

  .user-avatar {
    width: 40px;
    height: 40px;
  }

  .user-name-row {
    flex-wrap: wrap;
  }

  .user-actions {
    flex-direction: column;
  }

  .view-btn,
  .ban-btn,
  .unban-btn,
  .roles-btn,
  .impersonate-btn {
    width: 100%;
  }
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 16px;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 500px;
  width: 100%;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  color: #6b7280;
  font-size: 24px;
  line-height: 1;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #111827;
}

.modal-body {
  padding: 24px;
}

.role-info {
  margin-bottom: 20px;
}

.role-info p {
  margin: 8px 0;
  color: #374151;
  font-size: 14px;
}

.role-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.role-form label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.role-select {
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  color: #111827;
  background: white;
  cursor: pointer;
  transition: border-color 0.2s;
}

.role-select:hover {
  border-color: #9ca3af;
}

.role-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.modal-footer {
  padding: 16px 24px;
  background: #f9fafb;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.cancel-btn,
.confirm-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.cancel-btn:hover {
  background: #f3f4f6;
}

.confirm-btn {
  background: #3b82f6;
  color: white;
}

.confirm-btn:hover:not(:disabled) {
  background: #2563eb;
}

.confirm-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>

