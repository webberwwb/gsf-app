<template>
  <Teleport to="body">
  <div v-if="show" class="modal-overlay" @click="requestClose">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <div>
          <h2>新建订单</h2>
          <p class="modal-subtitle">为已有顾客代下单。团购已截单也可以创建。</p>
        </div>
        <button type="button" class="close-btn" @click="requestClose" aria-label="关闭">×</button>
      </div>

      <div class="modal-body">
        <p v-if="dealClosed" class="deal-note">
          当前团购为{{ dealStatusLabel }}。顾客端已不能下单，这里仍可按单处理。{{ createdStatusHint }}
        </p>
        <p v-else-if="groupDeal" class="deal-note">
          团购「{{ groupDeal.title }}」当前为{{ dealStatusLabel }}。
        </p>

        <div v-if="errorMessage" class="form-error">{{ errorMessage }}</div>

        <section class="form-section">
          <h3>顾客</h3>
          <div v-if="selectedUser" class="selected-user">
            <div>
              <strong>{{ userLabel(selectedUser) }}</strong>
              <span class="user-meta">{{ userMeta(selectedUser) }}</span>
            </div>
            <button type="button" class="text-btn" @click="clearUser">更换</button>
          </div>
          <template v-else>
            <div class="search-row">
              <input
                v-model="userQuery"
                type="text"
                class="text-input"
                placeholder="搜索姓名、微信、电话"
                @keyup.enter="searchUsers"
              />
              <button type="button" class="secondary-btn" :disabled="searchingUsers" @click="searchUsers">
                {{ searchingUsers ? '搜索中...' : '搜索' }}
              </button>
            </div>
            <p v-if="userSearchHint" class="hint">{{ userSearchHint }}</p>
            <ul v-if="userResults.length" class="result-list">
              <li v-for="user in userResults" :key="user.id">
                <button type="button" class="result-btn" @click="selectUser(user)">
                  <span>{{ userLabel(user) }}</span>
                  <span class="user-meta">{{ userMeta(user) }}</span>
                </button>
              </li>
            </ul>
          </template>
        </section>

        <section class="form-section">
          <div class="section-title-row">
            <h3>商品</h3>
            <button type="button" class="text-btn" @click="showProductPicker = !showProductPicker">
              {{ showProductPicker ? '收起商品' : '添加商品' }}
            </button>
          </div>
          <div v-if="showProductPicker" class="picker">
            <input v-model="productQuery" type="text" class="text-input" placeholder="筛选商品" />
            <p v-if="loadingProducts" class="hint">加载商品中...</p>
            <p v-else-if="filteredProducts.length === 0" class="hint">没有可添加的商品</p>
            <ul v-else class="result-list">
              <li v-for="product in filteredProducts" :key="product.id">
                <button type="button" class="result-btn" @click="addProduct(product)">
                  <span>{{ product.name }}</span>
                  <span class="user-meta">${{ formatProductListPrice(product) }}{{ stockLabel(product) }}</span>
                </button>
              </li>
            </ul>
          </div>
          <p v-if="lines.length === 0" class="hint">还没有商品</p>
          <div v-for="line in lines" :key="line.key" class="line-card">
            <div class="line-main">
              <div>
                <div class="line-name">{{ line.product.name }}</div>
                <ProductVariantPicker
                  v-if="activeVariants(line.product).length"
                  :variants="activeVariants(line.product)"
                  :product="line.product"
                  :model-value="line.variant_id"
                  @update:model-value="line.variant_id = $event"
                />
              </div>
              <div class="qty-controls">
                <button type="button" class="qty-btn" @click="changeQty(line, -1)">−</button>
                <span>{{ line.quantity }}</span>
                <button type="button" class="qty-btn" @click="changeQty(line, 1)">+</button>
                <button type="button" class="text-btn danger" @click="removeLine(line.key)">删除</button>
              </div>
            </div>
          </div>
        </section>

        <section class="form-section">
          <h3>配送与付款</h3>
          <div class="choice-row">
            <label><input v-model="deliveryMethod" type="radio" value="pickup" /> 自取</label>
            <label><input v-model="deliveryMethod" type="radio" value="delivery" /> 配送</label>
          </div>
          <div v-if="deliveryMethod === 'delivery'" class="field">
            <label class="field-label">配送地址</label>
            <p v-if="loadingAddresses" class="hint">加载地址中...</p>
            <p v-else-if="!selectedUser" class="hint">先选择顾客</p>
            <p v-else-if="addresses.length === 0" class="hint">该顾客没有配送地址。可先选自取，创建后再在订单里改地址。</p>
            <select v-else v-model="addressId" class="text-input">
              <option :value="null" disabled>选择地址</option>
              <option v-for="address in addresses" :key="address.id" :value="address.id">
                {{ formatAddress(address) }}
              </option>
            </select>
          </div>
          <div class="field">
            <label class="field-label">付款方式</label>
            <select v-model="paymentMethod" class="text-input">
              <option value="cash">现金</option>
              <option value="etransfer">电子转账</option>
              <option v-if="canPayByCard" value="card">信用卡</option>
            </select>
          </div>
          <div class="field">
            <label class="field-label">备注</label>
            <textarea v-model="notes" class="text-input" rows="2" placeholder="可选，例如补单原因"></textarea>
          </div>
        </section>
      </div>

      <div class="modal-footer">
        <button type="button" class="secondary-btn" :disabled="submitting" @click="requestClose">取消</button>
        <button type="button" class="primary-btn" :disabled="submitting" @click="submit">
          {{ submitting ? '创建中...' : '创建订单' }}
        </button>
      </div>
    </div>
  </div>
  </Teleport>
