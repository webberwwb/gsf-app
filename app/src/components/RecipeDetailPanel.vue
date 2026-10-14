<template>
  <div class="detail-page" :class="{ embedded }">
    <header v-if="!embedded" class="page-header">
      <button type="button" class="back-button" aria-label="返回" @click="back">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <div class="header-center">
        <h1>{{ recipe?.title }}</h1>
      </div>
      <div class="header-spacer"></div>
    </header>

    <div v-if="loading" class="state" aria-hidden="true"><span class="spinner"></span></div>
    <div v-else-if="!recipe" class="state">
      <p>这份菜谱不可用</p>
    </div>
    <article v-else class="card">
      <RecipePhotoCarousel class="hero" :images="photos" :alt="recipe.title" @click="onPhotoTap">
        <div class="photo-top">
          <div class="uploader">
            <span class="avatar">{{ recipe.author.initial }}</span>
            <span>{{ recipe.author.name }}</span>
          </div>
          <div v-if="recipe.products.length" class="product-side">
            <div v-for="product in recipe.products" :key="product.id" class="product-badge">
              <span class="chip">{{ product.name }}</span>
              <button type="button" @click.stop="openProduct(product)">
                {{ product.open_deal_id ? '去下单' : '查看商品' }}
              </button>
            </div>
          </div>
        </div>
        <div v-if="recipe.difficulty_label || recipe.cook_time_label" class="photo-facts">
          <span v-if="recipe.difficulty_label" class="chip">{{ recipe.difficulty_label }}</span>
          <span v-if="recipe.cook_time_label" class="chip">{{ recipe.cook_time_label }}</span>
        </div>
        <span v-if="burst" class="burst" aria-hidden="true">
          <span class="material-symbols-outlined fill">favorite</span>
        </span>
      </RecipePhotoCarousel>
      <div class="actions">
        <button type="button" aria-label="评论" @click="sheet = true">
          <span class="material-symbols-outlined" aria-hidden="true">chat_bubble</span>
          <span class="count">{{ recipe.comment_count }}</span>
        </button>
        <button type="button" :class="{ on: recipe.hearted }" :aria-label="recipe.hearted ? '取消喜欢' : '喜欢'" @click="heart()">
          <span class="material-symbols-outlined" :class="{ fill: recipe.hearted }" aria-hidden="true">favorite</span>
          <span class="count">{{ recipe.heart_count }}</span>
        </button>
        <button type="button" class="collect" :class="{ on: recipe.collected }" :aria-label="recipe.collected ? '取消收藏' : '收藏'" @click="collect">
          <span class="material-symbols-outlined" :class="{ fill: recipe.collected }" aria-hidden="true">bookmark</span>
          <span class="count">{{ recipe.collect_count }}</span>
        </button>
        <button type="button" class="share" aria-label="分享" @click="share">
          <span class="material-symbols-outlined" aria-hidden="true">ios_share</span>
        </button>
      </div>
      <h2 class="title">{{ recipe.title }}</h2>
      <section v-if="recipe.sides" class="block">
        <h3>其他配菜</h3>
        <p>{{ recipe.sides }}</p>
      </section>
      <section class="block">
        <h3>做法</h3>
        <p>{{ recipe.body }}</p>
      </section>
      <div v-if="recipe.is_owner" class="owner-actions">
        <button type="button" @click="edit">编辑</button>
        <button type="button" @click="remove">删除</button>
      </div>
    </article>

    <div v-if="sheet && recipe" class="sheet-mask" @click.self="closeSheet">
      <section class="sheet">
        <header>
          <strong>评论</strong>
          <button type="button" class="text" @click="closeSheet">关闭</button>
        </header>
        <div class="thread">
          <p v-if="!recipe.comments.length" class="muted">还没有评论</p>
          <article v-for="comment in recipe.comments" :key="comment.id">
            <div class="line">
              <b>{{ comment.author_name }}</b>
              <span>{{ comment.body }}</span>
              <button v-if="recipe.is_owner" type="button" class="text" @click="removeComment(comment)">删除</button>
              <button type="button" class="text" @click="replyTo = comment">回复</button>
            </div>
            <div v-for="reply in comment.replies" :key="reply.id" class="reply line">
              <b>{{ reply.author_name }}</b>
              <span>{{ reply.body }}</span>
              <button v-if="recipe.is_owner" type="button" class="text" @click="removeComment(reply)">删除</button>
            </div>
          </article>
        </div>
        <form class="composer" @submit.prevent="sendComment">
          <p v-if="replyTo" class="replying">回复 {{ replyTo.author_name }}
            <button type="button" class="text" @click="replyTo = null">取消</button>
          </p>
          <input v-model="draft" type="text" maxlength="500" placeholder="写评论" />
          <button type="submit" class="post-btn" :disabled="sending">发送</button>
        </form>
      </section>
    </div>
    <p v-if="notice" class="notice">{{ notice }}</p>
  </div>
</template>

<script>
import apiClient from '../api/client'
import { useAuthStore } from '../stores/auth'
import { shareRecipe } from '../utils/recipeShare'
import RecipePhotoCarousel from './RecipePhotoCarousel.vue'

