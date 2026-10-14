<template>
  <div class="recipes-admin">
    <div class="toolbar">
      <button type="button" class="primary" @click="openCreate">发布谷语农庄菜谱</button>
    </div>

    <p v-if="loading">加载中...</p>
    <p v-else-if="!recipes.length">还没有菜谱</p>
    <article v-for="recipe in recipes" :key="recipe.id" class="card">
      <img :src="recipe.cover_image" :alt="recipe.title" />
      <div>
        <h2>{{ recipe.title }}</h2>
        <p>{{ recipe.author.name }} · 喜欢 {{ recipe.heart_count }} · 收藏 {{ recipe.collect_count }} · 评论 {{ recipe.comment_count }}</p>
        <p class="products">{{ recipe.products.map(p => p.name).join('、') }}</p>
        <div class="row">
          <button type="button" @click="loadComments(recipe)">评论</button>
          <button type="button" @click="remove(recipe)">删除</button>
          <button type="button" :disabled="!!recipe.rewarded_at" @click="startReward(recipe)">
            {{ recipe.rewarded_at ? '已发代金券' : '奖励代金券' }}
          </button>
        </div>
        <ul v-if="openComments === recipe.id" class="comments">
          <li v-for="comment in comments" :key="comment.id">
            {{ comment.author_name }}：{{ comment.body }}
            <button type="button" @click="removeComment(recipe, comment)">删除</button>
            <div v-for="reply in comment.replies" :key="reply.id" class="reply">
              {{ reply.author_name }}：{{ reply.body }}
              <button type="button" @click="removeComment(recipe, reply)">删除</button>
            </div>
          </li>
          <li v-if="!comments.length">暂无评论</li>
        </ul>
        <form v-if="rewardId === recipe.id" class="reward" @submit.prevent="sendReward(recipe)">
          <input v-model="rewardAmount" type="number" min="0.01" step="0.01" placeholder="金额" />
          <input v-model="rewardReason" type="text" />
          <button type="submit" class="primary" :disabled="saving">发放</button>
        </form>
      </div>
    </article>
    <button v-if="recipes.length < total" type="button" @click="load(page + 1)">加载更多</button>
    <p v-if="message" class="message">{{ message }}</p>

    <form v-if="creating" class="composer" @submit.prevent="createOfficial">
      <h2>谷语农庄菜谱</h2>
      <label class="photo-add">添加照片
        <input type="file" accept="image/*" multiple @change="onFiles" />
      </label>
      <div class="photos">
        <button v-for="image in images" :key="image" type="button" :class="{ cover: image === cover }" @click="cover = image">
          <img :src="image" alt="" />
        </button>
      </div>
      <input v-model="title" placeholder="菜名" maxlength="80" />
      <select v-model="categoryId" @change="productId = ''">
        <option value="">主要食材 · 选择分类</option>
        <option v-for="category in categoryOptions" :key="category.id" :value="String(category.id)">{{ category.name }}</option>
      </select>
      <select v-model="productId" :disabled="!categoryId">
        <option value="">{{ categoryId ? '选择主要食材' : '先选分类' }}</option>
        <option v-for="product in productsInCategory" :key="product.id" :value="String(product.id)">{{ product.name }}</option>
      </select>
      <textarea v-model="sides" rows="3" maxlength="500" placeholder="其他配菜" />
      <div class="segments">
        <button v-for="item in difficulties" :key="item.id" type="button" :class="{ on: difficulty === item.id }" @click="difficulty = item.id">{{ item.name }}</button>
      </div>
      <div class="segments">
        <button v-for="item in cookTimes" :key="item.id" type="button" :class="{ on: cookTime === item.id }" @click="cookTime = item.id">{{ item.name }}</button>
      </div>
      <textarea v-model="body" rows="5" maxlength="4000" placeholder="做法" />
      <div class="row">
        <button type="submit" class="primary" :disabled="saving">发布</button>
        <button type="button" @click="creating = false">取消</button>
      </div>
    </form>
  </div>
</template>

<script>
import apiClient from '../api/client'

