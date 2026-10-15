<template>
  <div class="recipes-admin">
    <div class="feed-filters">
      <div class="toolbar">
        <div class="sort-row">
          <button type="button" :class="{ on: sort === 'latest' }" @click="setSort('latest')">最新</button>
          <button type="button" :class="{ on: sort === 'hearts' }" @click="setSort('hearts')">最多喜欢</button>
        </div>
        <div class="header-actions">
          <button type="button" class="icon-btn" :aria-label="layout === 'grid' ? '切换为单列' : '切换为三列'" @click="toggleLayout">
            <span class="material-symbols-outlined" aria-hidden="true">{{ layout === 'grid' ? 'view_cozy' : 'view_day' }}</span>
          </button>
          <button type="button" class="post-btn" aria-label="发布谷语农庄菜谱" @click="openCreate">
            <span class="material-symbols-outlined" aria-hidden="true">post_add</span>
            <span class="post-label">发布</span>
          </button>
        </div>
      </div>
      <div class="product-bar">
        <button type="button" class="product-filter" @click="openFilter">
          <span class="product-filter-copy">
            <span class="product-filter-kicker">商品</span>
            <strong>{{ productLabel }}</strong>
          </span>
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        <button v-if="productId" type="button" class="product-clear" aria-label="查看全部商品" @click="selectProduct('')">×</button>
      </div>
    </div>

    <div v-if="loading" class="skeleton" :class="layout === 'grid' ? 'grid' : 'feed'" aria-hidden="true">
      <template v-if="layout === 'grid'">
        <div v-for="n in 9" :key="n" class="grid-cell skel"></div>
      </template>
      <template v-else>
        <article v-for="n in 4" :key="n" class="post">
          <div class="photo-wrap skel"></div>
          <div class="skel-line"></div>
          <div class="skel-line short"></div>
        </article>
      </template>
    </div>
    <div v-else-if="error && !recipes.length" class="state">
      <p>{{ error }}</p>
      <button type="button" class="post-btn retry" @click="reload">重试</button>
    </div>
    <div v-else-if="!recipes.length" class="empty">
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
      <button type="button" class="post-btn retry" @click="openCreate">发布谷语农庄菜谱</button>
    </div>

    <div v-else-if="layout === 'grid'" class="grid">
      <button
        v-for="recipe in recipes"
        :key="recipe.id"
        type="button"
        class="grid-cell"
        @click="openRecipe(recipe)"
      >
        <img :src="recipe.cover_image" :alt="recipe.title" />
        <span v-if="recipe.rewarded_at" class="grid-badge">已发券</span>
      </button>
    </div>

    <div v-else class="feed">
      <article v-for="recipe in recipes" :key="recipe.id" class="post">
        <div class="photo-wrap" @click="openRecipe(recipe)">
          <RecipePhotoCarousel :images="photosOf(recipe)" :alt="recipe.title">
            <div class="photo-top">
              <div class="uploader">
                <span class="avatar">{{ recipe.author.initial }}</span>
                <span>{{ recipe.author.name }}</span>
                <span v-if="recipe.source === 'official'" class="official">官方</span>
              </div>
              <div v-if="recipe.products.length" class="product-badge">
                <button
                  v-for="product in recipe.products"
                  :key="product.id"
                  type="button"
                  class="chip"
                  @click.stop="selectProduct(product.id)"
                >{{ product.name }}</button>
              </div>
            </div>
            <div v-if="recipe.difficulty_label || recipe.cook_time_label || recipe.rewarded_at" class="photo-facts">
              <span v-if="recipe.difficulty_label" class="chip">{{ recipe.difficulty_label }}</span>
              <span v-if="recipe.cook_time_label" class="chip">{{ recipe.cook_time_label }}</span>
              <span v-if="recipe.rewarded_at" class="chip rewarded">已发券</span>
            </div>
          </RecipePhotoCarousel>
        </div>
        <div class="actions">
          <button type="button" aria-label="评论" @click="openRecipe(recipe)">
            <span class="material-symbols-outlined" aria-hidden="true">chat_bubble</span>
            <span class="count">{{ recipe.comment_count }}</span>
          </button>
          <span class="stat" aria-label="喜欢">
            <span class="material-symbols-outlined" aria-hidden="true">favorite</span>
            <span class="count">{{ recipe.heart_count }}</span>
          </span>
          <span class="stat" aria-label="收藏">
            <span class="material-symbols-outlined" aria-hidden="true">bookmark</span>
            <span class="count">{{ recipe.collect_count }}</span>
          </span>
        </div>
        <h2 @click="openRecipe(recipe)">{{ recipe.title }}</h2>
        <div class="manage">
          <button type="button" class="reward" :disabled="!!recipe.rewarded_at" @click="startReward(recipe)">
            <span class="material-symbols-outlined" aria-hidden="true">redeem</span>
            {{ recipe.rewarded_at ? '已发代金券' : '奖励代金券' }}
          </button>
          <button type="button" class="danger" @click="remove(recipe)">
            <span class="material-symbols-outlined" aria-hidden="true">delete</span>
            删除
          </button>
        </div>
      </article>
    </div>

    <div v-if="hasMore" ref="more" class="pager">
      <span v-if="loadingMore" class="spinner" aria-hidden="true"></span>
    </div>
    <p v-if="error && recipes.length" class="inline-error">{{ error }}</p>

    <div v-if="detailId" class="overlay detail-page">
      <header class="page-header">
        <button type="button" class="back-button" aria-label="返回" @click="closeDetail">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h1>{{ detail?.title || '菜谱' }}</h1>
        <span class="header-spacer"></span>
      </header>
      <div class="overlay-scroll">
        <div v-if="detailLoading && !detail" class="state"><span class="spinner" aria-hidden="true"></span></div>
        <article v-else-if="detail" class="card">
          <RecipePhotoCarousel class="hero" :images="photosOf(detail)" :alt="detail.title">
            <div class="photo-top detail-top">
              <div class="uploader">
                <span class="avatar">{{ detail.author.initial }}</span>
                <span>{{ detail.author.name }}</span>
                <span v-if="detail.source === 'official'" class="official">官方</span>
              </div>
              <div v-if="detail.products.length" class="product-side">
                <button
                  v-for="product in detail.products"
                  :key="product.id"
                  type="button"
                  class="chip"
                  @click="selectProduct(product.id)"
                >{{ product.name }}</button>
              </div>
            </div>
            <div v-if="detail.difficulty_label || detail.cook_time_label || detail.rewarded_at" class="photo-facts">
              <span v-if="detail.difficulty_label" class="chip">{{ detail.difficulty_label }}</span>
              <span v-if="detail.cook_time_label" class="chip">{{ detail.cook_time_label }}</span>
              <span v-if="detail.rewarded_at" class="chip rewarded">已发券</span>
            </div>
          </RecipePhotoCarousel>
          <div class="actions">
            <span class="stat">
              <span class="material-symbols-outlined" aria-hidden="true">chat_bubble</span>
              <span class="count">{{ detail.comment_count }}</span>
            </span>
            <span class="stat">
              <span class="material-symbols-outlined" aria-hidden="true">favorite</span>
              <span class="count">{{ detail.heart_count }}</span>
            </span>
            <span class="stat">
              <span class="material-symbols-outlined" aria-hidden="true">bookmark</span>
              <span class="count">{{ detail.collect_count }}</span>
            </span>
          </div>
          <h2 class="title">{{ detail.title }}</h2>
          <section v-if="detail.sides" class="block">
            <h3>其他配菜</h3>
            <p>{{ detail.sides }}</p>
          </section>
          <section class="block">
            <h3>做法</h3>
            <p>{{ detail.body }}</p>
          </section>
          <section class="comments">
            <h3>评论</h3>
            <p v-if="detailLoading" class="muted">加载评论...</p>
            <p v-else-if="!detailComments.length" class="muted">还没有评论</p>
            <article v-for="comment in detailComments" :key="comment.id">
              <div class="line">
                <b>{{ comment.author_name }}</b>
                <span>{{ comment.body }}</span>
                <button type="button" class="text danger-text" @click="removeComment(comment)">删除</button>
              </div>
              <div v-for="reply in comment.replies" :key="reply.id" class="reply line">
                <b>{{ reply.author_name }}</b>
                <span>{{ reply.body }}</span>
                <button type="button" class="text danger-text" @click="removeComment(reply)">删除</button>
              </div>
            </article>
          </section>
        </article>
        <div v-else class="state"><p>这份菜谱不可用</p></div>
      </div>
      <footer v-if="detail" class="detail-bar">
        <button type="button" class="reward" :disabled="!!detail.rewarded_at || saving" @click="startReward(detail)">
          <span class="material-symbols-outlined" aria-hidden="true">redeem</span>
          {{ detail.rewarded_at ? '已发代金券' : '奖励代金券' }}
        </button>
        <button type="button" class="danger" :disabled="saving" @click="remove(detail)">
          <span class="material-symbols-outlined" aria-hidden="true">delete</span>
          删除
        </button>
      </footer>
    </div>

    <div v-if="creating" class="overlay composer-page">
      <header class="page-header">
        <button type="button" class="back-button" aria-label="返回" @click="closeComposer">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h1>谷语农庄菜谱</h1>
        <button type="button" class="share-btn" :class="{ ready: canPublish }" :disabled="!canPublish" @click="createOfficial">
          {{ saving ? '发布中' : '发布' }}
        </button>
      </header>
      <div class="overlay-scroll">
        <section class="stage">
          <div v-if="!draftImages.length" class="stage-empty">
            <label>
              <input type="file" accept="image/*" multiple @change="onFiles" />
              <strong>{{ uploading ? '正在上传' : '上传配图' }}</strong>
              <span>最多 6 张，点一张设为封面</span>
            </label>
          </div>
          <div v-else class="film">
            <button
              v-for="image in draftImages"
              :key="image"
              type="button"
              class="photo"
              :class="{ cover: image === draftCover }"
              @click="draftCover = image"
            >
              <img :src="image" alt="" />
              <span v-if="image === draftCover" class="cover-pill">封面</span>
              <span class="remove-photo" role="button" aria-label="移除这张照片" @click.stop="removeImage(image)">×</span>
            </button>
            <label v-if="draftImages.length < 6" class="add-tile">
              <input type="file" accept="image/*" multiple @change="onFiles" />
              <strong>{{ uploading ? '…' : '+' }}</strong>
            </label>
          </div>
        </section>
        <section class="sheet-form">
          <label class="field">
            <span>菜名</span>
            <input v-model="draftTitle" maxlength="80" placeholder="这道菜叫什么" enterkeyhint="next" />
          </label>
          <button type="button" class="picker-row" @click="openDraftPicker('category')">
            <span>分类</span>
            <strong :class="{ empty: !draftCategoryId }">{{ draftCategoryLabel }}</strong>
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </button>
          <button type="button" class="picker-row" :disabled="!draftCategoryId" @click="openDraftPicker('product')">
            <span>主要食材</span>
            <strong :class="{ empty: !draftProductId }">{{ draftProductLabel }}</strong>
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </button>
          <label class="field">
            <span>其他配菜</span>
            <textarea v-model="draftSides" maxlength="500" rows="3" placeholder="还需要什么" />
          </label>
          <div class="choice">
            <span>难易程度</span>
            <div class="segments">
              <button v-for="item in difficulties" :key="item.id" type="button" :class="{ on: draftDifficulty === item.id }" @click="draftDifficulty = item.id">{{ item.name }}</button>
            </div>
          </div>
          <div class="choice">
            <span>烹饪时长</span>
            <div class="segments">
              <button v-for="item in cookTimes" :key="item.id" type="button" :class="{ on: draftCookTime === item.id }" @click="draftCookTime = item.id">{{ item.name }}</button>
            </div>
          </div>
          <label class="field">
            <span>做法</span>
            <textarea v-model="draftBody" maxlength="4000" rows="6" placeholder="步骤和火候" />
          </label>
        </section>
      </div>
    </div>

    <div v-if="sheet" class="sheet-mask" @click.self="closeSheet">
      <div class="picker-sheet" role="dialog" aria-modal="true" :style="sheetStyle" :aria-label="sheetTitle">
        <header>
          <h3>{{ sheetTitle }}</h3>
          <button type="button" aria-label="关闭" @click="closeSheet">×</button>
        </header>
        <div v-if="sheet === 'filter'" class="sheet-cats">
          <button type="button" :class="{ on: !sheetCategory }" @click="sheetCategory = ''">全部</button>
          <button
            v-for="category in filterCategories"
            :key="category.id"
            type="button"
            :class="{ on: String(sheetCategory) === String(category.id) }"
            @click="sheetCategory = String(category.id)"
          >{{ category.name }}</button>
        </div>
        <label v-if="sheet === 'filter' || sheet === 'product'" class="picker-search">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-4.35-4.35M11 18a7 7 0 100-14 7 7 0 000 14z" />
          </svg>
          <input
            v-model="productQuery"
            type="search"
            enterkeyhint="search"
            autocomplete="off"
            autocorrect="off"
            placeholder="搜索商品"
          />
          <button v-if="productQuery" type="button" aria-label="清除" @click="productQuery = ''">×</button>
        </label>
        <p v-if="sheet === 'reward' && rewardRecipe" class="reward-note">
          发给 {{ rewardRecipe.author.name }}
          <template v-if="rewardRecipe.source === 'official'"> · 官方菜谱的代金券进入发布者账户</template>
        </p>
        <form v-if="sheet === 'reward'" class="reward-form" @submit.prevent="sendReward">
          <label>
            <span>金额</span>
            <input v-model="rewardAmount" type="number" min="0.01" step="0.01" inputmode="decimal" required />
          </label>
          <label>
            <span>原因</span>
            <input v-model="rewardReason" type="text" maxlength="80" required />
          </label>
          <p v-if="rewardError" class="form-error">{{ rewardError }}</p>
          <button type="submit" class="post-btn retry" :disabled="saving">{{ saving ? '发放中' : '发放' }}</button>
        </form>
        <p v-else-if="sheet !== 'category' && productQuery && !listedProducts.length" class="picker-empty">没有找到「{{ productQuery.trim() }}」</p>
        <ul v-else-if="sheet !== 'reward'" class="picker-list">
          <li v-if="sheet === 'filter'">
            <button type="button" :class="{ on: !productId }" @click="selectProduct('')">
              <span>全部商品</span>
            </button>
          </li>
          <li v-for="option in sheetOptions" :key="option.id">
            <button type="button" :class="{ on: isPicked(option.id) }" @click="choose(option.id)">
              <img v-if="option.image" :src="option.image" alt="" />
              <span>{{ option.name }}</span>
              <em v-if="sheet === 'filter' && counts[String(option.id)]">{{ counts[String(option.id)] }}</em>
            </button>
          </li>
        </ul>
      </div>
    </div>

    <p v-if="message" class="toast" :class="{ raised: detailId || creating }" role="status">{{ message }}</p>
  </div>
