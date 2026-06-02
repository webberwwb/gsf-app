<template>
  <div v-if="substituteProducts.length" class="fulfillment-section">
    <h3 class="section-title">备选切换</h3>
    <p class="section-hint">
      仅显示已配置备选的商品。切换备选后：接受备选 → 换备选价；不要备选 → 保留订单行、标红待处理（$0），由管理员找货或手动删除。
    </p>
    <div class="fulfillment-list">
      <div
        v-for="product in substituteProducts"
        :key="product.id"
        class="fulfillment-row"
        :class="statusClass(product.id)"
      >
        <div class="fulfillment-info">
          <div class="product-name">{{ product.name }}</div>
          <div class="product-meta">
            <span v-if="(product.variants || []).length" class="meta-tag">有产品细节</span>
            <span v-if="product.substitute_enabled || product.substitute?.enabled" class="meta-tag">
              备选: {{ product.substitute?.name || product.substitute_name || '已配置' }}
            </span>
          </div>
          <div v-if="statsFor(product.id).lineCount" class="fulfillment-stats">
            {{ statsFor(product.id).lineCount }} 条订单行 ·
            <template v-if="statsFor(product.id).unavailableCount">
              已切换 {{ statsFor(product.id).unavailableCount }} ·
              换备选 {{ statsFor(product.id).substituteCount }} ·
              待处理 {{ statsFor(product.id).pendingCount }}
            </template>
          </div>
        </div>
        <div class="fulfillment-actions">
          <button
            type="button"
            class="action-btn"
            :disabled="loadingProductId === product.id || !statsFor(product.id).lineCount"
            @click="setFulfillment(product, true)"
          >
            切换备选
          </button>
          <button
            type="button"
            class="action-btn action-btn--secondary"
            :disabled="loadingProductId === product.id || statsFor(product.id).unavailableCount === 0"
            @click="setFulfillment(product, false)"
          >
            恢复原商品
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'

export default {
  name: 'GroupDealFulfillmentPanel',
  props: {
    groupDealId: { type: [Number, String], required: true },
    products: { type: Array, default: () => [] },
    orders: { type: Array, default: () => [] }
  },
  emits: ['fulfillment-updated'],
  data() {
    return {
      loadingProductId: null
    }
  },
  computed: {
    substituteProducts() {
      return (this.products || []).filter((p) => this.hasSubstitute(p))
    }
  },
  methods: {
    hasSubstitute(product) {
      return !!(product?.substitute_enabled || product?.substitute?.enabled)
    },
    statsFor(productId) {
      const lines = []
      for (const order of this.orders || []) {
        if (order.status === 'cancelled') continue
        for (const item of order.items || []) {
          if (item.product_id === productId) lines.push(item)
        }
      }
      const unavailable = lines.filter((i) => i.is_unavailable)
      const substitute = unavailable.filter((i) => i.accept_substitute === true)
      const pending = unavailable.filter((i) => i.accept_substitute !== true)
      return {
        lineCount: lines.length,
        unavailableCount: unavailable.length,
        substituteCount: substitute.length,
        pendingCount: pending.length
      }
    },
    statusClass(productId) {
      const s = this.statsFor(productId)
      if (!s.lineCount) return 'status--empty'
      if (s.unavailableCount === 0) return 'status--available'
      if (s.unavailableCount >= s.lineCount) return 'status--unavailable'
      return 'status--partial'
    },
    async setFulfillment(product, isUnavailable) {
      const stats = this.statsFor(product.id)
      if (isUnavailable && !stats.lineCount) return
      if (!isUnavailable && stats.unavailableCount === 0) return

      const action = isUnavailable ? '切换备选' : '恢复原商品'
      const detail = isUnavailable
        ? `将影响该团购中此商品的全部 ${stats.lineCount} 条订单行。接受备选的用户将换备选商品计价，不要备选的将保留在订单中（$0、标红待处理），由您找货或手动删除。`
        : `将恢复 ${stats.unavailableCount} 条已切换备选的行并按原价重新计价。`
      if (!window.confirm(`${action}「${product.name}」？\n\n${detail}`)) return

      this.loadingProductId = product.id
      try {
        const res = await apiClient.patch(
          `/admin/group-deals/${this.groupDealId}/products/${product.id}/fulfillment`,
          { is_unavailable: isUnavailable }
        )
        this.$emit('fulfillment-updated', res.data)
        alert(res.data.message || '已更新')
      } catch (err) {
        alert(err.response?.data?.error || err.response?.data?.message || '更新失败')
      } finally {
        this.loadingProductId = null
      }
    }
  }
}
</script>

<style scoped>
.fulfillment-section {
  background: #fff;
  border-radius: 12px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.section-title {
  margin: 0 0 0.35rem;
  font-size: 1.125rem;
}

.section-hint {
  margin: 0 0 1rem;
  font-size: 0.8125rem;
  color: #666;
  line-height: 1.4;
}

.fulfillment-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.fulfillment-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.65rem 0.75rem;
  border-radius: 8px;
  border: 1px solid #eee;
  background: #fafafa;
}

.fulfillment-row.status--partial {
  border-color: #ffe0b2;
  background: #fff8e1;
}

.fulfillment-row.status--unavailable {
  border-color: #ffcdd2;
  background: #ffebee;
}

.product-name {
  font-weight: 500;
  font-size: 0.9375rem;
}

.product-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-top: 0.2rem;
}

.meta-tag {
  font-size: 0.6875rem;
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
  background: #eee;
  color: #555;
}

.fulfillment-stats {
  font-size: 0.75rem;
  color: #666;
  margin-top: 0.25rem;
}

.fulfillment-actions {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  flex-shrink: 0;
}

.action-btn {
  font-size: 0.75rem;
  padding: 0.35rem 0.6rem;
  border-radius: 6px;
  border: none;
  background: #c62828;
  color: #fff;
  cursor: pointer;
  white-space: nowrap;
}

.action-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.action-btn--secondary {
  background: #fff;
  color: #333;
  border: 1px solid #ccc;
}
</style>
