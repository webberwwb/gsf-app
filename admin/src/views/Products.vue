<template>
  <div class="products-page">
    <div class="page-header-actions">
      <select v-model="sortBy" @change="fetchProducts" class="sort-select">
        <option value="created_at">按创建时间</option>
        <option value="popularity">按销量排序</option>
        <option value="name">按名称排序</option>
      </select>
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
    <div v-else class="products-grid">
      <div v-for="product in products" :key="product.id" class="product-card">
        <div class="product-image">
          <img v-if="product.image" :src="product.image" :alt="product.name" />
          <div v-else class="image-placeholder">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
            </svg>
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
              <span v-if="product.pricing_data?.original_price && product.pricing_data.original_price > (product.price || product.pricing_data?.price || 0)" class="original-price">
                ${{ product.pricing_data.original_price }}
              </span>
            </template>
            <template v-else-if="product.pricing_type === 'weight_range'">
              <span class="sale-price">{{ formatWeightRangePrice(product) }}</span>
              <span class="price-type-badge">重量区间</span>
            </template>
            <template v-else-if="product.pricing_type === 'unit_weight'">
              <span class="sale-price">${{ product.pricing_data?.price_per_unit || product.price || '0.00' }}</span>
              <span class="price-type-badge">/ {{ product.pricing_data?.unit === 'kg' ? 'kg' : 'lb' }}</span>
            </template>
            <template v-else>
              <span class="sale-price">${{ product.price || product.pricing_data?.price || '0.00' }}</span>
            </template>
          </div>
          <div class="product-status">
            <span :class="['status-badge', product.is_active ? 'active' : 'inactive']">
              {{ product.is_active ? '上架' : '下架' }}
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

export default {
  name: 'Products',
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
      sortBy: 'created_at' // 'created_at', 'popularity', 'name'
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
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || '加载商品失败'
        console.error('Failed to fetch products:', error)
      } finally {
        this.loading = false
      }
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
    truncateDescription(description) {
      if (!description) return ''
      if (description.length <= 30) return description
      return description.substring(0, 30) + '...'
    }
  }
}
</script>

<style scoped>
.products-page {
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

