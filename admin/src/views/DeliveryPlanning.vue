<template>
  <div class="delivery-planning-page">
    <div class="page-header-actions">
      <select v-model="selectedDealId" class="deal-select" @change="loadPlan">
        <option value="">选择团购</option>
        <option v-for="deal in deals" :key="deal.id" :value="String(deal.id)">
          {{ deal.title }}（{{ statusLabel(deal.status) }}）
        </option>
      </select>
      <button
        type="button"
        class="print-labels-btn"
        :disabled="!selectedDealId || printingLabels || !hasLoadedPlan"
        @click="printLabels"
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
        </svg>
        {{ printingLabels ? '准备打印...' : '打印配送标签' }}
      </button>
      <button
        type="button"
        class="print-labels-btn"
        :disabled="!canEdit || !plan.self.length || sortingRoute"
        @click="sortSelfByDistance"
      >
        {{ sortingRoute ? '排序中...' : '按距离排序' }}
      </button>
    </div>

    <div class="plan-stage">
    <PageLoading
      v-if="loading"
      :overlay="hasLoadedPlan"
      label="正在加载配送计划"
      hint="正在整理订单与地址"
    />
    <div v-if="error && !loading" class="error">{{ error }}</div>
    <div v-else-if="!selectedDealId && !loading" class="empty-state">
      <p>请选择一个团购查看配送订单</p>
    </div>
    <div v-else-if="hasLoadedPlan" class="plan-content" :class="{ dimmed: loading }">
      <div v-if="plan.deal && !plan.deal.fulfillable && !plan.deal.pii_locked" class="lock-banner lock-banner-warn">
        当前团购尚未进入配货阶段，仅可预览。
      </div>

      <div class="lane-tabs" role="tablist">
        <button
          type="button"
          class="lane-tab"
          :class="{ active: activeLane === 'unassigned' }"
          @click="activeLane = 'unassigned'"
        >
          未分配
          <span class="lane-count">{{ plan.unassigned.length }}</span>
        </button>
        <button
          type="button"
          class="lane-tab"
          :class="{ active: activeLane === 'self' }"
          @click="activeLane = 'self'"
        >
          我来送
          <span class="lane-count">{{ plan.self.length }}</span>
        </button>
        <button
          type="button"
          class="lane-tab"
          :class="{ active: activeLane === 'third_party' }"
          @click="activeLane = 'third_party'"
        >
          第三方
          <span class="lane-count">{{ plan.third_party.length }}</span>
        </button>
      </div>
      <div class="mobile-cash-banner" :class="{ due: activeLaneCash.count }">{{ activeLaneCash.text }}</div>

      <DeliveryPlanMap
        class="plan-map"
        :unassigned="plan.unassigned"
        :self="plan.self"
        :third-party="plan.third_party"
        :selected-order-id="selectedOrderId"
        :depot="shippingConfig?.depot"
        @select-order="onMapSelect"
      />

      <div class="lane-grid">
        <section class="lane" :class="{ 'is-active': activeLane === 'unassigned' }">
          <div class="lane-header">
            <h3>未分配</h3>
            <span class="lane-cash" :class="{ due: unassignedCash.count }">{{ unassignedCash.text }}</span>
            <span class="lane-count">{{ plan.unassigned.length }}</span>
          </div>
          <div v-if="!plan.unassigned.length" class="lane-empty">暂无</div>
          <article v-for="order in plan.unassigned" :key="order.id" class="order-card" :class="[payCardClass(order), { selected: selectedOrderId === order.id }]">
            <div class="order-top">
              <h4 class="customer-name">{{ displayName(order) }}</h4>
            </div>
            <AddressDetails class="address" :address="order.address" />
            <p v-if="displayContact(order)" class="contact">
              <a v-if="accountPhone(order)" class="tel-link" :href="`tel:${accountPhone(order)}`">账号 {{ accountPhone(order) }}</a>
              <span v-if="order.user?.wechat">微信 {{ order.user.wechat }}</span>
            </p>
            <DeliveryPayBar :order="order" />
            <p class="items">{{ itemSummary(order) }}</p>
            <div v-if="canEdit" class="card-actions">
              <button class="add-btn compact" @click="assign(order, 'self')">我来送</button>
              <button class="ghost-btn" @click="assignThirdParty(order)">第三方</button>
            </div>
          </article>
        </section>

        <section class="lane lane-self" :class="{ 'is-active': activeLane === 'self' }">
          <div class="lane-header">
            <h3>我来送</h3>
            <span class="lane-cash" :class="{ due: selfCash.count }">{{ selfCash.text }}</span>
            <span class="lane-count">{{ plan.self.length }}</span>
          </div>
          <div v-if="!plan.self.length" class="lane-empty">把要自己送的订单点到这里，再调整顺序</div>
          <article v-for="(order, index) in plan.self" :key="order.id" class="order-card" :class="[payCardClass(order), { selected: selectedOrderId === order.id }]">
            <div class="order-top">
              <span class="route-seq">{{ routeSeqLabel(order, index) }}</span>
              <h4 class="customer-name">{{ displayName(order) }}</h4>
              <span v-if="orderStatusChip(order)" class="status-chip" :class="order.status">{{ orderStatusChip(order) }}</span>
            </div>
            <AddressDetails class="address" :address="order.address" />
            <p v-if="displayContact(order)" class="contact">
              <a v-if="accountPhone(order)" class="tel-link" :href="`tel:${accountPhone(order)}`">账号 {{ accountPhone(order) }}</a>
              <span v-if="order.user?.wechat">微信 {{ order.user.wechat }}</span>
            </p>
            <DeliveryPayBar :order="order" />
            <p class="items">{{ itemSummary(order) }}</p>
            <div v-if="photoUrl(order)" class="photo-review">
              <button type="button" class="photo-preview" @click="viewingPhoto = photoUrl(order)">
                <img :src="photoUrl(order)" alt="送达照片" />
              </button>
              <p class="photo-status">
                <template v-if="uploadingId === order.id">正在保存照片…</template>
                <template v-else>送达照片 · 点击查看</template>
              </p>
              <button
                v-if="canTakePhoto"
                type="button"
                class="ghost-btn photo-delete-btn"
                :disabled="deletingId === order.id"
                @click="deletePhoto(order)"
              >
                {{ deletingId === order.id ? '删除中...' : '删除照片' }}
              </button>
            </div>
            <div class="card-actions">
              <template v-if="canEdit">
                <button class="ghost-btn" :disabled="index === 0" @click="move(index, -1)">上移</button>
                <button class="ghost-btn" :disabled="index === plan.self.length - 1" @click="move(index, 1)">下移</button>
                <button class="ghost-btn" @click="assign(order, 'unassigned')">取消</button>
              </template>
              <label v-if="canTakePhoto" class="photo-btn" :class="{ busy: uploadingId === order.id }">
                {{ photoUrl(order) ? '重拍' : '拍照' }}
                <input type="file" accept="image/*" capture="environment" :disabled="uploadingId === order.id" @change="onPhoto($event, order)" />
              </label>
              <button
                v-if="canMarkDelivered(order)"
                class="add-btn compact"
                :disabled="savingId === order.id"
                @click="markDelivered(order)"
              >
                {{ savingId === order.id && savingAction === 'delivered' ? '提交中...' : '确认送达' }}
              </button>
              <button
                v-if="canEdit"
                class="cash-btn"
                :class="{ placeholder: !canMarkCash(order) }"
                :disabled="!canMarkCash(order) || savingId === order.id"
                @click="markCashReceived(order)"
              >
                {{ cashButtonLabel(order) }}
              </button>
            </div>
          </article>
        </section>

        <section class="lane" :class="{ 'is-active': activeLane === 'third_party' }">
          <div class="lane-header">
            <h3>第三方</h3>
            <span class="lane-cash" :class="{ due: thirdPartyCash.count }">{{ thirdPartyCash.text }}</span>
            <span class="lane-count">{{ plan.third_party.length }}</span>
          </div>
          <div v-if="!plan.third_party.length" class="lane-empty">远单可交给第三方</div>
          <article v-for="order in plan.third_party" :key="order.id" class="order-card" :class="[payCardClass(order), { selected: selectedOrderId === order.id }]">
            <div class="order-top">
              <h4 class="customer-name">{{ displayName(order) }}</h4>
              <span v-if="orderStatusChip(order)" class="status-chip" :class="order.status">{{ orderStatusChip(order) }}</span>
            </div>
            <AddressDetails class="address" :address="order.address" />
            <p v-if="displayContact(order)" class="contact">
              <a v-if="accountPhone(order)" class="tel-link" :href="`tel:${accountPhone(order)}`">账号 {{ accountPhone(order) }}</a>
              <span v-if="order.user?.wechat">微信 {{ order.user.wechat }}</span>
            </p>
            <DeliveryPayBar :order="order" />
            <p v-if="order.third_party_note" class="note">承运: {{ order.third_party_note }}</p>
            <p class="items">{{ itemSummary(order) }}</p>
            <div v-if="photoUrl(order)" class="photo-review">
              <button type="button" class="photo-preview" @click="viewingPhoto = photoUrl(order)">
                <img :src="photoUrl(order)" alt="送达照片" />
              </button>
              <p class="photo-status">送达照片 · 点击查看</p>
              <button
                v-if="canTakePhoto"
                type="button"
                class="ghost-btn photo-delete-btn"
                :disabled="deletingId === order.id"
                @click="deletePhoto(order)"
              >
                {{ deletingId === order.id ? '删除中...' : '删除照片' }}
              </button>
            </div>
            <div class="card-actions">
              <button v-if="canEdit" class="ghost-btn" @click="assign(order, 'unassigned')">取消</button>
              <label v-if="canTakePhoto" class="photo-btn" :class="{ busy: uploadingId === order.id }">
                {{ photoUrl(order) ? '重拍' : '拍照' }}
                <input type="file" accept="image/*" capture="environment" :disabled="uploadingId === order.id" @change="onPhoto($event, order)" />
              </label>
              <button
                v-if="canMarkDelivered(order)"
                class="add-btn compact"
                :disabled="savingId === order.id"
                @click="markDelivered(order)"
              >
                {{ savingId === order.id && savingAction === 'delivered' ? '提交中...' : '确认送达' }}
              </button>
              <button
                v-if="canEdit"
                class="cash-btn"
                :class="{ placeholder: !canMarkCash(order) }"
                :disabled="!canMarkCash(order) || savingId === order.id"
                @click="markCashReceived(order)"
              >
                {{ cashButtonLabel(order) }}
              </button>
            </div>
          </article>
        </section>
      </div>
    </div>
    </div>

    <div v-if="thirdPartyModal.show" class="modal-overlay" @click="closeThirdPartyModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>交给第三方</h2>
          <button type="button" class="close-btn" @click="closeThirdPartyModal">×</button>
        </div>
        <div class="modal-body">
          <p class="modal-hint">{{ thirdPartyModal.orderNumber }} · {{ thirdPartyModal.customer }}</p>
          <label class="field-label">承运公司 / 备注（可选）</label>
          <input
            v-model="thirdPartyModal.note"
            type="text"
            class="form-input"
            placeholder="如 Uber、朋友帮忙"
          />
        </div>
        <div class="modal-footer">
          <button type="button" class="cancel-btn" @click="closeThirdPartyModal">取消</button>
          <button type="button" class="confirm-btn" @click="confirmThirdParty">确认分配</button>
        </div>
      </div>
    </div>
    <ImageLightbox :src="viewingPhoto" @close="viewingPhoto = ''" />
  </div>
