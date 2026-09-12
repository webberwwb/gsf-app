import { describe, it } from 'node:test'
import assert from 'node:assert/strict'
import {
  lookupBreakPrice,
  resolvePerItemUnit,
  estimateLinePrice,
  estimateAdminLinePrice,
  applyInfluencerDiscountToProduct,
  getSelectionQuantity,
  getVariantQuantity,
  setVariantQuantity,
  isSelectionComplete,
  buildPreviewLinesFromSelection,
  selectionsFromOrderItems,
  isOrderLinePriceEstimated,
  orderItemSelectionChanged,
  setCuttingQuantity,
  splitSelectionIntoOrderLines,
  cuttingFeesTotal
} from './orderItemPricing.js'

describe('quantity breaks', () => {
  it('uses the highest matching min_qty', () => {
    const breaks = [
      { min_qty: 3, price: 8 },
      { min_qty: 6, price: 7 }
    ]
    assert.equal(lookupBreakPrice(10, breaks, 1), 10)
    assert.equal(lookupBreakPrice(10, breaks, 3), 8)
    assert.equal(lookupBreakPrice(10, breaks, 6), 7)
  })

  it('pools mixed variant qty for shared-price breaks', () => {
    const product = {
      pricing_type: 'per_item',
      price: 10,
      pricing_data: { price: 10, quantity_breaks: [{ min_qty: 3, price: 8 }] },
      variants_share_price: true,
      variants: [
        { id: 1, name: 'A', price_delta: 0 },
        { id: 2, name: 'B', price_delta: 0 }
      ]
    }
    const a = estimateLinePrice(product, { quantity: 1, variant_id: 1, product_qty: 3 })
    const b = estimateLinePrice(product, { quantity: 2, variant_id: 2, product_qty: 3 })
    assert.equal(a.unitPrice, 8)
    assert.equal(a.totalPrice, 8)
    assert.equal(b.totalPrice, 16)
  })

  it('uses absolute variant price when not sharing', () => {
    const product = {
      pricing_type: 'per_item',
      price: 10,
      pricing_data: { price: 10 },
      variants_share_price: false,
      variants: [{ id: 1, name: 'A', price: 12, quantity_breaks: [{ min_qty: 3, price: 10 }] }]
    }
    const { unitPrice } = resolvePerItemUnit(product, product.variants[0], 3)
    assert.equal(unitPrice, 10)
  })
})

describe('sale price', () => {
  it('charges sale_price when the deal payload marks is_discount', () => {
    const product = {
      pricing_type: 'per_item',
      is_discount: true,
      price: 8,
      pricing_data: { price: 10, sale_price: 8 }
    }
    const { unitPrice } = resolvePerItemUnit(product, null, 1)
    assert.equal(unitPrice, 8)
  })

  it('ignores leftover sale_price when not on sale', () => {
    const product = {
      pricing_type: 'per_item',
      is_discount: false,
      price: 10,
      pricing_data: { price: 10, sale_price: 8 }
    }
    const { unitPrice } = resolvePerItemUnit(product, null, 1)
    assert.equal(unitPrice, 10)
  })

  it('applies influencer per_item on top of deal sale without double-counting', () => {
    const deal = {
      pricing_type: 'per_item',
      is_discount: true,
      pricing_data: { price: 16.99, sale_price: 14.99 }
    }
    const paid = applyInfluencerDiscountToProduct(deal, {
      commission_type: 'per_item',
      amount: 0.25
    })
    assert.equal(paid.influencer_discount, true)
    assert.equal(estimateAdminLinePrice(paid, { quantity: 1 }).unitPrice, 14.74)
    const again = applyInfluencerDiscountToProduct(paid, {
      commission_type: 'per_item',
      amount: 0.25
    })
    assert.equal(estimateAdminLinePrice(again, { quantity: 1 }).unitPrice, 14.74)
  })

  it('lets quantity breaks override the sale base', () => {
    const product = {
      pricing_type: 'per_item',
      is_discount: true,
      pricing_data: { price: 10, sale_price: 8, quantity_breaks: [{ min_qty: 3, price: 7 }] }
    }
    assert.equal(resolvePerItemUnit(product, null, 1).unitPrice, 8)
    assert.equal(resolvePerItemUnit(product, null, 3).unitPrice, 7)
  })
})

