<template>
  <div class="b-page">
    <section v-if="isMerchantPage">
      <div class="page-header-actions">
        <input v-model="merchantQuery" type="text" class="search-input" placeholder="搜索商家名称 / 联系人 / 电话" />
        <button type="button" class="add-btn" @click="openMerchant()">
          <span class="btn-label">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
            </svg>
            添加商家
          </span>
        </button>
      </div>
      <div v-if="loadingMerchants" class="loading">加载中...</div>
      <div v-else-if="merchantError" class="error">{{ merchantError }}</div>
      <div v-else-if="filteredMerchants.length === 0" class="empty-state">暂无商家</div>
      <div v-else>
        <div class="card-list">
          <article v-for="merchant in filteredMerchants" :key="merchant.id" class="record-card" :class="{ inactive: !merchant.is_active }">
            <div class="card-title">{{ merchant.name }}</div>
            <div class="card-meta">
              <span>{{ merchant.show_prices ? '显示单价' : '不显示单价' }}</span>
              <span>账期 {{ merchant.payment_due_days }} 天</span>
              <span :class="['status-badge', merchant.is_active ? 'active' : 'inactive']">
                {{ merchant.is_active ? '启用' : '停用' }}
              </span>
            </div>
            <p v-if="merchant.contact_person || merchant.phone" class="card-sub">
              {{ [merchant.contact_person, merchant.phone].filter(Boolean).join(' · ') }}
            </p>
            <div class="action-buttons">
              <button type="button" class="edit-btn" @click="openMerchant(merchant)">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                编辑
              </button>
              <button type="button" class="delete-btn" @click="removeMerchant(merchant)">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                删除
              </button>
            </div>
          </article>
        </div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>名称</th>
                <th>联系人</th>
                <th>电话</th>
                <th>送货单价格</th>
                <th>账期</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="merchant in filteredMerchants" :key="merchant.id" :class="{ inactive: !merchant.is_active }">
                <td>{{ merchant.name }}</td>
                <td>{{ merchant.contact_person || '—' }}</td>
                <td>{{ merchant.phone || '—' }}</td>
                <td>{{ merchant.show_prices ? '显示单价' : '不显示单价' }}</td>
                <td>{{ merchant.payment_due_days }} 天</td>
                <td>
                  <span :class="['status-badge', merchant.is_active ? 'active' : 'inactive']">
                    {{ merchant.is_active ? '启用' : '停用' }}
                  </span>
                </td>
                <td>
                  <div class="action-buttons">
                    <button type="button" class="edit-btn" @click="openMerchant(merchant)">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                      编辑
                    </button>
                    <button type="button" class="delete-btn" @click="removeMerchant(merchant)">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                      删除
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <section v-else-if="!composerOpen">
      <div class="page-header-actions">
        <select v-model="filters.merchant_id" class="filter-select" @change="fetchDeliveries">
          <option value="">全部商家</option>
          <option v-for="merchant in merchants" :key="merchant.id" :value="String(merchant.id)">
            {{ merchant.name }}
          </option>
        </select>
        <select v-model="filters.payment_status" class="filter-select" @change="fetchDeliveries">
          <option value="">全部付款</option>
          <option value="unpaid">未付</option>
          <option value="paid">已付</option>
        </select>
        <button type="button" class="add-btn" @click="openDelivery()">
          <span class="btn-label">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
            </svg>
            供货记录
          </span>
        </button>
      </div>

      <div class="stats">
        <div class="stat"><span>送货单</span><strong>{{ aggregates.count }}</strong></div>
        <div class="stat"><span>合计</span><strong>{{ money(aggregates.grand_total) }}</strong></div>
        <div class="stat"><span>未付</span><strong>{{ money(aggregates.unpaid_total) }}</strong></div>
        <div class="stat"><span>已付</span><strong>{{ money(aggregates.paid_total) }}</strong></div>
      </div>

      <div v-if="loadingDeliveries" class="loading">加载中...</div>
      <div v-else-if="deliveryError" class="error">{{ deliveryError }}</div>
      <div v-else-if="deliveries.length === 0" class="empty-state">没有符合条件的送货单</div>
      <div v-else>
        <div class="card-list">
          <article v-for="delivery in deliveries" :key="delivery.id" class="record-card click-row" @click="openDelivery(delivery)">
            <div class="card-title-row">
              <div class="card-title">{{ delivery.merchant_name }}</div>
              <strong>{{ money(delivery.grand_total) }}</strong>
            </div>
            <div class="card-meta">
              <span>{{ delivery.invoice_date }}</span>
              <span>{{ delivery.lines.length }} 项</span>
              <span>{{ delivery.show_prices ? '显示单价' : '不显示单价' }}</span>
              <span :class="['status-badge', delivery.payment_status === 'paid' ? 'active' : 'unpaid']">
                {{ delivery.payment_status === 'paid' ? '已付' : '未付' }}
              </span>
            </div>
            <img
              v-if="delivery.signature_images && delivery.signature_images[0]"
              :src="delivery.signature_images[0]"
              alt="签收单"
              class="thumb"
              @click.stop="previewImage = delivery.signature_images[0]"
            />
            <div class="action-buttons" @click.stop>
              <button type="button" class="edit-btn" @click="openDelivery(delivery)">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                编辑
              </button>
              <button type="button" class="delete-btn" @click="removeDelivery(delivery)">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                删除
              </button>
            </div>
          </article>
        </div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>日期</th>
                <th>商家</th>
                <th>品项</th>
                <th>金额</th>
                <th>单价</th>
                <th>付款</th>
                <th>签收</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="delivery in deliveries" :key="'row-' + delivery.id" class="click-row" @click="openDelivery(delivery)">
                <td>{{ delivery.invoice_date }}</td>
                <td>{{ delivery.merchant_name }}</td>
                <td>{{ delivery.lines.length }}</td>
                <td>{{ money(delivery.grand_total) }}</td>
                <td>{{ delivery.show_prices ? '显示' : '隐藏' }}</td>
                <td>
                  <span :class="['status-badge', delivery.payment_status === 'paid' ? 'active' : 'unpaid']">
                    {{ delivery.payment_status === 'paid' ? '已付' : '未付' }}
                  </span>
                </td>
                <td @click.stop>
                  <img
                    v-if="delivery.signature_images && delivery.signature_images[0]"
                    :src="delivery.signature_images[0]"
                    alt="签收单"
                    class="thumb"
                    @click="previewImage = delivery.signature_images[0]"
                  />
                  <span v-else>—</span>
                </td>
                <td @click.stop>
                  <div class="action-buttons">
                    <button type="button" class="edit-btn" @click="openDelivery(delivery)">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                      编辑
                    </button>
                    <button type="button" class="delete-btn" @click="removeDelivery(delivery)">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                      删除
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <section v-else class="composer">
      <div class="composer-form">
        <div class="composer-bar">
          <button type="button" class="edit-btn back-list-btn" @click="closeComposer">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            返回列表
          </button>
          <h2>{{ editingId ? `供货记录 #${editingId}` : '新建供货记录' }}</h2>
          <button type="button" class="add-btn" :disabled="saving" @click="saveDelivery()">
            <span class="btn-label">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              {{ saving ? '保存中...' : '保存' }}
            </span>
          </button>
        </div>

        <label>商家
          <select v-model="form.merchant_id" @change="onMerchantChange">
            <option value="">选择商家</option>
            <option v-for="merchant in merchants" :key="merchant.id" :value="String(merchant.id)">
              {{ merchant.name }}{{ merchant.is_active ? '' : '（停用）' }}
            </option>
          </select>
        </label>
        <div class="split">
          <label>发票日期
            <span class="date-slot">
              <input v-model="form.invoice_date" type="date" @change="onInvoiceDateChange" />
            </span>
          </label>
          <label>付款日期
            <span class="date-slot">
              <input v-model="form.due_date" type="date" />
            </span>
          </label>
        </div>
        <label>付款方式
          <textarea v-model="form.payment_terms" rows="2"></textarea>
        </label>
        <label class="check">
          <input v-model="form.show_prices" type="checkbox" />
          显示单价
        </label>
        <p class="hint">关闭后打印的送货单不显示单价和金额。Invoice 始终显示单价。记录里仍保存进货价，汇总金额不受影响。</p>
        <div class="split">
          <label>税 HST
            <input v-model="form.hst" type="number" min="0" step="0.01" />
          </label>
          <label>折扣
            <input v-model="form.discount" type="number" min="0" step="0.01" />
          </label>
        </div>
        <label>付款状态
          <select v-model="form.payment_status">
            <option value="unpaid">未付</option>
            <option value="paid">已付</option>
          </select>
        </label>
        <label>备注
          <textarea v-model="form.notes" rows="2"></textarea>
        </label>

        <div class="lines-head">
          <h3>商品</h3>
          <button type="button" class="edit-btn" @click="addLine">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
            </svg>
            添加一行
          </button>
        </div>
        <div v-for="(line, index) in form.lines" :key="index" class="line-card">
          <div class="product-pick">
            <input
              v-model="line.search"
              type="text"
              placeholder="搜索商品，或直接填写名称"
              @focus="line.open = true"
              @input="onLineName(line)"
              @blur="closeLineSearch(line)"
            />
            <ul v-if="line.open && suggestions(line).length" class="suggestions">
              <li v-for="product in suggestions(line)" :key="product.id" @mousedown.prevent="pickProduct(line, product)">
                {{ product.name }}
              </li>
            </ul>
          </div>
          <div class="line-fields">
            <label>数量
              <input v-model="line.quantity" type="number" min="0.01" step="0.01" />
            </label>
            <label>单位
              <input v-model="line.unit" type="text" />
            </label>
            <label>进货单价
              <input v-model="line.unit_price" type="number" min="0" step="0.01" />
            </label>
            <button type="button" class="delete-btn" :disabled="form.lines.length === 1" @click="form.lines.splice(index, 1)">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              删除
            </button>
          </div>
        </div>

        <div class="uploads">
          <h3>签收单与支票</h3>
          <p v-if="!editingId" class="hint">先保存送货单，再上传签收纸和付款支票。</p>
          <template v-else>
            <div class="upload-block">
              <span>签收纸</span>
              <div class="thumbs">
                <button
                  v-for="(url, index) in form.signature_images"
                  :key="url"
                  type="button"
                  class="thumb-wrap"
                  @click="previewImage = url"
                >
                  <img :src="url" alt="签收纸" />
                  <span class="remove-photo" @click.stop="removePhoto('signature_images', index)">×</span>
                </button>
                <label class="upload-btn">
                  {{ uploading === 'signature' ? '上传中...' : '上传' }}
                  <input type="file" accept="image/*" :disabled="uploading" @change="onPhoto($event, 'signature_images')" />
                </label>
              </div>
            </div>
            <div class="upload-block">
              <span>付款支票</span>
              <div class="thumbs">
                <button
                  v-for="(url, index) in form.check_images"
                  :key="url"
                  type="button"
                  class="thumb-wrap"
                  @click="previewImage = url"
                >
                  <img :src="url" alt="支票" />
                  <span class="remove-photo" @click.stop="removePhoto('check_images', index)">×</span>
                </button>
                <label class="upload-btn">
                  {{ uploading === 'check' ? '上传中...' : '上传' }}
                  <input type="file" accept="image/*" :disabled="uploading" @change="onPhoto($event, 'check_images')" />
                </label>
              </div>
            </div>
          </template>
        </div>
      </div>

      <div class="composer-preview">
        <div class="preview-bar">
          <div class="preview-switch">
            <button type="button" :class="{ active: previewDoc === 'delivery' }" @click="previewDoc = 'delivery'">送货单</button>
            <button type="button" :class="{ active: previewDoc === 'invoice' }" @click="previewDoc = 'invoice'">Invoice</button>
          </div>
          <button type="button" class="edit-btn" @click="printSheet">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
            </svg>
            打印
          </button>
        </div>
        <DeliverySheet
          v-if="previewDoc === 'delivery'"
          :customer-name="selectedMerchantName"
          :invoice-date="form.invoice_date"
          :show-prices="form.show_prices"
          :lines="form.lines"
          :hst="form.hst"
          :discount="form.discount"
        />
        <InvoiceSheet
          v-else
          :customer-name="selectedMerchantName"
          :customer-address="selectedMerchantAddress"
          :invoice-date="form.invoice_date"
          :due-date="form.due_date"
          :lines="form.lines"
          :hst="form.hst"
          :discount="form.discount"
        />
      </div>
    </section>

    <div v-if="showMerchantModal" class="modal-overlay" @click="showMerchantModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>{{ merchantForm.id ? '编辑商家' : '添加商家' }}</h2>
          <button type="button" class="close-btn" @click="showMerchantModal = false">×</button>
        </div>
        <form class="merchant-form" @submit.prevent="saveMerchant">
          <label>名称 <span class="required">*</span>
            <input v-model="merchantForm.name" required placeholder="1001280318 Ontario Inc. (Fusion Foodmart)" />
          </label>
          <label>联系人
            <input v-model="merchantForm.contact_person" />
          </label>
          <label>电话
            <input v-model="merchantForm.phone" />
          </label>
          <label>地址
            <textarea v-model="merchantForm.address" rows="2"></textarea>
          </label>
          <label>备注
            <textarea v-model="merchantForm.notes" rows="2"></textarea>
          </label>
          <label class="check">
            <input v-model="merchantForm.show_prices" type="checkbox" />
            送货单默认显示单价
          </label>
          <label>付款方式
            <textarea v-model="merchantForm.payment_terms" rows="2"></textarea>
          </label>
          <label>付款天数
            <input v-model.number="merchantForm.payment_due_days" type="number" min="0" max="365" />
          </label>
          <label class="check">
            <input v-model="merchantForm.is_active" type="checkbox" />
            启用
          </label>
          <div class="form-actions">
            <button type="button" class="edit-btn" @click="showMerchantModal = false">取消</button>
            <button type="submit" class="add-btn" :disabled="savingMerchant">
              <span class="btn-label">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                保存
              </span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="previewImage" class="modal-overlay" @click="previewImage = null">
      <img :src="previewImage" alt="附件" class="preview-full" @click.stop />
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'
import { useModal } from '../composables/useModal'
import { usePageHeader } from '../stores/pageHeader'
import DeliverySheet from '../components/DeliverySheet.vue'
import InvoiceSheet from '../components/InvoiceSheet.vue'

