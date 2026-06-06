<template>
  <div class="products-tab">
    <div class="page-header-actions">
      <select v-model="sortBy" @change="handleSortByChange" class="sort-select">
        <option value="custom">自定义排序</option>
        <option value="created_at">按创建时间</option>
        <option value="popularity">按销量排序</option>
        <option value="name">按名称排序</option>
      </select>
      <div v-if="sortBy === 'custom'" class="view-mode-toggle">
        <button
          :class="['view-mode-btn', { active: customSortViewMode === 'grid' }]"
          @click="customSortViewMode = 'grid'"
          title="卡片拖动排序"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
          </svg>
        </button>
        <button
          :class="['view-mode-btn', { active: customSortViewMode === 'table' }]"
          @click="customSortViewMode = 'table'"
          title="表格手动排序"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
          </svg>
        </button>
      </div>
      <input
        v-if="sortBy === 'custom' && customSortViewMode === 'table'"
        v-model="sortTableSearch"
        type="search"
        class="sort-table-search"
        placeholder="搜索商品名称或分类..."
      />
      <button
        v-if="sortBy === 'custom' && (hasUnsavedChanges || savingSortOrder)"
        @click="saveSortOrder"
        class="save-btn"
        :disabled="savingSortOrder"
      >
        <span v-if="savingSortOrder" class="save-btn-spinner" aria-hidden="true"></span>
        <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
        </svg>
        {{ savingSortOrder ? '保存中...' : '保存排序' }}
      </button>
      <button @click="openAddModal" class="add-btn">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
        </svg>
        添加商品
      </button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="products.length === 0" class="empty-state">
      <p>暂无商品</p>
      <button @click="openAddModal" class="add-first-btn">添加第一个商品</button>
    </div>
    <div v-else-if="sortBy === 'custom' && customSortViewMode === 'table'" class="sort-table-section">
      <p class="sort-table-hint">输入排序值（支持小数，如 1.1、1.2），按 Enter 确认后预览顺序会更新，完成后点击「保存排序」。</p>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th class="col-rank">预览</th>
              <th class="col-sort">排序值</th>
              <th class="col-image">图片</th>
              <th class="col-name">商品名称</th>
              <th class="col-category">分类</th>
              <th class="col-status">状态</th>
              <th class="col-actions">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(product, index) in filteredSortedProducts"
              :key="product.id"
              :class="{ 'row-changed': isSortOrderChanged(product) }"
            >
              <td class="col-rank">{{ index + 1 }}</td>
              <td class="col-sort">
                <input
                  type="text"
                  inputmode="decimal"
                  class="sort-order-input"
                  :value="getSortOrderInputValue(product)"
                  @input="handleSortOrderDraft(product, $event)"
                  @keydown.enter.prevent="commitSortOrder(product, $event)"
                  @blur="cancelSortOrderDraft(product)"
                />
              </td>
              <td class="col-image">
                <div class="table-product-image">
                  <img v-if="product.image" :src="product.image" :alt="product.name" />
                  <div v-else class="table-image-placeholder">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                    </svg>
                  </div>
                </div>
              </td>
              <td class="col-name">
                <span class="table-product-name">{{ product.name }}</span>
                <span v-if="product.supplier" class="table-supplier">{{ product.supplier.name }}</span>
              </td>
              <td class="col-category">{{ product.category?.name || '—' }}</td>
              <td class="col-status">
                <span :class="['status-badge', product.is_active ? 'active' : 'inactive']">
                  {{ product.is_active ? '上架' : '下架' }}
                </span>
              </td>
              <td class="col-actions">
                <button @click="editProduct(product)" class="table-edit-btn">编辑</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="filteredSortedProducts.length === 0" class="sort-table-empty">没有匹配的商品</p>
    </div>
    <div v-else class="products-grid">
      <div 
        v-for="(product, index) in products" 
        :key="product.id" 
        class="product-card"
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
        <div class="product-image">
          <div v-if="sortBy === 'custom'" class="drag-handle" title="拖动排序">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 8h16M4 16h16" />
            </svg>
          </div>
          <img v-if="product.image" :src="product.image" :alt="product.name" />
          <div v-else class="image-placeholder">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
            </svg>
          </div>
          <!-- Sold Out Badge -->
          <div v-if="isOutOfStock(product)" class="sold-out-badge">
            已售罄
          </div>
          <div class="image-mask"></div>
          <div v-if="product.description" class="image-description-overlay">
            {{ truncateDescription(product.description) }}
          </div>
        </div>
        <div class="product-info">
          <h3>{{ product.name }}</h3>
          <div v-if="product.supplier" class="supplier-info">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="supplier-icon">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <span class="supplier-name">{{ product.supplier.name }}</span>
          </div>
          <div class="price-info">
            <template v-if="product.pricing_type === 'per_item'">
              <span class="sale-price">${{ product.price || product.pricing_data?.price || '0.00' }}</span>
            </template>
            <template v-else-if="product.pricing_type === 'weight_range'">
              <span class="sale-price">{{ formatWeightRangePrice(product) }}</span>
              <span class="price-type-badge">重量区间</span>
            </template>
            <template v-else-if="product.pricing_type === 'unit_weight'">
              <span class="sale-price">${{ product.pricing_data?.price_per_unit || product.price || '0.00' }}</span>
              <span class="price-type-badge">/ {{ product.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }}</span>
            </template>
            <template v-else-if="product.pricing_type === 'bundled_weight'">
              <span class="sale-price">{{ formatBundledPrice(product) }}</span>
              <span class="price-type-badge">/ 份</span>
            </template>
            <template v-else>
              <span class="sale-price">${{ product.price || product.pricing_data?.price || '0.00' }}</span>
            </template>
          </div>
          <div class="product-status">
            <span :class="['status-badge', product.is_active ? 'active' : 'inactive']">
              {{ product.is_active ? '上架' : '下架' }}
            </span>
            <span v-if="product.category" class="category-badge">
              {{ product.category.name }}
            </span>
            <span 
              :class="['shipping-badge', product.counts_toward_free_shipping !== false ? 'counts-toward' : 'excluded']"
              :title="product.counts_toward_free_shipping !== false ? '计入免运费门槛' : '不计入免运费门槛'"
            >
              {{ product.counts_toward_free_shipping !== false ? '✓ 计入免运' : '✗ 不计免运' }}
            </span>
            <span v-if="product.sales_stats && product.sales_stats.total_sold > 0" class="sales-badge">
              已售: {{ product.sales_stats.total_sold }}
            </span>
          </div>
          <div class="product-actions">
            <button @click="editProduct(product)" class="edit-btn">编辑</button>
            <button @click="deleteProduct(product.id)" class="delete-btn">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Product Form Modal -->
    <ProductForm
      :show="showAddModal"
      :product="editingProduct"
      @close="closeModal"
      @saved="handleProductSaved"
    />
  </div>
