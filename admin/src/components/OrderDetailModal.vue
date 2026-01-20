<template>
  <div v-if="show" class="modal-overlay" @click="$emit('close')">
    <div class="modal-content order-detail-modal" @click.stop>
      <div class="modal-header">
        <div class="header-content">
          <div class="header-icon">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div class="header-text">
            <h2>订单详情</h2>
            <p class="order-number">{{ order?.order_number }}</p>
          </div>
          <div v-if="order" class="header-status-badges">
            <span class="payment-status-badge-header" :class="`payment-${order.payment_status}`">
              {{ getPaymentStatusText(order.payment_status) }}
            </span>
          </div>
          <button @click="$emit('close')" class="close-btn">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
      <div class="modal-body">
        <div v-if="order" class="order-detail-content">
          <div class="order-info-section">
            <div class="section-header">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3>订单信息</h3>
            </div>
            <div class="info-row">
              <div class="info-item-user">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <span class="value">{{ order.user?.nickname || order.user?.phone || 'N/A' }}</span>
                <span v-if="order.user?.wechat" class="wechat-badge">微信: {{ order.user.wechat }}</span>
                <button 
                  v-if="order.user && !order.user.is_admin" 
                  @click.stop="impersonateUser(order.user.id)" 
                  class="impersonate-btn-small"
                  title="代登录此用户">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  代登录
                </button>
              </div>
              <div class="info-item-price">
                <span class="value price">${{ parseFloat(order.total || 0).toFixed(2) }}</span>
              </div>
            </div>
            <div class="info-row">
              <div class="info-item-order-status">
                <label class="order-status-label">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="width: 18px; height: 18px;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  订单状态:
                </label>
                <select v-model="localOrderStatus" class="order-status-select" @change="handleOrderStatusChange">
                  <option value="submitted">已提交订单</option>
                  <option value="confirmed">已确认订单</option>
                  <option value="preparing">正在配货</option>
                  <option value="packing_complete">配货完成</option>
                  <option value="ready_for_pickup">可以取货</option>
                  <option value="out_for_delivery">正在配送</option>
                  <option value="completed">订单完成</option>
                  <option value="cancelled">已取消</option>
                </select>
              </div>
            </div>
            <div class="info-row">
              <div class="info-item-payment-method">
                <label class="payment-method-label">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="width: 18px; height: 18px;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                  </svg>
                  支付方式:
                </label>
                <select v-model="localPaymentMethod" class="payment-method-select" @change="handlePaymentMethodChange" :disabled="order && order.delivery_method === 'delivery'">
                  <option value="">未选择</option>
                  <option value="cash" :disabled="order && order.delivery_method === 'delivery'">现金</option>
                  <option value="etransfer">电子转账</option>
                </select>
              </div>
            </div>
            <!-- Mark as Paid Button (for EMT orders) -->
            <div class="info-row" v-if="order && localPaymentMethod === 'etransfer' && order.payment_status === 'unpaid'">
              <button @click="handleMarkAsPaid" class="mark-paid-btn">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="width: 18px; height: 18px;">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                标记为已付款
              </button>
            </div>
            <!-- Mark as Unpaid Button (for paid orders) -->
            <div class="info-row" v-if="order && order.payment_status === 'paid'">
              <button @click="handleMarkAsUnpaid" class="mark-unpaid-btn">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="width: 18px; height: 18px;">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                标记为未付款
              </button>
            </div>
          </div>

          <!-- Delivery Method Section -->
          <div class="order-info-section">
            <div class="section-header">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
              </svg>
              <h3>配送方式</h3>
            </div>
            <div class="info-row">
              <div class="delivery-method-selector">
                <label>
                  <input type="radio" v-model="localDeliveryMethod" value="pickup" name="delivery_method">
                  <span>自取</span>
                </label>
                <label>
                  <input type="radio" v-model="localDeliveryMethod" value="delivery" name="delivery_method">
                  <span>配送</span>
                </label>
              </div>
            </div>
            
            <!-- Pickup Location Selection -->
            <div v-if="localDeliveryMethod === 'pickup'" class="info-row">
              <div class="pickup-location-selector">
                <label class="field-label">取货点:</label>
                <select v-model="localPickupLocation" class="pickup-location-select">
                  <option value="">请选择取货点</option>
                  <option value="markham">Markham</option>
                  <option value="northyork">North York</option>
                  <option value="scarborough">Scarborough</option>
                  <option value="downtown">Downtown</option>
                </select>
              </div>
            </div>
            
            <!-- Delivery Address Selection -->
            <div v-if="localDeliveryMethod === 'delivery'" class="info-row">
              <div class="address-management">
                <div class="address-header">
                  <label class="field-label">配送地址:</label>
                  <div class="address-actions">
                    <button @click="loadUserAddresses" class="refresh-addresses-btn" :disabled="loadingAddresses">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    </button>
                    <button @click="showAddAddressForm = true" class="add-address-btn">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
                      </svg>
                      添加地址
                    </button>
                  </div>
                </div>
                
                <div v-if="loadingAddresses" class="loading-addresses">加载地址中...</div>
                <div v-else-if="userAddresses.length === 0 && !showAddAddressForm" class="no-addresses">
                  用户暂无保存的地址，请添加新地址
                </div>
                <div v-else class="addresses-list">
                  <div 
                    v-for="address in userAddresses" 
                    :key="address.id"
                    :class="['address-item', { 'selected': localAddressId === address.id }]"
                    @click="selectAddress(address.id)">
                    <div class="address-radio">
                      <input type="radio" :checked="localAddressId === address.id" readonly>
                    </div>
                    <div class="address-content">
                      <div class="address-line">{{ address.address_line1 }}</div>
                      <div v-if="address.address_line2" class="address-line">{{ address.address_line2 }}</div>
                      <div class="address-city">{{ address.city }}, {{ address.postal_code }}</div>
                    </div>
                  </div>
                </div>
                
                <!-- Add New Address Form -->
                <div v-if="showAddAddressForm" class="add-address-form">
                  <div class="form-header">
                    <h4>添加新地址</h4>
                    <button @click="cancelAddAddress" class="cancel-form-btn">×</button>
                  </div>
                  <div class="form-group">
                    <label>地址第一行 *</label>
                    <input v-model="newAddress.address_line1" type="text" placeholder="街道地址" class="form-input" required>
                  </div>
                  <div class="form-group">
                    <label>地址第二行</label>
                    <input v-model="newAddress.address_line2" type="text" placeholder="公寓、单元等" class="form-input">
                  </div>
                  <div class="form-row">
                    <div class="form-group">
                      <label>城市 *</label>
                      <input v-model="newAddress.city" type="text" placeholder="城市" class="form-input" required>
                    </div>
                    <div class="form-group">
                      <label>邮编 *</label>
                      <input v-model="newAddress.postal_code" type="text" placeholder="M1A 2B3" class="form-input" required>
                    </div>
                  </div>
                  <div class="form-actions">
                    <button @click="saveNewAddress" class="save-address-btn" :disabled="savingAddress || !isAddressValid">
                      {{ savingAddress ? '保存中...' : '保存地址' }}
                    </button>
                  </div>
                  <div v-if="addressError" class="address-error">{{ addressError }}</div>
                </div>
              </div>
            </div>
          </div>

          <div class="order-items-section">
            <div class="section-header">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
              <h3>商品列表</h3>
              <button @click="openAddProductModal" class="add-item-btn">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="width: 18px; height: 18px;">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
                </svg>
                添加商品
              </button>
            </div>
            <div class="items-list">
              <div v-for="(item, index) in editableItems" :key="item.tempId || item.id" class="order-item-row">
                <div class="item-info">
                  <div class="item-name">
                    {{ item.product?.name || 'N/A' }}
                    <div v-if="item.product" class="product-info-icon" @click.stop title="查看价格详情">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <div class="price-tooltip">
                        <div class="tooltip-content">
                          <div class="tooltip-header">{{ item.product.name }}</div>
                          <div class="tooltip-body">
                            <div class="tooltip-row">
                              <span class="tooltip-label">定价类型:</span>
                              <span class="tooltip-value">{{ formatPricingType(item.product.pricing_type) }}</span>
                            </div>
                            <div class="tooltip-divider"></div>
                            <div v-if="item.product.pricing_type === 'per_item'" class="tooltip-row">
                              <span class="tooltip-label">价格:</span>
                              <span class="tooltip-value">${{ item.product.pricing_data?.price?.toFixed(2) }}</span>
                            </div>
                            <div v-else-if="item.product.pricing_type === 'weight_range'" class="tooltip-section">
                              <div class="tooltip-label">价格区间:</div>
                              <div v-for="(range, idx) in item.product.pricing_data?.ranges" :key="idx" class="tooltip-range">
                                <span>{{ range.min }}{{ range.max ? ` - ${range.max}` : '+' }} {{ item.product.pricing_data?.unit || 'lb' }}:</span>
                                <span class="tooltip-price">${{ range.price?.toFixed(2) }}/{{ item.product.pricing_data?.unit || 'lb' }}</span>
                              </div>
                            </div>
                            <div v-else-if="item.product.pricing_type === 'unit_weight'" class="tooltip-row">
                              <span class="tooltip-label">单价:</span>
                              <span class="tooltip-value">${{ item.product.pricing_data?.price_per_unit?.toFixed(2) }}/{{ item.product.pricing_data?.unit || 'lb' }}</span>
                            </div>
                            <div v-else-if="item.product.pricing_type === 'bundled_weight'" class="tooltip-section">
                              <div class="tooltip-row">
                                <span class="tooltip-label">单价:</span>
                                <span class="tooltip-value">${{ item.product.pricing_data?.price_per_unit?.toFixed(2) }}/{{ item.product.pricing_data?.unit || 'lb' }}</span>
                              </div>
                              <div class="tooltip-row">
                                <span class="tooltip-label">重量范围:</span>
                                <span class="tooltip-value">{{ item.product.pricing_data?.min_weight }} - {{ item.product.pricing_data?.max_weight }} {{ item.product.pricing_data?.unit || 'lb' }}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="item-meta">
                    <div class="quantity-controls">
                      <button @click="decreaseQuantity(index)" class="qty-btn" :disabled="item.quantity <= 1">-</button>
                      <input 
                        type="number" 
                        v-model.number="item.quantity" 
                        @input="recalculateItemPrice(index)"
                        min="1"
                        class="quantity-input" />
                      <button @click="increaseQuantity(index)" class="qty-btn">+</button>
                    </div>
                    <span class="item-price">${{ parseFloat(item.total_price || 0).toFixed(2) }}</span>
                  </div>
                  <div v-if="item.product?.pricing_type === 'weight_range' || item.product?.pricing_type === 'unit_weight' || item.product?.pricing_type === 'bundled_weight'" class="weight-input-group">
                    <label>
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
                      </svg>
                      <span v-if="item.product?.pricing_type === 'bundled_weight'">总重量</span>
                      <span v-else>实际重量</span>
                      ({{ item.product?.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }})
                    </label>
                    <input 
                      type="number" 
                      step="0.001"
                      v-model.number="item.final_weight"
                      @input="recalculateItemPrice(index)"
                      :placeholder="item.final_weight ? item.final_weight.toString() : '输入重量'"
                      class="weight-input" />
                  </div>
                </div>
                <button @click="removeItem(index)" class="remove-item-btn" title="删除商品">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
          
          <!-- Add Product Modal -->
          <div v-if="showAddProductModal" class="modal-overlay-inner" @click.stop>
            <div class="modal-content-inner" @click.stop>
              <div class="modal-header-inner">
                <h3>选择商品</h3>
                <button @click="showAddProductModal = false" class="close-btn-small">×</button>
              </div>
              <div class="modal-body-inner">
                <div v-if="loadingProducts" class="empty-products">加载中...</div>
                <div v-else-if="availableProducts.length === 0" class="empty-products">暂无可用商品</div>
                <div v-else class="products-list">
                  <div 
                    v-for="product in availableProducts" 
                    :key="product.id"
                    @click="addProductToOrder(product)"
                    class="product-item"
                    :class="{ 'out-of-stock': isOutOfStock(product) }">
                    <div class="product-name">{{ product.name }}</div>
                    <div class="product-info">
                      <div class="product-price">${{ parseFloat(product.price || 0).toFixed(2) }}</div>
                      <div v-if="isOutOfStock(product)" class="out-of-stock-badge">缺货</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="updateError" class="error-message">{{ updateError }}</div>
        </div>
      </div>
      <div class="modal-footer">
        <button 
          v-if="order && order.status !== 'completed'"
          @click="$emit('mark-complete', order)" 
          class="complete-order-btn"
          :disabled="updatingOrder || markingComplete">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="width: 18px; height: 18px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {{ markingComplete ? '处理中...' : '标记订单完成' }}
        </button>
        <button 
          @click="handleUpdateOrder" 
          class="update-order-btn"
          :disabled="updatingOrder || markingComplete">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="width: 18px; height: 18px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {{ updatingOrder ? '更新中...' : '更新订单' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'
