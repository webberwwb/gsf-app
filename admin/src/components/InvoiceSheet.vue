<template>
  <article class="invoice-sheet">
    <header class="inv-header">
      <div class="company">
        <p>15891779 CANADA INC.</p>
        <p>Grain Story Farm</p>
        <p>Grainstoryfarm@gmail.com</p>
      </div>
      <div class="brand">
        <img class="mark" :src="mark" alt="" />
        <p class="brand-name">GRAIN STORY</p>
        <p class="brand-sub">Poultry Farm</p>
        <p class="brand-sub">谷语农庄</p>
      </div>
      <h1>INVOICE</h1>
    </header>

    <hr class="rule" />

    <div class="parties">
      <div>
        <p class="kicker">ISSUED TO:</p>
        <p class="party-name">{{ customerName || '—' }}</p>
        <p v-if="customerAddress" class="address">{{ customerAddress }}</p>
      </div>
      <div class="dates">
        <p class="kicker">INVOICE DATE:</p>
        <p>{{ formatUsDate(invoiceDate) }}</p>
        <p class="kicker due">DUE DATE:</p>
        <p>{{ formatUsDate(dueDate) }}</p>
      </div>
    </div>

    <div class="lines">
      <table>
        <thead>
          <tr>
            <th>DESCRIPTION</th>
            <th class="price">UNIT PRICE</th>
            <th class="qty">QTY</th>
            <th class="total">TOTAL</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(line, index) in lines" :key="index">
            <td>{{ line.product_name || '—' }}</td>
            <td class="price">{{ plain(line.unit_price) }}</td>
            <td class="qty">{{ plain(line.quantity) }}</td>
            <td class="total">{{ dollars(lineAmount(line)) }}</td>
          </tr>
          <tr v-if="!lines.length">
            <td colspan="4" class="empty">—</td>
          </tr>
        </tbody>
      </table>
    </div>

    <hr class="rule" />

    <footer class="foot">
      <img class="thanks" :src="thanks" alt="thank you" />
      <div class="totals">
        <p><span>Total</span><span>{{ dollars(subtotal) }}</span></p>
        <p><span>Tax</span><span>{{ dollars(hst) }}</span></p>
        <p v-if="hasDiscount"><span>Discount</span><span>-{{ dollars(discount) }}</span></p>
        <p class="due"><span>Amount due</span><span>{{ dollars(grandTotal) }}</span></p>
      </div>
    </footer>
  </article>
</template>

<script>
import mark from '../assets/invoice-mark.png'
import thanks from '../assets/invoice-thanks.png'

function plain(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return ''
  const amount = Math.round(number * 100) / 100
  return amount.toFixed(2).replace(/\.00$/, '').replace(/(\.\d)0$/, '$1')
}

function dollars(value) {
  const text = plain(value)
  return text === '' ? '' : `$${text}`
}

function lineAmount(line) {
  const quantity = Number(line.quantity)
  const price = Number(line.unit_price)
  if (!Number.isFinite(quantity) || !Number.isFinite(price)) return 0
  return Math.round(quantity * price * 100) / 100
}

function formatUsDate(iso) {
  if (!iso) return ''
  const [year, month, day] = String(iso).slice(0, 10).split('-')
  if (!year || !month || !day) return ''
  return `${month}/${day}/${year}`
}

export default {
  name: 'InvoiceSheet',
  props: {
    customerName: { type: String, default: '' },
    customerAddress: { type: String, default: '' },
    invoiceDate: { type: String, default: '' },
    dueDate: { type: String, default: '' },
    lines: { type: Array, default: () => [] },
    hst: { type: [Number, String], default: 0 },
    discount: { type: [Number, String], default: 0 }
  },
  data() {
    return { mark, thanks }
  },
  computed: {
    subtotal() {
      return this.lines.reduce((sum, line) => sum + lineAmount(line), 0)
    },
    hasDiscount() {
      return Number(this.discount) > 0
    },
    grandTotal() {
      const tax = Number(this.hst) || 0
      const discount = Number(this.discount) || 0
      return Math.round((this.subtotal + tax - discount) * 100) / 100
    }
  },
  methods: {
    plain,
    dollars,
    formatUsDate,
    lineAmount
  }
}
</script>

