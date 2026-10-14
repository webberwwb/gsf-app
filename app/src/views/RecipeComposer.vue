<template>
  <div class="composer-page">
    <header class="topbar">
      <button type="button" class="icon-btn" aria-label="返回" @click="back">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1>{{ editing ? '编辑菜谱' : '新菜谱' }}</h1>
      <button type="button" class="share-btn" :class="{ ready: canShare }" :disabled="saving || uploading" @click="save">
        {{ saving ? '发布中' : (editing ? '保存' : '分享') }}
      </button>
    </header>

    <section class="stage">
      <div v-if="!images.length" class="stage-empty">
        <label>
          <input type="file" accept="image/*" multiple @change="onFiles" />
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <strong>{{ uploading ? '正在上传' : '上传配图' }}</strong>
          <span>从相册选，最多 6 张</span>
        </label>
      </div>
      <div v-else class="film">
        <button
          v-for="image in images"
          :key="image"
          type="button"
          class="photo"
          :class="{ cover: image === cover }"
          @click="cover = image"
        >
          <img :src="image" alt="" />
          <span v-if="image === cover" class="cover-pill">封面</span>
          <span class="remove" role="button" aria-label="移除这张照片" @click.stop="removeImage(image)">×</span>
        </button>
        <label v-if="images.length < 6" class="add-tile">
          <input type="file" accept="image/*" multiple @change="onFiles" />
          <strong>{{ uploading ? '…' : '+' }}</strong>
          <span>继续添加</span>
        </label>
      </div>
      <p v-if="images.length" class="caption">点一张，当作封面</p>
    </section>

    <section class="sheet">
      <label class="field field-first">
        <span>菜名</span>
        <input
          v-model="title"
          class="title"
          maxlength="80"
          placeholder="这道菜叫什么"
          enterkeyhint="next"
        />
      </label>
      <div class="product-block">
        <h2 class="section-title">主要食材</h2>
        <button type="button" class="picker-row" @click="openPicker('category')">
          <span>分类</span>
          <strong :class="{ empty: !categoryId }">{{ categoryLabel }}</strong>
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </button>
        <button type="button" class="picker-row" :disabled="!categoryId" @click="openPicker('product')">
          <span>商品</span>
          <strong :class="{ empty: !productId }">{{ productLabel }}</strong>
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
      <label class="field">
        <span>其他配菜</span>
        <textarea
          v-model="sides"
          maxlength="500"
          rows="3"
          placeholder="还需要什么"
        />
      </label>
      <div class="choice choice-ease">
        <span>难易程度</span>
        <div class="segments">
          <button
            v-for="item in difficulties"
            :key="item.id"
            type="button"
            :class="{ on: difficulty === item.id }"
            @click="difficulty = item.id"
          >{{ item.name }}</button>
        </div>
      </div>
      <div class="choice choice-time">
        <span>烹饪时长</span>
        <div class="segments">
          <button
            v-for="item in cookTimes"
            :key="item.id"
            type="button"
            :class="{ on: cookTime === item.id }"
            @click="cookTime = item.id"
          >{{ item.name }}</button>
        </div>
      </div>
      <label class="field">
        <span>做法</span>
        <textarea
          v-model="body"
          maxlength="4000"
          rows="5"
          placeholder="步骤和火候"
        />
      </label>
    </section>

    <div v-if="picker" class="picker-layer" @click.self="closePicker">
      <div class="picker-sheet" role="dialog" aria-modal="true" :style="sheetStyle" :aria-label="picker === 'category' ? '选择分类' : '选择商品'">
        <header>
          <h3>{{ picker === 'category' ? '选择分类' : '选择商品' }}</h3>
          <button type="button" aria-label="关闭" @click="closePicker">×</button>
        </header>
        <label v-if="picker === 'product'" class="picker-search">
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
        <p v-if="picker === 'product' && productQuery && !pickerOptions.length" class="picker-empty">没有找到「{{ productQuery.trim() }}」</p>
        <ul>
          <li v-for="option in pickerOptions" :key="option.id">
            <button type="button" :class="{ on: String(option.id) === pickerValue }" @click="choose(option.id)">
              <span>{{ option.name }}</span>
              <svg v-if="String(option.id) === pickerValue" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.4" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </button>
          </li>
        </ul>
      </div>
    </div>

    <p v-if="error" class="error" role="alert">{{ error }}</p>
  </div>