import { useModal } from '../composables/useModal'

export default {
  name: 'OrderDetailModal',
  setup() {
    const { confirm, success, error } = useModal()
    return { confirm, success, error }
  },
  props: {
    show: {
      type: Boolean,
      default: false
    },
    order: {
      type: Object,
      default: null
    },
    availableProducts: {
      type: Array,
      default: () => []
    },
    updatingOrder: {
      type: Boolean,
      default: false
    },
    markingComplete: {
      type: Boolean,
      default: false
    },
    updateError: {
      type: String,
      default: null
    }
  },
  emits: ['close', 'update', 'mark-paid', 'mark-unpaid', 'mark-complete', 'status-change', 'payment-method-change', 'order-updated', 'update-error', 'products-loaded'],
  data() {
    return {
      localOrderStatus: '',
      localPaymentMethod: '',
      localDeliveryMethod: '',
      localPickupLocation: '',
      localAddressId: null,
      userAddresses: [],
      loadingAddresses: false,
      showAddAddressForm: false,
      savingAddress: false,
      addressError: null,
      newAddress: {
        address_line1: '',
        address_line2: '',
        city: '',
        postal_code: ''
      },
      editableItems: [],
      showAddProductModal: false,
      tempIdCounter: 0,
      isInitializingOrder: false,
      lastOrderId: null, // Track last initialized order ID to prevent duplicate initialization
      loadingProducts: false // Track if products are being loaded
    }
  },
  computed: {
    isAddressValid() {
      return this.newAddress.address_line1 && 
             this.newAddress.city && 
             this.newAddress.postal_code
    }
  },
  watch: {
    show(newVal) {
      if (newVal && this.order) {
        this.initializeOrder()
      } else if (!newVal) {
        this.resetModal()
      }
    },
    // Watch order.id instead of deep watching the entire object for better performance
    'order.id'(newId, oldId) {
      // Only reinitialize if order actually changed and modal is visible
      if (newId && newId !== oldId && this.show) {
        this.initializeOrder()
      }
    },
    // Watch for order.items changes - this handles updates to the same order
    // This is a backup - the parent should explicitly call updateOrderData
    'order.items': {
      handler(newItems, oldItems) {
        // If modal is open and this is the same order (ID matches lastOrderId)
        if (this.show && this.order && this.order.id === this.lastOrderId && !this.isInitializingOrder) {
          // Only update if items actually changed and we have complete data
          if (newItems && Array.isArray(newItems) && newItems.length >= 0) {
            // Small delay to avoid race conditions with explicit calls
            this.$nextTick(() => {
              if (!this.isInitializingOrder) {
                this.updateOrderData(this.order)
              }
            })
          }
        }
      },
      deep: true,
      immediate: false
    },
    localPaymentMethod(newVal, oldVal) {
      // Auto-mark as paid when cash is selected and order is unpaid
      // Don't trigger for cancelled orders or during initialization
      if (!this.isInitializingOrder && 
          newVal === 'cash' && 
          oldVal !== 'cash' && 
          this.order && 
          this.order.payment_status === 'unpaid' &&
          this.order.status !== 'cancelled') {
        this.$emit('payment-method-change', 'cash')
      }
    },
    localDeliveryMethod(newVal, oldVal) {
      if (this.isInitializingOrder) return
      
      // When switching to delivery, force etransfer and load addresses
      if (newVal === 'delivery') {
        this.localPaymentMethod = 'etransfer'
        if (this.order?.user_id && this.userAddresses.length === 0) {
          this.loadUserAddresses()
        }
      }
      
      // When switching to pickup, clear address selection
      if (newVal === 'pickup') {
        this.localAddressId = null
      }
    }
  },
  methods: {
    initializeOrder() {
      if (!this.order || !this.show) {
        return
      }
      
      // Prevent duplicate initialization for the same order
      if (this.order.id === this.lastOrderId && this.editableItems.length > 0) {
        return
      }
      
      // Set lastOrderId even if items aren't available yet (so watcher can detect updates)
      this.lastOrderId = this.order.id
      
      // Don't initialize if order doesn't have items yet (incomplete data)
      if (!this.order.items || !Array.isArray(this.order.items)) {
        // Wait for complete data - this will be handled by the order.items watcher
        this.isInitializingOrder = false
        return
      }
      
      this.isInitializingOrder = true
      
      // Initialize editable items
      this.editableItems = []
      if (this.order.items && Array.isArray(this.order.items)) {
        this.order.items.forEach(item => {
          // Check if product is weight-based
          const isWeightBased = item.product?.pricing_type === 'weight_range' || 
                               item.product?.pricing_type === 'unit_weight' || 
                               item.product?.pricing_type === 'bundled_weight'
          
          // For weight-based products with quantity > 1, split into separate items
          if (isWeightBased && item.quantity > 1) {
            // Create separate items for each unit
            for (let i = 0; i < item.quantity; i++) {
              if (i === 0) {
                // First item: keep original ID for update
                this.editableItems.push({
                  ...item,
                  tempId: item.id,
                  quantity: 1,
                  final_weight: item.final_weight ? parseFloat(item.final_weight) : null
                })
              } else {
                // Subsequent items: create new items (no ID, will be created on save)
                this.editableItems.push({
                  ...item,
                  id: undefined, // Remove ID so it's treated as new
                  tempId: `temp_${++this.tempIdCounter}`,
                  quantity: 1,
                  final_weight: null // Each needs its own weight
                })
              }
            }
          } else {
            // For non-weight-based or single quantity items, add as-is
            this.editableItems.push({
              ...item,
              tempId: item.id,
              final_weight: item.final_weight ? parseFloat(item.final_weight) : null
            })
          }
        })
      }
      
      // Initialize order status
      this.localOrderStatus = this.order.status || 'submitted'
      
      // Initialize payment method (watcher will check isInitializingOrder flag)
      // If delivery method is delivery, ensure payment is etransfer
      if (this.order.delivery_method === 'delivery') {
        this.localPaymentMethod = 'etransfer'
      } else {
        this.localPaymentMethod = this.order.payment_method || ''
      }
      
      // Initialize delivery method and location
      this.localDeliveryMethod = this.order.delivery_method || 'pickup'
      this.localPickupLocation = this.order.pickup_location || ''
      this.localAddressId = this.order.address_id || null
      
      // Load user addresses if delivery method is delivery
      if (this.localDeliveryMethod === 'delivery' && this.order.user_id) {
        this.loadUserAddresses()
      }
      
      // lastOrderId was already set above
      
      // Reset initialization flag after watcher has had chance to see it
      // Use nextTick to ensure watcher checks complete before we clear the flag
      this.$nextTick(() => {
        this.isInitializingOrder = false
      })
    },
    resetModal() {
      this.localOrderStatus = ''
      this.localPaymentMethod = ''
      this.localDeliveryMethod = ''
      this.localPickupLocation = ''
      this.localAddressId = null
      this.userAddresses = []
      this.loadingAddresses = false
      this.showAddAddressForm = false
      this.savingAddress = false
      this.addressError = null
      this.newAddress = {
        address_line1: '',
        address_line2: '',
        city: '',
        postal_code: ''
      }
      this.editableItems = []
      this.showAddProductModal = false
      this.tempIdCounter = 0
      this.isInitializingOrder = false
      this.lastOrderId = null
      this.loadingProducts = false
    },
    updateOrderData(updatedOrder) {
      // Update local state from updated order without full reinitialization
      // This is called when the same order is updated (ID stays the same)
      if (!updatedOrder) {
        return
      }
      
      // Don't update if we're currently initializing
      if (this.isInitializingOrder) {
        return
      }
      
      // Ensure we have items - if not, wait for complete data
      if (!updatedOrder.items || !Array.isArray(updatedOrder.items)) {
        console.warn('Order update received without items, waiting for complete data')
        return
      }
      
      // Update editable items from order items
      this.editableItems = []
      updatedOrder.items.forEach(item => {
        // Check if product is weight-based
        const isWeightBased = item.product?.pricing_type === 'weight_range' || 
                             item.product?.pricing_type === 'unit_weight' || 
                             item.product?.pricing_type === 'bundled_weight'
        
        // For weight-based products with quantity > 1, split into separate items
        if (isWeightBased && item.quantity > 1) {
          // Create separate items for each unit
          for (let i = 0; i < item.quantity; i++) {
            if (i === 0) {
              // First item: keep original ID for update
              this.editableItems.push({
                ...item,
                tempId: item.id,
                quantity: 1,
                final_weight: item.final_weight ? parseFloat(item.final_weight) : null
              })
            } else {
              // Subsequent items: create new items (no ID, will be created on save)
              this.editableItems.push({
                ...item,
                id: undefined, // Remove ID so it's treated as new
                tempId: `temp_${++this.tempIdCounter}`,
                quantity: 1,
                final_weight: null // Each needs its own weight
              })
            }
          }
        } else {
          // For non-weight-based or single quantity items, add as-is
          this.editableItems.push({
            ...item,
            tempId: item.id,
            final_weight: item.final_weight ? parseFloat(item.final_weight) : null
          })
        }
      })
      
      // Update order status and payment method (preserve current values if not provided)
      if (updatedOrder.status !== undefined) {
        this.localOrderStatus = updatedOrder.status
      }
      if (updatedOrder.payment_method !== undefined) {
        this.localPaymentMethod = updatedOrder.payment_method || ''
      }
      
      // Update lastOrderId to prevent reinitialization
      if (updatedOrder.id) {
        this.lastOrderId = updatedOrder.id
      }
    },
    async openAddProductModal() {
      // If products are already loaded, just show the modal
      if (this.availableProducts && this.availableProducts.length > 0) {
        this.showAddProductModal = true
        return
      }
      
      // Otherwise, load products first
      if (!this.order?.group_deal_id) {
        await this.error('无法加载商品：订单没有关联的团购活动')
        return
      }
      
      this.loadingProducts = true
      try {
        const response = await apiClient.get(`/admin/group-deals/${this.order.group_deal_id}`)
        const products = response.data.group_deal?.products || []
        
        // Emit event to update parent's availableProducts
        this.$emit('products-loaded', products)
        
        // Show modal after products are loaded
        this.showAddProductModal = true
      } catch (error) {
        console.error('Failed to load products:', error)
        await this.error('加载商品失败，请稍后重试')
      } finally {
        this.loadingProducts = false
      }
    },
    addProductToOrder(product) {
      // For weight-based products, always create a new item (don't stack) because each can have different weight
      const isWeightBased = product.pricing_type === 'weight_range' || 
                           product.pricing_type === 'unit_weight' || 
                           product.pricing_type === 'bundled_weight'
      
      if (!isWeightBased) {
        // For non-weight-based products, check if product already exists in order
        const existingIndex = this.editableItems.findIndex(item => item.product_id === product.id)
        if (existingIndex >= 0) {
          // Increase quantity if already exists
          this.editableItems[existingIndex].quantity += 1
          this.recalculateItemPrice(existingIndex)
          this.showAddProductModal = false
          return
        }
      }
      
      // Add new item (always for weight-based products, or if product doesn't exist for non-weight-based)
      let initialPrice = 0
      if (product.pricing_type === 'per_item') {
        initialPrice = parseFloat(product.price || 0)
      }
      
      this.editableItems.push({
        tempId: `temp_${++this.tempIdCounter}`,
        product_id: product.id,
        product: product,
        quantity: 1,
        unit_price: initialPrice,
        total_price: initialPrice,
        final_weight: null
      })
      this.showAddProductModal = false
    },
    removeItem(index) {
      this.editableItems.splice(index, 1)
    },
    increaseQuantity(index) {
      this.editableItems[index].quantity += 1
      this.recalculateItemPrice(index)
    },
    decreaseQuantity(index) {
      if (this.editableItems[index].quantity > 1) {
        this.editableItems[index].quantity -= 1
        this.recalculateItemPrice(index)
      }
    },
    recalculateItemPrice(index) {
      const item = this.editableItems[index]
      const product = item.product
      
      if (!product) return
      
      // If weight-based product
      if (product.pricing_type === 'weight_range' || product.pricing_type === 'unit_weight' || product.pricing_type === 'bundled_weight') {
        // Must have final_weight to calculate price
        if (!item.final_weight || item.final_weight <= 0) {
          item.unit_price = 0
          item.total_price = 0
          return
        }
        
        // For weight_range, find the matching range
        if (product.pricing_type === 'weight_range') {
          if (product.pricing_data && product.pricing_data.ranges && Array.isArray(product.pricing_data.ranges)) {
            const ranges = product.pricing_data.ranges
            let matchedPrice = 0
            for (const range of ranges) {
              const min = range.min || 0
              const max = range.max
              if (item.final_weight >= min && (max === null || max === undefined || item.final_weight < max)) {
                matchedPrice = parseFloat(range.price || 0)
                break
              }
            }
            item.unit_price = matchedPrice
            item.total_price = matchedPrice * item.quantity
          } else {
            const basePrice = parseFloat(product.price || 0)
            item.unit_price = basePrice
            item.total_price = basePrice * item.quantity
          }
        } else if (product.pricing_type === 'unit_weight') {
          if (product.pricing_data && product.pricing_data.price_per_unit) {
            const pricePerUnit = parseFloat(product.pricing_data.price_per_unit || 0)
            item.unit_price = pricePerUnit * item.final_weight
            item.total_price = pricePerUnit * item.final_weight * item.quantity
          } else {
            const pricePerUnit = parseFloat(product.price || 0)
            item.unit_price = pricePerUnit * item.final_weight
            item.total_price = pricePerUnit * item.final_weight * item.quantity
          }
        } else if (product.pricing_type === 'bundled_weight') {
          // Bundled weight: final_weight is total weight for all packages
          // Price = price_per_unit * final_weight
          // unit_price = total_price / quantity
          if (product.pricing_data && product.pricing_data.price_per_unit) {
            const pricePerUnit = parseFloat(product.pricing_data.price_per_unit || 0)
            item.total_price = pricePerUnit * item.final_weight
            item.unit_price = item.total_price / item.quantity
          } else {
            const pricePerUnit = parseFloat(product.price || 0)
            item.total_price = pricePerUnit * item.final_weight
            item.unit_price = item.total_price / item.quantity
          }
        }
      } else {
        // Regular pricing (per_item)
        const unitPrice = parseFloat(product.price || 0)
        item.unit_price = unitPrice
        item.total_price = unitPrice * item.quantity
      }
    },
    handleUpdateOrder() {
      if (!this.order || this.editableItems.length === 0) {
        this.$emit('update-error', '订单必须至少包含一个商品')
        return
      }
      
      // Validate delivery settings
      if (this.localDeliveryMethod === 'pickup' && !this.localPickupLocation) {
        this.$emit('update-error', '请选择取货点')
        return
      }
      
      if (this.localDeliveryMethod === 'delivery' && !this.localAddressId) {
        this.$emit('update-error', '请选择配送地址')
        return
      }
      
      const items = this.editableItems.map(item => ({
        product_id: item.product_id,
        quantity: item.quantity,
        final_weight: item.final_weight || null
      }))
      
      const updateData = {
        items: items,
        delivery_method: this.localDeliveryMethod
      }
      
      if (this.localPaymentMethod) {
        updateData.payment_method = this.localPaymentMethod
      }
      
      if (this.localDeliveryMethod === 'pickup') {
        updateData.pickup_location = this.localPickupLocation
      } else if (this.localDeliveryMethod === 'delivery') {
        updateData.address_id = this.localAddressId
        // Force payment method to etransfer for delivery
        updateData.payment_method = 'etransfer'
      }
      
      this.$emit('update', this.order.id, updateData)
    },
    handleOrderUpdated(order) {
      // Update local state when order is updated from parent
      if (order && order.id === this.order?.id) {
        // Reset lastOrderId to force re-initialization
        this.lastOrderId = null
        this.initializeOrder()
      }
    },
    handleOrderStatusChange() {
      if (!this.order || !this.localOrderStatus) {
        return
      }
      
      if (this.localOrderStatus === this.order.status) {
        return
      }
      
      this.$emit('status-change', this.order.id, this.localOrderStatus)
    },
    isOutOfStock(product) {
      // Check deal_stock_limit (deal-specific inventory) first, then stock_limit (product-level inventory)
      // null or undefined means unlimited stock, only 0 means out of stock
      // Admin can still add out-of-stock products, this is just for visual indication
      const inventory = (product.deal_stock_limit !== undefined && product.deal_stock_limit !== null)
        ? product.deal_stock_limit
        : (product.stock_limit !== undefined && product.stock_limit !== null ? product.stock_limit : null)
      
      return inventory === 0
    },
    handlePaymentMethodChange() {
      if (this.localPaymentMethod === 'cash' && this.order && this.order.payment_status === 'unpaid') {
        this.$emit('payment-method-change', 'cash')
      }
    },
    handleMarkAsPaid() {
      // Emit only the order ID and payment method, not the entire order object
      if (this.order && this.localPaymentMethod) {
        this.$emit('mark-paid', {
          orderId: this.order.id,
          paymentMethod: this.localPaymentMethod
        })
      }
    },
    handleMarkAsUnpaid() {
      // Emit order ID to mark as unpaid
      if (this.order) {
        this.$emit('mark-unpaid', {
          orderId: this.order.id
        })
      }
    },
    getPaymentStatusText(paymentStatus) {
      const paymentMap = {
        'unpaid': '未付款',
        'paid': '已付款'
      }
      return paymentMap[paymentStatus] || paymentStatus
    },
    async impersonateUser(userId) {
      const confirmed = await this.confirm('确定要以该用户身份登录吗？您将被重定向到用户端应用，可以直接修改订单。', {
        type: 'warning',
        title: '代登录确认'
      })
      if (!confirmed) {
        return
      }

      try {
        const response = await apiClient.post(`/admin/users/${userId}/impersonate`)
        const { redirect_url } = response.data
        
        // Redirect to app frontend with token
        window.location.href = redirect_url
      } catch (error) {
        await this.error(error.response?.data?.message || error.response?.data?.error || '代登录失败')
        console.error('Impersonate user error:', error)
      }
    },
    async loadUserAddresses() {
      if (!this.order?.user_id) return
      
      this.loadingAddresses = true
      try {
        const response = await apiClient.get(`/admin/users/${this.order.user_id}/addresses`)
        this.userAddresses = response.data.addresses || []
      } catch (error) {
        console.error('Failed to load user addresses:', error)
        this.userAddresses = []
      } finally {
        this.loadingAddresses = false
      }
    },
    selectAddress(addressId) {
      this.localAddressId = addressId
      this.showAddAddressForm = false
    },
    cancelAddAddress() {
      this.showAddAddressForm = false
      this.addressError = null
      this.newAddress = {
        address_line1: '',
        address_line2: '',
        city: '',
        postal_code: ''
      }
    },
    async saveNewAddress() {
      if (!this.isAddressValid) return
      if (!this.order?.user_id) {
        this.addressError = '无法获取用户信息'
        return
      }
      
      this.savingAddress = true
      this.addressError = null
      
      try {
        const response = await apiClient.post(`/admin/users/${this.order.user_id}/addresses`, this.newAddress)
        const savedAddress = response.data.address
        
        // Add to addresses list
        this.userAddresses.unshift(savedAddress)
        
        // Select the new address
        this.localAddressId = savedAddress.id
        
        // Reset form
        this.showAddAddressForm = false
        this.newAddress = {
          address_line1: '',
          address_line2: '',
          city: '',
          postal_code: ''
        }
        
        await this.success('地址已添加')
      } catch (error) {
        this.addressError = error.response?.data?.message || error.response?.data?.error || '保存地址失败'
        console.error('Failed to save address:', error)
      } finally {
        this.savingAddress = false
      }
    },
    formatPricingType(pricingType) {
      const typeMap = {
        'per_item': '按件计价',
        'weight_range': '按重量区间计价',
        'unit_weight': '按单位重量计价',
        'bundled_weight': '按捆绑重量计价'
      }
      return typeMap[pricingType] || pricingType
    }
  }
}
</script>