</template>

<script>
import apiClient from '../api/client'
import ProductForm from '../components/ProductForm.vue'
import { useModal } from '../composables/useModal'
import { formatProductPriceRange } from '../utils/productPriceDisplay'

export default {
  name: 'ProductsTab',
  components: {
    ProductForm
  },
  setup() {
    const { confirm, error: showError } = useModal()
    return { confirm, showError }
  },
  data() {
    return {
      loading: true,
      error: null,
      products: [],
      showAddModal: false,
      editingProduct: null,
      sortBy: 'custom', // 'custom', 'created_at', 'popularity', 'name'
      customSortViewMode: 'grid', // 'grid' | 'table'
      sortTableSearch: '',
      draggedIndex: null,
      dragOverIndex: null,
      hasUnsavedChanges: false,
      savingSortOrder: false,
      savedSortOrders: {},
      sortOrderDrafts: {}
    }
  },
  computed: {
    filteredSortedProducts() {
      const query = this.sortTableSearch.trim().toLowerCase()
      let list = this.products
      if (query) {
        list = list.filter((product) => {
          const name = product.name?.toLowerCase() || ''
          const category = product.category?.name?.toLowerCase() || ''
          const supplier = product.supplier?.name?.toLowerCase() || ''
          return name.includes(query) || category.includes(query) || supplier.includes(query)
        })
      }
      return this.sortProductsByOrder(list)
    }
  },
  mounted() {
    this.fetchProducts()
  },
  methods: {
    async fetchProducts() {
      this.loading = true
      this.error = null
      try {
        const response = await apiClient.get(`/admin/products?sort=${this.sortBy}&days=30`)
        this.products = response.data.products || []
        this.syncSavedSortOrders()
        this.hasUnsavedChanges = false
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || '加载商品失败'
        console.error('Failed to fetch products:', error)
      } finally {
        this.loading = false
      }
    },
    handleSortByChange() {
      this.sortTableSearch = ''
      this.sortOrderDrafts = {}
      this.fetchProducts()
    },
    formatSortOrderValue(value) {
      const num = Number(value ?? 0)
      if (!Number.isFinite(num)) return '0'
      if (Number.isInteger(num)) return String(num)
      return String(num)
    },
    getSortOrderInputValue(product) {
      if (Object.prototype.hasOwnProperty.call(this.sortOrderDrafts, product.id)) {
        return this.sortOrderDrafts[product.id]
      }
      return this.formatSortOrderValue(product.sort_order)
    },
    handleSortOrderDraft(product, event) {
      this.sortOrderDrafts = {
        ...this.sortOrderDrafts,
        [product.id]: event.target.value
      }
    },
    cancelSortOrderDraft(product) {
      if (!Object.prototype.hasOwnProperty.call(this.sortOrderDrafts, product.id)) {
        return
      }
      const drafts = { ...this.sortOrderDrafts }
      delete drafts[product.id]
      this.sortOrderDrafts = drafts
    },
    commitSortOrder(product, event) {
      const raw = (this.sortOrderDrafts[product.id] ?? event.target.value ?? '').trim()
      if (raw === '') {
        this.cancelSortOrderDraft(product)
        return
      }

      const parsed = Number.parseFloat(raw)
      if (Number.isNaN(parsed) || parsed < 0) {
        this.cancelSortOrderDraft(product)
        return
      }

      product.sort_order = parsed
      this.cancelSortOrderDraft(product)
      this.applyProductSortOrder()
      this.hasUnsavedChanges = true
      event.target.blur()
    },
    syncSavedSortOrders() {
      this.savedSortOrders = Object.fromEntries(
        this.products.map((product) => [product.id, product.sort_order ?? 0])
      )
    },
    sortProductsByOrder(list) {
      return [...list].sort((a, b) => {
        const orderDiff = (a.sort_order ?? 0) - (b.sort_order ?? 0)
        if (orderDiff !== 0) return orderDiff
        return (a.id ?? 0) - (b.id ?? 0)
      })
    },
    applyProductSortOrder() {
      this.products = this.sortProductsByOrder(this.products)
    },
    isSortOrderChanged(product) {
      const saved = this.savedSortOrders[product.id]
      if (saved === undefined) return false
      return Number(saved) !== Number(product.sort_order ?? 0)
    },
    openAddModal() {
      this.editingProduct = null
      this.showAddModal = true
    },
    editProduct(product) {
      this.editingProduct = product
      this.showAddModal = true
    },
    closeModal() {
      this.showAddModal = false
      this.editingProduct = null
    },
    async handleProductSaved() {
      await this.fetchProducts()
    },
    async deleteProduct(id) {
      const confirmed = await this.confirm('确定要删除这个商品吗？', {
        type: 'warning'
      })
      if (!confirmed) {
        return
      }

      try {
        await apiClient.delete(`/admin/products/${id}`)
        await this.fetchProducts()
      } catch (error) {
        await this.showError(error.response?.data?.message || error.response?.data?.error || '删除失败')
        console.error('Delete product error:', error)
      }
    },
    formatWeightRangePrice(product) {
      if (product.pricing_data && product.pricing_data.ranges && product.pricing_data.ranges.length > 0) {
        const ranges = product.pricing_data.ranges
        if (ranges.length === 1) {
          return `$${ranges[0].price || '0.00'}`
        }
        return `$${ranges[0].price || '0.00'} - $${ranges[ranges.length - 1].price || '0.00'}`
      }
      return `$${product.price || product.pricing_data?.price || '0.00'}`
    },
    formatBundledPrice(product) {
      if (product.pricing_type === 'bundled_weight') {
        if (!(product.pricing_data?.price_per_unit || 0)) {
          return product.price || '0.00'
        }
        return formatProductPriceRange(product)
      }
      return product.price || '0.00'
    },
    truncateDescription(description) {
      if (!description) return ''
      if (description.length <= 30) return description
      return description.substring(0, 30) + '...'
    },
    isOutOfStock(product) {
      // Check stock_limit (product-level inventory)
      // null or undefined means unlimited stock, only 0 means out of stock
      const inventory = product.stock_limit !== undefined && product.stock_limit !== null ? product.stock_limit : null
      return inventory === 0
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
        // Reorder the products array
        const draggedProduct = this.products[this.draggedIndex]
        const newProducts = [...this.products]
        
        // Remove from old position
        newProducts.splice(this.draggedIndex, 1)
        
        // Insert at new position
        newProducts.splice(index, 0, draggedProduct)

        this.products = newProducts.map((product, sortIndex) => ({
          ...product,
          sort_order: sortIndex
        }))
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
      if (this.savingSortOrder) return

      this.savingSortOrder = true
      try {
        const sortOrderData = {
          products: this.products.map((product) => ({
            product_id: product.id,
            sort_order: product.sort_order ?? 0
          }))
        }

        await apiClient.put('/admin/products/sort-order', sortOrderData)
        this.syncSavedSortOrders()
        this.hasUnsavedChanges = false
        this.applyProductSortOrder()
      } catch (error) {
        await this.showError(error.response?.data?.message || error.response?.data?.error || '保存排序失败')
        console.error('Save sort order error:', error)
      } finally {
        this.savingSortOrder = false
      }
    }
  }
}
</script>

