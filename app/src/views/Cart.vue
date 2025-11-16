<template>
  <div class="cart-page">
    <header class="page-header">
      <h1>购物车</h1>
    </header>
    <main class="page-content">
      <div v-if="cartItems.length === 0" class="empty-state">
        <div class="empty-icon">🛒</div>
        <h2>购物车是空的</h2>
        <p>快去挑选您喜欢的商品吧</p>
        <button @click="$router.push('/')" class="browse-btn">去逛逛</button>
      </div>
      <div v-else class="cart-items">
        <div v-for="item in cartItems" :key="item.id" class="cart-item">
          <div class="item-info">
            <h3>{{ item.name }}</h3>
            <p class="item-price">${{ item.price }}</p>
          </div>
          <div class="item-actions">
            <button @click="decreaseQuantity(item)" class="qty-btn">-</button>
            <span class="qty">{{ item.quantity }}</span>
            <button @click="increaseQuantity(item)" class="qty-btn">+</button>
          </div>
        </div>
        <div class="cart-footer">
          <div class="total">
            <span>总计：</span>
            <span class="total-price">${{ totalPrice }}</span>
          </div>
          <button class="checkout-btn">去结算</button>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
export default {
  name: 'Cart',
  data() {
    return {
      cartItems: []
    }
  },
  computed: {
    totalPrice() {
      return this.cartItems.reduce((sum, item) => {
        return sum + (parseFloat(item.price) * item.quantity)
      }, 0).toFixed(2)
    }
  },
  mounted() {
    this.loadCart()
  },
  methods: {
    loadCart() {
      const savedCart = localStorage.getItem('cart')
      this.cartItems = savedCart ? JSON.parse(savedCart) : []
    },
    increaseQuantity(item) {
      item.quantity++
      this.saveCart()
    },
    decreaseQuantity(item) {
      if (item.quantity > 1) {
        item.quantity--
      } else {
        this.cartItems = this.cartItems.filter(i => i.id !== item.id)
      }
      this.saveCart()
    },
    saveCart() {
      localStorage.setItem('cart', JSON.stringify(this.cartItems))
      // Update badge in bottom nav
      this.$root.$emit('cart-updated')
    }
  }
}
</script>

<style scoped>
.cart-page {
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
  font-size: 4rem;
  margin-bottom: 1rem;
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

.cart-items {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.cart-item {
  background: var(--md-surface);
  padding: var(--md-spacing-md);
  border-radius: var(--md-radius-lg);
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: var(--md-elevation-1);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.cart-item:hover {
  box-shadow: var(--md-elevation-2);
}

.item-info h3 {
  font-size: 1rem;
  color: #333;
  margin-bottom: 0.25rem;
}

.item-price {
  color: #FF8C00;
  font-size: 1.1rem;
  font-weight: 600;
}

.item-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.qty-btn {
  width: 36px;
  height: 36px;
  border: 1px solid var(--md-outline);
  background: var(--md-surface);
  border-radius: var(--md-radius-sm);
  font-size: 1.25rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  color: var(--md-on-surface);
}

.qty-btn:hover {
  background: var(--md-surface-variant);
  border-color: var(--md-primary);
}

.qty-btn:active {
  transform: scale(0.95);
}

.qty {
  min-width: 30px;
  text-align: center;
  font-weight: 600;
}

.cart-footer {
  position: fixed;
  bottom: 80px; /* Above bottom nav */
  left: 0;
  right: 0;
  background: var(--md-surface);
  padding: var(--md-spacing-md);
  border-top: none;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.95);
}

.total {
  font-size: var(--md-body-size);
  color: var(--md-on-surface);
  font-weight: 500;
}

.total-price {
  color: var(--md-primary);
  font-size: 1.5rem;
  font-weight: 600;
  margin-left: var(--md-spacing-sm);
  letter-spacing: -0.5px;
}

.checkout-btn {
  background: var(--md-primary);
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 4px rgba(255, 140, 0, 0.2);
  text-transform: uppercase;
}

.checkout-btn:hover {
  background: #FF7F00;
  box-shadow: 0 4px 8px rgba(255, 140, 0, 0.3);
  transform: translateY(-1px);
}

.checkout-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(255, 140, 0, 0.2);
}
</style>

