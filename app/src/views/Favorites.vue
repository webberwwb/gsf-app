<template>
  <div class="favorites-page">
    <header class="page-header">
      <h1>收藏</h1>
    </header>
    <main class="page-content">
      <div v-if="favorites.length === 0" class="empty-state">
        <div class="empty-icon">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
          </svg>
        </div>
        <h2>暂无收藏</h2>
        <p>您收藏的商品将显示在这里</p>
        <button @click="$router.push('/')" class="browse-btn">去逛逛</button>
      </div>
      <div v-else class="favorites-list">
        <div
          v-for="item in favorites"
          :key="item.id"
          class="favorite-item"
        >
          <div class="item-image">
            <img
              v-if="item.image"
              :src="item.image"
              :alt="item.name"
            />
            <div v-else class="image-placeholder">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
            </div>
          </div>
          <div class="item-info">
            <h3>{{ item.name }}</h3>
            <p v-if="item.description" class="item-description">
              {{ item.description.substring(0, 60) }}...
            </p>
            <div class="item-price">
              <span class="sale-price">${{ item.sale_price }}</span>
              <span v-if="item.original_price > item.sale_price" class="original-price">
                ${{ item.original_price }}
              </span>
            </div>
            <div class="item-actions">
              <button @click="removeFavorite(item.id)" class="remove-btn">取消收藏</button>
              <button @click="addToCart(item)" class="add-cart-btn">加入购物车</button>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
export default {
  name: 'Favorites',
  data() {
    return {
      favorites: []
    }
  },
  mounted() {
    this.loadFavorites()
  },
  methods: {
    loadFavorites() {
      const savedFavorites = localStorage.getItem('favorites')
      this.favorites = savedFavorites ? JSON.parse(savedFavorites) : []
    },
    removeFavorite(productId) {
      this.favorites = this.favorites.filter(item => item.id !== productId)
      localStorage.setItem('favorites', JSON.stringify(this.favorites))
    },
    addToCart(product) {
      // Get current cart
      const cart = JSON.parse(localStorage.getItem('cart') || '[]')
      
      // Check if product already in cart
      const existingItem = cart.find(item => item.id === product.id)
      
      if (existingItem) {
        existingItem.quantity++
      } else {
        cart.push({
          id: product.id,
          name: product.name,
          price: product.sale_price,
          image: product.image,
          quantity: 1
        })
      }
      
      // Save cart
      localStorage.setItem('cart', JSON.stringify(cart))
      
      // Update badge in bottom nav
      this.$root.$emit('cart-updated')
      
      alert(`已添加 ${product.name} 到购物车`)
    }
  }
}
</script>

<style scoped>
.favorites-page {
  min-height: 100vh;
  background: var(--md-background);
  padding-bottom: 80px; /* Space for bottom nav */
}

.page-header {
  background: var(--md-surface);
  padding: var(--md-spacing-md);
  border-bottom: none;
  box-shadow: var(--md-elevation-1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.page-header h1 {
  font-size: var(--md-headline-size);
  color: var(--md-on-surface);
  font-weight: 500;
  letter-spacing: -0.5px;
}

.page-content {
  padding: 1rem;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
}

.empty-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 1rem;
  opacity: 0.3;
  color: var(--md-on-surface-variant);
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-icon svg {
  width: 100%;
  height: 100%;
}

.empty-state h2 {
  font-size: 1.5rem;
  color: #333;
  margin-bottom: 0.5rem;
}

.empty-state p {
  color: #666;
  font-size: 1rem;
  margin-bottom: 2rem;
}

.browse-btn {
  background: #FF8C00;
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
}

.favorites-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.favorite-item {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-md);
  display: flex;
  gap: var(--md-spacing-md);
  box-shadow: var(--md-elevation-1);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.favorite-item:hover {
  box-shadow: var(--md-elevation-2);
  transform: translateY(-2px);
}

.item-image {
  width: 100px;
  height: 100px;
  background: #f9f9f9;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}

.item-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
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

.item-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.item-info h3 {
  font-size: 1rem;
  color: #333;
  font-weight: 600;
}

.item-description {
  font-size: 0.85rem;
  color: #666;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-price {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.sale-price {
  font-size: 1.2rem;
  color: #ff4444;
  font-weight: 600;
}

.original-price {
  font-size: 0.9rem;
  color: #999;
  text-decoration: line-through;
}

.item-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.remove-btn {
  flex: 1;
  background: var(--md-surface);
  color: var(--md-on-surface-variant);
  border: 1px solid var(--md-outline);
  padding: 0.625rem;
  border-radius: var(--md-radius-sm);
  font-size: var(--md-label-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.remove-btn:hover {
  background: var(--md-surface-variant);
  border-color: var(--md-on-surface-variant);
}

.remove-btn:active {
  transform: scale(0.98);
}

.add-cart-btn {
  flex: 1;
  background: var(--md-primary);
  color: white;
  border: none;
  padding: 0.625rem;
  border-radius: var(--md-radius-sm);
  font-size: var(--md-label-size);
  font-weight: 500;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 4px rgba(255, 140, 0, 0.2);
  text-transform: uppercase;
}

.add-cart-btn:hover {
  background: #FF7F00;
  box-shadow: 0 4px 8px rgba(255, 140, 0, 0.3);
  transform: translateY(-1px);
}

.add-cart-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(255, 140, 0, 0.2);
}
</style>