</template>

<script>
import apiClient from '../api/client'
import ProductVariantPicker from './ProductVariantPicker.vue'
import { formatProductListPrice } from '../utils/productPriceDisplay'

const STATUS_LABELS = {
  draft: '草稿',
  upcoming: '即将开始',
  active: '进行中',
  closed: '已截单',
  preparing: '正在配货',
  ready_for_pickup: '可以取货',
  completed: '已完成'
}

export default {
  name: 'AdminCreateOrderModal',
  components: { ProductVariantPicker },
  props: {
    show: { type: Boolean, default: false },
    groupDeal: { type: Object, default: null }
  },
  emits: ['close', 'created'],
  data() {
    return {
      userQuery: '',
      userResults: [],
      userSearchHint: '',
      searchingUsers: false,
      selectedUser: null,
      addresses: [],
      loadingAddresses: false,
      addressId: null,
      products: [],
      loadingProducts: false,
      productQuery: '',
      showProductPicker: false,
      lines: [],
      lineKey: 0,
      deliveryMethod: 'pickup',
      paymentMethod: 'cash',
      notes: '',
      submitting: false,
      errorMessage: ''
    }
  },
  computed: {
    dealStatusLabel() {
      return STATUS_LABELS[this.groupDeal?.status] || this.groupDeal?.status || ''
    },
    dealClosed() {
      const status = this.groupDeal?.status
      return status === 'closed' || status === 'preparing' || status === 'ready_for_pickup' || status === 'completed'
    },
    createdStatusHint() {
      const status = this.groupDeal?.status
      if (status === 'preparing') return '新订单会记为「正在配货」。'
      if (status === 'ready_for_pickup') return '新订单会记为「可以取货」。'
      return '新订单会记为「已确认订单」。'
    },
    filteredProducts() {
      const q = this.productQuery.trim().toLowerCase()
      if (!q) return this.products
      return this.products.filter((product) => (product.name || '').toLowerCase().includes(q))
    },
    canPayByCard() {
      return this.deliveryMethod === 'delivery' && Boolean(this.selectedUser?.has_card_on_file)
    }
  },
  watch: {
    show(open) {
      if (open) this.reset()
    },
    deliveryMethod(method) {
      if (method !== 'delivery') this.addressId = null
      if (this.paymentMethod === 'card' && !this.canPayByCard) this.paymentMethod = 'cash'
    },
    canPayByCard(ok) {
      if (!ok && this.paymentMethod === 'card') this.paymentMethod = 'cash'
    }
  },
  methods: {
    formatProductListPrice,
    requestClose() {
      if (this.submitting) return
      this.$emit('close')
    },
    reset() {
      this.userQuery = ''
      this.userResults = []
      this.userSearchHint = ''
      this.selectedUser = null
      this.addresses = []
      this.addressId = null
      this.productQuery = ''
      this.showProductPicker = false
      this.lines = []
      this.deliveryMethod = 'pickup'
      this.paymentMethod = 'cash'
      this.notes = ''
      this.errorMessage = ''
      this.loadProducts()
    },
    userLabel(user) {
      return user.nickname || user.wechat || user.phone || `用户${user.id}`
    },
    userMeta(user) {
      return [user.wechat, user.phone].filter(Boolean).join(' · ')
    },
    formatAddress(address) {
      return [
        address.recipient_name,
        address.address_line1,
        address.city,
        address.postal_code
      ].filter(Boolean).join(' ')
    },
    stockLabel(product) {
      if (product.deal_stock_remaining == null) return ''
      return ` · 剩余 ${product.deal_stock_remaining}`
    },
    activeVariants(product) {
      return (product.variants || []).filter((variant) => variant.is_active !== false)
    },
    async searchUsers() {
      const search = this.userQuery.trim()
      this.errorMessage = ''
      if (!search) {
        this.userSearchHint = '输入姓名、微信或电话后再搜索'
        this.userResults = []
        return
      }
      this.searchingUsers = true
      this.userSearchHint = ''
      try {
        const response = await apiClient.get('/admin/users', {
          params: { search, per_page: 8, status: 'active' }
        })
        this.userResults = response.data.users || []
        if (this.userResults.length === 0) this.userSearchHint = '没有找到顾客'
      } catch (error) {
        this.userSearchHint = error.response?.data?.error || '搜索顾客失败'
      } finally {
        this.searchingUsers = false
      }
    },
    async selectUser(user) {
      this.selectedUser = user
      this.userResults = []
      this.addresses = []
      this.addressId = null
      this.loadingAddresses = true
      try {
        const response = await apiClient.get(`/admin/users/${user.id}/addresses`)
        this.addresses = response.data.addresses || []
        const preferred = this.addresses.find((address) => address.is_default) || this.addresses[0]
        this.addressId = preferred ? preferred.id : null
      } catch (error) {
        this.errorMessage = error.response?.data?.error || '加载地址失败'
      } finally {
        this.loadingAddresses = false
      }
    },
    clearUser() {
      this.selectedUser = null
      this.addresses = []
      this.addressId = null
    },
    async loadProducts() {
      if (!this.groupDeal?.id) {
        this.products = []
        return
      }
      this.loadingProducts = true
      try {
        const response = await apiClient.get(`/admin/group-deals/${this.groupDeal.id}`)
        this.products = response.data.group_deal?.products || []
      } catch (error) {
        this.products = this.groupDeal.products || []
        this.errorMessage = error.response?.data?.error || '加载商品失败'
      } finally {
        this.loadingProducts = false
      }
    },
    addProduct(product) {
      const variants = this.activeVariants(product)
      const variantId = variants.length === 1 ? variants[0].id : null
      const existing = this.lines.find((line) => line.product.id === product.id && line.variant_id === variantId)
      if (existing && variants.length <= 1) {
        existing.quantity += 1
      } else {
        this.lines.push({
          key: ++this.lineKey,
          product,
          quantity: 1,
          variant_id: variantId
        })
      }
      this.showProductPicker = false
      this.productQuery = ''
    },
    changeQty(line, delta) {
      line.quantity = Math.max(1, line.quantity + delta)
    },
    removeLine(key) {
      this.lines = this.lines.filter((line) => line.key !== key)
    },
    async submit() {
      this.errorMessage = ''
      if (!this.groupDeal?.id) {
        this.errorMessage = '缺少团购'
        return
      }
      if (!this.selectedUser) {
        this.errorMessage = '请选择顾客'
        return
      }
      if (this.lines.length === 0) {
        this.errorMessage = '请添加至少一件商品'
        return
      }
      const missingVariant = this.lines.find((line) => this.activeVariants(line.product).length > 0 && !line.variant_id)
      if (missingVariant) {
        this.errorMessage = `请为「${missingVariant.product.name}」选择规格`
        return
      }
      if (this.deliveryMethod === 'delivery' && !this.addressId) {
        this.errorMessage = '配送订单需要选择地址'
        return
      }

      const payload = {
        user_id: this.selectedUser.id,
        group_deal_id: this.groupDeal.id,
        delivery_method: this.deliveryMethod,
        payment_method: this.paymentMethod,
        notes: this.notes.trim() || null,
        items: this.lines.map((line) => ({
          product_id: line.product.id,
          quantity: line.quantity,
          variant_id: line.variant_id,
          pricing_type: line.product.pricing_type || 'per_item'
        }))
      }
      if (this.deliveryMethod === 'delivery') {
        payload.address_id = this.addressId
      } else {
        payload.pickup_location = 'markham'
      }

      this.submitting = true
      try {
        const response = await apiClient.post('/admin/orders', payload)
        this.$emit('created', response.data.order)
      } catch (error) {
        this.errorMessage = error.response?.data?.error || error.response?.data?.message || '创建订单失败'
      } finally {
        this.submitting = false
      }
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  padding: 16px;
}

.modal-content {
  background: #fff;
  border-radius: 20px;
  width: min(720px, 100%);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header,
.modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 20px;
  flex-shrink: 0;
}

.modal-header {
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
}

.modal-subtitle,
.hint,
.user-meta {
  color: rgba(0, 0, 0, 0.6);
  font-size: 13px;
}

.modal-subtitle {
  margin: 4px 0 0;
}

.close-btn {
  border: none;
  background: transparent;
  font-size: 28px;
  line-height: 1;
  cursor: pointer;
}

.modal-body {
  overflow: auto;
  flex: 1;
  min-height: 0;
  padding: 16px 20px 8px;
}

.deal-note {
  margin: 0 0 12px;
  padding: 10px 12px;
  border-radius: 12px;
  background: #fff4e5;
  color: #8a4b08;
  font-size: 14px;
}

.form-error {
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  background: #fdecea;
  color: #b3261e;
  font-size: 14px;
}

.form-section {
  margin-bottom: 18px;
}

.form-section h3,
.line-name {
  margin: 0;
  font-size: 15px;
}

.section-title-row,
.line-main,
.search-row,
.choice-row,
.qty-controls,
.modal-footer {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title-row,
.line-main {
  justify-content: space-between;
}

.line-main {
  align-items: flex-start;
}

.search-row {
  margin-top: 8px;
}

.text-input,
.secondary-btn,
.primary-btn,
.text-btn,
.result-btn,
.qty-btn {
  font: inherit;
}

.text-input {
  width: 100%;
  border: 1px solid rgba(0, 0, 0, 0.16);
  border-radius: 12px;
  padding: 10px 12px;
  box-sizing: border-box;
}

.search-row .text-input {
  flex: 1;
}

.field {
  margin-top: 12px;
}

.field-label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
}

.choice-row {
  margin-top: 8px;
  gap: 16px;
}

.result-list {
  list-style: none;
  margin: 8px 0 0;
  padding: 0;
  max-height: 220px;
  overflow: auto;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
}

.result-btn {
  width: 100%;
  text-align: left;
  background: #fff;
  border: none;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  padding: 10px 12px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.result-btn:hover {
  background: #fff8f0;
}

.selected-user,
.line-card,
.picker {
  margin-top: 8px;
  padding: 10px 12px;
  border-radius: 12px;
  background: #fafafa;
}

.selected-user {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.user-meta {
  display: block;
}

.qty-controls {
  flex-shrink: 0;
}

.qty-btn,
.secondary-btn,
.primary-btn,
.text-btn {
  border-radius: 999px;
  cursor: pointer;
}

.qty-btn {
  width: 28px;
  height: 28px;
  border: 1px solid rgba(0, 0, 0, 0.16);
  background: #fff;
}

.secondary-btn,
.primary-btn {
  border: none;
  padding: 10px 16px;
  white-space: nowrap;
}

.secondary-btn {
  background: #f3f3f3;
}

.primary-btn {
  background: var(--md-primary, #ff8c00);
  color: #fff;
}

.text-btn {
  border: none;
  background: transparent;
  color: var(--md-primary, #ff8c00);
  padding: 0;
}

.text-btn.danger {
  color: #b3261e;
}

button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.modal-footer {
  justify-content: flex-end;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}
</style>