const DEFAULT_PAYMENT_TERMS = 'Certified Cheque to 15891779 Canada Inc., Payment due within 1 week / 一周内支付'
const DEFAULT_MERCHANT_NAME = '1001280318 Ontario Inc. (Fusion Foodmart)'

function todayIso() {
  const date = new Date()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}-${month}-${day}`
}

function addDays(iso, days) {
  const [year, month, day] = String(iso || todayIso()).slice(0, 10).split('-').map(Number)
  const date = new Date(year, month - 1, day)
  date.setDate(date.getDate() + Number(days || 0))
  const nextMonth = String(date.getMonth() + 1).padStart(2, '0')
  const nextDay = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}-${nextMonth}-${nextDay}`
}

function money(value) {
  const number = Number(value) || 0
  return `$${number.toFixed(2)}`
}

function blankLine() {
  return {
    product_id: null,
    product_name: '',
    search: '',
    quantity: 1,
    unit: 'pc',
    unit_price: '',
    open: false
  }
}

function blankMerchant() {
  return {
    id: null,
    name: '',
    contact_person: '',
    phone: '',
    address: '',
    notes: '',
    show_prices: true,
    payment_terms: DEFAULT_PAYMENT_TERMS,
    payment_due_days: 7,
    is_active: true
  }
}

