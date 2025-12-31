<template>
  <div class="suppliers-page">
    <div class="page-header-actions">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜索供应商 (名称/联系人/电话/邮箱)"
        class="search-input"
      />
      <button @click="openAddModal" class="add-btn">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
        </svg>
        添加供应商
      </button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="filteredSuppliers.length === 0" class="empty-state">
      <p>暂无供应商</p>
      <button @click="openAddModal" class="add-first-btn">添加第一个供应商</button>
    </div>
    <div v-else class="suppliers-table-container">
      <table class="suppliers-table">
        <thead>
          <tr>
            <th>名称</th>
            <th>联系人</th>
            <th>电话</th>
            <th>邮箱</th>
            <th>地址</th>
            <th>状态</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="supplier in filteredSuppliers" :key="supplier.id" :class="{ inactive: !supplier.is_active }">
            <td>{{ supplier.name }}</td>
            <td>{{ supplier.contact_person || '-' }}</td>
            <td>{{ supplier.phone || '-' }}</td>
            <td>{{ supplier.email || '-' }}</td>
            <td class="address-cell">{{ supplier.address || '-' }}</td>
            <td>
              <span :class="['status-badge', supplier.is_active ? 'active' : 'inactive']">
                {{ supplier.is_active ? '启用' : '禁用' }}
              </span>
            </td>
            <td>{{ formatDate(supplier.created_at) }}</td>
            <td>
              <div class="action-buttons">
                <button @click="editSupplier(supplier)" class="edit-btn">编辑</button>
                <button @click="toggleSupplierStatus(supplier)" :class="supplier.is_active ? 'deactivate-btn' : 'activate-btn'">
                  {{ supplier.is_active ? '禁用' : '启用' }}
                </button>
                <button @click="deleteSupplier(supplier.id)" class="delete-btn">删除</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Supplier Form Modal -->
    <div v-if="showModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>{{ editingSupplier ? '编辑供应商' : '添加供应商' }}</h2>
          <button @click="closeModal" class="close-btn">×</button>
        </div>
        <form @submit.prevent="saveSupplier" class="supplier-form">
          <div class="form-group">
            <label>名称 <span class="required">*</span></label>
            <input v-model="formData.name" type="text" required placeholder="供应商名称" />
          </div>
          <div class="form-group">
            <label>联系人</label>
            <input v-model="formData.contact_person" type="text" placeholder="联系人姓名" />
          </div>
          <div class="form-group">
            <label>电话</label>
            <input v-model="formData.phone" type="tel" placeholder="联系电话" />
          </div>
          <div class="form-group">
            <label>邮箱</label>
            <input v-model="formData.email" type="email" placeholder="邮箱地址" />
          </div>
          <div class="form-group">
            <label>地址</label>
            <textarea v-model="formData.address" rows="3" placeholder="供应商地址"></textarea>
          </div>
          <div class="form-group">
            <label>备注</label>
            <textarea v-model="formData.notes" rows="3" placeholder="备注信息"></textarea>
          </div>
          <div class="form-group">
            <label>
              <input v-model="formData.is_active" type="checkbox" />
              启用
            </label>
          </div>
          <div class="form-actions">
            <button type="button" @click="closeModal" class="cancel-btn">取消</button>
            <button type="submit" class="save-btn">保存</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'
import { formatDateTimeEST_CN } from '../utils/date'