</template>

<script>
import apiClient from '../api/client'
import RecipePhotoCarousel from '../components/RecipePhotoCarousel.vue'
import { useModal } from '../composables/useModal'

const LAYOUT_KEY = 'admin-recipe-feed-layout'

export default {
  name: 'AdminRecipes',
  components: { RecipePhotoCarousel },
  setup() {
    const { confirm } = useModal()
    return { confirm }
  },
  data() {
    return {
      recipes: [],
      page: 1,
      total: 0,
      loading: true,
      loadingMore: false,
      error: '',
      message: '',
      layout: localStorage.getItem(LAYOUT_KEY) === 'grid' ? 'grid' : 'column',
      products: [],
      categories: [],
      counts: {},
      sheet: '',
      sheetCategory: '',
      productQuery: '',
      keyboardInset: 0,
      detailId: null,
      detail: null,
      detailLoading: false,
      creating: false,
      draftTitle: '',
      draftBody: '',
      draftSides: '',
      draftDifficulty: '',
      draftCookTime: '',
      draftImages: [],
      draftCover: '',
      draftCategoryId: '',
      draftProductId: '',
      difficulties: [
        { id: 'easy', name: '新手友好' },
        { id: 'medium', name: '花点功夫' },
        { id: 'hard', name: '大制作' }
      ],
      cookTimes: [
        { id: 'under_1h', name: '1小时内' },
        { id: '1_to_4h', name: '1–4小时' },
        { id: 'over_4h', name: '4小时以上' }
      ],
      uploading: false,
      saving: false,
      rewardRecipe: null,
      rewardAmount: '5',
      rewardReason: '',
      rewardError: '',
      requestId: 0
    }
  },
  computed: {
    productId() {
      const raw = this.$route.query.product
      return raw ? String(raw) : ''
    },
    sort() {
      return this.$route.query.sort === 'hearts' ? 'hearts' : 'latest'
    },
    filterKey() {
      return `${this.productId}|${this.sort}`
    },
    hasMore() {
      return this.recipes.length < this.total
    },
    productLabel() {
      if (!this.productId) return '全部商品'
      const found = this.products.find((product) => String(product.id) === this.productId)
      return found?.name || '所选商品'
    },
    emptyMessage() {
      if (this.productId) return '这个商品还没有菜谱。'
      return '还没有菜谱。'
    },
    detailComments() {
      return this.detail?.comments || []
    },
    filterCategories() {
      const used = new Set()
      this.products.forEach((product) => {
        if (Number(this.counts[String(product.id)] || 0) > 0) used.add(product.category_id || 'none')
      })
      const rows = this.categories.filter((category) => !used.size || used.has(category.id))
      if (!used.size || used.has('none')) {
        if (this.products.some((product) => !product.category_id)) rows.push({ id: 'none', name: '其他' })
      }
      return rows
    },
    composeCategories() {
      const used = new Set(this.products.map((product) => product.category_id).filter(Boolean))
      const rows = this.categories.filter((category) => used.has(category.id))
      if (this.products.some((product) => !product.category_id)) rows.push({ id: 'none', name: '其他' })
      return rows
    },
    listedProducts() {
      let rows = this.products.slice()
      const category = this.sheet === 'filter'
        ? this.sheetCategory
        : (this.sheet === 'product' ? this.draftCategoryId : '')
      if (category) {
        rows = category === 'none'
          ? rows.filter((product) => !product.category_id)
          : rows.filter((product) => String(product.category_id) === String(category))
      }
      const query = this.productQuery.trim().toLowerCase()
      if (query) rows = rows.filter((product) => (product.name || '').toLowerCase().includes(query))
      else if (this.sheet === 'filter' && !category) {
        const withRecipes = rows.filter((product) => Number(this.counts[String(product.id)] || 0) > 0)
        if (withRecipes.length) rows = withRecipes
      }
      rows.sort((a, b) => (a.name || '').localeCompare(b.name || '', 'zh'))
      return rows
    },
    sheetOptions() {
      if (this.sheet === 'category') return this.composeCategories
      return this.listedProducts
    },
    sheetTitle() {
      if (this.sheet === 'reward') return '奖励代金券'
      if (this.sheet === 'category') return '选择分类'
      if (this.sheet === 'product') return '选择主要食材'
      return '按商品筛选'
    },
    sheetStyle() {
      if (!this.keyboardInset) return null
      return {
        marginBottom: `${this.keyboardInset}px`,
        maxHeight: `calc(100dvh - ${this.keyboardInset}px - env(safe-area-inset-top, 0px) - 0.75rem)`
      }
    },
    draftCategoryLabel() {
      if (!this.draftCategoryId) return '选择分类'
      const found = this.composeCategories.find((category) => String(category.id) === String(this.draftCategoryId))
      return found?.name || '选择分类'
    },
    draftProductLabel() {
      if (!this.draftCategoryId) return '先选分类'
      if (!this.draftProductId) return '选择主要食材'
      const found = this.products.find((product) => String(product.id) === String(this.draftProductId))
      return found?.name || '选择主要食材'
    },
    canPublish() {
      return !this.saving && !this.uploading
        && this.draftImages.length > 0
        && this.draftTitle.trim()
        && this.draftBody.trim()
        && this.draftDifficulty
        && this.draftCookTime
        && !!this.draftProductId
    }
  },
  watch: {
    filterKey: {
      immediate: true,
      handler() {
        this.reload()
      }
    },
    sheet(value) {
      if (value) this.bindViewport()
      else this.unbindViewport()
    }
  },
  mounted() {
    this.bindObserver()
    this.loadCatalog()
    this.onKey = (event) => {
      if (event.key !== 'Escape') return
      if (this.sheet) this.closeSheet()
      else if (this.creating) this.closeComposer()
      else if (this.detailId) this.closeDetail()
    }
    window.addEventListener('keydown', this.onKey)
  },
  beforeUnmount() {
    this.observer?.disconnect()
    this.unbindViewport()
    window.removeEventListener('keydown', this.onKey)
    clearTimeout(this.messageTimer)
  },
  updated() {
    this.watchMore()
  },
  methods: {
    bindObserver() {
      this.observer = new IntersectionObserver((entries) => {
        if (entries.some((entry) => entry.isIntersecting)) this.loadMore()
      }, { rootMargin: '280px' })
      this.watchMore()
    },
    watchMore() {
      const node = this.$refs.more
      if (!this.observer) return
      this.observer.disconnect()
      if (node) this.observer.observe(node)
    },
    bindViewport() {
      this.onViewport = () => this.syncKeyboard()
      window.visualViewport?.addEventListener('resize', this.onViewport)
      window.visualViewport?.addEventListener('scroll', this.onViewport)
      this.syncKeyboard()
    },
    unbindViewport() {
      if (!this.onViewport) return
      window.visualViewport?.removeEventListener('resize', this.onViewport)
      window.visualViewport?.removeEventListener('scroll', this.onViewport)
      this.onViewport = null
      this.keyboardInset = 0
    },
    syncKeyboard() {
      const viewport = window.visualViewport
      const typing = this.sheet === 'filter' || this.sheet === 'product' || this.sheet === 'reward'
      this.keyboardInset = typing && viewport
        ? Math.max(0, Math.round(window.innerHeight - viewport.height - viewport.offsetTop))
        : 0
    },
    async loadCatalog() {
      try {
        const [products, categories] = await Promise.all([
          apiClient.get('/products'),
          apiClient.get('/product-categories')
        ])
        this.products = products.data.products || []
        this.categories = categories.data.categories || []
      } catch (error) {
        this.products = []
        this.categories = []
      }
      try {
        const counts = await apiClient.get('/recipes/counts')
        this.counts = counts.data.counts || {}
      } catch (error) {
        this.counts = {}
      }
      if (this.creating && this.draftProductId && !this.draftCategoryId) {
        const product = this.products.find((row) => String(row.id) === String(this.draftProductId))
        if (product) this.draftCategoryId = product.category_id ? String(product.category_id) : 'none'
      }
    },
    setSort(sort) {
      const query = { ...this.$route.query }
      if (sort === 'latest') delete query.sort
      else query.sort = sort
      this.$router.replace({ query })
    },
    selectProduct(id) {
      const query = { ...this.$route.query }
      if (!id) delete query.product
      else query.product = String(id)
      this.closeSheet()
      if (this.detailId) this.closeDetail()
      const same = String(this.$route.query.product || '') === String(query.product || '')
      if (same) return
      this.$router.replace({ query })
    },
    toggleLayout() {
      this.layout = this.layout === 'grid' ? 'column' : 'grid'
      localStorage.setItem(LAYOUT_KEY, this.layout)
    },
    async reload() {
      const token = ++this.requestId
      this.page = 1
      this.recipes = []
      this.total = 0
      this.loading = true
      this.error = ''
      await this.fetchPage(1, false, token)
      if (token !== this.requestId) return
      this.loading = false
      this.$el?.closest('.content-area')?.scrollTo({ top: 0 })
    },
    async loadMore() {
      if (this.loading || this.loadingMore || !this.hasMore || this.error) return
      const token = this.requestId
      this.loadingMore = true
      const before = this.recipes.length
      await this.fetchPage(this.page + 1, true, token)
      if (token !== this.requestId) return
      this.loadingMore = false
      if (!this.error && this.recipes.length === before) this.total = this.recipes.length
    },
    async fetchPage(page, append, token) {
      try {
        const params = { page, per_page: 8, sort: this.sort }
        if (this.productId) params.product_id = this.productId
        const response = await apiClient.get('/admin/recipes', { params })
        if (token !== this.requestId) return
        const rows = response.data.recipes || []
        this.recipes = append ? this.recipes.concat(rows) : rows
        this.total = response.data.total || 0
        this.page = response.data.page || page
      } catch (error) {
        if (token !== this.requestId) return
        this.error = error.response?.data?.error || '加载失败'
      }
    },
    photosOf(recipe) {
      const images = (recipe?.images || []).filter(Boolean)
      if (images.length) return images
      return recipe?.cover_image ? [recipe.cover_image] : []
    },
    async openRecipe(recipe) {
      this.detailId = recipe.id
      this.detail = { ...recipe, comments: recipe.comments || null }
      this.detailLoading = true
      try {
        const response = await apiClient.get(`/recipes/${recipe.id}`)
        if (this.detailId !== recipe.id) return
        this.detail = response.data.recipe
        this.replace(response.data.recipe)
      } catch (error) {
        if (this.detailId === recipe.id && !this.detail?.title) this.detail = null
      } finally {
        if (this.detailId === recipe.id) this.detailLoading = false
      }
    },
    closeDetail() {
      this.detailId = null
      this.detail = null
    },
    replace(recipe) {
      const index = this.recipes.findIndex((row) => row.id === recipe.id)
      if (index >= 0) this.recipes.splice(index, 1, { ...this.recipes[index], ...recipe })
    },
    async remove(recipe) {
      const ok = await this.confirm(`删除「${recipe.title}」？删除后用户将看不到这份菜谱。`, {
        title: '删除菜谱',
        type: 'warning',
        confirmText: '删除'
      })
      if (!ok) return
      try {
        await apiClient.delete(`/admin/recipes/${recipe.id}`)
        this.recipes = this.recipes.filter((row) => row.id !== recipe.id)
        this.total = Math.max(0, this.total - 1)
        if (this.detailId === recipe.id) this.closeDetail()
        this.flash('菜谱已删除')
      } catch (error) {
        this.flash(error.response?.data?.error || '删除失败')
      }
    },
    async removeComment(comment) {
      if (!this.detail) return
      const preview = comment.body.length > 24 ? `${comment.body.slice(0, 24)}…` : comment.body
      const ok = await this.confirm(`删除这条评论？「${preview}」`, {
        title: '删除评论',
        type: 'warning',
        confirmText: '删除'
      })
      if (!ok) return
      try {
        const response = await apiClient.delete(`/admin/recipes/${this.detail.id}/comments/${comment.id}`)
        this.detail = response.data.recipe
        this.replace(response.data.recipe)
      } catch (error) {
        this.flash(error.response?.data?.error || '删除失败')
      }
    },
    startReward(recipe) {
      if (recipe.rewarded_at) return
      this.rewardRecipe = recipe
      this.rewardAmount = '5'
      this.rewardReason = `菜谱奖励：${recipe.title}`
      this.rewardError = ''
      this.sheet = 'reward'
    },
    async sendReward() {
      if (!this.rewardRecipe || this.saving) return
      this.saving = true
      this.rewardError = ''
      try {
        const response = await apiClient.post(`/admin/recipes/${this.rewardRecipe.id}/reward`, {
          amount: this.rewardAmount,
          reason: this.rewardReason
        })
        const next = response.data.recipe
        this.replace(next)
        if (this.detail && this.detail.id === next.id) {
          this.detail = { ...this.detail, ...next, comments: this.detail.comments }
        }
        this.closeSheet()
        this.flash('代金券已发放')
      } catch (error) {
        this.rewardError = error.response?.data?.error || '发放失败'
      } finally {
        this.saving = false
      }
    },
    openFilter() {
      const current = this.products.find((product) => String(product.id) === this.productId)
      this.sheetCategory = current?.category_id ? String(current.category_id) : (current && !current.category_id ? 'none' : '')
      this.productQuery = ''
      this.sheet = 'filter'
    },
    openDraftPicker(kind) {
      if (kind === 'product' && !this.draftCategoryId) return
      this.productQuery = ''
      this.sheet = kind
    },
    closeSheet() {
      this.sheet = ''
      this.productQuery = ''
      this.rewardRecipe = null
      this.rewardError = ''
    },
    isPicked(id) {
      if (this.sheet === 'category') return String(id) === String(this.draftCategoryId)
      if (this.sheet === 'product') return String(id) === String(this.draftProductId)
      return String(id) === this.productId
    },
    choose(id) {
      if (this.sheet === 'filter') {
        this.selectProduct(id)
        return
      }
      if (this.sheet === 'category') {
        if (String(id) !== String(this.draftCategoryId)) {
          this.draftCategoryId = String(id)
          this.draftProductId = ''
        }
        this.closeSheet()
        return
      }
      this.draftProductId = String(id)
      this.closeSheet()
    },
    openCreate() {
      this.creating = true
      this.draftTitle = ''
      this.draftBody = ''
      this.draftSides = ''
      this.draftDifficulty = ''
      this.draftCookTime = ''
      this.draftImages = []
      this.draftCover = ''
      this.draftCategoryId = ''
      this.draftProductId = this.productId || ''
      if (this.draftProductId) {
        const product = this.products.find((row) => String(row.id) === this.draftProductId)
        this.draftCategoryId = product ? (product.category_id ? String(product.category_id) : 'none') : ''
      }
    },
    async closeComposer() {
      const dirty = this.draftTitle || this.draftBody || this.draftSides || this.draftImages.length
      if (dirty) {
        const ok = await this.confirm('放弃正在编辑的菜谱？', {
          title: '取消发布',
          confirmText: '放弃',
          type: 'warning'
        })
        if (!ok) return
      }
      this.creating = false
    },
    removeImage(image) {
      this.draftImages = this.draftImages.filter((row) => row !== image)
      if (this.draftCover === image) this.draftCover = this.draftImages[0] || ''
    },
    async onFiles(event) {
      const files = Array.from(event.target.files || [])
      event.target.value = ''
      this.uploading = true
      try {
        for (const file of files) {
          if (this.draftImages.length >= 6) {
            this.flash('最多 6 张照片')
            break
          }
          const form = new FormData()
          form.append('image', file)
          const response = await apiClient.post('/recipes/images', form, {
            timeout: 60000,
            headers: { 'Content-Type': 'multipart/form-data' }
          })
          this.draftImages.push(response.data.url)
          if (!this.draftCover) this.draftCover = response.data.url
        }
      } catch (error) {
        this.flash(error.response?.data?.error || '照片上传失败')
      } finally {
        this.uploading = false
      }
    },
    async createOfficial() {
      if (!this.canPublish) return
      this.saving = true
      try {
        await apiClient.post('/admin/recipes', {
          title: this.draftTitle,
          body: this.draftBody,
          sides: this.draftSides,
          difficulty: this.draftDifficulty,
          cook_time: this.draftCookTime,
          images: this.draftImages,
          cover_image: this.draftCover || this.draftImages[0],
          product_ids: [Number(this.draftProductId)]
        })
        const product = this.draftProductId
        this.creating = false
        this.flash('菜谱已发布')
        await this.loadCatalog()
        const query = { ...this.$route.query, product: String(product) }
        delete query.sort
        const same = String(this.$route.query.product || '') === String(product) && !this.$route.query.sort
        if (same) await this.reload()
        else this.$router.replace({ query })
      } catch (error) {
        this.flash(error.response?.data?.error || '发布失败')
      } finally {
        this.saving = false
      }
    },
    flash(text) {
      this.message = text
      clearTimeout(this.messageTimer)
      this.messageTimer = setTimeout(() => {
        if (this.message === text) this.message = ''
      }, 2600)
    }
  }
}
</script>

