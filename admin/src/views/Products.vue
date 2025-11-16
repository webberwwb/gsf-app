<template>
  <div class="products-page">
    <div class="page-header-actions">
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
          <div v-else class="image-placeholder">🛒</div>
        </div>
        <div class="product-info">
          <h3>{{ product.name }}</h3>
          <p class="description">{{ product.description }}</p>
          <div class="price-info">
            <span class="sale-price">${{ product.sale_price }}</span>
            <span v-if="product.original_price > product.sale_price" class="original-price">
              ${{ product.original_price }}
            </span>
          </div>
          <div class="product-status">
            <span :class="['status-badge', product.is_active ? 'active' : 'inactive']">
              {{ product.is_active ? '上架' : '下架' }}
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

export default {
  name: 'Products',
  components: {
    ProductForm
  },
  data() {
    return {
      loading: true,
      error: null,
      products: [],
      showAddModal: false,
      editingProduct: null
    }
  },
  mounted() {
    this.fetchProducts()
  },
  methods: {
    async fetchProducts() {
      try {
        this.loading = true
        const response = await apiClient.get('/products')
        this.products = response.data.products || response.data || []
      } catch (error) {
        this.error = error.response?.data?.message || error.message || 'Failed to load products'
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
      if (!confirm('确定要删除这个商品吗？')) {
        return
      }

      try {
        await apiClient.delete(`/admin/products/${id}`)
        await this.fetchProducts()
      } catch (error) {
        alert(error.response?.data?.message || error.response?.data?.error || '删除失败')
        console.error('Delete product error:', error)
      }
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
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  overflow: hidden;
  box-shadow: var(--md-elevation-1);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.product-card:hover {
  box-shadow: var(--md-elevation-2);
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
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-placeholder {
  font-size: 4rem;
  opacity: 0.3;
}

.product-info {
  padding: var(--md-spacing-md);
}

.product-info h3 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-sm);
  font-weight: 500;
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

.price-info {
  margin-bottom: var(--md-spacing-sm);
}

.product-status {
  margin-bottom: var(--md-spacing-md);
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
  background: var(--md-primary-variant);
  color: var(--md-on-surface);
}

.edit-btn:hover {
  background: var(--md-primary);
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
</style>