</template>

<script>
import apiClient from '../api/client'

export default {
  name: 'RecipeComposer',
  data() {
    return {
      title: '',
      body: '',
      sides: '',
      difficulty: '',
      cookTime: '',
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
      images: [],
      cover: '',
      products: [],
      categories: [],
      categoryId: '',
      productId: '',
      picker: '',
      productQuery: '',
      keyboardInset: 0,
      uploading: false,
      saving: false,
      error: '',
      editing: false
    }
  },
  computed: {
    categoryOptions() {
      const used = new Set(this.products.map((product) => product.category_id).filter(Boolean))
      const rows = this.categories.filter((category) => used.has(category.id))
      if (this.products.some((product) => !product.category_id)) {
        rows.push({ id: 'none', name: '其他' })
      }
      return rows
    },
    productsInCategory() {
      if (!this.categoryId) return []
      if (this.categoryId === 'none') return this.products.filter((product) => !product.category_id)
      return this.products.filter((product) => String(product.category_id) === this.categoryId)
    },
    categoryLabel() {
      const match = this.categoryOptions.find((category) => String(category.id) === this.categoryId)
      return match ? match.name : '选择分类'
    },
    productLabel() {
      if (!this.categoryId) return '先选分类'
      const match = this.productsInCategory.find((product) => String(product.id) === this.productId)
      return match ? match.name : '选择商品'
    },
    pickerOptions() {
      if (this.picker !== 'product') return this.categoryOptions
      const q = this.productQuery.trim()
      if (!q) return this.productsInCategory
      return this.productsInCategory.filter((product) => product.name.includes(q))
    },
    sheetStyle() {
      if (!this.keyboardInset) return null
      return {
        marginBottom: `${this.keyboardInset}px`,
        maxHeight: `calc(100dvh - ${this.keyboardInset}px - env(safe-area-inset-top, 0px) - 0.75rem)`
      }
    },
    pickerValue() {
      return this.picker === 'product' ? this.productId : this.categoryId
    },
    canShare() {
      return !this.saving && !this.uploading && this.images.length > 0 && this.title.trim() && this.body.trim() && this.difficulty && this.cookTime && !!this.productId
    }
  },
  async mounted() {
    this.onViewport = () => this.syncKeyboard()
    window.visualViewport?.addEventListener('resize', this.onViewport)
    window.visualViewport?.addEventListener('scroll', this.onViewport)
    await this.loadProducts()
    const preset = Number(this.$route.query.product)
    if (preset) this.applyProduct(preset)
    if (this.$route.name === 'RecipeEdit') {
      this.editing = true
      await this.loadRecipe()
    }
  },
  beforeUnmount() {
    window.visualViewport?.removeEventListener('resize', this.onViewport)
    window.visualViewport?.removeEventListener('scroll', this.onViewport)
  },
  methods: {
    syncKeyboard() {
      if (this.picker !== 'product') {
        this.keyboardInset = 0
        return
      }
      const viewport = window.visualViewport
      this.keyboardInset = viewport
        ? Math.max(0, Math.round(window.innerHeight - viewport.height - viewport.offsetTop))
        : 0
    },
    closePicker() {
      this.picker = ''
      this.productQuery = ''
      this.keyboardInset = 0
    },
    back() {
      if (window.history.length > 1) this.$router.back()
      else this.$router.push('/recipes')
    },
    async loadProducts() {
      const [products, categories] = await Promise.all([
        apiClient.get('/products'),
        apiClient.get('/product-categories')
      ])
      this.products = products.data.products || []
      this.categories = categories.data.categories || []
    },
    openPicker(which) {
      if (which === 'product' && !this.categoryId) return
      this.productQuery = ''
      this.picker = which
    },
    choose(id) {
      const value = String(id)
      if (this.picker === 'category') {
        if (value !== this.categoryId) this.productId = ''
        this.categoryId = value
      } else {
        this.productId = value
      }
      this.closePicker()
    },
    applyProduct(id) {
      const product = this.products.find((item) => item.id === Number(id))
      if (!product) return
      this.categoryId = product.category_id ? String(product.category_id) : 'none'
      this.productId = String(product.id)
    },
    async loadRecipe() {
      const response = await apiClient.get(`/recipes/${this.$route.params.id}`)
      const recipe = response.data.recipe
      if (!recipe.is_owner) {
        this.$router.replace(`/recipes/${recipe.id}`)
        return
      }
      this.title = recipe.title
      this.body = recipe.body
      this.sides = recipe.sides || ''
      this.difficulty = recipe.difficulty || ''
      this.cookTime = recipe.cook_time || ''
      this.images = recipe.images || []
      this.cover = recipe.cover_image
      const linked = (recipe.products || [])[0]
      if (linked) this.applyProduct(linked.id)
    },
    async onFiles(event) {
      const files = Array.from(event.target.files || [])
      event.target.value = ''
      for (const file of files) {
        if (this.images.length >= 6) {
          this.error = '最多 6 张照片'
          break
        }
        this.uploading = true
        this.error = ''
        try {
          const form = new FormData()
          form.append('image', file)
          const response = await apiClient.post('/recipes/images', form, {
            timeout: 60000,
            headers: { 'Content-Type': 'multipart/form-data' }
          })
          this.images.push(response.data.url)
          if (!this.cover) this.cover = response.data.url
        } catch (error) {
          this.error = error.response?.data?.error || '照片上传失败，请再试一次'
        } finally {
          this.uploading = false
        }
      }
    },
    removeImage(url) {
      this.images = this.images.filter((image) => image !== url)
      if (this.cover === url) this.cover = this.images[0] || ''
    },
    async save() {
      this.error = ''
      if (!this.images.length) {
        this.error = '先加一张成品照片'
        return
      }
      if (!this.title.trim()) {
        this.error = '给这道菜起个名字'
        return
      }
      if (!this.difficulty) {
        this.error = '选一个难易程度'
        return
      }
      if (!this.cookTime) {
        this.error = '选一个烹饪时长'
        return
      }
      if (!this.body.trim()) {
        this.error = '写下做法'
        return
      }
      if (!this.productId) {
        this.error = '选一个主要食材'
        return
      }
      this.saving = true
      const payload = {
        title: this.title,
        body: this.body,
        sides: this.sides,
        difficulty: this.difficulty,
        cook_time: this.cookTime,
        images: this.images,
        cover_image: this.cover || this.images[0],
        product_ids: [Number(this.productId)]
      }
      try {
        const response = this.editing
          ? await apiClient.put(`/recipes/${this.$route.params.id}`, payload)
          : await apiClient.post('/recipes', payload)
        this.$router.replace(`/recipes/${response.data.recipe.id}`)
      } catch (error) {
        this.error = error.response?.data?.error || '没发出去，请再试一次'
      } finally {
        this.saving = false
      }
    }
  }
}
</script>