export default {
  name: 'BMerchants',
  components: { DeliverySheet, InvoiceSheet },
  setup() {
    const { confirm, error: showError } = useModal()
    const pageHeader = usePageHeader()
    return { confirm, showError, pageHeader }
  },
  data() {
    return {
      merchants: [],
      merchantQuery: '',
      loadingMerchants: true,
      merchantError: null,
      showMerchantModal: false,
      savingMerchant: false,
      merchantForm: blankMerchant(),
      deliveries: [],
      aggregates: { count: 0, grand_total: 0, unpaid_total: 0, paid_total: 0 },
      loadingDeliveries: true,
      deliveryError: null,
      filters: { merchant_id: '', payment_status: '' },
      composerOpen: false,
      previewDoc: 'delivery',
      editingId: null,
      saving: false,
      uploading: null,
      products: [],
      previewImage: null,
      form: {
        merchant_id: '',
        invoice_date: '',
        due_date: '',
        payment_terms: '',
        show_prices: true,
        hst: 0,
        discount: 0,
        payment_status: 'unpaid',
        notes: '',
        signature_images: [],
        check_images: [],
        lines: []
      }
    }
  },
  computed: {
    isMerchantPage() {
      return this.$route.name === 'BMerchants'
    },
    filteredMerchants() {
      const query = this.merchantQuery.trim().toLowerCase()
      if (!query) return this.merchants
      return this.merchants.filter(merchant => {
        return [merchant.name, merchant.contact_person, merchant.phone]
          .some(value => (value || '').toLowerCase().includes(query))
      })
    },
    selectedMerchant() {
      return this.merchants.find(item => String(item.id) === String(this.form.merchant_id)) || null
    },
    selectedMerchantName() {
      return this.selectedMerchant ? this.selectedMerchant.name : ''
    },
    selectedMerchantAddress() {
      return this.selectedMerchant ? (this.selectedMerchant.address || '') : ''
    }
  },
  watch: {
    '$route.name'(name) {
      if (name !== 'BSupplyRecords') this.composerOpen = false
      this.syncPageHeader()
    },
    composerOpen() {
      this.syncPageHeader()
    },
    editingId() {
      this.syncPageHeader()
    }
  },
  mounted() {
    this.fetchMerchants()
    this.fetchDeliveries()
    this.syncPageHeader()
  },
  beforeUnmount() {
    this.pageHeader.reset()
  },
  methods: {
    money,
    emptyDelivery() {
      const invoice = todayIso()
      return {
        merchant_id: '',
        invoice_date: invoice,
        due_date: addDays(invoice, 7),
        payment_terms: DEFAULT_PAYMENT_TERMS,
        show_prices: true,
        hst: 0,
        discount: 0,
        payment_status: 'unpaid',
        notes: '',
        signature_images: [],
        check_images: [],
        lines: [blankLine()]
      }
    },
    async fetchMerchants() {
      try {
        this.loadingMerchants = true
        this.merchantError = null
        const response = await apiClient.get('/admin/b-merchants')
        this.merchants = response.data.merchants || []
      } catch (error) {
        this.merchantError = error.response?.data?.error || '商家加载失败'
      } finally {
        this.loadingMerchants = false
      }
    },
    async fetchDeliveries() {
      try {
        this.loadingDeliveries = true
        this.deliveryError = null
        const params = {}
        if (this.filters.merchant_id) params.merchant_id = this.filters.merchant_id
        if (this.filters.payment_status) params.payment_status = this.filters.payment_status
        const response = await apiClient.get('/admin/b-deliveries', { params })
        this.deliveries = response.data.deliveries || []
        this.aggregates = response.data.aggregates || this.aggregates
      } catch (error) {
        this.deliveryError = error.response?.data?.error || '送货单加载失败'
      } finally {
        this.loadingDeliveries = false
      }
    },
    openMerchant(merchant) {
      this.merchantForm = merchant
        ? {
          id: merchant.id,
          name: merchant.name,
          contact_person: merchant.contact_person || '',
          phone: merchant.phone || '',
          address: merchant.address || '',
          notes: merchant.notes || '',
          show_prices: merchant.show_prices,
          payment_terms: merchant.payment_terms || DEFAULT_PAYMENT_TERMS,
          payment_due_days: merchant.payment_due_days,
          is_active: merchant.is_active
        }
        : blankMerchant()
      this.showMerchantModal = true
    },
    async saveMerchant() {
      this.savingMerchant = true
      const payload = { ...this.merchantForm }
      const id = payload.id
      delete payload.id
      try {
        if (id) await apiClient.put(`/admin/b-merchants/${id}`, payload)
        else await apiClient.post('/admin/b-merchants', payload)
        this.showMerchantModal = false
        await this.fetchMerchants()
      } catch (error) {
        await this.showError(error.response?.data?.error || '保存商家失败')
      } finally {
        this.savingMerchant = false
      }
    },
    async removeMerchant(merchant) {
      const ok = await this.confirm({
        type: 'warning',
        title: '删除商家',
        message: `删除 ${merchant.name}？已有送货记录的商家不能删除。`,
        showCancel: true,
        confirmText: '删除'
      })
      if (!ok) return
      try {
        await apiClient.delete(`/admin/b-merchants/${merchant.id}`)
        await this.fetchMerchants()
      } catch (error) {
        await this.showError(error.response?.data?.error || '删除失败')
      }
    },
    async ensureProducts() {
      if (this.products.length) return
      const response = await apiClient.get('/admin/products', { params: { sort: 'name' } })
      this.products = (response.data.products || []).filter(product => product.is_active !== false)
    },
    async openDelivery(delivery) {
      await this.ensureProducts()
      if (!delivery) {
        this.editingId = null
        this.form = this.emptyDelivery()
        const first = this.merchants.find(merchant => merchant.is_active && merchant.name === DEFAULT_MERCHANT_NAME)
          || this.merchants.find(merchant => merchant.is_active)
        if (first) {
          this.form.merchant_id = String(first.id)
          this.applyMerchantDefaults()
        }
      } else {
        this.editingId = delivery.id
        this.form = {
          merchant_id: String(delivery.merchant_id),
          invoice_date: delivery.invoice_date,
          due_date: delivery.due_date,
          payment_terms: delivery.payment_terms || '',
          show_prices: delivery.show_prices,
          hst: delivery.hst,
          discount: delivery.discount,
          payment_status: delivery.payment_status,
          notes: delivery.notes || '',
          signature_images: [...(delivery.signature_images || [])],
          check_images: [...(delivery.check_images || [])],
          lines: delivery.lines.map(line => ({
            product_id: line.product_id,
            product_name: line.product_name,
            search: line.product_name,
            quantity: line.quantity,
            unit: line.unit || 'pc',
            unit_price: line.unit_price,
            open: false
          }))
        }
        if (!this.form.lines.length) this.form.lines = [blankLine()]
      }
      this.composerOpen = true
    },
    syncPageHeader() {
      if (this.composerOpen && this.$route.name === 'BSupplyRecords') {
        this.pageHeader.setTitle(this.editingId ? `供货记录 #${this.editingId}` : '新建供货记录')
        this.pageHeader.setBackHandler(() => this.closeComposer())
        return
      }
      this.pageHeader.reset()
    },
    closeComposer() {
      this.composerOpen = false
      this.fetchDeliveries()
    },
    applyMerchantDefaults() {
      const merchant = this.merchants.find(item => String(item.id) === String(this.form.merchant_id))
      if (!merchant) return
      this.form.show_prices = merchant.show_prices
      this.form.payment_terms = merchant.payment_terms || DEFAULT_PAYMENT_TERMS
      this.form.due_date = addDays(this.form.invoice_date, merchant.payment_due_days)
    },
    onMerchantChange() {
      this.applyMerchantDefaults()
    },
    onInvoiceDateChange() {
      const merchant = this.merchants.find(item => String(item.id) === String(this.form.merchant_id))
      const days = merchant ? merchant.payment_due_days : 7
      this.form.due_date = addDays(this.form.invoice_date, days)
    },
    addLine() {
      this.form.lines.push(blankLine())
    },
    suggestions(line) {
      const query = (line.search || '').trim().toLowerCase()
      const rows = query
        ? this.products.filter(product => (product.name || '').toLowerCase().includes(query))
        : this.products
      return rows.slice(0, 8)
    },
    onLineName(line) {
      line.product_name = line.search
      line.open = true
      if (line.product_id) {
        const product = this.products.find(item => item.id === line.product_id)
        if (!product || product.name !== line.search) line.product_id = null
      }
    },
    closeLineSearch(line) {
      window.setTimeout(() => {
        line.open = false
      }, 150)
    },
    pickProduct(line, product) {
      line.product_id = product.id
      line.product_name = product.name
      line.search = product.name
      line.open = false
      if (product.pricing_type === 'per_item' && product.pricing_data && product.pricing_data.price != null) {
        line.unit_price = product.pricing_data.price
      }
    },
    payload() {
      return {
        merchant_id: Number(this.form.merchant_id),
        invoice_date: this.form.invoice_date,
        due_date: this.form.due_date,
        payment_terms: this.form.payment_terms,
        show_prices: this.form.show_prices,
        hst: this.form.hst === '' ? 0 : this.form.hst,
        discount: this.form.discount === '' ? 0 : this.form.discount,
        payment_status: this.form.payment_status,
        notes: this.form.notes,
        signature_images: this.form.signature_images,
        check_images: this.form.check_images,
        lines: this.form.lines.map(line => ({
          product_id: line.product_id,
          product_name: (line.product_name || line.search || '').trim(),
          quantity: line.quantity,
          unit: (line.unit || 'pc').trim() || 'pc',
          unit_price: line.unit_price === '' ? 0 : line.unit_price
        }))
      }
    },
    async saveDelivery(options = {}) {
      if (!this.form.merchant_id) {
        await this.showError('请选择商家')
        return false
      }
      this.saving = true
      try {
        const body = this.payload()
        const response = this.editingId
          ? await apiClient.put(`/admin/b-deliveries/${this.editingId}`, body)
          : await apiClient.post('/admin/b-deliveries', body)
        this.editingId = response.data.delivery.id
        if (!options.keepOpen) this.closeComposer()
        return true
      } catch (error) {
        await this.showError(error.response?.data?.error || '保存送货单失败')
        return false
      } finally {
        this.saving = false
      }
    },
    async removeDelivery(delivery) {
      const ok = await this.confirm({
        type: 'warning',
        title: '删除送货单',
        message: `删除 ${delivery.invoice_date} ${delivery.merchant_name} 的送货单？`,
        showCancel: true,
        confirmText: '删除'
      })
      if (!ok) return
      try {
        await apiClient.delete(`/admin/b-deliveries/${delivery.id}`)
        await this.fetchDeliveries()
      } catch (error) {
        await this.showError(error.response?.data?.error || '删除失败')
      }
    },
    async onPhoto(event, field) {
      const file = event.target.files?.[0]
      event.target.value = ''
      if (!file || !this.editingId) return
      const kind = field === 'signature_images' ? 'signature' : 'check'
      this.uploading = kind
      const formData = new FormData()
      formData.append('image', file)
      formData.append('folder', 'b-deliveries')
      try {
        const response = await apiClient.post('/admin/upload-image', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        this.form[field].push(response.data.url)
        const saved = await this.saveDelivery({ keepOpen: true })
        if (!saved) this.form[field].pop()
      } catch (error) {
        await this.showError(error.response?.data?.error || '上传失败')
      } finally {
        this.uploading = null
      }
    },
    async removePhoto(field, index) {
      this.form[field].splice(index, 1)
      await this.saveDelivery({ keepOpen: true })
    },
    printSheet() {
      window.print()
    }
  }
}
</script>

<style scoped>
.b-page {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
  min-width: 0;
  max-width: 100%;
}

.date-slot {
  display: contents;
}

.b-page > section:not(.composer) {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-lg);
}

