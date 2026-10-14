<template>
  <Transition name="recipe-sheet" @after-leave="onAfterLeave">
    <div v-if="show" class="overlay">
      <div class="sheet" role="dialog" aria-modal="true" :aria-label="title">
        <header class="sheet-header">
          <button
            v-if="recipeId"
            type="button"
            class="nav-btn"
            aria-label="返回"
            @click="backToList"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div v-else class="nav-spacer"></div>
          <h1>{{ title }}</h1>
          <button type="button" class="nav-btn" aria-label="关闭" @click="close">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </header>
        <div ref="scroller" class="sheet-body">
          <RecipeFeed
            v-show="!recipeId"
            embedded
            :product-id="productId"
            :scroll-root="scrollRoot"
            @open="openRecipe"
          />
          <RecipeDetailPanel
            v-if="recipeId"
            embedded
            :recipe-id="recipeId"
            @loaded="onLoaded"
            @deleted="backToList"
          />
        </div>
      </div>
    </div>
  </Transition>
</template>

<script>
import apiClient from '../api/client'
import RecipeFeed from './RecipeFeed.vue'
import RecipeDetailPanel from './RecipeDetailPanel.vue'

export default {
  name: 'RecipeBrowserModal',
  components: { RecipeFeed, RecipeDetailPanel },
  props: {
    show: { type: Boolean, default: false },
    productId: { type: [Number, String], default: '' }
  },
  emits: ['close'],
  data() {
    return {
      recipeId: null,
      recipeTitle: '',
      productName: '',
      scrollRoot: null,
      scrollY: 0,
      listScroll: 0
    }
  },
  computed: {
    title() {
      if (this.recipeId) return this.recipeTitle || '菜谱'
      return this.productName ? `${this.productName}菜谱` : '菜谱'
    }
  },
  watch: {
    show(value) {
      if (!value) return
      this.recipeId = null
      this.recipeTitle = ''
      this.listScroll = 0
      this.lockScroll()
      this.$nextTick(() => {
        this.scrollRoot = this.$refs.scroller || null
      })
    },
    productId: {
      immediate: true,
      handler() {
        this.recipeId = null
        this.recipeTitle = ''
        this.loadProductName()
      }
    },
    '$route.fullPath'() {
      if (this.show) this.close()
    }
  },
  beforeUnmount() {
    this.unlockScroll()
  },
  methods: {
    lockScroll() {
      if (document.body.style.position === 'fixed') return
      this.scrollY = window.scrollY || document.documentElement.scrollTop || 0
      document.body.style.position = 'fixed'
      document.body.style.top = `-${this.scrollY}px`
      document.body.style.left = '0'
      document.body.style.right = '0'
      document.body.style.width = '100%'
    },
    unlockScroll() {
      if (document.body.style.position !== 'fixed') return
      document.body.style.position = ''
      document.body.style.top = ''
      document.body.style.left = ''
      document.body.style.right = ''
      document.body.style.width = ''
      window.scrollTo(0, this.scrollY || 0)
    },
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
    },
    close() {
      this.$emit('close')
    },
    onAfterLeave() {
      if (this.show) return
      this.scrollRoot = null
      this.recipeId = null
      this.recipeTitle = ''
      this.listScroll = 0
      this.unlockScroll()
    },
    openRecipe(recipe) {
      this.listScroll = this.$refs.scroller ? this.$refs.scroller.scrollTop : 0
      this.recipeTitle = recipe?.title || ''
      this.recipeId = recipe.id
      this.$nextTick(() => {
        if (this.$refs.scroller) this.$refs.scroller.scrollTop = 0
      })
    },
    backToList() {
      this.recipeId = null
      this.recipeTitle = ''
      this.$nextTick(() => {
        if (this.$refs.scroller) this.$refs.scroller.scrollTop = this.listScroll || 0
      })
    },
    onLoaded(recipe) {
      this.recipeTitle = recipe?.title || ''
    }
  }
}
</script>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.5);
}
.sheet {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--md-background);
}
.sheet-header {
  display: grid;
  grid-template-columns: 40px 1fr 40px;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
  background: linear-gradient(135deg, #F9D561 0%, #F59B34 100%);
  padding: var(--md-spacing-lg);
  padding-top: calc(var(--md-spacing-lg) + var(--app-safe-top, env(safe-area-inset-top, 0px)));
  box-shadow: var(--md-elevation-2);
}
.sheet-header h1 {
  margin: 0;
  font-family: "Noto Sans SC", "PingFang SC", sans-serif;
  font-size: 1.15rem;
  color: white;
  font-weight: 600;
  letter-spacing: 0.02em;
  line-height: 1.35;
  text-align: center;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  padding: 0;
  border: none;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  color: white;
}
.nav-btn svg { width: 22px; height: 22px; }
.nav-spacer { width: 40px; height: 40px; }
.sheet-body {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
}
.recipe-sheet-enter-active,
.recipe-sheet-leave-active {
  transition: opacity 0.28s ease;
}
.recipe-sheet-enter-active .sheet,
.recipe-sheet-leave-active .sheet {
  transition: transform 0.28s ease;
}
.recipe-sheet-enter-from,
.recipe-sheet-leave-to {
  opacity: 0;
}
.recipe-sheet-enter-from .sheet,
.recipe-sheet-leave-to .sheet {
  transform: translateY(100%);
}
</style>