<style scoped>
/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--md-spacing-md);
}

.modal-content {
  background: #FFFFFF;
  border-radius: 24px;
  max-width: 800px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0px 11px 15px -7px rgba(0, 0, 0, 0.2), 0px 24px 38px 3px rgba(0, 0, 0, 0.14), 0px 9px 46px 8px rgba(0, 0, 0, 0.12);
  overflow: visible;
}

.order-detail-modal {
  max-width: 900px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  background: var(--gradient-primary);
  border-bottom: 1px solid rgba(255, 165, 0, 0.2);
  border-radius: 24px 24px 0 0;
}

.header-content {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
  width: 100%;
}

.header-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 10px;
  color: #FF8C00;
}

.header-icon svg {
  width: 20px;
  height: 20px;
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.header-status-badges {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  margin-left: auto;
}

.payment-status-badge-header {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.payment-status-badge-header.payment-unpaid {
  background: #FFF3E0;
  color: #E65100;
}

.payment-status-badge-header.payment-paid {
  background: #E8F5E9;
  color: #1B5E20;
}

.modal-header h2 {
  font-size: 1.125rem;
  color: rgba(0, 0, 0, 0.9);
  font-weight: 600;
  margin: 0;
}

.order-number {
  font-size: 0.8125rem;
  color: rgba(0, 0, 0, 0.7);
  font-family: 'Courier New', monospace;
  margin: 0;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: rgba(0, 0, 0, 0.7);
  cursor: pointer;
  border-radius: var(--md-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn svg {
  width: 20px;
  height: 20px;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  color: rgba(0, 0, 0, 0.9);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--md-spacing-md);
  background: #FAFAFA;
}

.modal-footer {
  display: flex;
  gap: var(--md-spacing-md);
  padding: var(--md-spacing-md);
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  background: #FFFFFF;
  border-radius: 0 0 24px 24px;
}

.update-order-btn {
  flex: 1;
  padding: 10px 24px;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.1px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(230, 81, 0, 0.2);
  background: #FFF3E0;
  color: #E65100;
  min-height: 40px;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  position: relative;
  overflow: hidden;
  outline: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.update-order-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(230, 81, 0, 0.1);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s, opacity 0.3s;
  opacity: 0;
}

.update-order-btn:hover:not(:disabled) {
  background: #FFE0B2;
  border-color: rgba(230, 81, 0, 0.4);
  box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.16), 0px 3px 6px rgba(0, 0, 0, 0.23);
  transform: translateY(-1px);
}

.update-order-btn:active:not(:disabled) {
  background: #FFCC80;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  transform: translateY(0);
}

.update-order-btn:active:not(:disabled)::before {
  width: 300px;
  height: 300px;
  opacity: 1;
  transition: width 0s, height 0s, opacity 0.3s;
}

.update-order-btn:disabled {
  opacity: 0.38;
  cursor: not-allowed;
  box-shadow: none;
}

/* Add Product Modal Styles */
.modal-overlay-inner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: var(--md-spacing-md);
}

.modal-content-inner {
  background: #FFFFFF;
  border-radius: 16px;
  max-width: 500px;
  width: 100%;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0px 11px 15px -7px rgba(0, 0, 0, 0.2), 0px 24px 38px 3px rgba(0, 0, 0, 0.14), 0px 9px 46px 8px rgba(0, 0, 0, 0.12);
  overflow: hidden;
}

.modal-header-inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.modal-header-inner h3 {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
}

.close-btn-small {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: rgba(0, 0, 0, 0.7);
  cursor: pointer;
  border-radius: 50%;
  font-size: 24px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn-small:hover {
  background: rgba(0, 0, 0, 0.05);
}

.modal-body-inner {
  flex: 1;
  overflow-y: auto;
  padding: var(--md-spacing-md);
}

.products-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
}

.product-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  background: #F5F5F5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.product-item:hover {
  background: #EEEEEE;
  transform: translateX(4px);
}