.tabs {
  display: flex;
  gap: 8px;
}

.tabs button {
  border: 1px solid rgba(0, 0, 0, 0.12);
  background: var(--surface-card);
  border-radius: 999px;
  padding: 10px 18px;
  min-height: 40px;
  cursor: pointer;
}

.tabs button.active {
  background: var(--md-primary);
  color: var(--text-on-brand);
  border-color: transparent;
}

.page-header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.search-input, .filter-select, .merchant-form input, .merchant-form textarea, .composer-form input, .composer-form select, .composer-form textarea {
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-md);
  padding: 8px 10px;
  font: inherit;
  background: var(--md-surface);
  color: var(--md-on-surface);
  accent-color: var(--md-primary);
}

.search-input:focus, .filter-select:focus, .merchant-form input:focus, .merchant-form textarea:focus, .composer-form input:focus, .composer-form select:focus, .composer-form textarea:focus {
  outline: none;
  border-color: var(--brand-ink);
  box-shadow: 0 0 0 3px var(--brand-focus);
}

.search-input {
  flex: 1;
  min-width: 200px;
}

.add-btn, .edit-btn, .delete-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--md-spacing-sm);
  border: none;
  border-radius: var(--md-radius-md);
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  min-height: 40px;
  cursor: pointer;
  font: inherit;
  font-weight: 500;
  line-height: 1.2;
  text-align: center;
  appearance: none;
  -webkit-appearance: none;
}

