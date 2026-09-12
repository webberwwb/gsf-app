import { formatOrderMoney2, orderAmountDueNumber } from './orderPricing'
import { routeSeqLabel, sortSelfDeliveryOrders } from './deliveryRoute'

const LABELS_PER_PAGE = 18

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

export function formatLabelDate(dateString) {
  if (!dateString) return ''
  const match = String(dateString).match(/^(\d{4})-(\d{2})-(\d{2})/)
  return match ? `${match[1]}-${match[2]}-${match[3]}` : ''
}

function recipientName(order) {
  return order?.address?.recipient_name || order?.user?.nickname || '客户'
}

function addressLines(address) {
  if (!address) return ['无地址']
  const lines = [
    address.address_line1,
    address.address_line2,
    [address.city, address.postal_code].filter(Boolean).join(', ')
  ].filter(Boolean)
  if (address.delivery_instructions) lines.push(address.delivery_instructions)
  return lines.length ? lines : ['无地址']
}

function collectCash(order) {
  return order?.payment_method === 'cash' && order?.payment_status !== 'paid'
}

function renderLabel(order, index, date, logoUrl) {
  const seq = routeSeqLabel(order, index)
  const cash = collectCash(order)
  const due = formatOrderMoney2(orderAmountDueNumber(order))
  const phone = order?.address?.phone || ''
  const lines = addressLines(order?.address)
    .map((line) => `<div class="addr">${escapeHtml(line)}</div>`)
    .join('')
  const prepaidLabel = order?.payment_method === 'cash' ? '不用收' : '线上支付'
  const payRow = cash
    ? `<div class="pay-bar cash">收现金 $${escapeHtml(due)}</div>`
    : `<div class="pay-bar prepaid">${prepaidLabel}</div>`

  return `<article class="label ${cash ? 'cash' : 'prepaid'}">
    <header class="row brand-row">
      <span class="brand">
        <img src="${escapeHtml(logoUrl)}" alt="" />
        <span>谷语农庄</span>
      </span>
      <span class="meta"><strong>#${escapeHtml(seq)}</strong></span>
    </header>
    <div class="row who">
      <span class="name">${escapeHtml(recipientName(order))}</span>
      ${phone ? `<span class="phone">${escapeHtml(phone)}</span>` : ''}
    </div>
    <div class="addr-block">${lines}</div>
    ${date ? `<div class="date">配送日期：${escapeHtml(date)}</div>` : ''}
    ${payRow}
  </article>`
}

function sheetCss() {
  return `@page { size: A4; margin: 0; }
* { box-sizing: border-box; }
html, body {
  margin: 0;
  padding: 0;
  background: #fff;
  color: #111;
  font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
}
.page {
  width: 210mm;
  height: 297mm;
  padding: 4mm;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(6, 1fr);
  gap: 3mm;
  page-break-after: always;
}
.page:last-child { page-break-after: auto; }
.label {
  overflow: hidden;
  min-width: 0;
  padding: 2.2mm 2.4mm;
  border: 0.5pt solid #cfcfcf;
  display: flex;
  flex-direction: column;
  gap: 0.8mm;
  font-size: 8.5pt;
  line-height: 1.25;
}
.label.empty { border-color: transparent; background: transparent; }
.label.cash {
  border: 1.4pt solid #b71c1c;
  background: #fff4f2;
}
.label.prepaid {
  border: 0.7pt solid #2e7d32;
  background: #f3f8f3;
}
.row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 2mm;
  flex-wrap: nowrap;
  min-width: 0;
}
.row > :first-child { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.row > :last-child { flex-shrink: 0; white-space: nowrap; }
.brand-row { align-items: center; }
.brand {
  display: inline-flex;
  align-items: center;
  gap: 1.2mm;
  font-weight: 700;
  font-size: 9.5pt;
  line-height: 1;
}
.brand img { width: 5.8mm; height: 5.8mm; object-fit: contain; flex-shrink: 0; display: block; }
.meta { font-size: 9pt; line-height: 1; display: inline-flex; align-items: center; }
.meta strong { font-size: 11pt; line-height: 1; }
.who { font-weight: 600; }
.addr-block { flex: 1; min-height: 0; overflow: hidden; }
.addr { overflow-wrap: anywhere; }
.date { font-size: 8pt; color: #444; white-space: nowrap; }
.pay-bar {
  margin-top: auto;
  text-align: center;
  font-weight: 800;
  font-size: 10.5pt;
  letter-spacing: 0.04em;
  padding: 1mm 1.4mm;
  border-radius: 0.6mm;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.pay-bar.cash {
  background: #b71c1c;
  color: #fff;
}
.pay-bar.prepaid {
  background: #e8f5e9;
  color: #1b5e20;
  border: 0.4pt solid #2e7d32;
  font-weight: 700;
  font-size: 8.5pt;
}
@media print {
  html, body, .label, .pay-bar { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .page { page-break-after: always; }
  .page:last-child { page-break-after: auto; }
}`
}

function buildSheetHtml({ deal, orders }) {
  const sorted = sortSelfDeliveryOrders(orders)
  const date = formatLabelDate(deal?.pickup_date)
  const logoUrl = `${window.location.origin}/logos/gsf-icon.png`
  const cells = sorted.map((order, index) => renderLabel(order, index, date, logoUrl))
  const pages = []
  for (let i = 0; i < cells.length; i += LABELS_PER_PAGE) {
    const chunk = cells.slice(i, i + LABELS_PER_PAGE)
    while (chunk.length < LABELS_PER_PAGE) chunk.push('<div class="label empty"></div>')
    pages.push(`<section class="page">${chunk.join('')}</section>`)
  }
  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>配送标签${deal?.title ? ` · ${escapeHtml(deal.title)}` : ''}</title>
  <style>${sheetCss()}</style>
</head>
<body>${pages.join('')}</body>
</html>`
}

export function printSelfDeliveryLabels({ deal, orders }) {
  const sorted = sortSelfDeliveryOrders(orders)
  if (!sorted.length) {
    return { ok: false, error: '暂无「我来送」订单' }
  }
  const win = window.open('', '_blank')
  if (!win) {
    return { ok: false, error: '无法打开打印窗口，请允许弹窗后重试' }
  }
  win.document.open()
  win.document.write(buildSheetHtml({ deal, orders: sorted }))
  win.document.close()

  let printed = false
  const triggerPrint = () => {
    if (printed) return
    printed = true
    win.focus()
    win.print()
  }

  const images = [...win.document.images]
  if (!images.length) {
    setTimeout(triggerPrint, 200)
    return { ok: true }
  }
  Promise.all(
    images.map(
      (img) =>
        new Promise((resolve) => {
          if (img.complete) {
            resolve()
            return
          }
          img.onload = resolve
          img.onerror = resolve
        })
    )
  ).then(() => setTimeout(triggerPrint, 80))
  setTimeout(triggerPrint, 1200)
  return { ok: true }
}