.product-item.out-of-stock {
  border-left: 3px solid #FF9800;
}

.product-name {
  font-weight: 500;
  color: rgba(0, 0, 0, 0.87);
}

.product-info {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
}

.product-price {
  font-weight: 600;
  color: #E65100;
}

.out-of-stock-badge {
  padding: 2px 8px;
  background: #FF9800;
  color: white;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.empty-products {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.order-detail-content {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
  overflow: visible;
}

.order-info-section,
.order-items-section {
  background: #FFFFFF;
  border-radius: 12px;
  padding: var(--md-spacing-md);
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.08), 0px 1px 2px rgba(0, 0, 0, 0.06);
  overflow: visible;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--md-spacing-xs);
  margin-bottom: var(--md-spacing-sm);
  padding-bottom: var(--md-spacing-xs);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.add-item-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #E8F5E9;
  color: #2E7D32;
  border: 1px solid rgba(46, 125, 50, 0.2);
  border-radius: 16px;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.add-item-btn:hover {
  background: #C8E6C9;
  border-color: rgba(46, 125, 50, 0.4);
}

.section-header svg {
  width: 20px;
  height: 20px;
  color: #E65100;
}

.order-info-section h3,
.order-items-section h3 {
  font-size: 1rem;
  color: rgba(0, 0, 0, 0.87);
  margin: 0;
  font-weight: 600;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--md-spacing-md);
  margin-top: var(--md-spacing-sm);
}

