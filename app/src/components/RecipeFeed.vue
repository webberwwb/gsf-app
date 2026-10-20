<template>
  <div class="recipe-feed" :class="{ embedded, pinned: !embedded }">
    <div class="feed-filters">
    <div class="toolbar">
      <div v-if="!mine && !liked && !collected" class="sort-row">
        <button type="button" :class="{ on: sort === 'latest' }" @click="setSort('latest')">最新</button>
        <button type="button" :class="{ on: sort === 'hearts' }" @click="setSort('hearts')">最多喜欢</button>
      </div>
      <div class="header-actions">
        <button type="button" class="icon-btn" :aria-label="layout === 'grid' ? '三列' : '单列'" @click="toggleLayout">
          <span class="material-symbols-outlined" aria-hidden="true">{{ layout === 'grid' ? 'view_cozy' : 'view_day' }}</span>
        </button>
        <button v-if="!embedded" type="button" class="post-btn post-add" aria-label="发布" @click="openComposer()">
          <span class="material-symbols-outlined" aria-hidden="true">post_add</span>
        </button>
      </div>
    </div>

    <CategoryTabs
      v-if="showCategoryFilter"
      mode="filter"
      show-all
      inline
      :categories="categories"
      :value="categoryId || null"
      @select="selectCategory"
    />
    </div>

    <div ref="cardScroller" class="feed-body">
    <div v-if="loading" class="skeleton" :class="layout === 'grid' ? 'grid' : 'feed'" aria-hidden="true">
      <template v-if="layout === 'grid'">
        <div v-for="n in 9" :key="n" class="grid-cell skel"></div>
      </template>
      <template v-else>
        <article v-for="n in 2" :key="n" class="post">
          <div class="photo-wrap skel"></div>
          <div class="skel-line"></div>
          <div class="skel-line short"></div>
        </article>
      </template>
    </div>
    <div v-else-if="error && !recipes.length" class="state">{{ error }}</div>
    <div v-else-if="recipes.length === 0" class="empty">
      <div class="empty-photo" aria-hidden="true">
        <svg viewBox="0 0 320 200" xmlns="http://www.w3.org/2000/svg">
          <rect width="320" height="200" fill="#f3f1ee" />
          <rect x="24" y="34" width="128" height="136" rx="8" fill="#ffffff" />
          <rect x="168" y="34" width="128" height="136" rx="8" fill="#ffffff" />
          <rect x="146" y="34" width="28" height="136" fill="#F59B34" />
          <rect x="184" y="56" width="92" height="6" rx="3" fill="#f3f1ee" />
          <rect x="184" y="74" width="78" height="6" rx="3" fill="#f3f1ee" />
          <rect x="184" y="92" width="86" height="6" rx="3" fill="#f3f1ee" />
          <rect x="184" y="110" width="58" height="6" rx="3" fill="#f3f1ee" />
          <circle cx="88" cy="112" r="24" fill="#E25B4A" />
          <ellipse cx="88" cy="86" rx="12" ry="8" fill="#7CB342" />
          <rect x="86" y="76" width="4" height="14" rx="2" fill="#689F38" />
        </svg>
      </div>
      <p>{{ emptyMessage }}</p>
      <button v-if="!embedded" type="button" class="post-btn" @click="openComposer(productId)">分享菜谱</button>
    </div>

    <div v-else-if="layout === 'grid'" class="grid">
      <button
        v-for="(recipe, recipeIndex) in recipes"
        :key="recipe.id"
        type="button"
        class="grid-cell"
        @click="openRecipe(recipe)"
      >
        <img
          :src="recipe.cover_thumb || recipe.cover_image"
          :alt="recipe.title"
          decoding="async"
          :loading="recipeIndex < 8 ? 'eager' : 'lazy'"
          :fetchpriority="recipeIndex < 8 ? 'high' : 'auto'"
        />
      </button>
    </div>

    <div v-else class="feed">
      <article v-for="recipe in recipes" :key="recipe.id" class="post">
        <div class="photo-wrap" @click="onPhotoTap(recipe)">
          <RecipePhotoCarousel :images="photosOf(recipe)" :alt="recipe.title">
          <div class="photo-top">
            <button type="button" class="uploader" @click.stop="openRecipe(recipe)">
              <span class="avatar">{{ recipe.author.initial }}</span>
              <span>{{ recipe.author.name }}</span>
            </button>
            <div v-if="recipe.products.length" class="product-badge">
              <span v-for="product in recipe.products" :key="product.id" class="chip">{{ product.name }}</span>
            </div>
          </div>
          <div v-if="recipe.difficulty_label || recipe.cook_time_label" class="photo-facts">
            <span v-if="recipe.difficulty_label" class="chip">{{ recipe.difficulty_label }}</span>
            <span v-if="recipe.cook_time_label" class="chip">{{ recipe.cook_time_label }}</span>
          </div>
          <span v-if="burstId === recipe.id" class="burst" aria-hidden="true">
            <span class="material-symbols-outlined fill">favorite</span>
          </span>
          </RecipePhotoCarousel>
        </div>
        <div class="actions">
          <button type="button" aria-label="评论" @click="openRecipe(recipe)">
            <span class="material-symbols-outlined" aria-hidden="true">chat_bubble</span>
            <span class="count">{{ recipe.comment_count }}</span>
          </button>
          <button type="button" :class="{ on: recipe.hearted }" :aria-label="recipe.hearted ? '取消喜欢' : '喜欢'" @click="heart(recipe)">
            <span class="material-symbols-outlined" :class="{ fill: recipe.hearted }" aria-hidden="true">favorite</span>
            <span class="count">{{ recipe.heart_count }}</span>
          </button>
          <button type="button" class="collect" :class="{ on: recipe.collected }" :aria-label="recipe.collected ? '取消收藏' : '收藏'" @click="collect(recipe)">
            <span class="material-symbols-outlined" :class="{ fill: recipe.collected }" aria-hidden="true">bookmark</span>
            <span class="count">{{ recipe.collect_count }}</span>
          </button>
          <button type="button" class="share" aria-label="分享" @click="share(recipe)">
            <span class="material-symbols-outlined" aria-hidden="true">ios_share</span>
          </button>
        </div>
        <h2 @click="openRecipe(recipe)">{{ recipe.title }}</h2>
        <section v-if="embedded && recipe.sides" class="recipe-copy">
          <h3>其他配菜</h3>
          <p>{{ recipe.sides }}</p>
        </section>
        <section v-if="embedded && recipe.body" class="recipe-copy">
          <h3>做法</h3>
          <p>{{ recipe.body }}</p>
        </section>
      </article>
    </div>

    <div v-if="hasMore" ref="more" class="pager">
      <span v-if="loadingMore" class="spinner" aria-hidden="true"></span>
    </div>
    <p v-if="error && recipes.length" class="notice">{{ error }}</p>
    <p v-if="notice" class="notice">{{ notice }}</p>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'
