<template>
  <article class="delivery-sheet">
    <header class="sheet-top">
      <img class="sheet-logo" :src="logo" alt="Grain Story Poultry Farm" />
      <h1>DELIVERY NOTE 送货单</h1>
      <p><span class="label">Supplier / 供货方:</span> {{ supplierName }}</p>
      <p><span class="label">Customer / 收货方:</span> {{ customerName || '—' }}</p>
      <p><span class="label">Delivery Date / 送货日期:</span> {{ formatInvoiceDate(invoiceDate) }}</p>
    </header>

    <div class="sheet-body">
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
    </div>

    <footer class="sheet-end">
      <div class="signature">
        <p class="sign-title">Received By (Signature) / 收货方签收</p>
        <p>Signature 签名: _____________________________</p>
        <p>Name 姓名: _________________________________</p>
        <p>Date 日期: _________________________________</p>
      </div>
    </footer>
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
  padding: 36px 40px 40px;
  border: 1px solid #e0e0e0;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  font-family: "Times New Roman", Times, "Songti SC", serif;
  font-size: 16px;
  line-height: 1.5;
  width: 100%;
  max-width: 816px;
  min-height: 1056px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

@media (max-width: 767px) {
  .delivery-sheet {
    max-width: 100%;
    min-height: 0;
    padding: 16px 12px 24px;
    font-size: 13px;
  }

  .delivery-sheet p,
  .delivery-sheet th,
  .delivery-sheet td {
    overflow-wrap: anywhere;
  }

  .sheet-logo {
    width: 96px;
    height: 96px;
  }

  h1 {
    font-size: 18px;
  }
}

.sheet-logo {
  display: block;
  width: 180px;
  height: 180px;
  object-fit: contain;
  margin: 0 auto 12px;
  print-color-adjust: exact;
  -webkit-print-color-adjust: exact;
}

h1 {
  text-align: center;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 0.04em;
  margin: 0 0 22px;
}

.sheet-top p {
  margin: 0 0 8px;
}

.label {
  font-weight: 700;
}

.sheet-body {
  flex: 0 0 auto;
  margin-top: 22px;
}

.sheet-end {
  margin-top: auto;
}

table {
  width: 100%;
  height: auto;
  border-collapse: collapse;
}

th, td {
  border: 1px solid #222;
  padding: 10px 12px;
  text-align: left;
  vertical-align: top;
}

th {
  font-weight: 700;
  background: var(--surface-subtle);
}

.col-num {
  width: 42px;
}

.empty {
  text-align: center;
  color: #888;
}

.totals {
  margin-top: 64px;
  margin-left: auto;
  width: min(100%, 420px);
}

.totals p {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin: 0 0 8px;
}

.totals .grand {
  font-weight: 700;
  margin-top: 8px;
}

.signature {
  margin-top: 40px;
}

.sign-title {
  font-weight: 700;
  margin-bottom: 14px;
}

.signature p {
  margin: 0 0 12px;
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
  .composer-preview {
    display: block !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    width: 8.5in !important;
    max-width: 8.5in !important;
    height: 11in !important;
    min-height: 0 !important;
    box-sizing: border-box !important;
  }

  .delivery-sheet {
    display: flex !important;
    flex-direction: column !important;
    width: 8.5in !important;
    max-width: 8.5in !important;
    height: 11in !important;
    min-height: 0 !important;
    max-height: 11in !important;
    margin: 0 !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0.4in 0.45in !important;
    font-size: 12pt !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
    page-break-after: avoid !important;
    page-break-inside: avoid !important;
    transform: scale(0.9) !important;
    transform-origin: center center !important;
  }

  .delivery-sheet .sheet-logo {
    width: 1.7in !important;
    height: 1.7in !important;
  }

  .delivery-sheet h1 {
    font-size: 22pt !important;
    margin-bottom: 16px !important;
  }

  .delivery-sheet .sheet-body {
    flex: 0 0 auto !important;
  }

  .delivery-sheet table {
    height: auto !important;
  }

  .delivery-sheet .totals {
    margin-top: 0.7in !important;
  }

  .delivery-sheet .sheet-end {
    margin-top: auto !important;
    flex-shrink: 0 !important;
    page-break-inside: avoid !important;
  }

  .delivery-sheet .signature {
    margin-top: 0 !important;
    flex-shrink: 0 !important;
    page-break-inside: avoid !important;
  }

  .delivery-sheet .signature p {
    margin-bottom: 8px !important;
  }

  /* Chrome draws the date, page title, and URL in the page margin. */
  @page {
    size: letter;
    margin: 0;
  }
}
</style>