.info-row:first-of-type {
  margin-top: 0;
}

.info-item-user {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-item-user svg {
  width: 18px;
  height: 18px;
  color: rgba(0, 0, 0, 0.6);
}

.info-item-user .wechat-badge {
  margin-left: 8px;
  padding: 2px 8px;
  background: #E8F5E9;
  color: #2E7D32;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.impersonate-btn-small {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: 8px;
  padding: 4px 10px;
  background: rgba(33, 150, 243, 0.1);
  color: #2196F3;
  border: 1px solid rgba(33, 150, 243, 0.3);
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.impersonate-btn-small:hover {
  background: rgba(33, 150, 243, 0.2);
  border-color: rgba(33, 150, 243, 0.5);
  transform: translateY(-1px);
}

.impersonate-btn-small svg {
  width: 14px;
  height: 14px;
}

.info-item-price {
  display: flex;
  align-items: center;
}

.info-item-price .value.price {
  color: var(--md-primary);
  font-weight: 600;
  font-size: 1.1rem;
}

.info-item-payment-method {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  width: 100%;
}

.payment-method-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.7);
  white-space: nowrap;
}

.payment-method-select {
  flex: 1;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  background: var(--md-surface);
  color: var(--md-on-surface);
  cursor: pointer;
  max-width: 200px;
}