<style scoped>
.products-tab {
  max-width: 1200px;
}

.page-header-actions {
  margin-bottom: var(--md-spacing-lg);
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: var(--md-spacing-md);
}

/* Laptop screens - more compact header */
@media (max-width: 1366px) {
  .page-header-actions {
    gap: var(--md-spacing-sm);
    flex-wrap: wrap;
  }
  
  .sort-select {
    padding: var(--md-spacing-xs) var(--md-spacing-sm);
    font-size: 0.875rem;
  }
  
  .add-btn,
  .save-btn {
    padding: var(--md-spacing-sm) var(--md-spacing-md);
    font-size: 0.875rem;
  }
  
  .add-btn svg,
  .save-btn svg {
    width: 18px;
    height: 18px;
  }
}

/* Mobile - stack vertically */
@media (max-width: 767px) {
  .page-header-actions {
    flex-direction: column;
    align-items: stretch;
    gap: var(--md-spacing-sm);
  }
  
  .sort-select,
  .add-btn,
  .save-btn,
  .sort-table-search {
    width: 100%;
  }

  .view-mode-toggle {
    align-self: center;
  }
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

.sort-select:focus {
  outline: none;
  border-color: var(--md-primary);
  box-shadow: 0 0 0 2px rgba(255, 140, 0, 0.2);
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

.add-btn svg {
  width: 20px;
  height: 20px;
}

.add-btn:hover {
  background: #FF7F00;
  box-shadow: var(--md-elevation-3);
  transform: translateY(-2px);
}

.save-btn {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--md-elevation-2);
}

.save-btn svg {
  width: 20px;
  height: 20px;
}

.save-btn:hover:not(:disabled) {
  background: #45a049;
  box-shadow: var(--md-elevation-3);
  transform: translateY(-2px);
}

.save-btn:disabled {
  cursor: not-allowed;
  opacity: 0.85;
  transform: none;
}

.save-btn-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: white;
  border-radius: 50%;
  animation: save-btn-spin 0.7s linear infinite;
  flex-shrink: 0;
}

