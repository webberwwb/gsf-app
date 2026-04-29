<template>
  <div class="assignment-tab">
    <div class="page-header">
      <h2>批量分配商品分类</h2>
      <p class="page-description">快速为商品分配分类</p>
    </div>

    <!-- Category Filter -->
    <div class="filter-section">
      <div class="filter-group">
        <label>筛选分类:</label>
        <select v-model="filterCategoryId" class="filter-select">
          <option :value="null">全部商品</option>
          <option :value="'unassigned'">未分配分类</option>
          <option v-for="category in categories" :key="category.id" :value="category.id">
            {{ category.name }}
          </option>
        </select>
      </div>
      <div class="stats">
        <span class="stat-item">总商品: {{ products.length }}</span>
        <span class="stat-item">已分配: {{ assignedCount }}</span>
        <span class="stat-item">未分配: {{ unassignedCount }}</span>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="filteredProducts.length === 0" class="empty-state">
      <p>没有符合条件的商品</p>
    </div>
    <div v-else class="products-table-container">
      <table class="products-table">
        <thead>
          <tr>
            <th class="col-checkbox">
              <input 
                type="checkbox" 
                @change="toggleSelectAll"
                :checked="isAllSelected"
                class="checkbox-input"
              />
            </th>
            <th class="col-image">图片</th>
            <th class="col-name">商品名称</th>
            <th class="col-supplier">供应商</th>
            <th class="col-current">当前分类</th>
            <th class="col-assign">分配分类</th>
            <th class="col-action">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="product in filteredProducts" :key="product.id" class="product-row">
            <td class="col-checkbox">
              <input 
                type="checkbox" 
                v-model="selectedProducts"
                :value="product.id"
                class="checkbox-input"
              />
            </td>
            <td class="col-image">
              <div class="product-image-thumb">
                <img v-if="product.image" :src="product.image" :alt="product.name" />
                <div v-else class="image-placeholder">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                  </svg>
                </div>
              </div>
            </td>
            <td class="col-name">
              <div class="product-name">{{ product.name }}</div>
            </td>
            <td class="col-supplier">
              <span v-if="product.supplier" class="supplier-badge">{{ product.supplier.name }}</span>
              <span v-else class="no-supplier">-</span>
            </td>
            <td class="col-current">
              <span v-if="product.category" class="category-badge current">
                {{ product.category.name }}
              </span>
              <span v-else class="no-category">未分配</span>
            </td>
            <td class="col-assign">
              <select 
                v-model="product.new_category_id" 
                class="category-select"
                @change="markAsChanged(product)"
              >
                <option :value="null">-- 不分配 --</option>
                <option 
                  v-for="category in categories" 
                  :key="category.id" 
                  :value="category.id"
                >
                  {{ category.name }}
                </option>
              </select>
            </td>
            <td class="col-action">
              <button 
                @click="saveProduct(product)" 
                class="save-btn"
                :disabled="!product.changed || savingIds.includes(product.id)"
                :class="{ 'saving': savingIds.includes(product.id) }"
              >
                {{ savingIds.includes(product.id) ? '保存中...' : '保存' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Bulk Actions -->
    <div v-if="!loading && selectedProducts.length > 0" class="bulk-actions">
      <div class="bulk-header">
        <span class="selected-count">已选择 {{ selectedProducts.length }} 个商品</span>
        <button @click="clearSelection" class="clear-btn">清除选择</button>
      </div>
      <div class="bulk-select">
        <label>批量分配到分类:</label>
        <select v-model="bulkCategoryId" class="category-select">
          <option :value="null">-- 选择分类 --</option>
          <option 
            v-for="category in categories" 
            :key="category.id" 
            :value="category.id"
          >
            {{ category.name }}
          </option>
        </select>
        <button 
          @click="applyBulkAssignment" 
          class="apply-bulk-btn"
          :disabled="bulkCategoryId === null || savingAll"
        >
          {{ savingAll ? '应用中...' : '应用到选中商品' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'
import { useModal } from '../composables/useModal'

export default {
  name: 'AssignmentTab',
  setup() {
    const { confirm, error: showError, success } = useModal()
    return { confirm, showError, success }
  },
  data() {
    return {
      loading: true,
      error: null,
      products: [],
      categories: [],
      filterCategoryId: 'unassigned',
      bulkCategoryId: null,
      savingIds: [],
      savingAll: false,
      selectedProducts: []
    }
  },
  computed: {
    filteredProducts() {
      if (this.filterCategoryId === null) {
        return this.products
      } else if (this.filterCategoryId === 'unassigned') {
        return this.products.filter(p => !p.category_id)
      } else {
        return this.products.filter(p => p.category_id === this.filterCategoryId)
      }
    },
    assignedCount() {
      return this.products.filter(p => p.category_id).length
    },
    unassignedCount() {
      return this.products.filter(p => !p.category_id).length
    },
    isAllSelected() {
      return this.filteredProducts.length > 0 && 
             this.selectedProducts.length === this.filteredProducts.length
    }
  },
  mounted() {
    this.loadData()
  },
  watch: {
    filterCategoryId() {
      // Clear selection when filter changes
      this.selectedProducts = []
    }
  },
  methods: {
    async loadData() {
      this.loading = true
      this.error = null
      try {
        const [productsRes, categoriesRes] = await Promise.all([
          apiClient.get('/admin/products'),
          apiClient.get('/admin/product-categories')
        ])
        
        this.products = (productsRes.data.products || []).map(p => ({
          ...p,
          new_category_id: p.category_id,
          changed: false
        }))
        
        this.categories = categoriesRes.data.categories || []
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || '加载失败'
        console.error('Failed to load data:', error)
      } finally {
        this.loading = false
      }
    },
    markAsChanged(product) {
      product.changed = product.new_category_id !== product.category_id
    },
    async saveProduct(product) {
      if (!product.changed) return
      
      this.savingIds.push(product.id)
      
      try {
        await apiClient.put(`/admin/products/${product.id}`, {
          category_id: product.new_category_id
        })
        
        // Update the product in the list
        product.category_id = product.new_category_id
        product.changed = false
        
        // Update category object
        if (product.new_category_id) {
          const category = this.categories.find(c => c.id === product.new_category_id)
          product.category = category ? { id: category.id, name: category.name } : null
        } else {
          product.category = null
        }
        
      } catch (error) {
        await this.showError(error.response?.data?.message || error.response?.data?.error || '保存失败')
        console.error('Save product error:', error)
      } finally {
        this.savingIds = this.savingIds.filter(id => id !== product.id)
      }
    },
    toggleSelectAll(event) {
      if (event.target.checked) {
        this.selectedProducts = this.filteredProducts.map(p => p.id)
      } else {
        this.selectedProducts = []
      }
    },
    clearSelection() {
      this.selectedProducts = []
    },
    async applyBulkAssignment() {
      if (this.bulkCategoryId === null || this.selectedProducts.length === 0) return
      
      const categoryName = this.categories.find(c => c.id === this.bulkCategoryId)?.name || '选定的分类'
      
      const confirmed = await this.confirm(
        `确定要将 ${this.selectedProducts.length} 个商品分配到 "${categoryName}" 吗？`,
        { type: 'warning' }
      )
      
      if (!confirmed) return
      
      this.savingAll = true
      
      try {
        // Update selected products only
        const selectedProductObjects = this.products.filter(p => 
          this.selectedProducts.includes(p.id)
        )
        
        const promises = selectedProductObjects.map(product => 
          apiClient.put(`/admin/products/${product.id}`, {
            category_id: this.bulkCategoryId
          })
        )
        
        await Promise.all(promises)
        
        // Update the products in the list
        const category = this.categories.find(c => c.id === this.bulkCategoryId)
        selectedProductObjects.forEach(product => {
          product.category_id = this.bulkCategoryId
          product.new_category_id = this.bulkCategoryId
          product.changed = false
          product.category = category ? { id: category.id, name: category.name } : null
        })
        
        await this.success(`成功分配 ${this.selectedProducts.length} 个商品到 "${categoryName}"`)
        
        // Reset selections
        this.bulkCategoryId = null
        this.selectedProducts = []
        
      } catch (error) {
        await this.showError(error.response?.data?.message || error.response?.data?.error || '批量分配失败')
        console.error('Bulk assignment error:', error)
      } finally {
        this.savingAll = false
      }
    }
  }
}
</script>

<style scoped>
.assignment-tab {
  max-width: 1400px;
}

.page-header {
  margin-bottom: var(--md-spacing-lg);
}

.page-header h2 {
  font-size: var(--md-headline-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-xs);
  font-weight: 500;
}

.page-description {
  font-size: var(--md-body-size);
  color: var(--md-on-surface-variant);
  margin: 0;
}

.filter-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-lg);
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  margin-bottom: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
  flex-wrap: wrap;
  gap: var(--md-spacing-md);
}

.filter-group {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
}

.filter-group label {
  font-size: var(--md-body-size);
  color: var(--md-on-surface);
  font-weight: 500;
}

.filter-select {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: 1px solid var(--md-outline-variant);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  background: var(--md-surface);
  color: var(--md-on-surface);
  min-width: 200px;
}

.stats {
  display: flex;
  gap: var(--md-spacing-lg);
}

.stat-item {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  font-weight: 500;
}

.loading, .error, .empty-state {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.products-table-container {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  overflow-x: auto;
  box-shadow: var(--md-elevation-1);
}

.products-table {
  width: 100%;
  border-collapse: collapse;
}

.products-table thead {
  background: var(--md-surface-variant);
}

.products-table th {
  padding: var(--md-spacing-md);
  text-align: left;
  font-size: var(--md-label-size);
  font-weight: 600;
  color: var(--md-on-surface);
  border-bottom: 2px solid var(--md-outline-variant);
}

.products-table td {
  padding: var(--md-spacing-md);
  border-bottom: 1px solid var(--md-surface-variant);
}

.product-row:hover {
  background: var(--md-surface-variant);
}

.col-checkbox {
  width: 50px;
  text-align: center;
}

.checkbox-input {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--md-primary);
}

.col-image {
  width: 80px;
}

.col-name {
  min-width: 200px;
}

.col-supplier {
  width: 150px;
}

.col-current {
  width: 150px;
}

.col-assign {
  width: 200px;
}

.col-action {
  width: 120px;
}

.product-image-thumb {
  width: 60px;
  height: 60px;
  border-radius: var(--md-radius-sm);
  overflow: hidden;
  background: var(--md-surface-variant);
  display: flex;
  align-items: center;
  justify-content: center;
}

.product-image-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-placeholder {
  opacity: 0.3;
  color: var(--md-on-surface-variant);
}

.image-placeholder svg {
  width: 24px;
  height: 24px;
}

.product-name {
  font-size: var(--md-body-size);
  color: var(--md-on-surface);
  font-weight: 500;
}

.supplier-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: var(--md-radius-xl);
  font-size: var(--md-label-size);
  background: var(--md-surface-variant);
  color: var(--md-on-surface-variant);
}

.no-supplier {
  color: var(--md-on-surface-variant);
  font-size: var(--md-label-size);
}

.category-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: var(--md-radius-xl);
  font-size: var(--md-label-size);
  font-weight: 500;
}