<style scoped>
.invoice-sheet {
  background: #fff;
  color: #1c1c1c;
  padding: 44px 48px 36px;
  border: 1px solid #e0e0e0;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  font-family: "Avenir Next", "PingFang SC", "Helvetica Neue", sans-serif;
  font-size: 15px;
  line-height: 1.45;
  width: 100%;
  max-width: 816px;
  min-height: 1056px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.inv-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: center;
  gap: 12px;
}

.company p,
.brand p {
  margin: 0;
}

.company {
  font-size: 13px;
  line-height: 1.45;
}

.brand {
  text-align: center;
}

.mark {
  width: 64px;
  height: 60px;
  object-fit: contain;
  display: block;
  margin: 0 auto 4px;
}

.brand-name {
  font-weight: 700;
  letter-spacing: 0.14em;
  font-size: 15px;
}

.brand-sub {
  font-size: 13px;
  line-height: 1.35;
}

h1 {
  margin: 0;
  text-align: right;
  font-size: 52px;
  font-weight: 800;
  letter-spacing: 0.02em;
  line-height: 1;
}

.rule {
  border: none;
  border-top: 1px solid #222;
  margin: 22px 0;
}

.parties {
  display: flex;
  justify-content: space-between;
  gap: 24px;
}

.parties p {
  margin: 0;
}

.kicker {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.12em;
  margin-bottom: 8px;
}

.party-name {
  font-weight: 600;
}

.address {
  white-space: pre-wrap;
  margin-top: 2px;
}

.dates {
  text-align: right;
  flex: 0 0 auto;
}

.dates .due {
  margin-top: 12px;
}

.lines {
  flex: 1 1 auto;
  min-height: 0;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 8px;
}

th {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-align: left;
  padding: 12px 10px;
  border-top: 1px solid #222;
  border-bottom: 1px solid #222;
}

td {
  padding: 16px 10px;
  vertical-align: top;
}

.price,
.qty {
  text-align: center;
  width: 18%;
}

.total {
  text-align: right;
  width: 18%;
}

.empty {
  text-align: center;
  color: #888;
}

.foot {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.thanks {
  width: 180px;
  height: auto;
  margin-top: 8px;
}

.totals {
  width: min(100%, 280px);
  margin-left: auto;
}

.totals p {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 32px;
  margin: 0 0 10px;
  font-size: 16px;
}

.due {
  font-weight: 700;
}

@media (max-width: 767px) {
  .invoice-sheet {
    max-width: 100%;
    min-height: 0;
    padding: 16px 12px 20px;
    font-size: 13px;
  }

  h1 {
    font-size: 26px;
  }

  .brand-name {
    letter-spacing: 0.06em;
    font-size: 11px;
  }

  .parties {
    flex-direction: column;
  }

  .dates {
    text-align: left;
  }

  .lines {
    min-height: 0;
  }

  th {
    letter-spacing: 0.04em;
    font-size: 11px;
  }
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

  .invoice-sheet {
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
    font-size: 11pt !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
    page-break-after: avoid !important;
    page-break-inside: avoid !important;
    transform: scale(0.9) !important;
    transform-origin: center center !important;
  }

  .invoice-sheet h1 {
    font-size: 36pt !important;
  }

  .invoice-sheet .lines {
    flex: 1 1 auto !important;
    min-height: 0 !important;
  }

  .invoice-sheet .foot {
    flex-shrink: 0 !important;
    page-break-inside: avoid !important;
  }

  @page {
    size: letter;
    margin: 0;
  }
}
</style>