@keyframes save-btn-spin {
  to {
    transform: rotate(360deg);
  }
}

.view-mode-toggle {
  display: flex;
  gap: 4px;
  background: #FFFFFF;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 24px;
  padding: 4px;
}

.view-mode-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: transparent;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s;
  color: rgba(0, 0, 0, 0.6);
}

.view-mode-btn svg {
  width: 20px;
  height: 20px;
}

.view-mode-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  color: rgba(0, 0, 0, 0.87);
}

.view-mode-btn.active {
  background: var(--md-primary);
  color: white;
  box-shadow: 0px 2px 4px rgba(255, 140, 0, 0.3);
}

.sort-table-search {
  min-width: 220px;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: 1px solid var(--md-outline-variant);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  background: var(--md-surface);
  color: var(--md-on-surface);
}

.sort-table-search:focus {
  outline: none;
  border-color: var(--md-primary);
  box-shadow: 0 0 0 2px rgba(255, 140, 0, 0.2);
}

.sort-table-section {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.sort-table-hint {
  margin: 0;
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.sort-table-empty {
  text-align: center;
  padding: var(--md-spacing-lg);
  color: var(--md-on-surface-variant);
}

.table-wrap {
  overflow-x: auto;
  border-radius: var(--md-radius-md);
  border: 1px solid var(--md-outline-variant);
  background: #FFFFFF;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--md-label-size);
}

.data-table th,
.data-table td {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  text-align: left;
  border-bottom: 1px solid var(--md-outline-variant);
  vertical-align: middle;
}

.data-table th {
  background: var(--md-surface-variant);
  font-weight: 600;
  color: var(--md-on-surface);
  white-space: nowrap;
  position: sticky;
  top: 0;
  z-index: 1;
}

.data-table tbody tr:hover {
  background: rgba(255, 140, 0, 0.04);
}

.data-table tbody tr.row-changed {
  background: rgba(76, 175, 80, 0.08);
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.col-rank {
  width: 56px;
  text-align: center;
  font-weight: 600;
  color: var(--md-on-surface-variant);
}

.col-sort {
  width: 96px;
}

.col-image {
  width: 72px;
}

.col-name {
  min-width: 200px;
}

.col-category {
  min-width: 100px;
}

.col-status {
  width: 80px;
}

.col-actions {
  width: 72px;
}

.sort-order-input {
  width: 80px;
  padding: 6px 8px;
  border: 1px solid var(--md-outline-variant);
  border-radius: var(--md-radius-sm);
  font-size: var(--md-label-size);
  text-align: center;
  background: var(--md-surface);
  color: var(--md-on-surface);
}

.sort-order-input:focus {
  outline: none;
  border-color: var(--md-primary);
  box-shadow: 0 0 0 2px rgba(255, 140, 0, 0.2);
}

.table-product-image {
  width: 48px;
  height: 48px;
  border-radius: var(--md-radius-sm);
  overflow: hidden;
  background: var(--md-surface-variant);
  display: flex;
  align-items: center;
  justify-content: center;
}

.table-product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.table-image-placeholder {
  opacity: 0.35;
  color: var(--md-on-surface-variant);
}

.table-image-placeholder svg {
  width: 24px;
  height: 24px;
}

.table-product-name {
  display: block;
  font-weight: 500;
  color: var(--md-on-surface);
  line-height: 1.3;
}

.table-supplier {
  display: block;
  margin-top: 2px;
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.table-edit-btn {
  padding: 4px 10px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: var(--md-radius-sm);
  background: rgba(0, 0, 0, 0.05);
  color: rgba(0, 0, 0, 0.87);
  font-size: var(--md-label-size);
  cursor: pointer;
  transition: all 0.2s;
}

.table-edit-btn:hover {
  background: rgba(0, 0, 0, 0.08);
  border-color: rgba(0, 0, 0, 0.2);
}

.loading, .error {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--md-spacing-lg);
}

/* Laptop screens - 2-3 columns with smaller cards */
@media (max-width: 1366px) {
  .products-grid {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: var(--md-spacing-md);
  }
}

/* Tablet screens - 2 columns */
@media (max-width: 1024px) {
  .products-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--md-spacing-md);
  }
}

/* Mobile screens - 1 column */
@media (max-width: 767px) {
  .products-grid {
    grid-template-columns: 1fr;
    gap: var(--md-spacing-sm);
  }
}

.product-card {
  background: #FFFFFF;
  border-radius: var(--md-radius-lg);
  overflow: hidden;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: none;
}

.product-card:hover {
  box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.16), 0px 2px 4px rgba(0, 0, 0, 0.23);
  transform: translateY(-2px);
}