.category-badge.current {
  background: #F3E5F5;
  color: #7B1FA2;
}

.no-category {
  color: var(--md-on-surface-variant);
  font-size: var(--md-label-size);
  font-style: italic;
}

.category-select {
  width: 100%;
  padding: var(--md-spacing-xs) var(--md-spacing-sm);
  border: 1px solid var(--md-outline-variant);
  border-radius: var(--md-radius-sm);
  font-size: var(--md-label-size);
  background: var(--md-surface);
  color: var(--md-on-surface);
}

.category-select:focus {
  outline: none;
  border-color: var(--md-primary);
  box-shadow: 0 0 0 2px rgba(255, 140, 0, 0.2);
}

.save-btn {
  padding: var(--md-spacing-xs) var(--md-spacing-md);
  border: none;
  border-radius: var(--md-radius-sm);
  font-size: var(--md-label-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  background: var(--md-primary);
  color: white;
}

.save-btn:hover:not(:disabled) {
  background: #FF7F00;
  box-shadow: var(--md-elevation-2);
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.save-btn.saving {
  background: #4CAF50;
}

.bulk-actions {
  margin-top: var(--md-spacing-lg);
  padding: var(--md-spacing-lg);
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  box-shadow: var(--md-elevation-1);
  border: 2px solid var(--md-primary);
}

.bulk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--md-spacing-md);
  padding-bottom: var(--md-spacing-md);
  border-bottom: 1px solid var(--md-outline-variant);
}