</template>

<script>
import apiClient from '../api/client'
import { cashDueSummary, deliveryPayKind, deliveryPayText, shouldCollectCash } from '../utils/deliveryPay'
import { isOrderPhysicallyDelivered, OrderStatus } from '@shared/status-enums.js'
import { nearestNeighborOrders, routeSeqLabel, sortSelfDeliveryOrders } from '../utils/deliveryRoute'
import { depotFromConfig, distanceKm, fetchShippingConfig } from '../utils/shipping'
import DeliveryPlanMap from '../components/DeliveryPlanMap.vue'
import { printSelfDeliveryLabels } from '../utils/printDeliveryLabels'
import { useModal } from '../composables/useModal'
import PageLoading from '../components/PageLoading.vue'
import ImageLightbox from '../components/ImageLightbox.vue'
import AddressDetails from '../components/AddressDetails.vue'
import DeliveryPayBar from '../components/DeliveryPayBar.vue'

export default {
  name: 'DeliveryPlanning',
  components: { PageLoading, ImageLightbox, AddressDetails, DeliveryPayBar, DeliveryPlanMap },
  setup() {
    const { confirm, success, error: showError } = useModal()
    return { confirm, success, showError }
  },
  data() {
    return {
      deals: [],
      selectedDealId: '',
      plan: { unassigned: [], self: [], third_party: [], deal: null },
      loading: false,
      error: null,
      savingId: null,
      savingAction: '',
      photoByOrder: {},
      viewingPhoto: '',
      uploadingId: null,
      deletingId: null,
      activeLane: 'unassigned',
      printingLabels: false,
      sortingRoute: false,
      selectedOrderId: null,
      shippingConfig: null,
      thirdPartyModal: {
        show: false,
        order: null,
        orderNumber: '',
        customer: '',
        note: ''
      }
    }
  },
  computed: {
    canEdit() {
      return this.plan.deal?.fulfillable && !this.plan.deal?.pii_locked
    },
    canTakePhoto() {
      return Boolean(this.plan.deal?.fulfillable)
    },
    hasLoadedPlan() {
      return Boolean(this.plan.deal)
    },
    unassignedCash() {
      return cashDueSummary(this.plan.unassigned)
    },
    selfCash() {
      return cashDueSummary(this.plan.self)
    },
    thirdPartyCash() {
      return cashDueSummary(this.plan.third_party)
    },
    activeLaneCash() {
      if (this.activeLane === 'self') return this.selfCash
      if (this.activeLane === 'third_party') return this.thirdPartyCash
      return this.unassignedCash
    }
  },
  async mounted() {
    this.shippingConfig = await fetchShippingConfig()
    this.loadDeals()
  },
  methods: {
    routeSeqLabel,
    onMapSelect(order, lane) {
      this.selectedOrderId = order.id
      if (lane) this.activeLane = lane
    },
    async sortSelfByDistance() {
      const depot = depotFromConfig(this.shippingConfig)
      const next = nearestNeighborOrders(this.plan.self, depot, distanceKm)
      this.plan.self = next
      this.sortingRoute = true
      try {
        const res = await apiClient.put(`/admin/fulfillment/deals/${this.selectedDealId}/route`, {
          order_ids: next.map((o) => o.id)
        })
        if (res.data?.self) {
          this.plan.self = sortSelfDeliveryOrders(res.data.self)
        }
      } catch (e) {
        await this.showError(e.response?.data?.error || '保存路线失败')
        await this.loadPlan()
      } finally {
        this.sortingRoute = false
      }
    },
    statusLabel(status) {
      const labels = {
        draft: '草稿',
        upcoming: '即将开始',
        active: '进行中',
        closed: '已截单',
        preparing: '正在配货',
        ready_for_pickup: '可以取货',
        completed: '已完成',
        submitted: '已提交',
        confirmed: '已确认',
        packing_complete: '配货完成',
        out_for_delivery: '正在配送',
        delivered: '已送达'
      }
      return labels[status] || status
    },
    displayName(order) {
      return order.user?.nickname || order.address?.recipient_name || '客户'
    },
    normalizePhone(phone) {
      const digits = String(phone || '').replace(/\D/g, '')
      if (digits.length === 11 && digits.startsWith('1')) return digits.slice(1)
      return digits
    },
    accountPhone(order) {
      const userPhone = order.user?.phone || ''
      const addressPhone = order.address?.phone || ''
      if (!userPhone) return ''
      const userDigits = this.normalizePhone(userPhone)
      const addressDigits = this.normalizePhone(addressPhone)
      if (userDigits && addressDigits && userDigits === addressDigits) return ''
      return userPhone
    },
    displayContact(order) {
      return this.accountPhone(order) || order.user?.wechat || ''
    },
    payCardClass(order) {
      return deliveryPayKind(order)
    },
    isDelivered(order) {
      return isOrderPhysicallyDelivered(order)
    },
    isCompleted(order) {
      return order.status === OrderStatus.COMPLETED
    },
    canMarkDelivered(order) {
      return this.canEdit && !this.isDelivered(order)
    },
    canMarkCash(order) {
      return this.canEdit && shouldCollectCash(order)
    },
    cashButtonLabel(order) {
      if (this.savingId === order.id && this.savingAction === 'cash') return '提交中...'
      return this.canMarkCash(order) ? '确认收款' : '无需收款'
    },
    orderStatusChip(order) {
      if (this.isCompleted(order)) return '已完成'
      if (order.status === OrderStatus.DELIVERED || order.delivered_at) return '已送达'
      return ''
    },
    photoUrl(order) {
      return this.photoByOrder[order.id] || order.delivery_photo_url || ''
    },
    rememberPhoto(orderId, url) {
      this.photoByOrder = { ...this.photoByOrder, [orderId]: url }
      for (const key of ['unassigned', 'self', 'third_party']) {
        const row = (this.plan[key] || []).find((item) => item.id === orderId)
        if (row) row.delivery_photo_url = url
      }
    },
    forgetPhoto(orderId) {
      const next = { ...this.photoByOrder }
      delete next[orderId]
      this.photoByOrder = next
      for (const key of ['unassigned', 'self', 'third_party']) {
        const row = (this.plan[key] || []).find((item) => item.id === orderId)
        if (row) row.delivery_photo_url = null
      }
      if (this.viewingPhoto) this.viewingPhoto = ''
    },
    itemSummary(order) {
      return (order.items || []).map((i) => {
        const bits = [i.name]
        if (i.variant_name) bits.push(i.variant_name)
        if (i.cutting) bits.push('切分')
        return `${bits.join(' / ')} x${i.quantity}`
      }).join('、')
    },
    async loadDeals() {
      this.loading = true
      this.error = null
      try {
        const res = await apiClient.get('/admin/group-deals', {
          params: { per_page: 50, include_products: 0 }
        })
        this.deals = res.data.group_deals || []
        const current = this.deals.find((d) => ['closed', 'preparing', 'ready_for_pickup'].includes(d.status))
        if (current) {
          this.selectedDealId = String(current.id)
          await this.loadPlan()
          return
        }
      } catch (e) {
        this.error = e.response?.data?.error || '加载团购失败'
      } finally {
        if (!this.selectedDealId || this.error) this.loading = false
      }
    },
    async loadPlan() {
      if (!this.selectedDealId) return
      this.loading = true
      this.error = null
      try {
        const res = await apiClient.get(`/admin/fulfillment/deals/${this.selectedDealId}/delivery-plan`)
        const next = {
          deal: res.data.deal,
          unassigned: res.data.unassigned || [],
          self: sortSelfDeliveryOrders(res.data.self || []),
          third_party: res.data.third_party || []
        }
        const photos = { ...this.photoByOrder }
        for (const order of [...next.unassigned, ...next.self, ...next.third_party]) {
          if (order.delivery_photo_url) photos[order.id] = order.delivery_photo_url
        }
        this.photoByOrder = photos
        this.plan = next
      } catch (e) {
        this.error = e.response?.data?.error || '加载配送计划失败'
      } finally {
        this.loading = false
      }
    },
    async assign(order, handler, note) {
      try {
        await apiClient.put(`/admin/fulfillment/orders/${order.id}/assignment`, {
          delivery_handler: handler,
          third_party_note: note || null
        })
        if (handler === 'self' || handler === 'third_party') {
          this.activeLane = handler
        }
        await this.loadPlan()
      } catch (e) {
        await this.showError(e.response?.data?.error || '分配失败')
      }
    },
    assignThirdParty(order) {
      this.thirdPartyModal = {
        show: true,
        order,
        orderNumber: order.order_number,
        customer: this.displayName(order),
        note: order.third_party_note || ''
      }
    },
    closeThirdPartyModal() {
      this.thirdPartyModal = {
        show: false,
        order: null,
        orderNumber: '',
        customer: '',
        note: ''
      }
    },
    async confirmThirdParty() {
      const order = this.thirdPartyModal.order
      const note = this.thirdPartyModal.note
      if (!order) return
      this.closeThirdPartyModal()
      await this.assign(order, 'third_party', note)
    },
    async move(index, delta) {
      const next = [...this.plan.self]
      const target = index + delta
      if (target < 0 || target >= next.length) return
      const [row] = next.splice(index, 1)
      next.splice(target, 0, row)
      this.plan.self = next
      try {
        const res = await apiClient.put(`/admin/fulfillment/deals/${this.selectedDealId}/route`, {
          order_ids: next.map((o) => o.id)
        })
        if (res.data?.self) {
          this.plan = {
            deal: res.data.deal || this.plan.deal,
            unassigned: res.data.unassigned || this.plan.unassigned,
            self: sortSelfDeliveryOrders(res.data.self),
            third_party: res.data.third_party || this.plan.third_party
          }
        }
      } catch (e) {
        await this.showError(e.response?.data?.error || '保存路线失败')
        await this.loadPlan()
      }
    },
    async onPhoto(event, order) {
      const file = event.target.files?.[0]
      event.target.value = ''
      if (!file) return
      const localUrl = URL.createObjectURL(file)
      this.rememberPhoto(order.id, localUrl)
      this.uploadingId = order.id
      const formData = new FormData()
      formData.append('image', file)
      formData.append('folder', 'deliveries')
      try {
        const res = await apiClient.post('/admin/upload-image', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        const url = res.data.url
        URL.revokeObjectURL(localUrl)
        this.rememberPhoto(order.id, url)
        try {
          await apiClient.put(`/admin/fulfillment/orders/${order.id}/photo`, { photo_url: url })
        } catch {
          await apiClient.put(`/admin/fulfillment/orders/${order.id}/photo`, { photo_url: url })
        }
      } catch (e) {
        if (this.photoByOrder[order.id] === localUrl) {
          URL.revokeObjectURL(localUrl)
          const next = { ...this.photoByOrder }
          delete next[order.id]
          this.photoByOrder = next
        }
        await this.showError(e.response?.data?.error || '照片上传失败，请重拍')
      } finally {
        if (this.uploadingId === order.id) this.uploadingId = null
      }
    },
    async deletePhoto(order) {
      const ok = await this.confirm('删除这张送达照片？', { type: 'warning' })
      if (!ok) return
      this.deletingId = order.id
      try {
        await apiClient.delete(`/admin/fulfillment/orders/${order.id}/photo`)
        this.forgetPhoto(order.id)
      } catch (e) {
        await this.showError(e.response?.data?.error || '删除照片失败')
      } finally {
        this.deletingId = null
      }
    },
    async markDelivered(order) {
      const raw = this.photoByOrder[order.id] || order.delivery_photo_url
      const photo = raw && !String(raw).startsWith('blob:') ? raw : (order.delivery_photo_url || null)
      const ok = await this.confirm('确认该订单已送达？', { type: 'warning' })
      if (!ok) return
      this.savingId = order.id
      this.savingAction = 'delivered'
      try {
        const res = await apiClient.post(`/admin/fulfillment/orders/${order.id}/mark-delivered`, {
          photo_url: photo || null
        })
        const next = res.data?.order || {}
        await this.success(next.status === OrderStatus.COMPLETED ? '已送达，订单已完成' : '已标记送达')
        await this.loadPlan()
      } catch (e) {
        await this.showError(e.response?.data?.error || '标记失败')
      } finally {
        this.savingId = null
        this.savingAction = ''
      }
    },
    async markCashReceived(order) {
      const ok = await this.confirm(`确认已收到现金 ${deliveryPayText(order).replace('收现金 ', '')}？`, { type: 'warning' })
      if (!ok) return
      this.savingId = order.id
      this.savingAction = 'cash'
      try {
        const res = await apiClient.post(`/admin/fulfillment/orders/${order.id}/mark-cash-received`)
        const next = res.data?.order || {}
        await this.success(next.status === OrderStatus.COMPLETED ? '已收款，订单已完成' : '已标记收款')
        await this.loadPlan()
      } catch (e) {
        await this.showError(e.response?.data?.error || '标记收款失败')
      } finally {
        this.savingId = null
        this.savingAction = ''
      }
    },
    async printLabels() {
      if (!this.plan.deal) return
      this.printingLabels = true
      try {
        const result = printSelfDeliveryLabels({
          deal: this.plan.deal,
          orders: this.plan.self
        })
        if (!result.ok) await this.showError(result.error)
      } finally {
        this.printingLabels = false
      }
    }
  }
}
</script>

<style scoped>
.delivery-planning-page {
  min-width: 0;
  max-width: 100%;
}
.page-header-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--md-spacing-md);
  margin-bottom: var(--md-spacing-md);
}
.deal-select {
  width: 100%;
  max-width: 420px;
  padding: var(--md-spacing-md);
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: var(--md-radius-md);
  font-size: 16px;
  background: #fff;
}
.print-labels-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--md-spacing-sm);
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  background: #E1F5FE;
  color: #0277BD;
  border: 1px solid rgba(2, 119, 189, 0.2);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  box-shadow: var(--md-elevation-2);
}
.print-labels-btn svg {
  width: 20px;
  height: 20px;
}
.print-labels-btn:hover:not(:disabled) {
  background: #B3E5FC;
}
.print-labels-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.plan-stage {
  position: relative;
  min-height: min(56vh, 440px);
}
.plan-content.dimmed {
  pointer-events: none;
  filter: saturate(0.7);
}
.error, .empty-state {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}
.lock-banner {
  background: #F3E5F5;
  color: #7B1FA2;
  padding: var(--md-spacing-md);
  border-radius: var(--md-radius-md);
  margin-bottom: var(--md-spacing-md);
}
.lock-banner-warn {
  background: #FFF3E0;
  color: #F57C00;
}
.lane-tabs {
  display: none;
}
.mobile-cash-banner {
  display: none;
}
.plan-map {
  margin-bottom: var(--md-spacing-lg);
}
.lane-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--md-spacing-lg);
}
@media (min-width: 960px) {
  .lane-grid {
    grid-template-columns: 1fr 1fr 1fr;
  }
}
.lane {
  background: #fff;
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-md);
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12);
  min-width: 0;
}
.lane-self {
  border: 1px solid rgba(255, 140, 0, 0.25);
}
.lane-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--md-spacing-sm);
  margin-bottom: var(--md-spacing-md);
}
.lane-cash {
  margin-left: auto;
  font-size: var(--md-label-size);
  font-weight: 600;
  color: #1b5e20;
  background: #e8f5e9;
  border: 1px solid #2e7d32;
  border-radius: var(--md-radius-xl);
  padding: 0.15rem 0.6rem;
  white-space: nowrap;
}
.lane-cash.due {
  color: #fff;
  background: #b71c1c;
  border-color: #b71c1c;
}
.lane-header h3 {
  margin: 0;
  font-size: var(--md-title-size);
}
.lane-count {
  background: rgba(0, 0, 0, 0.06);
  border-radius: var(--md-radius-xl);
  padding: 0.125rem 0.6rem;
  font-size: var(--md-label-size);
}
.lane-empty {
  color: var(--md-on-surface-variant);
  font-size: var(--md-label-size);
  padding: var(--md-spacing-md) 0;
}
.order-card {
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: var(--md-radius-md);
  padding: var(--md-spacing-md);
  margin-bottom: var(--md-spacing-md);
  min-width: 0;
}
.order-card:last-child {
  margin-bottom: 0;
}
.order-card.cash {
  border: 1.5px solid #b71c1c;
  background: #fff4f2;
}
.order-card.prepaid {
  border: 1px solid #2e7d32;
  background: #f3f8f3;
}
.order-card.selected {
  box-shadow: 0 0 0 2px var(--md-primary);
}
.order-top {
  display: flex;
  gap: var(--md-spacing-sm);
  align-items: center;
  flex-wrap: wrap;
}
.customer-name {
  margin: 0;
  flex: 1;
  min-width: 0;
  font-size: 1.05rem;
  font-weight: 600;
  line-height: 1.3;
  color: var(--md-on-surface);
  overflow-wrap: anywhere;
}
.route-seq {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--md-primary);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}
.status-chip {
  flex-shrink: 0;
  padding: 0.15rem 0.55rem;
  border-radius: var(--md-radius-xl);
  font-size: 12px;
  font-weight: 600;
  background: #FFF3E0;
  color: #E65100;
}
.status-chip.delivered {
  background: #E3F2FD;
  color: #1565C0;
}
.status-chip.completed {
  background: #E8F5E9;
  color: #2E7D32;
}
.cash-btn {
  background: #2e7d32;
  color: #fff;
  border: none;
  border-radius: var(--md-radius-sm);
  padding: 0.4rem 0.75rem;
  font-size: var(--md-label-size);
  font-weight: 600;
  cursor: pointer;
}
.cash-btn.placeholder,
.cash-btn:disabled.placeholder {
  background: #e0e0e0;
  color: #9e9e9e;
  cursor: not-allowed;
}
.address, .contact, .items, .note {
  margin: 0.35rem 0 0;
  color: var(--md-on-surface-variant);
  font-size: var(--md-label-size);
  line-height: 1.45;
  overflow-wrap: break-word;
  word-break: break-word;
}
.address {
  color: var(--md-on-surface);
}
.contact {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}
.tel-link {
  display: inline-flex;
  align-items: center;
  color: var(--md-primary);
  text-decoration: none;
  font-weight: 500;
}
.card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: var(--md-spacing-md);
}
.add-btn {
  background: var(--md-primary);
  color: #fff;
  border: none;
  border-radius: var(--md-radius-sm);
  padding: 0.4rem 0.75rem;
  font-weight: 500;
  cursor: pointer;
}
.add-btn.compact {
  font-size: var(--md-label-size);
}
.ghost-btn, .photo-btn {
  background: rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: var(--md-radius-sm);
  padding: 0.4rem 0.75rem;
  font-size: var(--md-label-size);
  cursor: pointer;
}
.photo-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.photo-btn input {
  display: none;
}
.photo-review {
  margin-top: 0.5rem;
}
.photo-preview {
  display: block;
  width: 100%;
  padding: 0;
  border: none;
  background: transparent;
  text-align: left;
  cursor: zoom-in;
}
.photo-preview img {
  width: 100%;
  max-height: 220px;
  object-fit: contain;
  background: #111;
  border-radius: var(--md-radius-sm);
}
.photo-status {
  margin: 0.4rem 0 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--md-primary);
}
.photo-btn.busy {
  opacity: 0.6;
  pointer-events: none;
}
.photo-delete-btn {
  margin-top: 0.45rem;
  min-height: 40px;
  color: #C62828;
  border-color: rgba(198, 40, 40, 0.28);
}
.status-badge {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  border-radius: var(--md-radius-xl);
  font-size: 12px;
  background: #F5F5F5;
  flex-shrink: 0;
}
.status-badge.out_for_delivery, .status-badge.preparing {
  background: #FFF3E0;
  color: #F57C00;
}
.status-badge.completed {
  background: #E8F5E9;
  color: #2E7D32;
}
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: var(--md-spacing-md);
  padding-bottom: calc(var(--md-spacing-md) + env(safe-area-inset-bottom));
}
.modal-content {
  background: #fff;
  border-radius: var(--md-radius-lg);
  max-width: 420px;
  width: 100%;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-lg);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}