.product-card.draggable {
  cursor: move;
}

.product-card.drag-over {
  border: 2px dashed var(--md-primary);
  background: rgba(255, 140, 0, 0.05);
}

.product-image {
  width: 100%;
  height: 200px;
  background: var(--md-surface-variant);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
}

/* Laptop screens - smaller product images */
@media (max-width: 1366px) {
  .product-image {
    height: 160px;
  }
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-mask {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
  height: 100%;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.7) 0%, rgba(0, 0, 0, 0.4) 50%, transparent 100%);
  pointer-events: none;
}

.image-description-overlay {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
  padding: var(--md-spacing-md);
  color: white;
  font-size: var(--md-label-size);
  line-height: 1.4;
  word-wrap: break-word;
  word-break: break-word;
  display: flex;
  align-items: flex-end;
  z-index: 1;
  box-sizing: border-box;
  white-space: pre-line;
}

.image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.3;
  color: var(--md-on-surface-variant);
}

.image-placeholder svg {
  width: 32px;
  height: 32px;
}

.drag-handle {
  position: absolute;
  top: 8px;
  left: 8px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  padding: 6px;
  border-radius: var(--md-radius-sm);
  z-index: 10;
  cursor: move;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}

.drag-handle svg {
  width: 20px;
  height: 20px;
}