.payment-method-select:focus {
  outline: none;
  border-color: var(--md-primary);
  border-width: 2px;
}

.info-item-order-status {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  width: 100%;
}

.order-status-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.7);
  white-space: nowrap;
}

.order-status-select {
  flex: 1;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  background: var(--md-surface);
  color: var(--md-on-surface);
  cursor: pointer;
  max-width: 200px;
}

.order-status-select:focus {
  outline: none;
  border-color: var(--md-primary);
  border-width: 2px;
}

.mark-paid-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid rgba(46, 125, 50, 0.2);
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0.1px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  background: #E8F5E9;
  color: #2E7D32;
  min-height: 36px;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  position: relative;
  overflow: hidden;
  outline: none;
  width: auto;
  justify-content: center;
  white-space: nowrap;
}

.mark-paid-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(46, 125, 50, 0.1);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s, opacity 0.3s;
  opacity: 0;
}

.mark-paid-btn:hover {
  background: #C8E6C9;
  border-color: rgba(46, 125, 50, 0.4);
  box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.16), 0px 3px 6px rgba(0, 0, 0, 0.23);
  transform: translateY(-1px);
}

.mark-paid-btn:active {
  background: #A5D6A7;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  transform: translateY(0);
}

.mark-paid-btn:active::before {
  width: 300px;
  height: 300px;
  opacity: 1;
  transition: width 0s, height 0s, opacity 0.3s;
}

