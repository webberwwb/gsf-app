<template>
  <div class="categories-tab">
    <div class="page-header-actions">
      <select v-model="sortBy" @change="fetchCategories" class="sort-select">
        <option value="custom">自定义排序</option>
        <option value="name">按名称排序</option>
      </select>
      <button v-if="sortBy === 'custom' && hasUnsavedChanges" @click="saveSortOrder" class="save-btn">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
        </svg>
        保存排序
      </button>
      <button @click="openAddModal" class="add-btn">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
        </svg>
        添加分类
      </button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="categories.length === 0" class="empty-state">
      <p>暂无分类</p>
      <button @click="openAddModal" class="add-first-btn">添加第一个分类</button>
    </div>
    <div v-else class="categories-list">
      <div 
        v-for="(category, index) in categories" 
        :key="category.id" 
        class="category-card"
        :draggable="sortBy === 'custom'"
        @dragstart="handleDragStart(index, $event)"
        @dragover.prevent="handleDragOver(index, $event)"
        @dragenter="handleDragEnter(index)"
        @dragleave="handleDragLeave"
        @drop="handleDrop(index, $event)"
        @dragend="handleDragEnd"
        :class="{ 
          'draggable': sortBy === 'custom',
          'drag-over': dragOverIndex === index && draggedIndex !== index
        }"
      >
        <div v-if="sortBy === 'custom'" class="drag-handle" title="拖动排序">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 8h16M4 16h16" />
          </svg>
        </div>
        <div class="category-info">
          <h3>{{ category.name }}</h3>
          <p v-if="category.description" class="category-description">{{ category.description }}</p>
          <div class="category-meta">
            <span :class="['status-badge', category.is_active ? 'active' : 'inactive']">
              {{ category.is_active ? '启用' : '停用' }}
            </span>
            <span class="product-count">{{ category.product_count || 0 }} 个商品</span>
          </div>
        </div>
        <div class="category-actions">
          <button @click="editCategory(category)" class="edit-btn">编辑</button>
          <button @click="deleteCategory(category.id)" class="delete-btn">删除</button>
        </div>
      </div>
    </div>

    <!-- Category Form Modal -->
    <CategoryForm
      :show="showAddModal"
      :category="editingCategory"
      @close="closeModal"
      @saved="handleCategorySaved"
    />
  </div>
</template>

<script>
import apiClient from '../api/client'
import CategoryForm from '../components/CategoryForm.vue'
import { useModal } from '../composables/useModal'

