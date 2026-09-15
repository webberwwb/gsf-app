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
  calculateShippingFee,
  matchRegionSurcharge
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

  it('excludes cutting fees from the product amount used for allocation', () => {
    const items = [
      {
        product: { counts_toward_free_shipping: true },
        total_price: 52,
        quantity: 1,
        cutting: true,
        cutting_fee: 2
      }
    ]
    assert.equal(eligibleTierSubtotalFromItems(items, 50), 50)
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

describe('region surcharges', () => {
  const config = {
    tiers: [
      { threshold: 0, fee: 7.99 },
      { threshold: 150, fee: 0 }
    ]
  }

  it('Waterloo / Kitchener / Guelph add $4', () => {
    assert.equal(matchRegionSurcharge(config, { city: 'Waterloo' }).surcharge, 4)
    assert.equal(matchRegionSurcharge(config, { city: 'kitchener' }).surcharge, 4)
    assert.equal(matchRegionSurcharge(config, { city: 'Guelph' }).surcharge, 4)
  })

  it('Whitby / Pickering / Ajax / Hamilton / Burlington add $2', () => {
    assert.equal(matchRegionSurcharge(config, { city: 'Whitby' }).surcharge, 2)
    assert.equal(matchRegionSurcharge(config, { city: 'Pickering' }).surcharge, 2)
    assert.equal(matchRegionSurcharge(config, { city: 'Ajax' }).surcharge, 2)
    assert.equal(matchRegionSurcharge(config, { city: 'Hamilton' }).surcharge, 2)
    assert.equal(matchRegionSurcharge(config, { city: 'Burlington' }).surcharge, 2)
  })

  it('Markham and unknown cities add $0', () => {
    assert.equal(matchRegionSurcharge(config, { city: 'Markham' }).surcharge, 0)
    assert.equal(matchRegionSurcharge(config, { city: 'Toronto' }).surcharge, 0)
    assert.equal(matchRegionSurcharge(config, { city: '' }).surcharge, 0)
    assert.equal(matchRegionSurcharge(config, null).surcharge, 0)
  })

  it('ignores old km-ring config and still uses city defaults', () => {
    const withRings = {
      ...config,
      distance_surcharges: [{ max_km: 10, surcharge: 99, label: 'near' }],
      beyond_surcharge: 12
    }
    assert.equal(matchRegionSurcharge(withRings, { city: 'Waterloo' }).surcharge, 4)
    assert.equal(matchRegionSurcharge(withRings, { city: 'Markham' }).surcharge, 0)
  })

  it('preview adds city surcharge on top of tier', () => {
    const fee = previewShippingFeeForOrder({
      items: [{ product: {}, total_price: 40 }],
      deliveryMethod: 'delivery',
      shippingConfig: config,
      address: { city: 'Waterloo' }
    })
    assert.equal(fee, 11.99)
  })

  it('free shipping waives only the 7.99 base, not the region delta', () => {
    const whitby = previewShippingFeeForOrder({
      items: [{ product: {}, total_price: 160 }],
      deliveryMethod: 'delivery',
      shippingConfig: config,
      address: { city: 'Whitby' }
    })
    const waterloo = previewShippingFeeForOrder({
      items: [{ product: {}, total_price: 160 }],
      deliveryMethod: 'delivery',
      shippingConfig: config,
      address: { city: 'Waterloo' }
    })
    const markham = previewShippingFeeForOrder({
      items: [{ product: {}, total_price: 160 }],
      deliveryMethod: 'delivery',
      shippingConfig: config,
      address: { city: 'Markham' }
    })
    assert.equal(whitby, 2)
    assert.equal(waterloo, 4)
    assert.equal(markham, 0)
  })

  it('pickup stays 0 with region surcharge', () => {
    assert.equal(
      previewShippingFeeForOrder({
        items: [{ product: {}, total_price: 40 }],
        deliveryMethod: 'pickup',
        shippingConfig: config,
        address: { city: 'Waterloo' }
      }),
      0
    )
  })
})

