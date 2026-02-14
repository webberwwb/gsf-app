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
        <div class="search-and-actions">
          <div class="search-row">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索用户 (手机号/昵称/微信号)"
              class="search-input"
            />
            <button @click="toggleCheckboxes" class="add-source-btn" :class="{ 'active': showCheckboxes }">
              {{ showCheckboxes ? '取消' : '管理获客渠道' }}
            </button>
          </div>
          <div class="bulk-actions" v-if="showCheckboxes && selectedUsers.length > 0">
            <span class="selected-count">已选择 {{ selectedUsers.length }} 个用户</span>
            <button @click="showBulkAssignModal = true" class="bulk-assign-btn">
              批量分配来源
            </button>
            <button @click="clearSelection" class="clear-selection-btn">清除选择</button>
          </div>
        </div>
      </div>

      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else-if="filteredUsers.length === 0" class="empty-state">
        <p>暂无用户</p>
      </div>
      <div v-else>
        <div class="users-list">
          <div v-for="user in filteredUsers" :key="user.id" class="user-card" :class="{ 'selected': isUserSelected(user.id) }">
            <div class="user-checkbox" v-if="showCheckboxes">
              <input
                type="checkbox"
                :checked="isUserSelected(user.id)"
                @change="toggleUserSelection(user.id)"
                class="checkbox-input"
              />
            </div>
            <div class="user-avatar">{{ getUserInitial(user) }}</div>
            <div class="user-info">
              <div class="user-name-row">
                <span class="user-name">{{ user.nickname || user.phone || '未设置' }}</span>
                <span v-if="user.is_admin" class="admin-badge">管理员</span>
                <span v-else class="normal-user-badge">普通用户</span>
                <span v-if="user.user_source" class="source-badge" :class="user.user_source === '花泽' ? 'source-huaze' : 'source-default'">
                  {{ user.user_source }}
                </span>
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
              <button @click="editUser(user)" class="edit-btn">编辑</button>
              <button v-if="!user.is_admin" @click="impersonateUser(user.id)" class="impersonate-btn">代登录</button>
              <button @click="manageRoles(user)" class="roles-btn">角色</button>
              <button v-if="user.status === 'active'" @click="banUser(user.id)" class="ban-btn">
                禁用
              </button>
              <button v-else @click="unbanUser(user.id)" class="unban-btn">
                启用
              </button>
            </div>
          </div>
        </div>
        
        <!-- Loading more indicator -->
        <div v-if="loadingMore" class="loading-more">
          加载更多...
        </div>
        
        <!-- End of list indicator -->
        <div v-else-if="!hasMore && users.length > 0" class="end-of-list">
          已显示全部 {{ totalUsers }} 个用户
        </div>
      </div>
    </div>

    <!-- OTP Stats Tab -->
    <div v-if="activeTab === 'otp-stats'" class="tab-content">
      <OTPStats />
    </div>

    <!-- Bulk Assign Source Modal -->
    <div v-if="showBulkAssignModal" class="modal-overlay" @click="closeBulkAssignModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>批量分配用户来源</h2>
          <button @click="closeBulkAssignModal" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="bulk-assign-info">
            <p><strong>已选择用户:</strong> {{ selectedUsers.length }} 个</p>
          </div>
          <div class="bulk-assign-form">
            <label>用户来源:</label>
            <select v-model="bulkAssignSource" class="role-select">
              <option value="">请选择来源</option>
              <option value="花泽">花泽</option>
              <option value="default">默认</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeBulkAssignModal" class="cancel-btn">取消</button>
          <button @click="executeBulkAssign" class="confirm-btn" :disabled="!bulkAssignSource">确定</button>
        </div>
      </div>
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
              <option value="user">普通用户</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeRoleModal" class="cancel-btn">取消</button>
          <button @click="executeRoleAction" class="confirm-btn" :disabled="!roleAction || !roleName">确定</button>
        </div>
      </div>
    </div>

    <!-- Edit User Modal -->
    <div v-if="showEditModal" class="modal-overlay" @click="closeEditModal">
      <div class="modal-content edit-modal" @click.stop>
        <div class="modal-header">
          <h2>编辑用户信息</h2>
          <button @click="closeEditModal" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="edit-form">
            <div class="form-group">
              <label>手机号:</label>
              <input v-model="editForm.phone" type="text" class="form-input" placeholder="手机号" />
            </div>
            <div class="form-group">
              <label>昵称:</label>
              <input v-model="editForm.nickname" type="text" class="form-input" placeholder="昵称" />
            </div>
            <div class="form-group">
              <label>邮箱:</label>
              <input v-model="editForm.email" type="email" class="form-input" placeholder="邮箱" />
            </div>
            <div class="form-group">
              <label>微信号:</label>
              <input v-model="editForm.wechat" type="text" class="form-input" placeholder="微信号" />
            </div>
            <div class="form-group">
              <label>积分:</label>
              <input v-model.number="editForm.points" type="number" class="form-input" placeholder="积分" min="0" />
            </div>
            <div class="form-group">
              <label>用户来源:</label>
              <select v-model="editForm.user_source" class="form-input">
                <option value="default">默认</option>
                <option value="花泽">花泽</option>
              </select>
            </div>
            <div class="form-group">
              <label>状态:</label>
              <select v-model="editForm.status" class="form-input">
                <option value="active">激活</option>
                <option value="banned">禁用</option>
                <option value="inactive">未激活</option>
              </select>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeEditModal" class="cancel-btn">取消</button>
          <button @click="saveUserEdit" class="confirm-btn">保存</button>
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
      selectedUsers: [],
      showCheckboxes: false,
      showRoleModal: false,
      roleModalUser: null,
      roleAction: '',
      roleName: '',
      showBulkAssignModal: false,
      bulkAssignSource: '',
      showEditModal: false,
      editForm: {
        phone: '',
        nickname: '',
        email: '',
        wechat: '',
        points: 0,
        user_source: 'default',
        status: 'active'
      },
      editingUser: null,
      // Pagination state
      currentPage: 1,
      perPage: 50,
      totalUsers: 0,
      hasMore: true,
      loadingMore: false
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
        const wechat = (user.wechat || '').toLowerCase()
        return phone.includes(query) || nickname.includes(query) || wechat.includes(query)
      })
    }
  },
  watch: {
    searchQuery() {
      // Reset pagination when search query changes
      // Note: We're using client-side filtering, so no need to refetch
      // If you want server-side search, uncomment the line below
      // this.fetchUsers(true)
    }
  },
  mounted() {
    this.fetchUsers()
    // Set up infinite scroll
    window.addEventListener('scroll', this.handleScroll)
  },
  beforeUnmount() {
    // Clean up scroll listener
    window.removeEventListener('scroll', this.handleScroll)
  },
  methods: {
    async fetchUsers(reset = true) {
      try {
        if (reset) {
          this.loading = true
          this.currentPage = 1
          this.users = []
          this.hasMore = true
        } else {
          this.loadingMore = true
        }
        
        this.error = null
        const params = {
          page: this.currentPage,
          per_page: this.perPage
        }
        
        const response = await apiClient.get('/admin/users', { params })
        const newUsers = response.data.users || []
        const pagination = response.data.pagination
        
        if (reset) {
          this.users = newUsers
        } else {
          this.users = [...this.users, ...newUsers]
        }
        
        // Update pagination state
        if (pagination) {
          this.totalUsers = pagination.total
          this.hasMore = pagination.page < pagination.pages
        } else {
          // Fallback if pagination info is missing
          this.hasMore = newUsers.length === this.perPage
        }
        
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || error.message || 'Failed to load users'
        console.error('Failed to fetch users:', error)
      } finally {
        this.loading = false
        this.loadingMore = false
      }
    },
    async loadMoreUsers() {
      if (this.loadingMore || !this.hasMore) return
      
      this.currentPage++
      await this.fetchUsers(false)
    },
    handleScroll() {
      // Check if user has scrolled near the bottom
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop
      const windowHeight = window.innerHeight
      const documentHeight = document.documentElement.scrollHeight
      
      // Trigger when user is 300px from bottom
      if (scrollTop + windowHeight >= documentHeight - 300) {
        this.loadMoreUsers()
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
        'user': '普通用户'
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
    },
    toggleUserSelection(userId) {
      const index = this.selectedUsers.indexOf(userId)
      if (index > -1) {
        this.selectedUsers.splice(index, 1)
      } else {
        this.selectedUsers.push(userId)
      }
    },
    isUserSelected(userId) {
      return this.selectedUsers.includes(userId)
    },
    clearSelection() {
      this.selectedUsers = []
    },
    toggleCheckboxes() {
      this.showCheckboxes = !this.showCheckboxes
      if (!this.showCheckboxes) {
        // Clear selection when hiding checkboxes
        this.selectedUsers = []
      }
    },
    closeBulkAssignModal() {
      this.showBulkAssignModal = false
      this.bulkAssignSource = ''
    },
    async executeBulkAssign() {
      if (!this.bulkAssignSource || this.selectedUsers.length === 0) {
        await this.$alert('请选择用户来源', {
          type: 'warning',
          title: '输入错误'
        })
        return
      }
      
      try {
        await apiClient.post('/admin/users/bulk-assign-source', {
          user_ids: this.selectedUsers,
          user_source: this.bulkAssignSource
        })
        await this.success(`成功为 ${this.selectedUsers.length} 个用户分配来源`)
        await this.fetchUsers()
        this.clearSelection()
        this.closeBulkAssignModal()
      } catch (error) {
        await this.error(error.response?.data?.message || error.response?.data?.error || '批量分配失败')
        console.error('Bulk assign error:', error)
      }
    },
    editUser(user) {
      this.editingUser = user
      this.editForm = {
        phone: user.phone || '',
        nickname: user.nickname || '',
        email: user.email || '',
        wechat: user.wechat || '',
        points: user.points || 0,
        user_source: user.user_source || 'default',
        status: user.status || 'active'
      }
      this.showEditModal = true
    },
    closeEditModal() {
      this.showEditModal = false
      this.editingUser = null
      this.editForm = {
        phone: '',
        nickname: '',
        email: '',
        wechat: '',
        points: 0,
        user_source: 'default',
        status: 'active'
      }
    },
    async saveUserEdit() {
      if (!this.editingUser) {
        await this.$alert('无效的用户', {
          type: 'warning',
          title: '错误'
        })
        return
      }
      
      try {
        // Create update payload with only changed fields
        const updateData = {}
        
        if (this.editForm.phone !== this.editingUser.phone) {
          updateData.phone = this.editForm.phone || null
        }
        if (this.editForm.nickname !== this.editingUser.nickname) {
          updateData.nickname = this.editForm.nickname || null
        }
        if (this.editForm.email !== this.editingUser.email) {
          updateData.email = this.editForm.email || null
        }
        if (this.editForm.wechat !== this.editingUser.wechat) {
          updateData.wechat = this.editForm.wechat || null
        }
        if (this.editForm.points !== this.editingUser.points) {
          // Handle empty/NaN values - treat as 0
          updateData.points = parseInt(this.editForm.points) || 0
        }
        if (this.editForm.user_source !== this.editingUser.user_source) {
          updateData.user_source = this.editForm.user_source
        }
        if (this.editForm.status !== this.editingUser.status) {
          updateData.status = this.editForm.status
        }
        
        // If no changes, just close modal
        if (Object.keys(updateData).length === 0) {
          await this.$alert('没有任何更改', {
            type: 'info',
            title: '提示'
          })
          this.closeEditModal()
          return
        }
        
        await apiClient.patch(`/admin/users/${this.editingUser.id}`, updateData)
        await this.success('用户信息更新成功')
        await this.fetchUsers()
        this.closeEditModal()
      } catch (error) {
        await this.error(error.response?.data?.message || error.response?.data?.error || '更新失败')
        console.error('Update user error:', error)
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

.search-and-actions {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.search-row {
  display: flex;
  gap: var(--md-spacing-md);
  align-items: center;
}

.add-source-btn {
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition-fast);
  background: rgba(255, 140, 0, 0.1);
  color: var(--md-primary);
  border: 1px solid rgba(255, 140, 0, 0.3);
  white-space: nowrap;
}

.add-source-btn:hover {
  background: rgba(255, 140, 0, 0.2);
  border-color: rgba(255, 140, 0, 0.5);
}

.add-source-btn.active {
  background: var(--gradient-primary);
  color: white;
  border-color: transparent;
}

.add-source-btn.active:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 140, 0, 0.3);
}

.bulk-actions {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
  padding: var(--md-spacing-md);
  background: rgba(255, 140, 0, 0.1);
  border-radius: var(--md-radius-md);
  border: 1px solid rgba(255, 140, 0, 0.3);
}

.selected-count {
  font-size: var(--md-body-size);
  font-weight: 500;
  color: var(--md-primary);
}

.bulk-assign-btn,
.clear-selection-btn {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-label-size);
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition-fast);
}

