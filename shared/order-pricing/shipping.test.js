/**
 * Node built-in test runner: node shipping.test.js
 * (also invoked from backend/run_tests.py)
 */
import { describe, it } from 'node:test'
import assert from 'node:assert/strict'
import {
  adjustmentDiscount,
  shippingTierBaseFromParts,
  eligibleTierSubtotalFromItems,
  previewShippingFeeForOrder,
  calculateShippingFee
} from './shipping.js'

describe('shipping tier base', () => {
  it('applies credit and admin discount only', () => {
    assert.equal(shippingTierBaseFromParts(100, 20, -10), 70)
  })

  it('ignores admin penalty for tier base', () => {
    assert.equal(shippingTierBaseFromParts(100, 0, 15), 100)
  })

  it('adjustmentDiscount helper', () => {
    assert.equal(adjustmentDiscount(10), 0)
    assert.equal(adjustmentDiscount(-10), -10)
  })
})

describe('eligible tier subtotal', () => {
  it('excludes non-counting products proportionally', () => {
    const items = [
      { product: { counts_toward_free_shipping: true }, total_price: 60 },
      { product: { counts_toward_free_shipping: false }, total_price: 40 }
    ]
    assert.equal(eligibleTierSubtotalFromItems(items, 80), 48)
  })
})

describe('previewShippingFeeForOrder', () => {
  const config = {
    tiers: [
      { threshold: 0, fee: 7.99 },
      { threshold: 150, fee: 0 }
    ]
  }

  it('pickup is free', () => {
    assert.equal(
      previewShippingFeeForOrder({
        items: [{ product: {}, total_price: 100 }],
        deliveryMethod: 'pickup',
        shippingConfig: config
      }),
      0
    )
  })

  it('credit reduces shipping tier', () => {
    const noCredit = previewShippingFeeForOrder({
      items: [{ product: {}, total_price: 160 }],
      deliveryMethod: 'delivery',
      shippingConfig: config,
      storeCredit: 0
    })
    const withCredit = previewShippingFeeForOrder({
      items: [{ product: {}, total_price: 160 }],
      deliveryMethod: 'delivery',
      shippingConfig: config,
      storeCredit: 20
    })
    assert.equal(noCredit, 0)
    assert.equal(withCredit, 7.99)
  })
})

describe('calculateShippingFee', () => {
  it('default free over 150', () => {
    assert.equal(calculateShippingFee(160, null), 0)
  })
})