.modal-header h2 {
  margin: 0;
  font-size: var(--md-title-size);
}
.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  line-height: 1;
  color: var(--md-on-surface-variant);
  cursor: pointer;
  min-width: 44px;
  min-height: 44px;
}
.modal-body {
  padding: var(--md-spacing-lg);
}
.modal-hint {
  margin: 0 0 var(--md-spacing-md);
  color: var(--md-on-surface-variant);
  font-size: var(--md-label-size);
  overflow-wrap: anywhere;
}
.field-label {
  display: block;
  margin-bottom: var(--md-spacing-sm);
  font-weight: 500;
}
.form-input {
  width: 100%;
  box-sizing: border-box;
  padding: var(--md-spacing-md);
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: var(--md-radius-md);
  font-size: 16px;
}
.form-input:focus {
  outline: none;
  border-color: var(--md-primary);
  box-shadow: 0 0 0 3px rgba(255, 140, 0, 0.15);
}
.modal-footer {
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  background: #fafafa;
  display: flex;
  justify-content: flex-end;
  gap: var(--md-spacing-sm);
}
.cancel-btn, .confirm-btn {
  border: none;
  border-radius: var(--md-radius-sm);
  padding: 0.55rem 1rem;
  font-weight: 500;
  cursor: pointer;
}
.cancel-btn {
  background: #fff;
  color: var(--md-on-surface);
  border: 1px solid rgba(0, 0, 0, 0.12);
}
.confirm-btn {
  background: var(--md-primary);
  color: #fff;
}