.bulk-assign-btn {
  background: var(--gradient-primary);
  color: white;
}

.bulk-assign-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 140, 0, 0.3);
}

.clear-selection-btn {
  background: rgba(0, 0, 0, 0.05);
  color: rgba(0, 0, 0, 0.87);
  border: 1px solid rgba(0, 0, 0, 0.12);
}

.clear-selection-btn:hover {
  background: rgba(0, 0, 0, 0.08);
  border-color: rgba(0, 0, 0, 0.2);
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

.loading-more {
  text-align: center;
  padding: var(--md-spacing-lg);
  color: var(--md-on-surface-variant);
  font-size: var(--md-body-size);
}

.end-of-list {
  text-align: center;
  padding: var(--md-spacing-lg);
  color: var(--md-on-surface-variant);
  font-size: var(--md-label-size);
  border-top: 1px solid var(--md-outline-variant);
  margin-top: var(--md-spacing-md);
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
  border: 2px solid transparent;
  position: relative;
  overflow: hidden;
}

.user-card.selected {
  border-color: var(--md-primary);
  background: rgba(255, 140, 0, 0.05);
}

.user-checkbox {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
}

.checkbox-input {
  width: 20px;
  height: 20px;
  cursor: pointer;
  accent-color: var(--md-primary);
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

.normal-user-badge {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  background: rgba(0, 0, 0, 0.08);
  color: rgba(0, 0, 0, 0.6);
  border-radius: var(--md-radius-sm);
  font-size: var(--md-label-size);
  font-weight: 500;
}

.source-badge {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  border-radius: var(--md-radius-sm);
  font-size: var(--md-label-size);
  font-weight: 500;
}

.source-badge.source-huaze {
  background: rgba(156, 39, 176, 0.2);
  color: #9c27b0;
}

.source-badge.source-default {
  background: rgba(0, 0, 0, 0.05);
  color: rgba(0, 0, 0, 0.6);
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

.view-btn, .ban-btn, .unban-btn, .roles-btn, .impersonate-btn, .edit-btn {
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

.edit-btn {
  background: rgba(76, 175, 80, 0.1);
  color: #2E7D32;
  border: 1px solid rgba(76, 175, 80, 0.3);
}

.edit-btn:hover {
  background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
  color: white;
  border-color: transparent;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
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
  .search-row {
    flex-direction: column;
    align-items: stretch;
  }

  .search-input {
    max-width: 100%;
  }

  .add-source-btn {
    width: 100%;
  }

  .bulk-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .bulk-assign-btn,
  .clear-selection-btn {
    width: 100%;
  }

  .user-card {
    flex-direction: column;
    align-items: flex-start;
    padding: var(--md-spacing-md);
  }

  .user-checkbox {
    position: absolute;
    top: var(--md-spacing-md);
    right: var(--md-spacing-md);
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
  .impersonate-btn,
  .edit-btn {
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
  .impersonate-btn,
  .edit-btn {
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

.role-form,
.bulk-assign-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.bulk-assign-info {
  margin-bottom: 20px;
}

.bulk-assign-info p {
  margin: 8px 0;
  color: #374151;
  font-size: 14px;
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

.edit-modal {
  max-width: 600px;
}

.edit-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.form-input {
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  color: #111827;
  background: white;
  transition: border-color 0.2s;
}

.form-input:hover {
  border-color: #9ca3af;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-input[type="number"] {
  -moz-appearance: textfield;
}

.form-input[type="number"]::-webkit-outer-spin-button,
.form-input[type="number"]::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
</style>