.mark-unpaid-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid rgba(229, 57, 53, 0.2);
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0.1px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  background: #FFEBEE;
  color: #C62828;
  min-height: 36px;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  position: relative;
  overflow: hidden;
  outline: none;
  width: auto;
  justify-content: center;
  white-space: nowrap;
}

.mark-unpaid-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(229, 57, 53, 0.1);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s, opacity 0.3s;
  opacity: 0;
}

.mark-unpaid-btn:hover {
  background: #FFCDD2;
  border-color: rgba(229, 57, 53, 0.4);
  box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.16), 0px 3px 6px rgba(0, 0, 0, 0.23);
  transform: translateY(-1px);
}

.mark-unpaid-btn:active {
  background: #EF9A9A;
  transform: translateY(0);
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
}

.mark-unpaid-btn:active::before {
  width: 300px;
  height: 300px;
  opacity: 1;
  transition: width 0s, height 0s, opacity 0.3s;
}

.complete-order-btn {
  padding: 10px 24px;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.1px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(46, 125, 50, 0.2);
  background: #E8F5E9;
  color: #2E7D32;
  min-height: 40px;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  position: relative;
  overflow: hidden;
  outline: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.complete-order-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(46, 125, 50, 0.1);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s, opacity 0.3s;
  opacity: 0;
}

.complete-order-btn:hover:not(:disabled) {
  background: #C8E6C9;
  border-color: rgba(46, 125, 50, 0.4);
  box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.16), 0px 3px 6px rgba(0, 0, 0, 0.23);
  transform: translateY(-1px);
}

.complete-order-btn:active:not(:disabled) {
  background: #A5D6A7;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  transform: translateY(0);
}

.complete-order-btn:active:not(:disabled)::before {
  width: 300px;
  height: 300px;
  opacity: 1;
  transition: width 0s, height 0s, opacity 0.3s;
}

.complete-order-btn:disabled {
  opacity: 0.38;
  cursor: not-allowed;
  box-shadow: none;
}

.info-item .value {
  color: rgba(0, 0, 0, 0.87);
  font-size: 0.875rem;
  line-height: 1.2;
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
  overflow: visible;
}

.order-item-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--md-spacing-sm);
  background: #F5F5F5;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  transition: all 0.2s;
  gap: var(--md-spacing-sm);
  position: relative;
  overflow: visible;
  z-index: 1;
}

.order-item-row:hover {
  background: #EEEEEE;
  border-color: rgba(0, 0, 0, 0.1);
  z-index: 2002;
}

.item-info {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
  flex: 1;
  overflow: visible;
}

.item-name {
  font-size: var(--md-body-size);
  font-weight: 500;
  color: var(--md-on-surface);
  display: flex;
  align-items: center;
  gap: 6px;
}

.item-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin-top: var(--md-spacing-xs);
  gap: var(--md-spacing-md);
}

.quantity-controls {
  display: flex;
  align-items: center;
  gap: 4px;
}

.qty-btn {
  width: 28px;
  height: 28px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 4px;
  background: #FFFFFF;
  color: rgba(0, 0, 0, 0.87);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 500;
  transition: all 0.2s;
}

.qty-btn:hover:not(:disabled) {
  background: #F5F5F5;
  border-color: rgba(0, 0, 0, 0.2);
}

.qty-btn:disabled {
  opacity: 0.38;
  cursor: not-allowed;
}

.quantity-input {
  width: 50px;
  padding: 4px 8px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 4px;
  text-align: center;
  font-size: 0.875rem;
}

.remove-item-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid rgba(244, 67, 54, 0.3);
  border-radius: 50%;
  color: #F44336;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.remove-item-btn:hover {
  background: rgba(244, 67, 54, 0.2);
  border-color: rgba(244, 67, 54, 0.5);
}

.remove-item-btn svg {
  width: 18px;
  height: 18px;
}

.item-price {
  font-weight: 600;
  color: var(--md-primary);
}

.weight-input-group {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  margin-top: var(--md-spacing-sm);
  padding-top: var(--md-spacing-sm);
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.weight-input-group label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--md-label-size);
  color: rgba(0, 0, 0, 0.7);
  font-weight: 500;
  min-width: 120px;
}

.weight-input-group label svg {
  color: #E65100;
}

.weight-input {
  flex: 1;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  background: var(--md-surface);
  color: var(--md-on-surface);
  max-width: 200px;
}

.weight-input:focus {
  outline: none;
  border-color: var(--md-primary);
  border-width: 2px;
}

.error-message {
  padding: var(--md-spacing-md);
  background: #FFEBEE;
  color: #C62828;
  border-radius: var(--md-radius-md);
  font-size: var(--md-label-size);
  margin-top: var(--md-spacing-md);
}

/* Delivery Method Section */
.delivery-method-selector {
  display: flex;
  gap: var(--md-spacing-md);
  width: 100%;
}

.delivery-method-selector label {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: 2px solid rgba(0, 0, 0, 0.12);
  border-radius: var(--md-radius-md);
  cursor: pointer;
  transition: all 0.2s;
  flex: 1;
}

.delivery-method-selector label:hover {
  border-color: var(--md-primary);
  background: rgba(255, 140, 0, 0.05);
}