describe('mixed variant selection', () => {
  it('sums variant quantities', () => {
    let sel = setVariantQuantity({}, 1, 1)
    sel = setVariantQuantity(sel, 2, 2)
    assert.equal(getSelectionQuantity(sel), 3)
    assert.equal(sel.variant_quantities[1], 1)
    assert.equal(sel.variant_quantities[2], 2)
  })

  it('resets quantity to 0 when the last variant is cleared', () => {
    let sel = setVariantQuantity({}, 1, 2)
    assert.equal(getSelectionQuantity(sel), 2)
    sel = setVariantQuantity(sel, 1, 0)
    assert.equal(getSelectionQuantity(sel), 0)
    assert.equal(sel.quantity, 0)
    assert.equal(sel.variant_id, null)
    assert.equal(getVariantQuantity(sel, 1), 0)
  })

  it('does not reuse leftover quantity when the variant map is empty', () => {
    const leftover = { quantity: 1, variant_id: 1, variant_quantities: {} }
    assert.equal(getVariantQuantity(leftover, 1), 0)
    const sel = setVariantQuantity(leftover, 1, 0)
    assert.equal(getSelectionQuantity(sel), 0)
    assert.equal(sel.quantity, 0)
    assert.equal(sel.variant_id, null)
  })

  it('is complete when any variant has qty', () => {
    const product = { variants: [{ id: 1, name: 'A' }] }
    assert.equal(isSelectionComplete(product, { quantity: 0 }), true)
    assert.equal(isSelectionComplete(product, { variant_quantities: { 1: 1 }, quantity: 1 }), true)
  })

  it('builds one preview line per variant', () => {
    const product = {
      id: 9,
      pricing_type: 'per_item',
      price: 10,
      pricing_data: { price: 10 },
      variants: [
        { id: 1, name: 'A', price_delta: 0 },
        { id: 2, name: 'B', price_delta: 0 }
      ]
    }
    const lines = buildPreviewLinesFromSelection(
      [product],
      { 9: { variant_quantities: { 1: 1, 2: 2 }, quantity: 3 } }
    )
    assert.equal(lines.length, 2)
    assert.equal(lines[0].quantity, 1)
    assert.equal(lines[1].quantity, 2)
  })
})

describe('orderItemSelectionChanged', () => {
  it('treats pooled weight qty as unchanged vs N qty-1 lines', () => {
    assert.equal(
      orderItemSelectionChanged(
        [
          { product_id: 5, quantity: 1 },
          { product_id: 5, quantity: 1 },
          { product_id: 5, quantity: 1 }
        ],
        [{ product_id: 5, quantity: 3 }]
      ),
      false
    )
  })

  it('detects a real quantity change', () => {
    assert.equal(
      orderItemSelectionChanged(
        [{ product_id: 5, quantity: 2 }],
        [{ product_id: 5, quantity: 3 }]
      ),
      true
    )
  })
})