export default {
  name: 'Suppliers',
  data() {
    return {
      loading: true,
      error: null,
      suppliers: [],
      searchQuery: '',
      showModal: false,
      editingSupplier: null,
      formData: {
        name: '',
        contact_person: '',
        phone: '',
        email: '',
        address: '',
        notes: '',
        is_active: true
      }
    }
  },
  computed: {
    filteredSuppliers() {
      if (!this.searchQuery) {
        return this.suppliers
      }
      const query = this.searchQuery.toLowerCase()
      return this.suppliers.filter(supplier => {
        const name = (supplier.name || '').toLowerCase()
        const contact = (supplier.contact_person || '').toLowerCase()
        const phone = (supplier.phone || '').toLowerCase()
        const email = (supplier.email || '').toLowerCase()
        return name.includes(query) || contact.includes(query) || phone.includes(query) || email.includes(query)
      })
    }
  },
  mounted() {
    this.fetchSuppliers()
  },
  methods: {
    async fetchSuppliers() {
      try {
        this.loading = true
        this.error = null
        const response = await apiClient.get('/admin/suppliers')
        this.suppliers = response.data.suppliers || []
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || error.message || 'Failed to load suppliers'
        console.error('Failed to fetch suppliers:', error)
      } finally {
        this.loading = false
      }
    },
    openAddModal() {
      this.editingSupplier = null
      this.formData = {
        name: '',
        contact_person: '',
        phone: '',
        email: '',
        address: '',
        notes: '',
        is_active: true
      }
      this.showModal = true
    },
    editSupplier(supplier) {
      this.editingSupplier = supplier
      this.formData = {
        name: supplier.name,
        contact_person: supplier.contact_person || '',
        phone: supplier.phone || '',
        email: supplier.email || '',
        address: supplier.address || '',
        notes: supplier.notes || '',
        is_active: supplier.is_active
      }
      this.showModal = true
    },
    closeModal() {
      this.showModal = false
      this.editingSupplier = null
    },
    async saveSupplier() {
      try {
        if (this.editingSupplier) {
          await apiClient.put(`/admin/suppliers/${this.editingSupplier.id}`, this.formData)
        } else {
          await apiClient.post('/admin/suppliers', this.formData)
        }
        await this.fetchSuppliers()
        this.closeModal()
      } catch (error) {
        alert(error.response?.data?.message || error.response?.data?.error || '保存失败')
        console.error('Save supplier error:', error)
      }
    },
    async toggleSupplierStatus(supplier) {
      const action = supplier.is_active ? '禁用' : '启用'
      if (!confirm(`确定要${action}这个供应商吗？`)) {
        return
      }

      try {
        await apiClient.put(`/admin/suppliers/${supplier.id}`, {
          is_active: !supplier.is_active
        })
        await this.fetchSuppliers()
      } catch (error) {
        alert(error.response?.data?.message || error.response?.data?.error || `${action}失败`)
        console.error('Toggle supplier status error:', error)
      }
    },
    async deleteSupplier(id) {
      if (!confirm('确定要删除这个供应商吗？删除后供应商将被禁用。')) {
        return
      }

      try {
        await apiClient.delete(`/admin/suppliers/${id}`)
        await this.fetchSuppliers()
      } catch (error) {
        alert(error.response?.data?.message || error.response?.data?.error || '删除失败')
        console.error('Delete supplier error:', error)
      }
    },
    formatDate(dateString) {
      return formatDateTimeEST_CN(dateString) || 'N/A'
    }
  }
}
</script>

<style scoped>
.suppliers-page {
  max-width: 1400px;
}

.page-header-actions {
  margin-bottom: var(--md-spacing-lg);
  display: flex;
  gap: var(--md-spacing-md);
  align-items: center;
}

.search-input {
  flex: 1;
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

.add-btn {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  background: var(--md-primary);
  color: white;
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--md-elevation-2);
}

.add-btn:hover {
  background: #FF7F00;
  box-shadow: var(--md-elevation-3);
  transform: translateY(-2px);
}

.add-btn svg {
  width: 20px;
  height: 20px;
}