export default {
  name: 'AdminRecipes',
  data() {
    return {
      recipes: [],
      page: 1,
      total: 0,
      loading: true,
      message: '',
      creating: false,
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
      saving: false,
      rewardId: null,
      rewardAmount: '5',
      rewardReason: '',
      openComments: null,
      comments: []
    }
  },
  computed: {
    categoryOptions() {
      const used = new Set(this.products.map((product) => product.category_id).filter(Boolean))
      const rows = this.categories.filter((category) => used.has(category.id))
      if (this.products.some((product) => !product.category_id)) rows.push({ id: 'none', name: '其他' })
      return rows
    },
    productsInCategory() {
      if (!this.categoryId) return []
      if (this.categoryId === 'none') return this.products.filter((product) => !product.category_id)
      return this.products.filter((product) => String(product.category_id) === this.categoryId)
    }
  },
  mounted() {
    this.load(1)
    this.loadProducts()
  },
  methods: {
    async load(page) {
      this.loading = page === 1
      try {
        const response = await apiClient.get('/admin/recipes', { params: { page } })
        const rows = response.data.recipes || []
        this.recipes = page === 1 ? rows : this.recipes.concat(rows)
        this.total = response.data.total || 0
        this.page = page
      } catch (error) {
        this.message = error.response?.data?.error || '加载失败'
      } finally {
        this.loading = false
      }
    },
    async loadProducts() {
      const [products, categories] = await Promise.all([
        apiClient.get('/products'),
        apiClient.get('/product-categories')
      ])
      this.products = products.data.products || []
      this.categories = categories.data.categories || []
    },
    openCreate() {
      this.creating = true
      this.title = ''
      this.body = ''
      this.sides = ''
      this.difficulty = ''
      this.cookTime = ''
      this.images = []
      this.cover = ''
      this.categoryId = ''
      this.productId = ''
    },
    async onFiles(event) {
      const files = Array.from(event.target.files || [])
      event.target.value = ''
      for (const file of files) {
        if (this.images.length >= 6) break
        const form = new FormData()
        form.append('image', file)
        const response = await apiClient.post('/recipes/images', form, {
          timeout: 60000,
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        this.images.push(response.data.url)
        if (!this.cover) this.cover = response.data.url
      }
    },
    async createOfficial() {
      this.saving = true
      this.message = ''
      try {
        await apiClient.post('/admin/recipes', {
          title: this.title,
          body: this.body,
          sides: this.sides,
          difficulty: this.difficulty,
          cook_time: this.cookTime,
          images: this.images,
          cover_image: this.cover || this.images[0],
          product_ids: this.productId ? [Number(this.productId)] : []
        })
        this.creating = false
        await this.load(1)
      } catch (error) {
        this.message = error.response?.data?.error || '发布失败'
      } finally {
        this.saving = false
      }
    },
    async remove(recipe) {
      if (!window.confirm(`删除「${recipe.title}」？`)) return
      await apiClient.delete(`/admin/recipes/${recipe.id}`)
      this.recipes = this.recipes.filter((row) => row.id !== recipe.id)
      this.total = Math.max(0, this.total - 1)
    },
    async loadComments(recipe) {
      if (this.openComments === recipe.id) {
        this.openComments = null
        return
      }
      const response = await apiClient.get(`/recipes/${recipe.id}`)
      this.comments = response.data.recipe.comments || []
      this.openComments = recipe.id
    },
    async removeComment(recipe, comment) {
      await apiClient.delete(`/admin/recipes/${recipe.id}/comments/${comment.id}`)
      const response = await apiClient.get(`/recipes/${recipe.id}`)
      this.comments = response.data.recipe.comments || []
      const index = this.recipes.findIndex((row) => row.id === recipe.id)
      if (index >= 0) this.recipes[index].comment_count = response.data.recipe.comment_count
    },
    startReward(recipe) {
      this.rewardId = recipe.id
      this.rewardAmount = '5'
      this.rewardReason = `菜谱奖励：${recipe.title}`
    },
    async sendReward(recipe) {
      this.saving = true
      this.message = ''
      try {
        const response = await apiClient.post(`/admin/recipes/${recipe.id}/reward`, {
          amount: this.rewardAmount,
          reason: this.rewardReason
        })
        const index = this.recipes.findIndex((row) => row.id === recipe.id)
        if (index >= 0) this.recipes.splice(index, 1, response.data.recipe)
        this.rewardId = null
        this.message = '代金券已发放'
      } catch (error) {
        this.message = error.response?.data?.error || '发放失败'
      } finally {
        this.saving = false
      }
    }
  }
}
</script>

<style scoped>
.recipes-admin { display: flex; flex-direction: column; gap: 0.8rem; }
.toolbar, .row { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.card {
  display: flex; gap: 0.8rem; background: var(--md-surface, #fff);
  border-radius: 12px; padding: 0.7rem; align-items: flex-start;
}
.card img, .photos img { width: 96px; height: 96px; object-fit: contain; background: #f3f1ee; border-radius: 8px; }
.card h2 { margin: 0 0 0.25rem; font-size: 1rem; }
.card p { margin: 0.15rem 0; font-size: 0.85rem; color: #49454f; }
button { border: none; border-radius: 999px; padding: 0.4rem 0.75rem; background: #f3f1ee; }
.primary { background: #ff8c00; color: white; }
.composer, .reward { display: flex; flex-direction: column; gap: 0.5rem; }
.composer input, .composer textarea, .reward input {
  border: 1px solid #ddd; border-radius: 10px; padding: 0.6rem; font: inherit;
}
.photo-add input { display: none; }
.photos { display: flex; gap: 0.4rem; overflow-x: auto; }
.photos button { padding: 0; border: 2px solid transparent; background: transparent; }
.photos button.cover { border-color: #ff8c00; }
.segments { display: flex; gap: 0.4rem; }
.segments button.on { background: #ff8c00; color: white; }
.message { color: #9a3412; }
button:disabled { opacity: 0.55; }
</style>