.sold-out-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: linear-gradient(135deg, #D32F2F 0%, #B71C1C 100%);
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(211, 47, 47, 0.4);
  z-index: 10;
  text-transform: uppercase;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.9;
    transform: scale(1.02);
  }
}

.product-info {
  padding: var(--md-spacing-md);
}

.product-info h3 {
  font-size: 16px;
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-sm);
  font-weight: 500;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
}

.description {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin-bottom: var(--md-spacing-md);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.supplier-info {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-xs);
  margin-bottom: var(--md-spacing-sm);
  padding: var(--md-spacing-xs) var(--md-spacing-sm);
  background: var(--md-surface-variant);
  border-radius: var(--md-radius-sm);
  width: fit-content;
}

.supplier-icon {
  width: 16px;
  height: 16px;
  color: var(--md-on-surface-variant);
  flex-shrink: 0;
}

.supplier-name {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  font-weight: 500;
}

.price-info {
  margin-bottom: var(--md-spacing-sm);
}

.product-status {
  margin-bottom: var(--md-spacing-md);
  display: flex;
  gap: var(--md-spacing-xs);
  flex-wrap: wrap;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: var(--md-radius-xl);
  font-size: var(--md-label-size);
  font-weight: 500;
}

.sales-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: var(--md-radius-xl);
  font-size: var(--md-label-size);
  font-weight: 500;
  background: #E3F2FD;
  color: #1976D2;
}

.shipping-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: var(--md-radius-xl);
  font-size: var(--md-label-size);
  font-weight: 500;
  cursor: help;
}

.shipping-badge.counts-toward {
  background: #E8F5E9;
  color: #2E7D32;
}

.shipping-badge.excluded {
  background: #FFF3E0;
  color: #E65100;
}

.status-badge.active {
  background: #E8F5E9;
  color: #2E7D32;
}

.status-badge.inactive {
  background: #FFEBEE;
  color: #C62828;
}

.category-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: var(--md-radius-xl);
  font-size: var(--md-label-size);
  font-weight: 500;
  background: #F3E5F5;
  color: #7B1FA2;
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

.sale-price {
  font-size: 1.25rem;
  color: #FF4444;
  font-weight: 600;
  margin-right: var(--md-spacing-sm);
}

.original-price {
  font-size: var(--md-label-size);
  color: var(--md-outline);
  text-decoration: line-through;
}

.bundled-price-admin {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.unit-price-badge {
  font-size: 12px;
  color: var(--md-on-surface-variant);
  background: var(--md-surface-variant);
  padding: 2px 6px;
  border-radius: 4px;
}

.price-type-badge {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin-left: var(--md-spacing-xs);
  padding: 0.125rem 0.5rem;
  background: var(--md-surface-variant);
  border-radius: var(--md-radius-sm);
}

.product-actions {
  display: flex;
  gap: var(--md-spacing-sm);
}

.edit-btn, .delete-btn {
  flex: 1;
  padding: var(--md-spacing-sm);
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

