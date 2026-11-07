<template>
  <article class="delivery-sheet">
    <img class="sheet-logo" :src="logo" alt="Grain Story Poultry Farm" />
    <h1>INVOICE 发票</h1>
    <p><span class="label">Supplier / 供货方:</span> {{ supplierName }}</p>
    <p><span class="label">Customer / 收货方:</span> {{ customerName || '—' }}</p>
    <p><span class="label">Invoice Date / 发票日期:</span> {{ formatInvoiceDate(invoiceDate) }}</p>
    <p><span class="label">Due Date / 付款日期:</span> {{ formatInvoiceDate(dueDate) }}</p>
    <p><span class="label">Payment Terms / 付款方式:</span> {{ paymentTerms }}</p>

    <table>
      <thead>
        <tr>
          <th class="col-num">#</th>
          <th>Product / 产品</th>
          <th>Quantity / 数量</th>
          <th v-if="showPrices">Unit Price / 单价</th>
          <th v-if="showPrices">Amount / 金额</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(line, index) in lines" :key="index">
          <td>{{ index + 1 }}</td>
          <td>{{ line.product_name || '—' }}</td>
          <td>{{ formatQty(line.quantity, line.unit) }}</td>
          <td v-if="showPrices">{{ formatMoney(line.unit_price) }}/{{ line.unit || 'pc' }}</td>
          <td v-if="showPrices">{{ formatMoney(lineAmount(line)) }}</td>
        </tr>
        <tr v-if="!lines.length">
          <td :colspan="showPrices ? 5 : 3" class="empty">—</td>
        </tr>
      </tbody>
    </table>

    <div v-if="showPrices" class="totals">
      <p><span>Subtotal / 小计:</span> {{ formatMoney(subtotal) }}</p>
      <p><span>HST (if applicable) / 税（如适用）:</span> {{ formatMoney(hst, true) }}</p>
      <p><span>Discount/折扣:</span> {{ discount ? formatMoney(discount) : '' }}</p>
      <p class="grand"><span>Grand Total / 总计:</span> {{ formatMoney(grandTotal) }}</p>
    </div>

    <div class="signature">
      <p class="sign-title">Received By (Signature) / 收货方签收</p>
      <p>Signature 签名: _____________________________</p>
      <p>Name 姓名: _________________________________</p>
      <p>Date 日期: _________________________________</p>
    </div>
  </article>
</template>

<script>
import logo from '../assets/invoice-logo.png'

const SUPPLIER_NAME = '15891779 Canada Inc. (Grain Story Farm)'

function formatMoney(value, forceCents = false) {
  const number = Number(value)
  const amount = Number.isFinite(number) ? Math.round(number * 100) / 100 : 0
  if (forceCents) return `$${amount.toFixed(2)}`
  const text = amount.toFixed(2).replace(/\.00$/, '').replace(/(\.\d)0$/, '$1')
  return `$${text}`
}

function formatQty(quantity, unit) {
  const number = Number(quantity)
  const text = Number.isFinite(number)
    ? String(Math.round(number * 100) / 100).replace(/\.0+$/, '').replace(/(\.\d)0$/, '$1')
    : ''
  return `${text}${unit || ''}`
}

function lineAmount(line) {
  const quantity = Number(line.quantity)
  const price = Number(line.unit_price)
  if (!Number.isFinite(quantity) || !Number.isFinite(price)) return 0
  return Math.round(quantity * price * 100) / 100
}

function formatInvoiceDate(iso) {
  if (!iso) return ''
  const [year, month, day] = String(iso).slice(0, 10).split('-').map(Number)
  if (!year || !month || !day) return ''
  const date = new Date(year, month - 1, day)
  const monthName = date.toLocaleString('en-US', { month: 'long' })
  const mod = day % 10
  const teen = day % 100
  const suffix = teen >= 11 && teen <= 13 ? 'th' : mod === 1 ? 'st' : mod === 2 ? 'nd' : mod === 3 ? 'rd' : 'th'
  return `${monthName} ${day}${suffix}, ${year}`
}

export default {
  name: 'DeliverySheet',
  props: {
    customerName: { type: String, default: '' },
    invoiceDate: { type: String, default: '' },
    dueDate: { type: String, default: '' },
    paymentTerms: { type: String, default: '' },
    showPrices: { type: Boolean, default: true },
    lines: { type: Array, default: () => [] },
    hst: { type: [Number, String], default: 0 },
    discount: { type: [Number, String], default: 0 }
  },
  data() {
    return { logo, supplierName: SUPPLIER_NAME }
  },
  computed: {
    subtotal() {
      return this.lines.reduce((sum, line) => sum + lineAmount(line), 0)
    },
    grandTotal() {
      const hst = Number(this.hst) || 0
      const discount = Number(this.discount) || 0
      return Math.round((this.subtotal + hst - discount) * 100) / 100
    }
  },
  methods: {
    formatMoney,
    formatQty,
    formatInvoiceDate,
    lineAmount
  }
}
</script>

<style scoped>
.delivery-sheet {
  background: var(--surface-card);
  color: #111;
  padding: 28px 32px 36px;
  border: 1px solid #e0e0e0;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  font-family: "Times New Roman", Times, "Songti SC", serif;
  font-size: 15px;
  line-height: 1.45;
  max-width: 800px;
  box-sizing: border-box;
}

@media (max-width: 767px) {
  .delivery-sheet {
    max-width: 100%;
    padding: 16px 12px 24px;
    font-size: 13px;
  }

  .delivery-sheet p,
  .delivery-sheet th,
  .delivery-sheet td {
    overflow-wrap: anywhere;
  }

  .sheet-logo {
    width: 72px;
    height: 72px;
  }

  h1 {
    font-size: 18px;
  }
}

.sheet-logo {
  display: block;
  width: 108px;
  height: 108px;
  object-fit: contain;
  margin: 0 auto 4px;
}

h1 {
  text-align: center;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0.04em;
  margin: 0 0 16px;
}

p {
  margin: 0 0 4px;
}

.label {
  font-weight: 700;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 16px;
}

th, td {
  border: 1px solid #222;
  padding: 6px 8px;
  text-align: left;
  vertical-align: top;
}

th {
  font-weight: 700;
  background: var(--surface-subtle);
}

.col-num {
  width: 36px;
}

.empty {
  text-align: center;
  color: #888;
}

.totals {
  margin-top: 14px;
  margin-left: auto;
  width: min(100%, 420px);
}

.totals p {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 4px;
}

.totals .grand {
  font-weight: 700;
  margin-top: 6px;
}

.signature {
  margin-top: 28px;
}

.sign-title {
  font-weight: 700;
  margin-bottom: 10px;
}

.signature p {
  margin-bottom: 8px;
}
</style>

<style>
@media print {
  .sidebar,
  .top-header,
  .sidebar-overlay,
  .tabs,
  .composer-form,
  .preview-bar {
    display: none !important;
  }

  html,
  body,
  #app,
  .admin-layout,
  .main-content,
  .content-area,
  .composer,
  .composer-preview,
  .delivery-sheet {
    display: block !important;
    margin: 0 !important;
    overflow: visible !important;
    height: auto !important;
    min-height: 0 !important;
    width: 100% !important;
    max-width: none !important;
    box-sizing: border-box !important;
  }

  .admin-layout,
  .main-content,
  .content-area,
  .composer,
  .composer-preview {
    padding: 0 !important;
  }

  .delivery-sheet {
    border: none !important;
    box-shadow: none !important;
    padding: 10mm 12mm !important;
  }

  /* Chrome draws the date, page title, and URL in the page margin. */
  @page {
    margin: 0;
  }
}
</style>