.btn-label {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--md-spacing-sm);
  line-height: 1.2;
}

.add-btn svg, .edit-btn svg, .delete-btn svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.add-btn {
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  background: var(--md-primary);
  color: var(--text-on-brand);
  box-shadow: var(--md-elevation-2);
}

.add-btn:hover:not(:disabled) {
  background: var(--brand-hover);
}

.add-btn:disabled {
  opacity: 0.6;
  cursor: default;
}

.edit-btn {
  background: rgba(0, 0, 0, 0.06);
}

.delete-btn {
  background: #ffebee;
  color: #b71c1c;
}

.table-wrap {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  min-width: 760px;
  border-collapse: collapse;
  background: var(--surface-card);
}

.data-table th, .data-table td {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  vertical-align: middle;
}

.data-table th {
  white-space: nowrap;
}

.card-list {
  display: none;
}

.record-card {
  background: var(--surface-card);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
  box-shadow: var(--md-elevation-1);
}

.card-title-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.card-title {
  font-weight: 600;
  line-height: 1.35;
}

.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  color: rgba(0, 0, 0, 0.65);
  font-size: 13px;
  align-items: center;
}

.card-sub {
  margin: 0;
  color: rgba(0, 0, 0, 0.7);
  font-size: 14px;
}

.click-row {
  cursor: pointer;
}