@media (max-width: 959px) {
  .lane-tabs {
    display: flex;
    position: sticky;
    top: 0;
    z-index: 5;
    gap: 0.4rem;
    margin: 0 0 var(--md-spacing-md);
    padding: 0.35rem 0 0.55rem;
    background: var(--md-background, #f5f5f5);
  }
  .lane-tab {
    flex: 1;
    min-height: 44px;
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: var(--md-radius-md);
    background: #fff;
    color: var(--md-on-surface-variant);
    font-size: 13px;
    font-weight: 500;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.3rem;
    cursor: pointer;
  }
  .lane-tab.active {
    background: var(--md-primary);
    border-color: var(--md-primary);
    color: #fff;
  }
  .lane-tab.active .lane-count {
    background: rgba(255, 255, 255, 0.22);
    color: #fff;
  }
  .lane-grid {
    display: block;
  }
  .lane {
    display: none;
  }
  .lane.is-active {
    display: block;
  }
  .lane-header {
    display: none;
  }
  .mobile-cash-banner {
    display: block;
    margin: 0 0 var(--md-spacing-md);
    text-align: center;
    font-size: 0.95rem;
    font-weight: 700;
    color: #1b5e20;
    background: #e8f5e9;
    border: 1px solid #2e7d32;
    border-radius: var(--md-radius-md);
    padding: 0.45rem 0.75rem;
  }
  .mobile-cash-banner.due {
    color: #fff;
    background: #b71c1c;
    border-color: #b71c1c;
  }
  .deal-select {
    max-width: none;
  }
  .print-labels-btn {
    width: 100%;
    min-height: 44px;
  }
  .card-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
  }
  .add-btn, .ghost-btn, .photo-btn, .cash-btn {
    min-height: 44px;
    width: 100%;
    justify-content: center;
    font-size: 14px;
    padding: 0.65rem 0.75rem;
  }
  .tel-link {
    display: inline-flex;
    min-height: 32px;
    padding: 0 0.35rem;
  }
  .modal-overlay {
    align-items: flex-end;
    padding: 0;
  }
  .modal-content {
    max-width: none;
    border-radius: var(--md-radius-lg) var(--md-radius-lg) 0 0;
  }
  .modal-footer {
    flex-direction: column-reverse;
  }
  .cancel-btn, .confirm-btn {
    width: 100%;
    min-height: 44px;
  }
}
</style>