import { useAuthStore } from '../stores/auth'
import { shareRecipe } from '../utils/recipeShare'
import CategoryTabs from './CategoryTabs.vue'
import RecipePhotoCarousel from './RecipePhotoCarousel.vue'

const LAYOUT_KEY = 'recipe-feed-layout'
const PAGE_SIZE = 6

export default {
  name: 'RecipeFeed',
  components: { CategoryTabs, RecipePhotoCarousel },
  props: {
    productId: { type: [Number, String], default: '' },
    categoryId: { type: [Number, String], default: '' },
    mine: { type: Boolean, default: false },
    liked: { type: Boolean, default: false },
    collected: { type: Boolean, default: false },
    embedded: { type: Boolean, default: false },
    scrollRoot: { type: Object, default: null }
  },
  emits: ['open'],
  setup() {
    return { authStore: useAuthStore() }
  },
  data() {
    return {
      recipes: [],
      page: 1,
      total: 0,
      loading: true,
      loadingMore: false,
      error: '',
      sort: 'latest',
      layout: localStorage.getItem(LAYOUT_KEY) === 'grid' ? 'grid' : 'column',
      notice: '',
      moreVisible: false,
      burstId: null,
      lastTap: 0,
      lastTapId: null,
      categories: []
    }
  },
  computed: {
    hasMore() {
      return this.recipes.length < this.total
    },
    filterKey() {
      return [this.productId || '', this.categoryId || '', this.mine, this.liked, this.collected].join('|')
    },
    emptyMessage() {
      if (this.embedded) return '还没有菜谱。'
      if (this.categoryId) return '这个分类还没有菜谱。做一道菜，分享给大家吧！'
      return '还没有菜谱。做一道菜，分享给大家吧！'
    },
    showCategoryFilter() {
      return !this.embedded && !this.productId && this.categories.length > 0
    }
  },
  watch: {
    filterKey() {
      this.reload()
    },
    scrollRoot() {
      this.bindObserver()
    }
  },
  mounted() {
    this.bindObserver()
    this.reload()
    if (!this.embedded) this.loadCategories()
  },
  beforeUnmount() {
    this.observer?.disconnect()
  },
  updated() {
    this.watchMore()
  },
  methods: {
    bindObserver() {
      this.observer?.disconnect()
      this.observer = null
      if (this.embedded && !this.scrollRoot) return
      const options = { rootMargin: '240px' }
      const root = this.embedded ? this.scrollRoot : this.$refs.cardScroller
      if (root) options.root = root
      this.observer = new IntersectionObserver((entries) => {
        this.moreVisible = entries.some((entry) => entry.isIntersecting)
        if (this.moreVisible) this.loadMore()
      }, options)
      this.watchMore()
    },
    async loadCategories() {
      try {
        const response = await apiClient.get('/recipes/categories')
        this.categories = response.data.categories || []
      } catch (error) {
        this.categories = []
      }
      this.clearMissingCategory()
    },
    selectCategory(id) {
      const query = { ...this.$route.query }
      if (id == null || id === '') delete query.category
      else query.category = String(id)
      this.$router.replace({ query })
    },
    clearMissingCategory() {
      if (this.categoryId == null || this.categoryId === '' || !this.categories.length) return
      const known = this.categories.some((category) => String(category.id) === String(this.categoryId))
      if (!known) this.selectCategory(null)
    },
    toggleLayout() {
      this.layout = this.layout === 'grid' ? 'column' : 'grid'
      localStorage.setItem(LAYOUT_KEY, this.layout)
    },
    setSort(sort) {
      this.sort = sort
      this.reload()
    },
    async reload() {
      this.page = 1
      this.recipes = []
      this.total = 0
      this.loading = true
      this.error = ''
      await this.fetchPage(1, false)
      this.loading = false
    },
    watchMore() {
      const node = this.$refs.more
      if (!this.observer) return
      this.observer.disconnect()
      if (node) this.observer.observe(node)
    },
    async loadMore() {
      if (this.loading || this.loadingMore || !this.hasMore) return
      this.loadingMore = true
      const before = this.recipes.length
      await this.fetchPage(this.page + 1, true)
      this.loadingMore = false
      if (this.moreVisible && this.recipes.length > before) this.loadMore()
    },
    async fetchPage(page, append) {
      try {
        const params = { page, per_page: PAGE_SIZE, sort: this.sort }
        if (this.productId) params.product_id = this.productId
        if (this.categoryId) params.category_id = this.categoryId
        if (this.mine) params.mine = '1'
        if (this.liked) params.liked = '1'
        if (this.collected) params.collected = '1'
        const response = await apiClient.get('/recipes', { params })
        const rows = response.data.recipes || []
        this.recipes = append ? this.recipes.concat(rows) : rows
        this.total = response.data.total || 0
        this.page = response.data.page || page
      } catch (error) {
        this.error = error.response?.data?.error || '加载失败'
      }
    },
    photosOf(recipe) {
      const images = (recipe.images || []).filter(Boolean)
      if (images.length) return images
      return recipe.cover_image ? [recipe.cover_image] : []
    },
    openRecipe(recipe) {
      if (this.embedded) {
        this.$emit('open', recipe)
        return
      }
      this.$router.push(`/recipes/${recipe.id}`)
    },
    openComposer(product) {
      const query = {}
      const id = product || this.productId
      if (id) query.product = String(id)
      this.$router.push({ path: '/recipes/new', query })
    },
    requireLogin() {
      if (this.authStore.isAuthenticated) return true
      this.$router.push('/login')
      return false
    },
    onPhotoTap(recipe) {
      const now = Date.now()
      if (this.lastTapId === recipe.id && now - this.lastTap < 280) {
        this.heart(recipe, true)
        this.lastTap = 0
        this.lastTapId = null
        return
      }
      this.lastTap = now
      this.lastTapId = recipe.id
    },
    async heart(recipe, fromDouble = false) {
      if (!this.requireLogin()) return
      if (fromDouble === true && recipe.hearted) {
        this.burstId = recipe.id
        setTimeout(() => { if (this.burstId === recipe.id) this.burstId = null }, 500)
        return
      }
      try {
        const method = recipe.hearted && fromDouble !== true ? 'delete' : 'post'
        const response = await apiClient[method](`/recipes/${recipe.id}/heart`)
        this.replace(response.data.recipe)
        if (method === 'post') {
          this.burstId = recipe.id
          setTimeout(() => { if (this.burstId === recipe.id) this.burstId = null }, 500)
        }
      } catch (error) {
        this.notice = error.response?.data?.error || '操作失败'
      }
    },
    async collect(recipe) {
      if (!this.requireLogin()) return
      try {
        const method = recipe.collected ? 'delete' : 'post'
        const response = await apiClient[method](`/recipes/${recipe.id}/collect`)
        this.replace(response.data.recipe)
      } catch (error) {
        this.notice = error.response?.data?.error || '操作失败'
      }
    },
    replace(recipe) {
      const index = this.recipes.findIndex((row) => row.id === recipe.id)
      if (index >= 0) this.recipes.splice(index, 1, { ...this.recipes[index], ...recipe })
    },
    async share(recipe) {
      try {
        const result = await shareRecipe(recipe)
        if (result === 'copied') this.notice = '链接已复制'
        if (typeof result === 'string' && result.startsWith('http')) this.notice = result
      } catch (error) {
        if (error?.name !== 'AbortError') this.notice = '分享失败'
      }
    }
  }
}
</script>