<style scoped>
.recipes-admin {
  padding-bottom: 1.5rem;
}
.feed-filters {
  position: sticky;
  top: 0;
  z-index: 4;
  background: #f6f7fa;
  padding: 0.7rem 0.85rem 0.55rem;
  box-shadow: 0 6px 10px rgba(0, 0, 0, 0.04);
}
.toolbar, .header-actions, .sort-row, .product-bar, .manage, .detail-bar, .segments {
  display: flex;
  align-items: center;
}
.toolbar { justify-content: space-between; gap: 0.5rem; }
.header-actions, .sort-row, .segments { gap: 0.4rem; }
.header-actions { margin-left: auto; }
.sort-row button, .icon-btn, .post-btn, .product-filter, .product-clear {
  border: none;
  border-radius: 999px;
  background: #fff;
  color: var(--md-on-surface);
  min-height: 40px;
}
.sort-row button {
  padding: 0.4rem 0.85rem;
  font-size: 0.82rem;
}
.sort-row button.on, .post-btn, .share-btn.ready {
  background: var(--md-primary);
  color: white;
}
.icon-btn, .post-btn {
  min-width: 40px;
  height: 40px;
  padding: 0 0.7rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.15rem;
}
.icon-btn { color: var(--md-primary); }
.post-btn { color: white; }
.post-label { font-size: 0.82rem; font-weight: 500; }
.product-bar { gap: 0.45rem; margin-top: 0.55rem; }
.product-filter {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
  padding: 0.4rem 0.85rem;
  text-align: left;
  box-shadow: 0 1px 4px rgba(58, 42, 26, 0.06);
}
.product-filter svg { width: 18px; height: 18px; flex: none; color: #8a8178; }
.product-filter-copy { min-width: 0; display: flex; flex-direction: column; }
.product-filter-kicker { font-size: 0.68rem; color: #8a8178; line-height: 1.1; }
.product-filter strong {
  font-size: 0.92rem;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.product-clear {
  width: 40px;
  min-width: 40px;
  padding: 0;
  font-size: 1.3rem;
  line-height: 1;
  color: #8a8178;
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
.feed {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 0.75rem;
  margin: 0.7rem;
  align-items: start;
}
.post, .card {
  background: white;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(58, 42, 26, 0.08);
  min-width: 0;
}
.photo-wrap {
  position: relative;
  container-type: inline-size;
  --recipe-photo-h: 62cqi;
  margin: 8px 8px 0;
  border-radius: 10px;
  overflow: hidden;
  background: #FFF6EA;
  cursor: pointer;
}
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
  pointer-events: none;
}
.uploader {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  max-width: 58%;
  min-width: 0;
  padding: 0.5rem 1.1rem 0.35rem 0.55rem;
  background: radial-gradient(ellipse at top left, rgba(0, 0, 0, 0.42) 0%, rgba(0, 0, 0, 0.14) 46%, rgba(0, 0, 0, 0) 72%);
  color: white;
  font-size: 0.78rem;
  font-weight: 500;
  line-height: 1;
}
.uploader span:nth-child(2) {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.official {
  flex: none;
  border-radius: 999px;
  padding: 0.12rem 0.4rem;
  background: rgba(255, 255, 255, 0.22);
  font-size: 0.68rem;
}
.product-badge, .product-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.3rem;
  max-width: 52%;
  min-width: 0;
  padding: 0.5rem 0.55rem 0;
  pointer-events: auto;
}
.avatar {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: linear-gradient(135deg, #F9D561 0%, #F59B34 100%);
  color: white;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.68rem;
  font-weight: 500;
  flex: none;
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
.chip {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  border: none;
  border-radius: 999px;
  padding: 0.18rem 0.55rem;
  background: #FFF3E0;
  color: #D27529;
  font-size: 0.72rem;
  font-weight: 400;
  min-height: 0;
  min-width: 0;
}
button.chip { pointer-events: auto; cursor: pointer; }
.chip.rewarded { background: #E8F5E9; color: #2E7D32; }
.actions {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  min-height: 36px;
  padding: 0.15rem 0.55rem 0;
  color: #C47A3A;
}
.actions button, .stat {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  min-width: 0;
  min-height: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: inherit;
  font-size: 0.82rem;
  font-weight: 500;
  padding: 0 0.2rem;
}
.actions .material-symbols-outlined { font-size: 20px; }
.post h2, .title {
  margin: 0.15rem 0.75rem 0.35rem;
  font-family: "Noto Sans SC", "PingFang SC", sans-serif;
  font-size: 1.02rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  line-height: 1.35;
  cursor: pointer;
}
.manage {
  gap: 0.5rem;
  padding: 0.15rem 0.7rem 0.75rem;
}
.manage button, .detail-bar button, .reward-form .post-btn {
  flex: 1;
  min-height: 44px;
  border: none;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  font-size: 0.88rem;
  font-weight: 500;
}
.manage .material-symbols-outlined, .detail-bar .material-symbols-outlined { font-size: 18px; }
.reward { background: #FFF3E0; color: #D27529; }
.danger { background: #FDECEC; color: #C62828; }
button:disabled { opacity: 0.55; }
.grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 2px;
  margin-top: 0.75rem;
}
.grid-cell {
  position: relative;
  border: none;
  padding: 0;
  background: #f3f1ee;
  aspect-ratio: 1;
  overflow: hidden;
  min-width: 0;
  min-height: 0;
}
.grid-cell img { width: 100%; height: 100%; object-fit: contain; background: #f3f1ee; }
.grid-badge {
  position: absolute;
  left: 6px;
  bottom: 6px;
  border-radius: 999px;
  padding: 0.12rem 0.4rem;
  background: rgba(46, 125, 50, 0.92);
  color: white;
  font-size: 0.68rem;
}
.state, .empty, .inline-error, .muted, .picker-empty {
  text-align: center;
  color: var(--md-on-surface-variant);
}
.state, .empty { padding: 2rem 1.25rem; }
.empty { display: flex; flex-direction: column; align-items: center; }
.empty-photo {
  width: min(72%, 168px);
  margin-bottom: 0.85rem;
  border-radius: 14px;
  overflow: hidden;
}
.empty-photo svg, .film img, .photo img { display: block; width: 100%; height: auto; }
.empty p, .state p { margin: 0 0 1rem; }
.retry { margin-top: 0.2rem; padding: 0 1rem; }
.skel, .skel-line {
  background: linear-gradient(90deg, #f3f1ee 25%, #faf8f6 50%, #f3f1ee 75%);
  background-size: 200% 100%;
  animation: shimmer 1.2s ease-in-out infinite;
}
.photo-wrap.skel { height: 62cqi; margin: 0.7rem 0.7rem 0; }
.skel-line { height: 14px; margin: 0.7rem 0.9rem 0; border-radius: 999px; }
.skel-line.short { width: 42%; margin-bottom: 0.9rem; }
.pager { display: flex; justify-content: center; min-height: 28px; padding: 0.6rem 0 0.2rem; }
.spinner {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 2px solid #f3f1ee;
  border-top-color: var(--md-primary);
  animation: spin 0.7s linear infinite;
  display: inline-block;
}
.inline-error { padding: 0.4rem 1rem 0.8rem; }
.overlay {
  position: fixed;
  inset: 0;
  z-index: 140;
  background: #f6f7fa;
  display: flex;
  flex-direction: column;
}
.page-header {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr) 64px;
  align-items: center;
  gap: 0.25rem;
  background: linear-gradient(135deg, #F9D561 0%, #F59B34 100%);
  padding: 0.7rem 0.7rem 0.85rem;
  padding-top: calc(0.7rem + var(--app-safe-top, env(safe-area-inset-top, 0px)));
  box-shadow: var(--md-elevation-2);
}
.page-header h1 {
  margin: 0;
  color: white;
  font-family: "Noto Sans SC", "PingFang SC", sans-serif;
  font-size: 1.05rem;
  font-weight: 600;
  text-align: center;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.back-button, .share-btn {
  width: 40px;
  height: 40px;
  min-width: 40px;
  min-height: 40px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}
.back-button svg { width: 22px; height: 22px; }
.share-btn {
  width: auto;
  min-width: 64px;
  border-radius: 999px;
  padding: 0 0.8rem;
  font-weight: 600;
  opacity: 0.55;
}
.share-btn.ready { opacity: 1; }
.header-spacer { width: 44px; }
.overlay-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
}
.card { margin: 0.7rem; padding-bottom: 0.85rem; }
.hero { --recipe-photo-h: min(62vw, 460px); }
.detail-top { padding-top: 0; }
.detail-top .uploader { max-width: 62%; }
.title { cursor: default; }
.block, .comments { margin: 0.7rem 0.75rem 0; }
.block h3, .comments h3 {
  margin: 0 0 0.25rem;
  font-size: 0.78rem;
  font-weight: 500;
  color: #D27529;
}
.block p { margin: 0; white-space: pre-wrap; line-height: 1.55; font-size: 0.95rem; }
.comments { padding-bottom: 0.4rem; }
.line {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  align-items: baseline;
  margin: 0.55rem 0;
  line-height: 1.45;
}
.line b { font-weight: 600; }
.line span { flex: 1; min-width: 8rem; }
.reply { padding-left: 1rem; }
.text {
  border: none;
  background: transparent;
  color: var(--md-primary);
  min-height: 32px;
  min-width: 0;
  padding: 0;
  font-weight: 500;
}
.danger-text { color: #C62828; }
.muted { margin: 0.35rem 0 0.6rem; }
.detail-bar {
  gap: 0.6rem;
  padding: 0.7rem 0.9rem calc(0.7rem + env(safe-area-inset-bottom));
  background: white;
  box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.06);
}
.stage { padding: 0.85rem 0.85rem 0.2rem; }
.stage-empty label, .add-tile {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  min-height: 140px;
  border-radius: 16px;
  background: white;
  color: #D27529;
  border: 1px dashed #F3C48A;
}
.stage-empty input, .add-tile input { display: none; }
.stage-empty span { color: #8a8178; font-size: 0.8rem; }
.film {
  display: flex;
  gap: 0.5rem;
  overflow-x: auto;
  padding-bottom: 0.35rem;
}
.photo, .add-tile {
  position: relative;
  flex: none;
  width: 112px;
  height: 112px;
  min-width: 112px;
  min-height: 112px;
  padding: 0;
  border-radius: 14px;
  overflow: hidden;
  border: 2px solid transparent;
  background: #FFF6EA;
}
.photo.cover { border-color: #F59B34; }
.photo img { width: 100%; height: 100%; object-fit: cover; }
.cover-pill, .remove-photo {
  position: absolute;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.62);
  color: white;
  font-size: 0.72rem;
}
.cover-pill { left: 6px; bottom: 6px; padding: 0.1rem 0.4rem; }
.remove-photo {
  top: 4px;
  right: 4px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.sheet-form { display: flex; flex-direction: column; gap: 0.15rem; padding: 0.4rem 0.85rem 1.4rem; }
.field, .choice { display: flex; flex-direction: column; gap: 0.35rem; padding: 0.7rem 0; }
.field span, .choice span { font-size: 0.78rem; color: #D27529; font-weight: 500; }
.field input, .field textarea, .reward-form input {
  width: 100%;
  border: none;
  border-radius: 12px;
  background: white;
  padding: 0.75rem 0.85rem;
  font: inherit;
  font-size: 1rem;
}
.field textarea { resize: vertical; }
.picker-row {
  width: 100%;
  min-height: 52px;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  border: none;
  background: transparent;
  padding: 0.35rem 0;
  text-align: left;
  font: inherit;
}
.picker-row span { color: #8a8178; }
.picker-row strong { margin-left: auto; font-weight: 600; }
.picker-row strong.empty { color: #b0a79e; font-weight: 500; }
.picker-row svg { width: 18px; height: 18px; color: #b0a79e; flex: none; }
.segments { flex-wrap: wrap; }
.segments button {
  border: none;
  border-radius: 999px;
  background: white;
  min-height: 40px;
  padding: 0.4rem 0.75rem;
  font: inherit;
  font-size: 0.82rem;
}
.segments button.on { background: var(--md-primary); color: white; }
.sheet-mask {
  position: fixed;
  inset: 0;
  z-index: 160;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}
.picker-sheet {
  width: min(640px, 100%);
  max-height: min(78dvh, 720px);
  background: white;
  border-radius: 20px 20px 0 0;
  display: flex;
  flex-direction: column;
  padding-bottom: env(safe-area-inset-bottom);
}
.picker-sheet header, .reward-note, .reward-form, .picker-search, .sheet-cats {
  padding-left: 1rem;
  padding-right: 1rem;
}
.picker-sheet header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 0.9rem;
  padding-bottom: 0.35rem;
}
.picker-sheet h3 { margin: 0; font-size: 1rem; font-weight: 600; }
.picker-sheet header button, .picker-search button {
  width: 36px;
  height: 36px;
  min-width: 36px;
  min-height: 36px;
  border: none;
  border-radius: 50%;
  background: #f3f1ee;
  font-size: 1.2rem;
}
.sheet-cats {
  display: flex;
  gap: 0.4rem;
  overflow-x: auto;
  padding-bottom: 0.45rem;
  scrollbar-width: none;
}
.sheet-cats::-webkit-scrollbar { display: none; }
.sheet-cats button {
  flex: none;
  border: none;
  border-radius: 999px;
  background: #f3f1ee;
  min-height: 36px;
  padding: 0.35rem 0.75rem;
  font: inherit;
  font-size: 0.82rem;
}
.sheet-cats button.on, .picker-list button.on { background: #FFF3E0; color: #D27529; }
.picker-search {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0.15rem 1rem 0.45rem;
  padding: 0 0.35rem 0 0.75rem;
  border-radius: 999px;
  background: #f6f4f1;
  min-height: 44px;
}
.picker-search svg { width: 18px; height: 18px; color: #8a8178; flex: none; }
.picker-search input {
  flex: 1;
  min-width: 0;
  border: none;
  background: transparent;
  font: inherit;
  font-size: 1rem;
  padding: 0.65rem 0;
  outline: none;
}
.picker-list {
  list-style: none;
  margin: 0;
  padding: 0 0.4rem 0.8rem;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}
.picker-list button {
  width: 100%;
  min-height: 52px;
  display: flex;
  align-items: center;
  gap: 0.7rem;
  border: none;
  background: transparent;
  border-radius: 12px;
  padding: 0.4rem 0.7rem;
  text-align: left;
  font: inherit;
  font-size: 0.98rem;
}
.picker-list img {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  object-fit: cover;
  background: #f3f1ee;
  flex: none;
}
.picker-list span { flex: 1; min-width: 0; }
.picker-list em { font-style: normal; color: #8a8178; font-size: 0.82rem; }
.picker-empty { padding: 1.2rem 1rem 1.6rem; }
.reward-note { margin: 0.2rem 0 0.6rem; color: #6b625b; font-size: 0.84rem; }
.reward-form { display: flex; flex-direction: column; gap: 0.65rem; padding-bottom: 1rem; }
.reward-form label { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.78rem; color: #D27529; }
.form-error { margin: 0; color: #C62828; font-size: 0.85rem; }
.toast {
  position: fixed;
  left: 50%;
  bottom: calc(1.1rem + env(safe-area-inset-bottom));
  transform: translateX(-50%);
  z-index: 180;
  max-width: min(92vw, 420px);
  margin: 0;
  padding: 0.7rem 1rem;
  border-radius: 999px;
  background: rgba(28, 27, 31, 0.92);
  color: white;
  font-size: 0.88rem;
  text-align: center;
}
.toast.raised { bottom: calc(5.6rem + env(safe-area-inset-bottom)); }
@keyframes shimmer {
  from { background-position: 100% 0; }
  to { background-position: -100% 0; }
}
@keyframes spin { to { transform: rotate(360deg); } }

@media (min-width: 768px) {
  .feed {
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 340px), 1fr));
  }
  .product-filter { flex: 0 1 420px; }
}
@media (min-width: 1100px) {
  .grid { grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); }
}
@media (max-width: 767px) {
  .toolbar .post-label { display: none; }
  .toolbar .post-btn { width: 40px; padding: 0; }
  .photo-wrap { --recipe-photo-h: 62vw; }
  .photo-wrap.skel { height: 62vw; }
}
</style>