.selected-count {
  font-size: var(--md-body-size);
  color: var(--md-primary);
  font-weight: 600;
}

.clear-btn {
  padding: var(--md-spacing-xs) var(--md-spacing-md);
  border: 1px solid var(--md-outline-variant);
  border-radius: var(--md-radius-sm);
  font-size: var(--md-label-size);
  background: transparent;
  color: var(--md-on-surface-variant);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.clear-btn:hover {
  background: var(--md-surface-variant);
  border-color: var(--md-outline);
}

.bulk-select {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
  flex-wrap: wrap;
}

.bulk-select label {
  font-size: var(--md-body-size);
  color: var(--md-on-surface);
  font-weight: 500;
}

.bulk-select .category-select {
  min-width: 200px;
  width: auto;
}

.apply-bulk-btn {
  padding: var(--md-spacing-sm) var(--md-spacing-lg);
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  background: #4CAF50;
  color: white;
  box-shadow: var(--md-elevation-2);
}

.apply-bulk-btn:hover:not(:disabled) {
  background: #45a049;
  box-shadow: var(--md-elevation-3);
  transform: translateY(-2px);
}

.apply-bulk-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .products-table-container {
    overflow-x: scroll;
  }
  
  .filter-section {
    flex-direction: column;
    align-items: stretch;
  }
  
  .stats {
    flex-direction: column;
    gap: var(--md-spacing-xs);
  }
  
  .bulk-select {
    flex-direction: column;
    align-items: stretch;
  }
  
  .bulk-select .category-select {
    width: 100%;
  }
}
</style>