<style scoped>
.recipe-feed.embedded {
  padding-bottom: calc(16px + env(safe-area-inset-bottom));
}
.recipe-feed.pinned {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.feed-filters {
  flex-shrink: 0;
  background: var(--md-background);
}
.recipe-feed.pinned .feed-filters {
  position: relative;
  z-index: 2;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.08);
}
.feed-body {
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.recipe-feed.pinned .feed-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
  padding-bottom: calc(88px + env(safe-area-inset-bottom));
}
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.7rem 1rem 0;
}
.header-actions, .sort-row { display: flex; gap: 0.4rem; }
.header-actions { margin-left: auto; }
.sort-row button, .icon-btn, .post-btn {
  border: none;
  border-radius: 999px;
  background: var(--md-surface-variant);
  color: var(--md-on-surface);
  padding: 0.4rem 0.8rem;
  font-size: 0.82rem;
}
.sort-row button.on, .post-btn { background: var(--md-primary); color: white; }
.icon-btn {
  width: 36px;
  height: 36px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--md-primary);
}
.post-add {
  width: 36px;
  height: 36px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.material-symbols-outlined {
  font-family: 'Material Symbols Outlined';
  font-size: 22px;
  font-weight: normal;
  font-style: normal;
  line-height: 1;
  letter-spacing: normal;
  display: inline-block;
  white-space: nowrap;
  font-feature-settings: 'liga';
  -webkit-font-feature-settings: 'liga';
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}
.material-symbols-outlined.fill {
  font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}
.state, .empty, .notice { text-align: center; padding: 1.25rem 1.25rem 2rem; color: var(--md-on-surface-variant); }
.empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.empty-photo {
  width: min(72%, 168px);
  margin-bottom: 0.85rem;
  border-radius: 14px;
  overflow: hidden;
  background: #f3f1ee;
}
.empty-photo svg { display: block; width: 100%; height: auto; }
.empty p { margin: 0 0 1rem; }
.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2px;
  margin-top: 0.75rem;
}
.grid-cell {
  border: none;
  padding: 0;
  background: #f3f1ee;
  aspect-ratio: 1;
  overflow: hidden;
}
.grid-cell img, .photo-wrap img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #f3f1ee;
}
.feed {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  margin: 0.7rem 0.7rem 0;
}
.post {
  background: var(--md-surface);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(58, 42, 26, 0.08);
}
.photo-wrap {
  position: relative;
  --recipe-photo-h: 52vw;
  margin: 8px 8px 0;
  border-radius: 10px;
  overflow: hidden;
  background: #FFF6EA;
  padding: 0;
}
.feed .photo-wrap img { object-fit: cover; background: #FFF6EA; }
.photo-top {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.4rem;
  padding: 0;
  pointer-events: none;
}
.uploader {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  max-width: 52%;
  min-width: 0;
  margin: 0;
  border: none;
  padding: 0.5rem 1.3rem 0.35rem 0.55rem;
  background: radial-gradient(ellipse at top left, rgba(0, 0, 0, 0.42) 0%, rgba(0, 0, 0, 0.14) 46%, rgba(0, 0, 0, 0) 72%);
  color: white;
  font-size: 0.78rem;
  font-weight: 500;
  line-height: 1;
  text-align: left;
  pointer-events: auto;
}
.uploader span:last-child {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.product-badge {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.3rem;
  max-width: 52%;
  min-width: 0;
  margin: 0;
  padding: 0.5rem 0.55rem 0;
}
.product-badge .chip {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.uploader .avatar {
  width: 22px;
  height: 22px;
  font-size: 0.68rem;
  flex: none;
}
.burst {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  animation: pop 0.45s ease;
  pointer-events: none;
}
.burst .material-symbols-outlined {
  font-size: 92px;
  color: white;
  font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 48;
  filter: drop-shadow(0 8px 24px rgba(0,0,0,0.25));
}
@keyframes pop {
  from { transform: scale(0.6); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
.actions {
  display: flex;
  align-items: center;
  gap: 0.1rem;
  min-height: 36px;
  padding: 0.05rem 0.45rem 0;
}
.actions button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.2rem;
  height: 32px;
  border: none;
  background: transparent;
  font-size: 0.82rem;
  font-weight: 500;
  line-height: 1;
  color: #C47A3A;
  padding: 0 0.3rem;
}
.actions .material-symbols-outlined {
  width: 22px;
  height: 22px;
  font-size: 20px;
  line-height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.actions .count {
  display: inline-flex;
  align-items: center;
  height: 22px;
  line-height: 22px;
}
.actions .on { color: #E25B4A; }
.actions .share { margin-left: auto; }
.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #F9D561 0%, #F59B34 100%);
  color: white;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  font-weight: 500;
}
.photo-facts {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  padding: 1.15rem 0.55rem 0.5rem;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.4) 0%, rgba(0, 0, 0, 0) 100%);
  pointer-events: none;
}
.post h2 {
  margin: 0 0.75rem 0.15rem;
  font-family: "Noto Sans SC", "PingFang SC", sans-serif;
  font-size: 1.02rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  line-height: 1.35;
  color: var(--md-on-surface);
}
.post h2:last-child { margin-bottom: 0.65rem; }
.recipe-copy { margin: 0.55rem 0.75rem 0; }
.recipe-copy:last-child { margin-bottom: 0.75rem; }
.recipe-copy h3 { margin: 0 0 0.2rem; font-size: 0.78rem; font-weight: 500; color: #D27529; }
.recipe-copy p { margin: 0; white-space: pre-wrap; line-height: 1.55; font-size: 0.92rem; color: var(--md-on-surface); }
.chips { display: flex; flex-wrap: wrap; gap: 0.3rem; padding: 0.15rem 0.75rem 0.65rem; }
.chip {
  border-radius: 999px;
  padding: 0.18rem 0.55rem;
  background: #FFF3E0;
  color: #D27529;
  font-size: 0.72rem;
  font-weight: 400;
  letter-spacing: 0.01em;
}
.skel, .skel-line {
  background: linear-gradient(90deg, #f3f1ee 25%, #faf8f6 50%, #f3f1ee 75%);
  background-size: 200% 100%;
  animation: shimmer 1.2s ease-in-out infinite;
}
.skel-line {
  height: 14px;
  margin: 0.7rem 0.9rem 0;
  border-radius: 999px;
}
.skel-line.short { width: 42%; margin-bottom: 0.9rem; }
@keyframes shimmer {
  from { background-position: 100% 0; }
  to { background-position: -100% 0; }
}
.pager { display: flex; justify-content: center; min-height: 28px; padding: 1rem 0 0.25rem; }
.spinner {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 2px solid #f3f1ee;
  border-top-color: var(--md-primary);
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