export default {
  name: 'RecipeDetailPanel',
  components: { RecipePhotoCarousel },
  props: {
    recipeId: { type: [Number, String], required: true },
    embedded: { type: Boolean, default: false }
  },
  emits: ['back', 'deleted', 'loaded'],
  setup() {
    return { authStore: useAuthStore() }
  },
  data() {
    return {
      recipe: null,
      loading: true,
      sheet: false,
      draft: '',
      replyTo: null,
      sending: false,
      notice: '',
      burst: false,
      lastTap: 0
    }
  },
  mounted() {
    this.load()
  },
  computed: {
    photos() {
      const images = (this.recipe?.images || []).filter(Boolean)
      if (images.length) return images
      return this.recipe?.cover_image ? [this.recipe.cover_image] : []
    }
  },
  watch: {
    recipeId() {
      this.sheet = false
      this.draft = ''
      this.replyTo = null
      this.load()
    }
  },
  methods: {
    back() {
      if (this.embedded) {
        this.$emit('back')
        return
      }
      if (window.history.length > 1) this.$router.back()
      else this.$router.push('/recipes')
    },
    async load() {
      this.loading = true
      this.recipe = null
      if (!this.recipeId) {
        this.loading = false
        this.$emit('loaded', null)
        return
      }
      try {
        const response = await apiClient.get(`/recipes/${this.recipeId}`)
        this.recipe = response.data.recipe
      } catch (error) {
        this.recipe = null
      } finally {
        this.loading = false
        this.$emit('loaded', this.recipe)
      }
    },
    requireLogin() {
      if (this.authStore.isAuthenticated) return true
      this.$router.push('/login')
      return false
    },
    onPhotoTap() {
      const now = Date.now()
      if (now - this.lastTap < 280) {
        this.heart(true)
        this.lastTap = 0
        return
      }
      this.lastTap = now
    },
    async heart(fromDouble = false) {
      if (!this.requireLogin() || !this.recipe) return
      if (fromDouble === true && this.recipe.hearted) {
        this.flash()
        return
      }
      const method = this.recipe.hearted && fromDouble !== true ? 'delete' : 'post'
      try {
        const response = await apiClient[method](`/recipes/${this.recipe.id}/heart`)
        this.recipe = { ...this.recipe, ...response.data.recipe, comments: this.recipe.comments }
        if (method === 'post') this.flash()
      } catch (error) {
        this.notice = error.response?.data?.error || '操作失败'
      }
    },
    flash() {
      this.burst = true
      setTimeout(() => { this.burst = false }, 500)
    },
    async collect() {
      if (!this.requireLogin()) return
      const method = this.recipe.collected ? 'delete' : 'post'
      const response = await apiClient[method](`/recipes/${this.recipe.id}/collect`)
      this.recipe = { ...this.recipe, ...response.data.recipe, comments: this.recipe.comments }
    },
    async share() {
      try {
        const result = await shareRecipe(this.recipe)
        if (result === 'copied') this.notice = '链接已复制'
      } catch (error) {
        if (error?.name !== 'AbortError') this.notice = '分享失败'
      }
    },
    buy(product) {
      this.$router.push({ path: `/group-deals/${product.open_deal_id}`, query: { highlight: String(product.id) } })
    },
    openProduct(product) {
      if (product.open_deal_id) {
        this.buy(product)
        return
      }
      this.$router.push({ path: '/products', query: { product: String(product.id) } })
    },
    edit() {
      this.$router.push(`/recipes/${this.recipe.id}/edit`)
    },
    async remove() {
      if (!window.confirm('删除这份菜谱？')) return
      await apiClient.delete(`/recipes/${this.recipe.id}`)
      if (this.embedded) {
        this.$emit('deleted')
        return
      }
      this.$router.replace('/recipes')
    },
    closeSheet() {
      this.sheet = false
      this.replyTo = null
    },
    async sendComment() {
      if (!this.requireLogin()) return
      const body = this.draft.trim()
      if (!body) return
      this.sending = true
      try {
        const payload = { body }
        if (this.replyTo) payload.parent_id = this.replyTo.id
        const response = await apiClient.post(`/recipes/${this.recipe.id}/comments`, payload)
        this.recipe = response.data.recipe
        this.draft = ''
        this.replyTo = null
      } catch (error) {
        this.notice = error.response?.data?.error || '发送失败'
      } finally {
        this.sending = false
      }
    },
    async removeComment(comment) {
      const response = await apiClient.delete(`/recipes/${this.recipe.id}/comments/${comment.id}`)
      this.recipe = response.data.recipe
    }
  }
}
</script>