.loading, .error, .empty-state {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.add-first-btn {
  margin-top: var(--md-spacing-md);
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  background: var(--md-primary);
  color: white;
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
}

.suppliers-table-container {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  overflow: hidden;
  box-shadow: var(--md-elevation-1);
}

.suppliers-table {
  width: 100%;
  border-collapse: collapse;
}

.suppliers-table thead {
  background: var(--md-surface-variant);
}

.suppliers-table th {
  padding: var(--md-spacing-md);
  text-align: left;
  font-weight: 500;
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  border-bottom: 1px solid var(--md-outline);
}

.suppliers-table td {
  padding: var(--md-spacing-md);
  border-bottom: 1px solid var(--md-outline-variant);
  font-size: var(--md-body-size);
  color: var(--md-on-surface);
}

.suppliers-table tbody tr:hover {
  background: var(--md-surface-variant);
}

.suppliers-table tbody tr.inactive {
  opacity: 0.6;
}

.address-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: var(--md-radius-sm);
  font-size: var(--md-label-size);
  font-weight: 500;
}

.status-badge.active {
  background: #E8F5E9;
  color: #2E7D32;
}

.status-badge.inactive {
  background: #FFEBEE;
  color: #C62828;
}

.action-buttons {
  display: flex;
  gap: var(--md-spacing-xs);
  flex-wrap: wrap;
}

.edit-btn, .activate-btn, .deactivate-btn, .delete-btn {
  padding: var(--md-spacing-xs) var(--md-spacing-sm);
  border: none;
  border-radius: var(--md-radius-sm);
  font-size: var(--md-label-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.edit-btn {
  background: rgba(0, 0, 0, 0.05);
  color: rgba(0, 0, 0, 0.87);
  border: 1px solid rgba(0, 0, 0, 0.12);
}

.edit-btn:hover {
  background: rgba(0, 0, 0, 0.08);
  border-color: rgba(0, 0, 0, 0.2);
}

.activate-btn {
  background: #E8F5E9;
  color: #2E7D32;
}

.activate-btn:hover {
  background: #2E7D32;
  color: white;
}

.deactivate-btn {
  background: #FFF3E0;
  color: #E65100;
}

.deactivate-btn:hover {
  background: #E65100;
  color: white;
}

.delete-btn {
  background: #FFEBEE;
  color: #C62828;
}

.delete-btn:hover {
  background: #C62828;
  color: white;
}

/* Modal Styles */
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
  z-index: 1000;
}

.modal-content {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--md-elevation-24);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-lg);
  border-bottom: 1px solid var(--md-outline-variant);
}

.modal-header h2 {
  margin: 0;
  font-size: var(--md-headline-size);
  font-weight: 500;
  color: var(--md-on-surface);
}

.close-btn {
  background: none;
  border: none;
  font-size: 2rem;
  color: var(--md-on-surface-variant);
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.close-btn:hover {
  background: var(--md-surface-variant);
  color: var(--md-on-surface);
}

.supplier-form {
  padding: var(--md-spacing-lg);
}

.form-group {
  margin-bottom: var(--md-spacing-lg);
}

.form-group label {
  display: block;
  margin-bottom: var(--md-spacing-xs);
  font-size: var(--md-body-size);
  font-weight: 500;
  color: var(--md-on-surface);
}

.form-group .required {
  color: #C62828;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: var(--md-spacing-md);
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  background: var(--md-surface);
  color: var(--md-on-surface);
  font-family: inherit;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--md-primary);
  border-width: 2px;
  box-shadow: 0 0 0 4px rgba(255, 140, 0, 0.12);
}

.form-group input[type="checkbox"] {
  width: auto;
  margin-right: var(--md-spacing-xs);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--md-spacing-md);
  margin-top: var(--md-spacing-xl);
  padding-top: var(--md-spacing-lg);
  border-top: 1px solid var(--md-outline-variant);
}

.cancel-btn, .save-btn {
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.cancel-btn {
  background: rgba(0, 0, 0, 0.05);
  color: rgba(0, 0, 0, 0.87);
  border: 1px solid rgba(0, 0, 0, 0.12);
}

.cancel-btn:hover {
  background: rgba(0, 0, 0, 0.08);
  border-color: rgba(0, 0, 0, 0.2);
}

.save-btn {
  background: var(--md-primary);
  color: white;
}

.save-btn:hover {
  background: #e67e00;
}
</style>