describe('selectionsFromOrderItems', () => {
  it('restores quantity for products without variants', () => {
    const next = selectionsFromOrderItems(
      [{ id: 11, product_id: 5, quantity: 3 }],
      { 5: { quantity: 0, variant_id: null, variant_quantities: {}, accept_substitute: null } }
    )
    assert.equal(next[5].quantity, 3)
    assert.equal(getSelectionQuantity(next[5]), 3)
    assert.equal(next[5].item_id, 11)
  })

  it('restores variant quantities and keeps other products empty', () => {
    const next = selectionsFromOrderItems(
      [
        { id: 21, product_id: 8, quantity: 1, variant_id: 101 },
        { id: 22, product_id: 8, quantity: 2, variant_id: 102 }
      ],
      {
        8: { quantity: 0, variant_id: null, variant_quantities: {}, accept_substitute: null },
        9: { quantity: 0, variant_id: null, variant_quantities: {}, accept_substitute: null }
      }
    )
    assert.equal(getSelectionQuantity(next[8]), 3)
    assert.equal(next[8].variant_quantities[101], 1)
    assert.equal(next[8].variant_quantities[102], 2)
    assert.equal(next[8].item_ids[101], 21)
    assert.equal(next[8].item_ids[102], 22)
    assert.equal(next[9].quantity, 0)
  })

  it('does not double quantities when applied twice', () => {
    const first = selectionsFromOrderItems([{ id: 31, product_id: 4, quantity: 2 }])
    const second = selectionsFromOrderItems([{ id: 31, product_id: 4, quantity: 2 }], first)
    assert.equal(second[4].quantity, 2)
  })

  it('restores weight and substitute preference', () => {
    const next = selectionsFromOrderItems([
      { id: 41, product_id: 7, quantity: 1, final_weight: 8.5, accept_substitute: true }
    ])
    assert.equal(next[7].weight, 8.5)
    assert.equal(next[7].accept_substitute, true)
  })
})

describe('cutting service', () => {
  const product = {
    id: 3,
    pricing_type: 'per_item',
    cutting_enabled: true,
    cutting_fee: 2,
    pricing_data: { price: 10 },
    variants: [
      { id: 1, name: '大', price_delta: 0 },
      { id: 2, name: '小', price_delta: 0 }
    ]
  }

  it('adds a flat per-piece fee, not to the variant rate', () => {
    const { unitPrice, totalPrice } = estimateLinePrice(product, {
      quantity: 2,
      variant_id: 1,
      cutting: true
    })
    assert.equal(unitPrice, 12)
    assert.equal(totalPrice, 24)
  })

  it('splits mixed cut / uncut qty into two lines', () => {
    let sel = setVariantQuantity({}, 1, 3)
    sel = setCuttingQuantity(sel, 1, 1)
    const lines = splitSelectionIntoOrderLines(product, sel)
    assert.equal(lines.length, 2)
    assert.deepEqual(
      lines.map((l) => ({ qty: l.quantity, cutting: l.cutting })),
      [
        { qty: 2, cutting: false },
        { qty: 1, cutting: true }
      ]
    )
  })

  it('does not offer cutting when the product flag is off', () => {
    const off = { ...product, cutting_enabled: false }
    let sel = setVariantQuantity({}, 1, 2)
    sel = setCuttingQuantity(sel, 2, 1)
    const lines = splitSelectionIntoOrderLines(off, sel)
    assert.equal(lines.length, 1)
    assert.equal(lines[0].cutting, false)
    assert.equal(lines[0].quantity, 2)
  })

  it('sums cutting fees for shipping/points exclusion', () => {
    assert.equal(
      cuttingFeesTotal([
        { cutting: true, cutting_fee: 2, quantity: 3, total_price: 36 },
        { cutting: false, cutting_fee: 2, quantity: 1, total_price: 10 }
      ]),
      6
    )
  })
})

describe('isOrderLinePriceEstimated', () => {
  const bundled = { pricing_type: 'bundled_weight' }

  it('is estimated when a weight product has no final_weight', () => {
    assert.equal(
      isOrderLinePriceEstimated({ product: bundled, total_price: 48.93, quantity: 1 }),
      true
    )
  })

  it('is final when staff entered final_weight', () => {
    assert.equal(
      isOrderLinePriceEstimated({ product: bundled, total_price: 62.1, final_weight: 8.5 }),
      false
    )
  })

  it('is not estimated for per-item products', () => {
    assert.equal(
      isOrderLinePriceEstimated({ product: { pricing_type: 'per_item' }, total_price: 10 }),
      false
    )
  })
})