<style scoped>
.detail-page {
  min-height: 100vh;
  background: var(--md-background);
  padding-bottom: calc(88px + env(safe-area-inset-bottom));
}
.detail-page.embedded {
  min-height: 0;
  padding-bottom: calc(16px + env(safe-area-inset-bottom));
}
.page-header {
  background: linear-gradient(135deg, #F9D561 0%, #F59B34 100%);
  padding: var(--md-spacing-lg);
  padding-top: calc(var(--md-spacing-lg) + var(--app-safe-top, env(safe-area-inset-top, 0px)));
  box-shadow: var(--md-elevation-2);
  position: sticky;
  top: 0;
  z-index: 200;
  display: grid;
  grid-template-columns: 40px 1fr 40px;
  align-items: center;
}
.back-button {
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
.back-button svg { width: 22px; height: 22px; }
.header-center { display: flex; justify-content: center; }
.page-header h1 {
  margin: 0;
  max-width: 100%;
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
.card {
  margin: 0.7rem;
  background: var(--md-surface);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(58, 42, 26, 0.08);
  padding-bottom: 0.75rem;
}
.material-symbols-outlined {
  font-family: 'Material Symbols Outlined';
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
.hero {
  --recipe-photo-h: 62vw;
  background: #FFF6EA;
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
  padding: 0.55rem 0.6rem 1.5rem;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.5) 0%, rgba(0, 0, 0, 0.16) 68%, rgba(0, 0, 0, 0) 100%);
}
.uploader {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  max-width: 48%;
  min-width: 0;
  color: white;
  font-size: 0.78rem;
  font-weight: 500;
  line-height: 1;
  pointer-events: none;
}
.uploader span:last-child {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.product-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.35rem;
  max-width: 52%;
  min-width: 0;
}
.product-badge {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.4rem;
  max-width: 100%;
  min-width: 0;
}
.product-badge .chip {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.product-badge button {
  flex: none;
  border: none;
  background: var(--md-primary);
  color: white;
  border-radius: 999px;
  padding: 0.28rem 0.65rem;
  font-size: 0.75rem;
  font-weight: 500;
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
.burst {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  pointer-events: none;
  animation: pop 0.45s ease;
}
.burst .material-symbols-outlined {
  font-size: 92px;
  color: white;
  font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 48;
  filter: drop-shadow(0 8px 24px rgba(0,0,0,0.25));
}
@keyframes pop { from { transform: scale(0.6); opacity: 0; } to { transform: scale(1); opacity: 1; } }
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
.share { margin-left: auto; }
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
.title {
  margin: 0.45rem 0.75rem 0.15rem;
  font-family: "Noto Sans SC", "PingFang SC", sans-serif;
  font-size: 1.02rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  line-height: 1.35;
  color: var(--md-on-surface);
}
.chip {
  border-radius: 999px;
  padding: 0.18rem 0.55rem;
  background: #FFF3E0;
  color: #D27529;
  font-size: 0.72rem;
  font-weight: 400;
}
.block { margin: 0.7rem 0.75rem 0; }
.block h3 { margin: 0 0 0.2rem; font-size: 0.78rem; font-weight: 500; color: #D27529; }
.block p { margin: 0; white-space: pre-wrap; line-height: 1.55; font-size: 0.92rem; }
.owner-actions { display: flex; justify-content: flex-end; gap: 0.8rem; padding: 0.45rem 0.75rem 0; }
.owner-actions button, .text {
  border: none;
  background: transparent;
  color: var(--md-primary);
  font-size: 0.84rem;
  font-weight: 500;
}
.state, .notice, .muted { text-align: center; color: var(--md-on-surface-variant); padding: 1.5rem 1rem; }
.spinner {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 2px solid #f3f1ee;
  border-top-color: var(--md-primary);
  animation: spin 0.7s linear infinite;
  display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }
.sheet-mask {
  position: fixed; inset: 0; background: rgba(0,0,0,0.35); z-index: 1200;
  display: flex; align-items: flex-end;
}
.sheet {
  width: 100%;
  max-height: 72vh;
  background: white;
  border-radius: 20px 20px 0 0;
  display: flex;
  flex-direction: column;
  padding-bottom: calc(72px + env(safe-area-inset-bottom));
}
.embedded .sheet {
  padding-bottom: calc(12px + env(safe-area-inset-bottom));
}
.sheet header { display: flex; justify-content: space-between; align-items: center; padding: 0.8rem 1rem 0.4rem; }
.sheet header strong { font-weight: 500; }
.thread { overflow: auto; padding: 0.2rem 1rem 0.6rem; }
.line { display: flex; flex-wrap: wrap; gap: 0.35rem; align-items: baseline; margin: 0.45rem 0; }
.line b { font-weight: 500; color: var(--md-on-surface); }
.reply { padding-left: 1.2rem; }
.composer { display: flex; flex-wrap: wrap; gap: 0.4rem; align-items: center; padding: 0.5rem 0.8rem; }
.replying { width: 100%; margin: 0; font-size: 0.78rem; color: var(--md-on-surface-variant); }
.composer input {
  flex: 1; min-width: 0; border: none; background: var(--md-surface-variant);
  border-radius: 999px; padding: 0.65rem 0.9rem; font-size: 1rem;
  outline: none;
}
.post-btn { border: none; background: var(--md-primary); color: white; border-radius: 999px; padding: 0.55rem 0.9rem; font-weight: 500; }
</style>