<style scoped>
.composer-page {
  min-height: 100vh;
  background: var(--md-background);
  color: var(--md-on-surface);
  padding-bottom: calc(1.5rem + env(safe-area-inset-bottom));
  font-family: var(--md-font-family);
}
.topbar {
  position: sticky;
  top: 0;
  z-index: 2;
  display: grid;
  grid-template-columns: 44px 1fr auto;
  align-items: center;
  gap: 0.25rem;
  padding: calc(0.4rem + var(--app-safe-top, env(safe-area-inset-top, 0px))) 0.75rem 0.45rem;
  background: var(--md-surface);
  backdrop-filter: blur(12px);
}
.topbar h1 {
  margin: 0;
  text-align: center;
  font-size: 1.05rem;
  font-weight: 600;
  letter-spacing: 0.01em;
  color: var(--md-on-surface);
}
.icon-btn, .share-btn {
  border: none;
  background: transparent;
  color: var(--md-on-surface-variant);
  padding: 0;
}
.icon-btn {
  width: 44px;
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.icon-btn svg { width: 22px; height: 22px; }
.share-btn {
  min-width: 52px;
  height: 32px;
  padding: 0 0.85rem;
  border-radius: 999px;
  background: var(--md-primary);
  color: white;
  font-size: 0.88rem;
  font-weight: 500;
  opacity: 0.4;
}
.share-btn.ready { opacity: 1; }
.share-btn:disabled { opacity: 0.4; }
.stage { padding: 0.35rem 1rem 0; }
.stage-empty label, .add-tile {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.2rem;
  border-radius: 18px;
  background: #f3f1ee;
  color: var(--md-on-surface-variant);
}
.stage-empty label {
  height: 46vw;
  min-height: 180px;
}
.stage-empty svg { width: 36px; height: 36px; color: var(--md-primary); }
.stage-empty strong, .add-tile strong {
  color: var(--md-on-surface);
  font-size: 1rem;
  font-weight: 500;
}
.stage-empty span, .add-tile span, .caption, .quiet, .section-head span {
  font-size: 0.8rem;
  color: var(--md-on-surface-variant);
}
.stage-empty input, .add-tile input { display: none; }
.film {
  display: flex;
  gap: 0.55rem;
  overflow-x: auto;
  padding-bottom: 0.2rem;
}
.photo, .add-tile {
  position: relative;
  flex: 0 0 58vw;
  height: 58vw;
  border: 2px solid transparent;
  padding: 0;
  overflow: hidden;
}
.add-tile { flex-basis: 28vw; height: 58vw; }
.photo { background: #f3f1ee; border-radius: 18px; }
.photo.cover { border-color: var(--md-primary); }
.photo img { width: 100%; height: 100%; object-fit: contain; background: #f3f1ee; }
.cover-pill, .remove {
  position: absolute;
  border-radius: 999px;
  font-size: 0.72rem;
  line-height: 1;
}
.cover-pill {
  left: 0.55rem;
  bottom: 0.55rem;
  padding: 0.28rem 0.5rem;
  background: rgba(28, 27, 31, 0.72);
  color: white;
}
.remove {
  top: 0.45rem;
  right: 0.45rem;
  width: 26px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(28, 27, 31, 0.55);
  color: white;
  font-size: 1rem;
}
.caption { margin: 0.55rem 0.15rem 0; }
.sheet {
  margin: 0.85rem 1rem 0;
  padding: 0.95rem 1rem 0.45rem;
  background: var(--md-surface);
  border-radius: 22px;
}
.composer-page ::selection {
  background: rgba(245, 155, 52, 0.22);
  color: inherit;
}
.title, textarea, .search, button {
  outline: none;
  -webkit-tap-highlight-color: transparent;
}
.title:focus, textarea:focus, .search:focus,
.title:focus-visible, textarea:focus-visible, .search:focus-visible {
  outline: none;
  box-shadow: none;
}
.title, textarea, .search {
  width: 100%;
  border: none;
  background: transparent;
  font-family: inherit;
  color: var(--md-on-surface);
  font-size: 1rem;
  font-weight: 400;
  caret-color: var(--md-primary);
  appearance: none;
}
.title {
  font-family: "Noto Sans SC", "PingFang SC", sans-serif;
  font-size: 1.2rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: var(--md-on-surface);
  padding: 0.15rem 0 0.55rem;
}
.title::placeholder { color: var(--md-outline); }
textarea::placeholder, .search::placeholder { color: var(--md-outline); }
.choice {
  padding: 0.85rem 0 0.15rem;
  border-top: 1px solid #eeeeee;
}
.choice > span, .field > span {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.8rem;
  font-weight: 500;
  letter-spacing: 0.04em;
  color: var(--md-on-surface-variant);
}
.segments { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.4rem; }
.segments button {
  min-height: 44px;
  border: none;
  border-radius: 999px;
  background: var(--md-surface-variant);
  color: var(--md-on-surface-variant);
  font-size: 0.86rem;
  font-weight: 500;
  padding: 0.4rem 0.2rem;
}
.choice-ease .segments button.on { background: #FFF3E0; color: #D27529; }
.choice-time .segments button.on { background: #FFF3E0; color: #D27529; }
.field { display: block; padding-top: 0.85rem; border-top: 1px solid #eeeeee; margin-top: 0.8rem; }
.field-first { padding-top: 0; border-top: none; margin-top: 0; }
.product-block { margin-top: 0.35rem; padding-top: 0.85rem; border-top: 1px solid #eeeeee; }
.product-block .picker-row:first-of-type { border-top: none; }
.field textarea {
  resize: none;
  line-height: 1.55;
  min-height: 4.6rem;
  padding: 0 0 0.35rem;
}
.field:last-child textarea { min-height: 6.4rem; }
.section-title {
  margin: 0 0 0.15rem;
  font-size: 0.8rem;
  font-weight: 500;
  letter-spacing: 0.04em;
  color: var(--md-on-surface-variant);
}
.picker-row {
  width: 100%;
  min-height: 52px;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  border: none;
  border-top: 1px solid #eeeeee;
  background: transparent;
  padding: 0.7rem 0;
  text-align: left;
  color: var(--md-on-surface);
  font-weight: 400;
}
.picker-row span {
  flex: 0 0 2.5rem;
  font-size: 0.85rem;
  color: var(--md-on-surface-variant);
}
.picker-row strong {
  flex: 1;
  min-width: 0;
  font-size: 1rem;
  font-weight: 500;
  color: var(--md-on-surface);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.picker-row strong.empty { color: var(--md-outline); font-weight: 400; }
.picker-row svg { width: 18px; height: 18px; color: var(--md-outline); flex: none; }
.picker-row:disabled { opacity: 0.45; }
.picker-layer {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: flex;
  align-items: flex-end;
  background: rgba(0, 0, 0, 0.45);
}
.picker-sheet {
  width: 100%;
  max-height: 72vh;
  display: flex;
  flex-direction: column;
  background: var(--md-surface);
  border-radius: 22px 22px 0 0;
  padding-bottom: env(safe-area-inset-bottom);
}
.picker-sheet header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.85rem 1rem 0.7rem;
  border-bottom: 1px solid #eeeeee;
}
.picker-sheet h3 { margin: 0; font-size: 1.05rem; font-weight: 500; color: var(--md-on-surface); }
.picker-sheet header button {
  border: none;
  background: transparent;
  font-size: 1.6rem;
  line-height: 1;
  color: var(--md-on-surface-variant);
  padding: 0 0.15rem;
}
.picker-search {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  margin: 0.7rem 1rem 0.35rem;
  min-height: 44px;
  padding: 0 0.35rem 0 0.8rem;
  border-radius: 999px;
  background: var(--md-surface-variant);
}
.picker-search svg { width: 18px; height: 18px; color: var(--md-outline); flex: none; }
.picker-search input {
  flex: 1;
  min-width: 0;
  height: 44px;
  border: none;
  background: transparent;
  font-family: inherit;
  font-size: 16px;
  color: var(--md-on-surface);
  caret-color: var(--md-primary);
  outline: none;
  box-shadow: none;
  appearance: none;
}
.picker-search input::-webkit-search-cancel-button { display: none; }
.picker-search input::placeholder { color: var(--md-outline); }
.picker-search input:focus,
.picker-search input:focus-visible {
  outline: none;
  box-shadow: none;
}
.picker-search button {
  width: 44px;
  height: 44px;
  border: none;
  background: transparent;
  color: var(--md-on-surface-variant);
  font-size: 1.35rem;
  line-height: 1;
}
.picker-empty {
  margin: 1.4rem 1.1rem;
  color: var(--md-on-surface-variant);
  font-size: 0.95rem;
}
.picker-sheet ul {
  list-style: none;
  margin: 0;
  padding: 0.25rem 0 0.5rem;
  overflow: auto;
  -webkit-overflow-scrolling: touch;
}
.picker-sheet li button {
  width: 100%;
  min-height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  border: none;
  background: transparent;
  padding: 0.85rem 1.1rem;
  text-align: left;
  font-size: 1.02rem;
  color: var(--md-on-surface);
  font-weight: 400;
}
.picker-sheet li button.on { color: #D27529; font-weight: 500; background: #FFF3E0; }
.picker-sheet li button svg { width: 20px; height: 20px; flex: none; color: var(--md-primary); }
.error {
  margin: 0.85rem 1.15rem 0;
  color: #b42318;
  font-size: 0.88rem;
}
</style>
