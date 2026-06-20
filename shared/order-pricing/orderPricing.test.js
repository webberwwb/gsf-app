import { describe, it } from 'node:test'
import assert from 'node:assert/strict'
import { previewOrderTotals } from './orderPricing.js'

describe('previewOrderTotals', () => {
  const config = {
    tiers: [
      { threshold: 0, fee: 7.99 },
      { threshold: 150, fee: 0 }
    ]
  }

  it('amount_due = subtotal - credit + adjustment + shipping', () => {
    const t = previewOrderTotals({
      items: [{ product: {}, total_price: 100 }],
      deliveryMethod: 'delivery',
      shippingConfig: config,
      storeCredit: 10,
      adjustment: 5
    })
    assert.equal(t.subtotal, 100)
    assert.equal(t.credit, 10)
    assert.equal(t.adjustment, 5)
    assert.equal(t.shipping, 7.99)
    assert.equal(t.amountDue, 102.99)
  })

  it('admin discount reduces amount due', () => {
    const t = previewOrderTotals({
      items: [{ product: {}, total_price: 50 }],
      deliveryMethod: 'pickup',
      adjustment: -5
    })
    assert.equal(t.amountDue, 45)
  })
})