.click-row:hover {
  background: var(--md-surface-variant);
}

.inactive {
  opacity: 0.65;
}

.status-badge {
  display: inline-block;
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 12px;
}

.status-badge.active {
  background: #e8f5e9;
  color: #2e7d32;
}

.status-badge.inactive, .status-badge.unpaid {
  background: var(--warning-bg);
  color: var(--warning-text);
}

.action-buttons {
  display: flex;
  gap: 6px;
}

.stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.stat {
  background: var(--surface-card);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 10px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat span {
  color: rgba(0, 0, 0, 0.6);
  font-size: 13px;
}

.thumb {
  width: 42px;
  height: 42px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.12);
}

.composer {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 16px;
  align-items: start;
  min-width: 0;
  max-width: 100%;
}

.composer-form, .composer-preview, .modal-content {
  background: var(--surface-card);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  padding: 16px;
  min-width: 0;
  max-width: 100%;
  box-sizing: border-box;
}

.composer-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.composer-form label, .merchant-form label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 14px;
  min-width: 0;
}

.composer-form input:not([type="checkbox"]),
.composer-form select,
.composer-form textarea {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.composer-bar, .preview-bar, .lines-head, .form-actions, .modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.composer-bar h2, .lines-head h3, .uploads h3 {
  margin: 0;
  font-size: 16px;
}

.split, .line-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.line-fields {
  grid-template-columns: 1fr 80px 1fr auto;
  align-items: end;
}

.line-card {
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 10px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.product-pick {
  position: relative;
}

.product-pick input, .line-fields input {
  width: 100%;
}

.suggestions {
  position: absolute;
  z-index: 5;
  left: 0;
  right: 0;
  top: 100%;
  margin: 4px 0 0;
  padding: 4px 0;
  list-style: none;
  background: var(--surface-card);
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 8px;
  max-height: 220px;
  overflow: auto;
}

.suggestions li {
  padding: 8px 10px;
  cursor: pointer;
}

.suggestions li:hover {
  background: rgba(240, 168, 0, 0.12);
}

.check {
  flex-direction: row !important;
  align-items: center;
  gap: 10px !important;
  min-height: 40px;
}

.check input {
  width: 20px;
  height: 20px;
  margin: 0;
  flex: 0 0 20px;
  accent-color: var(--brand-ink);
}

.hint {
  margin: 0;
  color: rgba(0, 0, 0, 0.6);
  font-size: 13px;
}

.uploads {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}

.thumbs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.thumb-wrap {
  position: relative;
  border: none;
  padding: 0;
  background: none;
  cursor: pointer;
}

.thumb-wrap img {
  width: 72px;
  height: 72px;
  object-fit: cover;
  border-radius: 8px;
}

.remove-photo {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #b71c1c;
  color: var(--text-on-brand);
  font-size: 12px;
  line-height: 18px;
}

.upload-btn {
  border: 1px dashed rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  padding: 8px 12px;
  cursor: pointer;
}

.upload-btn input {
  display: none;
}

.preview-bar {
  margin-bottom: 10px;
}

.preview-switch {
  display: inline-flex;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 999px;
  overflow: hidden;
  background: var(--surface-card);
}

.preview-switch button {
  border: none;
  background: transparent;
  min-height: 36px;
  padding: 6px 14px;
  cursor: pointer;
  font: inherit;
}

.preview-switch button.active {
  background: var(--md-primary);
  color: var(--text-on-brand);
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 40;
  padding: 16px;
}

.modal-content {
  width: min(520px, 100%);
  max-height: 90vh;
  overflow: auto;
}

.merchant-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.required {
  color: #b71c1c;
}

.close-btn {
  border: none;
  background: none;
  font-size: 24px;
  cursor: pointer;
}

.preview-full {
  max-width: min(960px, 100%);
  max-height: 90vh;
  object-fit: contain;
  background: var(--surface-card);
}

.loading, .error, .empty-state {
  padding: 24px 0;
}

.error {
  color: #b71c1c;
}

@media (max-width: 960px) {
  .composer, .line-fields, .split {
    grid-template-columns: minmax(0, 1fr);
  }

  .stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 767px) {
  .page-header-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .page-header-actions,
  .composer,
  .composer-form,
  .split,
  .composer-form label {
    width: 100%;
    max-width: 100%;
    min-width: 0;
    box-sizing: border-box;
  }

  .search-input, .filter-select, .add-btn {
    width: 100%;
    min-width: 0;
    max-width: 100%;
    box-sizing: border-box;
  }

  /* Real iOS only. Chrome's device mode does not apply this.
     WebKit gives a date input a minimum width from the date text and
     ignores min-width: 0, which pushes the field past the screen.
     Dropping the native appearance is what lets the width stick. */
  @supports (-webkit-touch-callout: none) {
    .date-slot {
      display: block;
      width: 100%;
      max-width: 100%;
      min-width: 0;
      overflow: hidden;
      contain: inline-size;
    }

    .composer-form .date-slot input {
      display: block;
      box-sizing: border-box;
      width: 100%;
      max-width: 100%;
      min-width: 0;
      min-inline-size: 0;
      margin: 0;
      min-height: 44px;
      padding: 8px 36px 8px 12px;
      font-size: 16px;
      line-height: 1.2;
      text-align: left;
      appearance: none;
      -webkit-appearance: none;
      background-color: var(--md-surface);
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23666' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z'/%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: right 10px center;
      background-size: 18px 18px;
    }

    .composer-form .date-slot input::-webkit-date-and-time-value {
      text-align: left;
      margin: 0;
      min-width: 0;
    }

    .composer-form .date-slot input::-webkit-datetime-edit,
    .composer-form .date-slot input::-webkit-datetime-edit-fields-wrapper {
      padding: 0;
      min-width: 0;
      max-width: 100%;
    }
  }

  .back-list-btn {
    display: none;
  }

  .table-wrap {
    display: none;
  }

  .card-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .composer-bar, .preview-bar, .lines-head, .form-actions {
    flex-wrap: wrap;
  }

  .composer-bar h2 {
    flex: 1 1 100%;
  }

  .composer-preview {
    overflow-x: auto;
  }

  .composer-form, .composer-preview, .record-card {
    padding: var(--md-spacing-md);
  }
}
</style>
