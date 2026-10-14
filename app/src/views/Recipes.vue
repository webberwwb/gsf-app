<template>
  <div class="recipes-page">
    <header class="page-header">
      <div class="header-content">
        <img src="/logos/gsf-icon.png" alt="谷语农庄" class="logo" />
        <div class="header-text">
          <h1>谷语农庄</h1>
          <p>{{ pageTitle }}</p>
        </div>
      </div>
    </header>

    <RecipeFeed
      :product-id="productId"
      :category-id="categoryId"
      :mine="mine"
      :liked="liked"
      :collected="collected"
    />
  </div>
</template>

<script>
import apiClient from '../api/client'
import RecipeFeed from '../components/RecipeFeed.vue'

export default {
  name: 'Recipes',
  components: { RecipeFeed },
  data() {
    return {
      productName: ''
    }
  },
  computed: {
    productId() {
      const raw = this.$route.query.product
      return raw ? String(raw) : ''
    },
    categoryId() {
      const raw = this.$route.query.category
      if (!raw || raw === 'all') return null
      if (raw === 'none') return 'none'
      const id = parseInt(raw, 10)
      return Number.isNaN(id) ? null : id
    },
    mine() {
      return this.$route.query.mine === '1'
    },
    liked() {
      return this.$route.query.liked === '1'
    },
    collected() {
      return this.$route.query.collected === '1'
    },
    pageTitle() {
      if (this.productId) return this.productName ? `${this.productName}菜谱` : '菜谱'
      if (this.mine) return '我的菜谱'
      if (this.liked) return '我喜欢的'
      if (this.collected) return '我收藏的'
      return '菜谱分享'
    }
  },
  watch: {
    productId: {
      immediate: true,
      handler() {
        this.loadProductName()
      }
    }
  },
  methods: {
    async loadProductName() {
      const id = this.productId
      this.productName = ''
      if (!id) return
      try {
        const response = await apiClient.get(`/products/${id}`)
        if (String(this.productId) !== String(id)) return
        this.productName = response.data.product?.name || ''
      } catch (error) {
        this.productName = ''
      }
    }
  }
}
</script>

<style scoped>
.recipes-page {
  height: 100vh;
  height: 100dvh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--md-background);
}
.page-header {
  flex-shrink: 0;
  background: linear-gradient(135deg, #F9D561 0%, #F59B34 100%);
  padding: var(--md-spacing-lg);
  padding-top: calc(var(--md-spacing-lg) + var(--app-safe-top, env(safe-area-inset-top, 0px)));
  box-shadow: var(--md-elevation-2);
  position: relative;
  z-index: 3;
}
.header-content {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
  max-width: 600px;
  margin: 0 auto;
}
.header-text {
  min-width: 0;
}
.logo {
  width: 64px;
  height: 64px;
  object-fit: contain;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.15));
}
.header-text h1 {
  font-size: var(--md-headline-size);
  color: white;
  margin: 0 0 var(--md-spacing-xs);
  font-weight: 500;
  letter-spacing: -0.5px;
}
.header-text p {
  margin: 0;
  font-size: var(--md-label-size);
  color: rgba(255, 255, 255, 0.9);
  font-weight: 400;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