.delivery-method-selector input[type="radio"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.delivery-method-selector input[type="radio"]:checked + span {
  color: var(--md-primary);
  font-weight: 600;
}

.delivery-method-selector label:has(input:checked) {
  border-color: var(--md-primary);
  background: rgba(255, 140, 0, 0.1);
  border-width: 2px;
}

.pickup-location-selector {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  width: 100%;
}

.field-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.7);
  white-space: nowrap;
}

.pickup-location-select {
  flex: 1;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  background: var(--md-surface);
  color: var(--md-on-surface);
  cursor: pointer;
}

.pickup-location-select:focus {
  outline: none;
  border-color: var(--md-primary);
  border-width: 2px;
}

/* Address Management */
.address-management {
  width: 100%;
}

.address-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--md-spacing-sm);
}

.address-actions {
  display: flex;
  gap: var(--md-spacing-sm);
}

.refresh-addresses-btn,
.add-address-btn {
  padding: 6px 12px;
  background: rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: var(--md-radius-sm);
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.8125rem;
  font-weight: 500;
}

.add-address-btn {
  background: #E8F5E9;
  color: #2E7D32;
  border-color: rgba(46, 125, 50, 0.2);
}

.refresh-addresses-btn:hover:not(:disabled),
.add-address-btn:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.08);
  border-color: rgba(0, 0, 0, 0.2);
}

.add-address-btn:hover:not(:disabled) {
  background: #C8E6C9;
  border-color: rgba(46, 125, 50, 0.4);
}

.refresh-addresses-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-addresses,
.no-addresses {
  padding: var(--md-spacing-md);
  text-align: center;
  color: rgba(0, 0, 0, 0.6);
  font-size: 0.875rem;
}

.addresses-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
  max-height: 300px;
  overflow-y: auto;
}

.address-item {
  display: flex;
  gap: var(--md-spacing-sm);
  padding: var(--md-spacing-sm);
  border: 2px solid rgba(0, 0, 0, 0.08);
  border-radius: var(--md-radius-md);
  cursor: pointer;
  transition: all 0.2s;
}

.address-item:hover {
  border-color: rgba(255, 140, 0, 0.5);
  background: rgba(255, 140, 0, 0.05);
}

.address-item.selected {
  border-color: var(--md-primary);
  background: rgba(255, 140, 0, 0.1);
  border-width: 2px;
}

.address-radio {
  display: flex;
  align-items: flex-start;
  padding-top: 2px;
}

.address-radio input[type="radio"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  pointer-events: none;
}

.address-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.address-line {
  font-size: 0.875rem;
  color: rgba(0, 0, 0, 0.87);
  line-height: 1.4;
}

.address-city {
  font-size: 0.8125rem;
  color: rgba(0, 0, 0, 0.6);
}

/* Add Address Form */
.add-address-form {
  margin-top: var(--md-spacing-md);
  padding: var(--md-spacing-md);
  background: rgba(46, 125, 50, 0.05);
  border: 2px solid rgba(46, 125, 50, 0.2);
  border-radius: var(--md-radius-md);
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--md-spacing-md);
}

.form-header h4 {
  margin: 0;
  font-size: 1rem;
  color: rgba(0, 0, 0, 0.87);
}

.cancel-form-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: rgba(0, 0, 0, 0.6);
  cursor: pointer;
  border-radius: 50%;
  font-size: 24px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.cancel-form-btn:hover {
  background: rgba(0, 0, 0, 0.1);
  color: rgba(0, 0, 0, 0.87);
}

.form-group {
  margin-bottom: var(--md-spacing-md);
}

.form-group label {
  display: block;
  margin-bottom: var(--md-spacing-xs);
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.7);
}

.form-input {
  width: 100%;
  padding: var(--md-spacing-sm);
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: var(--md-radius-sm);
  font-size: 0.875rem;
  background: white;
}

.form-input:focus {
  outline: none;
  border-color: var(--md-primary);
  border-width: 2px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--md-spacing-md);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--md-spacing-md);
}

.save-address-btn {
  padding: 10px 24px;
  background: #2E7D32;
  color: white;
  border: none;
  border-radius: var(--md-radius-md);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.save-address-btn:hover:not(:disabled) {
  background: #1B5E20;
  transform: translateY(-1px);
}

.save-address-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.address-error {
  margin-top: var(--md-spacing-sm);
  padding: var(--md-spacing-sm);
  background: #FFEBEE;
  color: #C62828;
  border-radius: var(--md-radius-sm);
  font-size: 0.8125rem;
}

/* Product Info Icon and Tooltip */
.product-info-icon {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  cursor: help;
  color: rgba(0, 0, 0, 0.4);
  transition: all 0.2s;
}

.product-info-icon svg {
  width: 16px;
  height: 16px;
}

.product-info-icon:hover {
  color: var(--md-primary);
  transform: scale(1.1);
}

.price-tooltip {
  position: absolute;
  left: calc(100% + 8px);
  top: 50%;
  transform: translateY(-50%);
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
  z-index: 2001;
}

.product-info-icon:hover .price-tooltip {
  opacity: 1;
  visibility: visible;
  left: calc(100% + 12px);
}

.tooltip-content {
  background: #FFFFFF;
  border-radius: 12px;
  box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.15), 0px 2px 8px rgba(0, 0, 0, 0.1);
  padding: 12px 16px;
  min-width: 260px;
  max-width: 350px;
  width: max-content;
  border: 1px solid rgba(0, 0, 0, 0.08);
  position: relative;
}

.tooltip-content::after {
  content: '';
  position: absolute;
  left: -6px;
  top: 50%;
  width: 12px;
  height: 12px;
  background: #FFFFFF;
  border-left: 1px solid rgba(0, 0, 0, 0.08);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  transform: translateY(-50%) rotate(45deg);
}

.tooltip-header {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--md-on-surface);
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--md-primary);
}

.tooltip-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tooltip-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  font-size: 0.8125rem;
}

.tooltip-label {
  color: rgba(0, 0, 0, 0.6);
  font-weight: 500;
  white-space: nowrap;
}

.tooltip-value {
  color: var(--md-on-surface);
  font-weight: 600;
  text-align: right;
}

.tooltip-divider {
  height: 1px;
  background: rgba(0, 0, 0, 0.08);
  margin: 4px 0;
}

.tooltip-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tooltip-section .tooltip-label {
  display: block;
  margin-bottom: 4px;
}

.tooltip-range {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 8px;
  background: rgba(255, 140, 0, 0.05);
  border-radius: 6px;
  font-size: 0.75rem;
  gap: 8px;
  white-space: nowrap;
}

.tooltip-range span:first-child {
  color: rgba(0, 0, 0, 0.7);
}

.tooltip-price {
  color: var(--md-primary);
  font-weight: 600;
  white-space: nowrap;
}
</style>