export default {
  name: 'CategoriesTab',
  components: {
    CategoryForm
  },
  setup() {
    const { confirm, error: showError } = useModal()
    return { confirm, showError }
  },
  data() {
    return {
      loading: true,
      error: null,
      categories: [],
      showAddModal: false,
      editingCategory: null,
      sortBy: 'custom',
      draggedIndex: null,
      dragOverIndex: null,
      hasUnsavedChanges: false
    }
  },
  mounted() {
    this.fetchCategories()
  },
  methods: {
    async fetchCategories() {
      this.loading = true
      this.error = null
      try {
        const response = await apiClient.get(`/admin/product-categories?sort=${this.sortBy}`)
        this.categories = response.data.categories || []
        
        // Fetch product counts for each category
        await this.fetchProductCounts()
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || '加载分类失败'
        console.error('Failed to fetch categories:', error)
      } finally {
        this.loading = false
      }
    },
    async fetchProductCounts() {
      try {
        const response = await apiClient.get('/admin/products')
        const products = response.data.products || []
        
        // Count products by category
        const counts = {}
        products.forEach(product => {
          if (product.category_id) {
            counts[product.category_id] = (counts[product.category_id] || 0) + 1
          }
        })
        
        // Update categories with counts
        this.categories = this.categories.map(cat => ({
          ...cat,
          product_count: counts[cat.id] || 0
        }))
      } catch (error) {
        console.error('Failed to fetch product counts:', error)
      }
    },
    openAddModal() {
      this.editingCategory = null
      this.showAddModal = true
    },
    editCategory(category) {
      this.editingCategory = category
      this.showAddModal = true
    },
    closeModal() {
      this.showAddModal = false
      this.editingCategory = null
    },
    async handleCategorySaved() {
      await this.fetchCategories()
    },
    async deleteCategory(id) {
      const confirmed = await this.confirm('确定要删除这个分类吗？', {
        type: 'warning'
      })
      if (!confirmed) {
        return
      }

      try {
        await apiClient.delete(`/admin/product-categories/${id}`)
        await this.fetchCategories()
      } catch (error) {
        await this.showError(error.response?.data?.message || error.response?.data?.error || '删除失败')
        console.error('Delete category error:', error)
      }
    },
    handleDragStart(index, event) {
      this.draggedIndex = index
      event.dataTransfer.effectAllowed = 'move'
      event.dataTransfer.setData('text/html', event.target.innerHTML)
      event.target.style.opacity = '0.4'
    },
    handleDragOver(index, event) {
      event.preventDefault()
      event.dataTransfer.dropEffect = 'move'
      return false
    },
    handleDragEnter(index) {
      this.dragOverIndex = index
    },
    handleDragLeave() {
      // Don't clear dragOverIndex here as it causes flickering
    },
    handleDrop(index, event) {
      event.stopPropagation()
      event.preventDefault()
      
      if (this.draggedIndex !== null && this.draggedIndex !== index) {
        // Reorder the categories array
        const draggedCategory = this.categories[this.draggedIndex]
        const newCategories = [...this.categories]
        
        // Remove from old position
        newCategories.splice(this.draggedIndex, 1)
        
        // Insert at new position
        newCategories.splice(index, 0, draggedCategory)
        
        this.categories = newCategories
        this.hasUnsavedChanges = true
      }
      
      this.dragOverIndex = null
      return false
    },
    handleDragEnd(event) {
      event.target.style.opacity = '1'
      this.draggedIndex = null
      this.dragOverIndex = null
    },
    async saveSortOrder() {
      try {
        // Prepare the data for bulk update
        const sortOrderData = {
          categories: this.categories.map((category, index) => ({
            category_id: category.id,
            sort_order: index
          }))
        }
        
        await apiClient.put('/admin/product-categories/sort-order', sortOrderData)
        this.hasUnsavedChanges = false
        
        console.log('Sort order saved successfully')
      } catch (error) {
        await this.showError(error.response?.data?.message || error.response?.data?.error || '保存排序失败')
        console.error('Save sort order error:', error)
      }
    }
  }
}
</script>

<style scoped>
.categories-tab {
  max-width: 1200px;
}

.page-header-actions {
  margin-bottom: var(--md-spacing-lg);
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: var(--md-spacing-md);
}

.sort-select {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: 1px solid var(--md-outline-variant);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  background: var(--md-surface);
  color: var(--md-on-surface);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.sort-select:hover {
  border-color: var(--md-primary);
}

.add-btn, .save-btn {
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

.add-btn svg, .save-btn svg {
  width: 20px;
  height: 20px;
}

.add-btn:hover {
  background: #FF7F00;
  box-shadow: var(--md-elevation-3);
  transform: translateY(-2px);
}

.save-btn {
  background: #4CAF50;
}

.save-btn:hover {
  background: #45a049;
  box-shadow: var(--md-elevation-3);
  transform: translateY(-2px);
}

.loading, .error {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.empty-state {
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
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--md-elevation-2);
}

.add-first-btn:hover {
  background: #FF7F00;
  box-shadow: var(--md-elevation-3);
  transform: translateY(-2px);
}

.categories-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.category-card {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
  position: relative;
}

.category-card:hover {
  box-shadow: var(--md-elevation-2);
}

.category-card.draggable {
  cursor: move;
}

.category-card.drag-over {
  border: 2px dashed var(--md-primary);
  background: rgba(255, 140, 0, 0.05);
}

.drag-handle {
  width: 24px;
  height: 24px;
  color: var(--md-on-surface-variant);
  cursor: move;
  flex-shrink: 0;
}

.drag-handle svg {
  width: 100%;
  height: 100%;
}

.category-info {
  flex: 1;
}

.category-info h3 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-xs);
  font-weight: 500;
}

.category-description {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin-bottom: var(--md-spacing-sm);
  line-height: 1.5;
}

.category-meta {
  display: flex;
  gap: var(--md-spacing-sm);
  align-items: center;
  flex-wrap: wrap;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: var(--md-radius-xl);
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

.product-count {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.category-actions {
  display: flex;
  gap: var(--md-spacing-sm);
}

.edit-btn, .delete-btn {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
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

.delete-btn {
  background: #FFEBEE;
  color: #C62828;
}

.delete-btn:hover {
  background: #C62828;
  color: white;
}
</style>
