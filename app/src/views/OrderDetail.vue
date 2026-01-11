<template>
  <div class="order-detail-page">
    <header class="page-header">
      <button @click="$router.back()" class="back-btn">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <div class="header-center">
        <h1>订单详情</h1>
      </div>
      <div class="header-spacer"></div>
    </header>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="order && deal" class="order-content">
      <!-- Order Info Section -->
      <div class="order-info-section">
        <div class="order-header-info">
          <div class="order-number">订单号: {{ order.order_number }}</div>
          <span :class="['status-badge', getStatusClass(order.status)]">
            {{ getStatusLabel(order.status) }}
          </span>
        </div>
        <div class="order-date">创建时间: {{ formatDate(order.created_at) }}</div>
      </div>

      <!-- Group Deal Info Section -->
      <div class="deal-info-section">
        <div class="deal-header">
          <h2>{{ deal.title }}</h2>
          <span :class="['deal-badge', deal.status]">
            {{ getDealStatusLabel(deal.status) }}
          </span>
        </div>
        <p v-if="deal.description" class="deal-description">{{ deal.description }}</p>
        
        <div class="deal-dates">
          <div class="date-row">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="date-icon">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <div class="date-info">
              <span class="date-label">开团时间</span>
              <span class="date-value">{{ formatDateTime(deal.order_start_date) }}</span>
            </div>
          </div>
          <div class="date-row">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="date-icon">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <div class="date-info">
              <span class="date-label">截单时间</span>
              <span class="date-value">{{ formatDateTime(deal.order_end_date) }}</span>
            </div>
          </div>
          <div class="date-row">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="date-icon">
              <path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
            <div class="date-info">
              <span class="date-label">取货时间</span>
              <span class="date-value">{{ formatPickupDate(deal.pickup_date) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Products Section -->
      <div class="products-section">
        <h3 class="section-title">商品选择</h3>
        
        <div v-if="deal.products && deal.products.length === 0" class="empty-products">
          <p>暂无商品</p>
        </div>
        <div v-else class="products-list">
          <div
            v-for="product in deal.products"
            :key="product.id"
            class="product-item"
          >
            <div class="product-image" @click="openProductModal(product)">
              <img v-if="getProductImage(product)" :src="getProductImage(product)" :alt="product.name" />
              <div v-else class="image-placeholder">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                </svg>
              </div>
              <div v-if="isOutOfStock(product)" class="sold-out-badge">
                已售罄
              </div>
            </div>
            <div class="product-details">
              <div class="product-name-row">
                <h4 class="product-name" @click="openProductModal(product)">{{ product.name }}</h4>
                <span v-if="product.counts_toward_free_shipping === false" class="shipping-excluded-badge">
                  不计入免运
                </span>
              </div>
              <p v-if="product.description" class="product-description-preview" @click="openProductModal(product)">
                {{ product.description.length > 80 ? product.description.substring(0, 80) + '...' : product.description }}
              </p>
              
              <!-- Price Display -->
              <div class="product-price">
                <span class="price-label">团购价:</span>
                <span v-if="product.pricing_type === 'bundled_weight'" class="price-value">
                  ${{ (product.pricing_data?.price_per_unit || 0).toFixed(2) }}/{{ product.pricing_data?.unit === 'kg' ? 'kg' : 'lb' }}
                </span>
                <span v-else-if="product.pricing_type === 'weight_range' || product.pricing_type === 'unit_weight'" class="price-value price-range">
                  {{ formatPriceRange(product) }}
                </span>
                <span v-else class="price-value">${{ formatPrice(product) }}</span>
              </div>

              <!-- Stock Info -->
              <div v-if="product.deal_stock_limit !== undefined && product.deal_stock_limit !== null" class="stock-info" :class="{ 'out-of-stock': isOutOfStock(product) }">
                <span v-if="isOutOfStock(product)">缺货</span>
                <span v-else>库存: {{ product.deal_stock_limit }} 件</span>
              </div>

              <!-- Product Selection Controls -->
              <div class="product-selection" :class="{ 'disabled': isOutOfStock(product) || !canEditProducts || isOrderCompleted }">
                <!-- Per Item Pricing -->
                <div v-if="product.pricing_type === 'per_item'" class="selection-controls">
                  <div class="quantity-control">
                    <button @click="decreaseQuantity(product)" :disabled="getQuantity(product) === 0 || !canEditProducts || isOutOfStock(product) || isOrderCompleted" class="qty-btn">-</button>
                    <input
                      type="number"
                      :value="getQuantity(product)"
                      @input="setQuantity(product, $event.target.value)"
                      min="0"
                      :max="product.deal_stock_limit || 999"
                      :disabled="!canEditProducts || isOutOfStock(product) || isOrderCompleted"
                      class="qty-input"
                    />
                    <button @click="increaseQuantity(product)" :disabled="(product.deal_stock_limit && getQuantity(product) >= product.deal_stock_limit) || !canEditProducts || isOutOfStock(product) || isOrderCompleted" class="qty-btn">+</button>
                  </div>
                  <div class="item-total">
                    小计: ${{ calculateItemTotal(product) }}
                  </div>
                </div>

                <!-- Weight Range Pricing -->
                <div v-else-if="product.pricing_type === 'weight_range'" class="selection-controls">
                  <div class="quantity-control">
                    <label>数量:</label>
                    <button @click="decreaseQuantity(product)" :disabled="getQuantity(product) === 0 || !canEditProducts || isOutOfStock(product) || isOrderCompleted" class="qty-btn">-</button>
                    <input
                      type="number"
                      :value="getQuantity(product)"
                      @input="setQuantity(product, $event.target.value)"
                      min="0"
                      :disabled="!canEditProducts || isOutOfStock(product) || isOrderCompleted"
                      class="qty-input"
                    />
                    <button @click="increaseQuantity(product)" :disabled="!canEditProducts || isOutOfStock(product) || isOrderCompleted" class="qty-btn">+</button>
                  </div>
                  <div class="item-total estimated">
                    <span>预估小计: ${{ calculateItemTotal(product) }}</span>
                    <div class="tooltip-container" @click.stop="showPriceInfo('价格基于中等重量估算，实际价格可能因实际重量而有所不同，取货时确认最终价格')">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="info-icon">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                  </div>
                </div>

                <!-- Unit Weight Pricing -->
                <div v-else-if="product.pricing_type === 'unit_weight'" class="selection-controls">
                  <div class="quantity-control">
                    <label>数量:</label>
                    <button @click="decreaseQuantity(product)" :disabled="getQuantity(product) === 0 || !canEditProducts || isOutOfStock(product) || isOrderCompleted" class="qty-btn">-</button>
                    <input
                      type="number"
                      :value="getQuantity(product)"
                      @input="setQuantity(product, $event.target.value)"
                      min="0"
                      :disabled="!canEditProducts || isOutOfStock(product) || isOrderCompleted"
                      class="qty-input"
                    />
                    <button @click="increaseQuantity(product)" :disabled="!canEditProducts || isOutOfStock(product) || isOrderCompleted" class="qty-btn">+</button>
                  </div>
                  <div class="item-total estimated">
                    <span>预估小计: ${{ calculateItemTotal(product) }}</span>
                    <div class="tooltip-container" @click="showPriceInfo('价格基于中等重量估算，实际价格可能因实际重量而有所不同，取货时确认最终价格')">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="info-icon">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                  </div>
                </div>

                <!-- Bundled Weight Pricing -->
                <div v-else-if="product.pricing_type === 'bundled_weight'" class="selection-controls">
                  <div class="quantity-control">
                    <label>份数:</label>
                    <button @click="decreaseQuantity(product)" :disabled="getQuantity(product) === 0 || !canEditProducts || isOutOfStock(product) || isOrderCompleted" class="qty-btn">-</button>
                    <input
                      type="number"
                      :value="getQuantity(product)"
                      @input="setQuantity(product, $event.target.value)"
                      min="0"
                      step="1"
                      :disabled="!canEditProducts || isOutOfStock(product) || isOrderCompleted"
                      class="qty-input"
                    />
                    <button @click="increaseQuantity(product)" :disabled="!canEditProducts || isOutOfStock(product) || isOrderCompleted" class="qty-btn">+</button>
                  </div>
                  <div class="package-info-wrapper">
                    <span class="package-info">(每份 {{ product.pricing_data?.min_weight || 7 }}-{{ product.pricing_data?.max_weight || 15 }}{{ product.pricing_data?.unit === 'kg' ? 'kg' : 'lb' }})</span>
                  </div>
                  <div class="item-total estimated">
                    <span>预估小计: {{ calculateBundledItemTotal(product) }}</span>
                    <div class="tooltip-container" @click="showPriceInfo('价格基于每份重量范围估算，实际价格可能因实际重量而有所不同，取货时确认最终价格')">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="info-icon">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
              <!-- Show note when products cannot be edited (deal closed or order confirmed) but order is editable -->
              <div v-if="!canEditProducts && canEditPaymentDelivery && !isOrderCompleted" class="deal-closed-product-note">
                <span v-if="isDealClosed && order && order.status === 'confirmed'">团购已截单且订单已确认，无法修改商品</span>
                <span v-else-if="isDealClosed">团购已截单，无法修改商品</span>
                <span v-else-if="order && order.status === 'confirmed'">订单已确认，无法修改商品</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Delivery Method Selection -->
      <div class="delivery-section">
        <h3 class="section-title">配送方式</h3>
        <div class="delivery-options">
          <button 
            @click="setDeliveryMethod('pickup')"
            :class="['delivery-option', { active: deliveryMethod === 'pickup' }]"
            :disabled="!canEditPaymentDelivery"
          >
            <div class="option-icon">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <div class="option-content">
              <h4>自取</h4>
            </div>
            <div class="option-check">
              <svg v-if="deliveryMethod === 'pickup'" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </button>

          <button 
            @click="setDeliveryMethod('delivery')"
            :class="['delivery-option', { active: deliveryMethod === 'delivery' }]"
            :disabled="!canEditPaymentDelivery"
          >
            <div class="option-icon">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <div class="option-content">
              <h4>配送</h4>
            </div>
            <div class="option-check">
              <svg v-if="deliveryMethod === 'delivery'" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </button>
        </div>

        <!-- Pickup Location Selection -->
        <div v-if="deliveryMethod === 'pickup'" class="pickup-location-selection">
          <h4 class="selection-subtitle">选择自取点</h4>
          <div class="pickup-locations">
            <div 
              @click="setPickupLocation('markham')"
              :class="['pickup-location-card', { active: selectedPickupLocation === 'markham' }, { disabled: !canEditPaymentDelivery }]"
            >
              <div class="location-icon">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <div class="location-content">
                <h5>Markham</h5>
                <p>Woodbine Ave & 16th Avenue</p>
              </div>
              <div class="location-check">
                <svg v-if="selectedPickupLocation === 'markham'" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>

            <div 
              @click="setPickupLocation('northyork')"
              :class="['pickup-location-card', { active: selectedPickupLocation === 'northyork' }, { disabled: !canEditPaymentDelivery }]"
            >
              <div class="location-icon">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <div class="location-content">
                <h5>North York</h5>
                <p>Yorkdale附近</p>
              </div>
              <div class="location-check">
                <svg v-if="selectedPickupLocation === 'northyork'" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        <!-- Address Selection for Delivery -->
        <div v-if="deliveryMethod === 'delivery'" class="address-selection">
          <button @click="openAddressModal" class="select-address-btn" :disabled="!canEditPaymentDelivery">
            <div class="btn-content">
              <div class="btn-icon">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <div class="btn-text">
                <div v-if="selectedAddress" class="selected-address-preview">
                  <div class="preview-header">
                    <span class="preview-name">{{ selectedAddress.recipient_name }}</span>
                    <span class="preview-phone">{{ selectedAddress.phone }}</span>
                  </div>
                  <div class="preview-address">
                    {{ selectedAddress.address_line1 }}, {{ selectedAddress.city }}
                  </div>
                </div>
                <div v-else class="no-address-selected">
                  <span>选择配送地址</span>
                  <span class="hint">点击选择或添加新地址</span>
                </div>
              </div>
              <div class="btn-arrow">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </div>
          </button>
        </div>
      </div>

      <!-- Payment Method Selection -->
      <div class="payment-section">
        <h3 class="section-title">支付方式</h3>
        <div class="payment-options">
          <label 
            :class="['payment-option', { active: paymentMethod === 'cash' }]"
          >
            <input 
              type="radio" 
              name="paymentMethod" 
              value="cash" 
              v-model="paymentMethod"
              :disabled="!canEditPaymentDelivery"
              class="payment-radio"
            />
            <div class="option-icon">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <div class="option-content">
              <h4>现金</h4>
            </div>
            <div class="option-check">
              <svg v-if="paymentMethod === 'cash'" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </label>

          <label 
            :class="['payment-option', { active: paymentMethod === 'etransfer' }]"
          >
            <input 
              type="radio" 
              name="paymentMethod" 
              value="etransfer" 
              v-model="paymentMethod"
              :disabled="!canEditPaymentDelivery"
              class="payment-radio"
            />
            <div class="option-icon">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
            </div>
            <div class="option-content">
              <h4>e-transfer</h4>
            </div>
            <div class="option-check">
              <svg v-if="paymentMethod === 'etransfer'" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </label>
        </div>
        <p class="payment-note">取货时根据实际重量支付</p>
      </div>

      <!-- Notes Section -->
      <div class="notes-section">
        <h3 class="section-title">备注</h3>
        <textarea
          v-model="notes"
          placeholder="请输入您的特殊要求或备注（选填）"
          class="notes-input"
          rows="3"
          maxlength="1000"
          :disabled="!canEditPaymentDelivery"
        ></textarea>
        <p class="notes-hint">{{ notes.length }}/1000</p>
      </div>

      <!-- Order Summary -->
      <div v-if="order && deal && hasSelectedItems()" class="order-summary-section">
        <h3 class="section-title">订单摘要</h3>
        <div class="order-breakdown">
          <div class="breakdown-row">
            <span class="breakdown-label">小计:</span>
            <span class="breakdown-amount">${{ calculateSubtotal() }}</span>
          </div>
          <div v-if="deliveryMethod === 'delivery'" class="breakdown-row">
            <span class="breakdown-label">运费:</span>
            <span class="breakdown-amount">{{ shippingFeeDisplay }}</span>
          </div>
          <div class="breakdown-row total-row">
            <span class="total-label">{{ hasEstimatedTotal() ? '预估总计' : '总计' }}:</span>
            <span class="total-amount">${{ calculateTotal().total }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Update Order Button -->
    <div v-if="order && deal && canEditPaymentDelivery" class="update-order-section">
      <div class="order-actions">
        <button @click="updateOrder" class="update-order-btn" :disabled="saving || (!hasSelectedItems() && canEditProducts)">
          {{ saving ? '保存中...' : '更新订单' }}
        </button>
        <button @click="confirmCancelOrder" class="cancel-order-btn" :disabled="saving || cancelling">
          {{ cancelling ? '取消中...' : '取消订单' }}
        </button>
      </div>
    </div>

    <!-- Reactivate Order Button (for cancelled orders) -->
    <div v-if="order && deal && order.status === 'cancelled'" class="update-order-section">
      <div class="order-actions">
        <button 
          @click="reactivateOrder" 
          class="reactivate-order-btn" 
          :disabled="reactivating || isDealClosed"
        >
          {{ reactivating ? '重新激活中...' : '重新下单' }}
        </button>
        <div v-if="isDealClosed" class="deal-closed-note">
          团购已截单，无法提交订单
        </div>
      </div>
    </div>

    <!-- Product Detail Modal -->
    <ProductDetailModal
      :show="showProductModal"
      :product="selectedProduct"
      @close="closeProductModal"
    />

    <!-- Price Info Modal -->
    <Modal
      :show="showPriceInfoModal"
      type="info"
      title="价格说明"
      :message="priceInfoMessage"
      :showCancel="false"
      :icon="true"
      confirmText="知道了"
      @confirm="closePriceInfoModal"
      @close="closePriceInfoModal"
    />

    <!-- Cancel Order Confirmation Modal -->
    <div v-if="showCancelModal" class="modal-overlay" @click="closeCancelModal">
      <div class="modal-content cancel-modal" @click.stop>
        <div class="modal-header">
          <h2>取消订单</h2>
          <button @click="closeCancelModal" class="close-btn">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div class="modal-body">
          <div v-if="order" class="cancel-warning">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div class="warning-content">
              <h3>确认取消订单？</h3>
              <p>订单号: {{ order.order_number }}</p>
              <p class="warning-text">团购截止之前仍可恢复订单。</p>
            </div>
          </div>

          <div v-if="cancelError" class="error-message">{{ cancelError }}</div>
        </div>

        <div class="modal-footer">
          <button @click="closeCancelModal" class="cancel-btn-secondary">返回</button>
          <button @click="cancelOrder" class="confirm-cancel-btn" :disabled="cancelling">
            {{ cancelling ? '取消中...' : '确认取消' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Address Selection Modal -->
    <div v-if="showAddressModal" class="modal-overlay" @click="closeAddressModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>选择配送地址</h2>
          <button @click="closeAddressModal" class="close-btn">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <div v-if="addressesLoading" class="loading-addresses">加载地址中...</div>
          <div v-else-if="addresses.length === 0" class="no-addresses">
            <div class="empty-icon">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <p>暂无地址</p>
            <button @click="goToAddresses" class="add-address-btn">添加地址</button>
          </div>
          <div v-else class="addresses-list">
            <div
              v-for="address in addresses"
              :key="address.id"
              @click="selectAddress(address)"
              :class="['address-card', { active: selectedAddressId === address.id }]"
            >
              <div class="address-header">
                <span class="address-name">{{ address.recipient_name }}</span>
                <span class="address-phone">{{ address.phone }}</span>
              </div>
              <div class="address-body">
                <div class="address-line">{{ address.address_line1 }}</div>
                <div v-if="address.address_line2" class="address-line">{{ address.address_line2 }}</div>
                <div class="address-line">{{ address.city }}, {{ address.postal_code }}</div>
                <div v-if="address.delivery_instructions" class="address-instructions">
                  配送说明: {{ address.delivery_instructions }}
                </div>
              </div>
              <div class="address-check">
                <svg v-if="selectedAddressId === address.id" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
            <button @click="goToAddresses" class="add-address-btn-secondary">添加新地址</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'
import { useAuthStore } from '../stores/auth'
import { formatDateEST_CN, formatDateTimeEST_CN, formatPickupDateTime_CN } from '../utils/date'
import { useModal } from '../composables/useModal'
import ProductDetailModal from '../components/ProductDetailModal.vue'
import Modal from '../components/Modal.vue'

export default {
  name: 'OrderDetail',
  components: {
    ProductDetailModal,
    Modal
  },
  data() {
    return {
      loading: true,
      error: null,
      order: null,
      deal: null,
      selectedItems: {}, // { productId: { quantity } }
      paymentMethod: 'cash',
      deliveryMethod: 'pickup',
      selectedPickupLocation: 'markham',
      selectedAddressId: null,
      selectedAddress: null,
      notes: '',
      showProductModal: false,
      selectedProduct: null,
      showPriceInfoModal: false,
      priceInfoMessage: '',
      showAddressModal: false,
      addresses: [],
      addressesLoading: false,
      saving: false,
      showCancelModal: false,
      cancelling: false,
      cancelError: null,
      reactivating: false
    }
  },
  setup() {
    const authStore = useAuthStore()
    const { warning, error: showError, success } = useModal()
    return { authStore, warning, showError, success }
  },
  computed: {
    isAuthenticated() {
      return this.authStore.isAuthenticated
    },
    isOrderCompleted() {
      // Order is completed
      return this.order && this.order.status === 'completed'
    },
    isEditable() {
      // Order is editable if status is 'submitted' (regardless of deal status)
      return this.order && this.order.status === 'submitted'
    },
    canEditProducts() {
      // Can edit products only if order is submitted AND deal is not closed AND order is not confirmed
      // Products are NOT editable when: deal is closed OR order status is confirmed
      if (!this.order) return false
      const isOrderConfirmed = this.order.status === 'confirmed'
      return this.isEditable && !this.isDealClosed && !isOrderConfirmed
    },
    canEditPaymentDelivery() {
      // Can edit payment/delivery/notes if order is submitted OR confirmed (even if deal is closed)
      // Everything is read-only for: preparing, ready_for_pickup, out_for_delivery, completed, and other statuses
      if (!this.order) return false
      const editableStatuses = ['submitted', 'confirmed']
      return editableStatuses.includes(this.order.status)
    },
    isDealClosed() {
      // Check if group deal is closed
      if (!this.deal) return false
      const now = new Date()
      const orderEndDate = this.deal.order_end_date ? new Date(this.deal.order_end_date) : null
      return this.deal.status === 'closed' || (orderEndDate && orderEndDate < now)
    },
    shippingFeeDisplay() {
      const shipping = this.calculateShippingFee()
      if (shipping === 0) {
        return '免运费'
      }
      return `$${shipping.toFixed(2)}`
    }
  },
  async mounted() {
    if (!this.authStore.token) {
      this.authStore.loadFromStorage()
    }
    
    if (!this.isAuthenticated) {
      this.error = '请先登录'
      this.loading = false
      return
    }
    
    await this.loadOrder()
  },
  methods: {
    async loadOrder() {
      this.loading = true
      this.error = null
      try {
        const orderId = this.$route.params.id
        const response = await apiClient.get(`/orders/${orderId}`)
        this.order = response.data.order
        
        // Load group deal
        if (this.order.group_deal && this.order.group_deal.id) {
          await this.loadGroupDeal(this.order.group_deal.id)
        } else {
          this.error = '订单关联的团购不存在'
          return
        }
        
        // Load order items into selectedItems
        if (this.order.items && this.order.items.length > 0) {
          this.order.items.forEach(item => {
            if (this.selectedItems[item.product_id] === undefined) {
              this.selectedItems[item.product_id] = { quantity: 0 }
            }
            this.selectedItems[item.product_id].quantity = item.quantity
          })
        }
        
        // Load order settings
        this.paymentMethod = this.order.payment_method || 'cash'
        this.deliveryMethod = this.order.delivery_method || 'pickup'
        this.selectedPickupLocation = this.order.pickup_location || 'markham'
        this.selectedAddressId = this.order.address_id || null
        this.notes = this.order.notes || ''
        
        // Load address if delivery
        if (this.deliveryMethod === 'delivery' && this.selectedAddressId) {
          await this.loadAddresses()
          const addr = this.addresses.find(a => a.id === this.selectedAddressId)
          if (addr) {
            this.selectedAddress = addr
          }
        }
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || '加载订单失败'
        console.error('Failed to load order:', error)
      } finally {
        this.loading = false
      }
    },
    async loadGroupDeal(dealId) {
      try {
        const response = await apiClient.get(`/group-deals/${dealId}`)
        this.deal = response.data.deal
        
        // Initialize selected items for products not in order
        if (this.deal.products) {
          this.deal.products.forEach(product => {
            if (this.selectedItems[product.id] === undefined) {
              this.selectedItems[product.id] = { quantity: 0 }
            }
          })
        }
      } catch (error) {
        console.error('Failed to load group deal:', error)
        this.error = '加载团购信息失败'
      }
    },
    async loadAddresses() {
      this.addressesLoading = true
      try {
        const response = await apiClient.get('/addresses')
        this.addresses = response.data.addresses || []
      } catch (error) {
        console.error('Failed to load addresses:', error)
      } finally {
        this.addressesLoading = false
      }
    },
    formatDate(dateString) {
      return formatDateEST_CN(dateString)
    },
    formatDateTime(dateString) {
      return formatDateTimeEST_CN(dateString)
    },
    formatPickupDate(dateString) {
      return formatPickupDateTime_CN(dateString)
    },
    getStatusLabel(status) {
      const labels = {
        'submitted': '已提交订单',
        'confirmed': '已确认订单',
        'preparing': '正在配货',
        'ready_for_pickup': '可以取货',
        'out_for_delivery': '正在配送',
        'completed': '订单完成',
        'cancelled': '已取消'
      }
      return labels[status] || status
    },
    getStatusClass(status) {
      const classes = {
        'submitted': 'pending',
        'confirmed': 'confirmed',
        'preparing': 'processing',
        'ready_for_pickup': 'processing',
        'out_for_delivery': 'processing',
        'completed': 'completed',
        'cancelled': 'cancelled'
      }
      return classes[status] || 'pending'
    },
    getDealStatusLabel(status) {
      const labels = {
        'upcoming': '即将开始',
        'active': '进行中',
        'closed': '已截单',
        'completed': '已完成'
      }
      return labels[status] || status
    },
    formatPrice(product) {
      if (product.deal_price) {
        return parseFloat(product.deal_price).toFixed(2)
      }
      if (product.display_price) {
        return parseFloat(product.display_price).toFixed(2)
      }
      if (product.sale_price) {
        return parseFloat(product.sale_price).toFixed(2)
      }
      return '0.00'
    },
    formatPriceRange(product) {
      if (product.pricing_type === 'weight_range') {
        const ranges = product.pricing_data?.ranges || []
        if (ranges.length === 0) {
          if (product.deal_price) {
            return `$${parseFloat(product.deal_price).toFixed(2)}`
          }
          return '价格待定'
        }
        
        const sortedRanges = [...ranges].sort((a, b) => (a.min || 0) - (b.min || 0))
        const prices = sortedRanges
          .map(r => parseFloat(r.price || 0))
          .filter(p => p > 0)
        
        if (prices.length === 0) {
          if (product.deal_price) {
            return `$${parseFloat(product.deal_price).toFixed(2)}`
          }
          return '价格待定'
        }
        
        const minPrice = Math.min(...prices)
        const maxPrice = Math.max(...prices)
        
        if (minPrice === maxPrice) {
          return `$${minPrice.toFixed(2)}`
        }
        return `$${minPrice.toFixed(2)} - $${maxPrice.toFixed(2)}`
      } else if (product.pricing_type === 'unit_weight') {
        const pricePerUnit = product.pricing_data?.price_per_unit || 0
        const unit = product.pricing_data?.unit || 'kg'
        
        if (pricePerUnit === 0) {
          if (product.deal_price) {
            return `$${parseFloat(product.deal_price).toFixed(2)}/${unit}`
          }
          return '价格待定'
        }
        
        return `$${parseFloat(pricePerUnit).toFixed(2)}/${unit}`
      } else if (product.pricing_type === 'bundled_weight') {
        const pricePerUnit = product.pricing_data?.price_per_unit || 0
        const minWeight = product.pricing_data?.min_weight || 7
        const maxWeight = product.pricing_data?.max_weight || 15
        const unit = product.pricing_data?.unit || 'lb'
        
        if (pricePerUnit === 0) {
          if (product.deal_price) {
            return `$${parseFloat(product.deal_price).toFixed(2)}/份`
          }
          return '价格待定'
        }
        
        const minPrice = pricePerUnit * minWeight
        const maxPrice = pricePerUnit * maxWeight
        const unitPriceDisplay = `$${pricePerUnit.toFixed(2)}/${unit}`
        
        if (minPrice === maxPrice) {
          return `$${minPrice.toFixed(2)}/份 (${minWeight}-${maxWeight}${unit}/份) · ${unitPriceDisplay}`
        }
        return `$${minPrice.toFixed(2)} - $${maxPrice.toFixed(2)}/份 (${minWeight}-${maxWeight}${unit}/份) · ${unitPriceDisplay}`
      }
      return '价格待定'
    },
    getQuantity(product) {
      return this.selectedItems[product.id]?.quantity || 0
    },
    setQuantity(product, value) {
      if (this.isOutOfStock(product)) {
        return
      }
      
      const qty = parseInt(value) || 0
      const maxQty = product.deal_stock_limit || 999
      const finalQty = Math.max(0, Math.min(qty, maxQty))
      
      if (!this.selectedItems[product.id]) {
        this.selectedItems[product.id] = { quantity: 0 }
      }
      this.selectedItems[product.id].quantity = finalQty
    },
    increaseQuantity(product) {
      if (this.isOutOfStock(product)) {
        return
      }
      
      const current = this.getQuantity(product)
      const maxQty = product.deal_stock_limit || 999
      this.setQuantity(product, Math.min(current + 1, maxQty))
    },
    decreaseQuantity(product) {
      const current = this.getQuantity(product)
      this.setQuantity(product, Math.max(current - 1, 0))
    },
    isOutOfStock(product) {
      if (!product) return false
      
      if (product.deal_stock_limit !== undefined && product.deal_stock_limit !== null) {
        return product.deal_stock_limit === 0
      }
      
      if (product.stock_limit !== undefined && product.stock_limit !== null) {
        return product.stock_limit === 0
      }
      
      return false
    },
    calculateItemTotal(product) {
      const quantity = this.getQuantity(product)
      if (quantity === 0) return '0.00'
      
      if (product.pricing_type === 'per_item') {
        const price = product.deal_price || product.display_price || product.sale_price || 0
        return (parseFloat(price) * quantity).toFixed(2)
      } else if (product.pricing_type === 'weight_range') {
        const ranges = product.pricing_data?.ranges || []
        if (ranges.length === 0) return '0.00'
        
        const minPrice = Math.min(...ranges.map(r => parseFloat(r.price || 0)))
        return (minPrice * quantity).toFixed(2)
      } else if (product.pricing_type === 'unit_weight') {
        const pricePerUnit = product.pricing_data?.price_per_unit || 0
        const estimatedWeight = 1
        return (parseFloat(pricePerUnit) * estimatedWeight * quantity).toFixed(2)
      } else if (product.pricing_type === 'bundled_weight') {
        const pricePerUnit = product.pricing_data?.price_per_unit || 0
        const minWeight = product.pricing_data?.min_weight || 7
        const maxWeight = product.pricing_data?.max_weight || 15
        const midWeight = (minWeight + maxWeight) / 2
        
        if (pricePerUnit === 0) return '0.00'
        
        return (pricePerUnit * midWeight * quantity).toFixed(2)
      }
      return '0.00'
    },
    calculateBundledItemTotal(product) {
      const quantity = this.getQuantity(product)
      if (quantity === 0) return '$0.00'
      
      const pricePerUnit = product.pricing_data?.price_per_unit || 0
      const minWeight = product.pricing_data?.min_weight || 7
      const maxWeight = product.pricing_data?.max_weight || 15
      
      if (pricePerUnit === 0) return '$0.00'
      
      const minPrice = pricePerUnit * minWeight * quantity
      const maxPrice = pricePerUnit * maxWeight * quantity
      
      if (minPrice === maxPrice) {
        return `$${minPrice.toFixed(2)}`
      }
      return `$${minPrice.toFixed(2)} - $${maxPrice.toFixed(2)}`
    },
    calculateSubtotal() {
      if (!this.deal || !this.deal.products) return '0.00'
      
      let subtotal = 0
      this.deal.products.forEach(product => {
        const itemTotal = parseFloat(this.calculateItemTotal(product))
        subtotal += itemTotal
      })
      
      return subtotal.toFixed(2)
    },
    calculateShippingFee() {
      if (this.deliveryMethod === 'pickup') {
        return 0
      }
      
      // Calculate free shipping subtotal (excluding products that don't count)
      const freeShippingSubtotal = this.deal.products.reduce((sum, product) => {
        const quantity = this.getQuantity(product)
        if (quantity === 0) return sum
        const countsTowardFreeShipping = product.counts_toward_free_shipping !== false
        if (countsTowardFreeShipping) {
          const itemTotal = parseFloat(this.calculateItemTotal(product))
          return sum + itemTotal
        }
        return sum
      }, 0)
      
      // Free shipping for orders >= $150
      return freeShippingSubtotal >= 150 ? 0 : 7.99
    },
    calculateTotal() {
      if (!this.deal || !this.deal.products) return { total: '0.00', hasEstimated: false }
      
      const subtotal = parseFloat(this.calculateSubtotal())
      const shipping = this.calculateShippingFee()
      let hasEstimatedItems = false
      
      this.deal.products.forEach(product => {
        const quantity = this.getQuantity(product)
        if (quantity > 0 && (product.pricing_type === 'weight_range' || product.pricing_type === 'unit_weight' || product.pricing_type === 'bundled_weight')) {
          hasEstimatedItems = true
        }
      })
      
      return { total: (subtotal + shipping).toFixed(2), hasEstimated: hasEstimatedItems }
    },
    hasSelectedItems() {
      return Object.values(this.selectedItems).some(item => item.quantity > 0)
    },
    hasEstimatedTotal() {
      const result = this.calculateTotal()
      return result.hasEstimated
    },
    async updateOrder() {
      if (!this.canEditPaymentDelivery) {
        await this.warning('订单无法修改')
        return
      }
      
      // Build order items - use existing order items if products can't be edited (deal closed or order confirmed)
      let orderItems = []
      
      if (this.canEditProducts) {
        // Can edit products - build from current selections
        this.deal.products.forEach(product => {
          const selection = this.selectedItems[product.id]
          if (selection && selection.quantity > 0) {
            orderItems.push({
              product_id: product.id,
              quantity: selection.quantity,
              pricing_type: product.pricing_type
            })
          }
        })
        
        if (orderItems.length === 0) {
          await this.warning('请至少选择一个商品')
          return
        }
      } else {
        // Products can't be edited (deal closed or order confirmed) - use existing order items (can only update payment/delivery/notes)
        if (this.order.items && this.order.items.length > 0) {
          orderItems = this.order.items.map(item => ({
            product_id: item.product_id,
            quantity: item.quantity,
            pricing_type: item.product?.pricing_type || 'per_item'
          }))
        } else {
          await this.warning('订单中没有商品')
          return
        }
      }
      
      // Validate delivery address if needed
      if (this.deliveryMethod === 'delivery' && !this.selectedAddressId) {
        await this.warning('请选择配送地址')
        return
      }
      
      this.saving = true
      try {
        const orderData = {
          items: orderItems,
          payment_method: this.paymentMethod,
          delivery_method: this.deliveryMethod,
          address_id: this.deliveryMethod === 'delivery' ? this.selectedAddressId : null,
          pickup_location: this.deliveryMethod === 'pickup' ? this.selectedPickupLocation : null,
          notes: this.notes.trim() || null
        }
        
        const response = await apiClient.patch(`/orders/${this.order.id}`, orderData)
        
        // Update local order data
        this.order = response.data.order
        
        await this.success('订单已更新')
        
        // Reload order to get latest data
        await this.loadOrder()
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || '更新订单失败'
        await this.showError(errorMsg)
        console.error('Failed to update order:', error)
      } finally {
        this.saving = false
      }
    },
    openProductModal(product) {
      this.selectedProduct = product
      this.showProductModal = true
    },
    closeProductModal() {
      this.showProductModal = false
      this.selectedProduct = null
    },
    showPriceInfo(message) {
      this.priceInfoMessage = message
      this.showPriceInfoModal = true
    },
    closePriceInfoModal() {
      this.showPriceInfoModal = false
      this.priceInfoMessage = ''
    },
    getProductImage(product) {
      if (product.images && Array.isArray(product.images) && product.images.length > 0) {
        return product.images[0]
      }
      if (product.image) {
        return product.image
      }
      return null
    },
    openAddressModal() {
      if (!this.canEditPaymentDelivery) return
      this.loadAddresses()
      this.showAddressModal = true
    },
    closeAddressModal() {
      this.showAddressModal = false
    },
    selectAddress(address) {
      if (!this.canEditPaymentDelivery) return
      this.selectedAddressId = address.id
      this.selectedAddress = address
      this.closeAddressModal()
    },
    setDeliveryMethod(method) {
      if (!this.canEditPaymentDelivery) return
      this.deliveryMethod = method
    },
    setPickupLocation(location) {
      if (!this.canEditPaymentDelivery) return
      this.selectedPickupLocation = location
    },
    goToAddresses() {
      this.$router.push('/addresses')
    },
    confirmCancelOrder() {
      if (!this.order) return
      this.showCancelModal = true
      this.cancelError = null
    },
    closeCancelModal() {
      this.showCancelModal = false
      this.cancelError = null
    },
    async cancelOrder() {
      if (!this.order) return
      
      this.cancelling = true
      this.cancelError = null
      
      try {
        const response = await apiClient.post(`/orders/${this.order.id}/cancel`)
        
        // Update local order data
        this.order = response.data.order
        
        // Close modal and show success
        this.closeCancelModal()
        
        await this.success('订单已取消')
        
        // Navigate back to orders list after a short delay
        setTimeout(() => {
          this.$router.push('/orders')
        }, 1500)
      } catch (error) {
        this.cancelError = error.response?.data?.message || error.response?.data?.error || '取消订单失败'
        console.error('Failed to cancel order:', error)
      } finally {
        this.cancelling = false
      }
    },
    async reactivateOrder() {
      if (!this.order || !this.deal) return
      
      // Check if deal is closed
      if (this.isDealClosed) {
        await this.warning('团购已截单，无法提交订单')
        return
      }
      
      this.reactivating = true
      
      try {
        const response = await apiClient.post(`/orders/${this.order.id}/reactivate`)
        
        // Update local order data
        this.order = response.data.order
        
        await this.success('订单已重新激活')
        
        // Reload order to get latest data
        await this.loadOrder()
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || '重新激活订单失败'
        await this.showError(errorMsg)
        console.error('Failed to reactivate order:', error)
      } finally {
        this.reactivating = false
      }
    }
  }
}
</script>

<style scoped>
.order-detail-page {
  min-height: 100vh;
  background: var(--md-background);
  padding-bottom: calc(80px + env(safe-area-inset-bottom)); /* Space for bottom nav */
}

.page-header {
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  padding: var(--md-spacing-lg);
  padding-top: calc(var(--md-spacing-lg) + env(safe-area-inset-top));
  box-shadow: var(--md-elevation-2);
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
}

.back-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  padding: var(--md-spacing-xs);
  cursor: pointer;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--md-radius-sm);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
  width: 40px;
  height: 40px;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.back-btn svg {
  width: 24px;
  height: 24px;
  color: white;
}

.header-spacer {
  width: 40px;
  flex-shrink: 0;
}

.header-center {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--md-spacing-sm);
}

.page-header h1 {
  font-size: var(--md-headline-size);
  color: white;
  font-weight: 500;
  text-align: center;
  letter-spacing: -0.5px;
  margin: 0;
}

.loading, .error {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.error {
  color: #C62828;
}

.order-content {
  padding: var(--md-spacing-md);
}

.order-info-section {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  margin-bottom: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
}

.order-header-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--md-spacing-sm);
}

.order-number {
  font-size: var(--md-body-size);
  font-weight: 600;
  color: var(--md-on-surface);
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: var(--md-radius-xl);
  font-size: var(--md-label-size);
  font-weight: 500;
  white-space: nowrap;
}

.status-badge.pending {
  background: #FFF3E0;
  color: #E65100;
}

.status-badge.confirmed {
  background: #E3F2FD;
  color: #1565C0;
}

.status-badge.processing {
  background: #E8F5E9;
  color: #2E7D32;
}

.status-badge.completed {
  background: #4CAF50;
  color: white;
}

.status-badge.cancelled {
  background: #FFEBEE;
  color: #C62828;
}

.order-date {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.deal-info-section {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  margin-bottom: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
}

.deal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--md-spacing-md);
  gap: var(--md-spacing-sm);
  flex-wrap: wrap;
}

.deal-header h2 {
  font-size: var(--md-headline-size);
  color: var(--md-on-surface);
  font-weight: 500;
  flex: 1;
}

.deal-badge {
  padding: 0.375rem 0.875rem;
  border-radius: var(--md-radius-xl);
  font-size: var(--md-label-size);
  font-weight: 500;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  white-space: nowrap;
}

.deal-badge.active {
  background: #FF4444;
  color: white;
}

.deal-badge.closed {
  background: #FFF3E0;
  color: #F57C00;
}

.deal-description {
  color: var(--md-on-surface-variant);
  font-size: var(--md-body-size);
  margin-bottom: var(--md-spacing-lg);
  line-height: 1.5;
  white-space: pre-line;
}

.deal-dates {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
}

.date-row {
  display: flex;
  align-items: flex-start;
  gap: var(--md-spacing-md);
}

.date-icon {
  width: 14px;
  height: 14px;
  color: var(--md-primary);
  flex-shrink: 0;
}

.date-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-xs);
}

.date-label {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.date-value {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  font-weight: 500;
}

.products-section,
.delivery-section,
.payment-section,
.notes-section,
.order-summary-section {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  margin-bottom: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
}

.section-title {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-lg);
  font-weight: 500;
}

.empty-products {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.products-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-lg);
}

.product-item {
  display: flex;
  gap: var(--md-spacing-md);
  padding-bottom: var(--md-spacing-lg);
  border-bottom: 1px solid var(--md-surface-variant);
  flex-wrap: wrap;
}

.product-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.product-image {
  position: relative;
  width: 100px;
  height: 100px;
  flex-shrink: 0;
  border-radius: var(--md-radius-md);
  overflow: hidden;
  background: var(--md-surface-variant);
  cursor: pointer;
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.3;
  color: var(--md-on-surface-variant);
}

.image-placeholder svg {
  width: 32px;
  height: 32px;
}

.sold-out-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: linear-gradient(135deg, #D32F2F 0%, #B71C1C 100%);
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(211, 47, 47, 0.4);
  z-index: 10;
  text-transform: uppercase;
}

.product-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
}

.product-name-row {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-xs);
  flex-wrap: wrap;
}

.product-name {
  font-size: var(--md-body-size);
  font-weight: 500;
  color: var(--md-on-surface);
  cursor: pointer;
  margin: 0;
}

.shipping-excluded-badge {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  background: #FFF3E0;
  color: #E65100;
  flex-shrink: 0;
}

.product-description-preview {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  line-height: 1.4;
  cursor: pointer;
  white-space: pre-line;
}

.product-price {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
}

.price-label {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.price-value {
  font-size: var(--md-body-size);
  font-weight: 600;
  color: var(--md-primary);
}

.stock-info {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin-bottom: var(--md-spacing-xs);
}

.stock-info.out-of-stock {
  color: #D32F2F;
  font-weight: 600;
}

.product-selection.disabled {
  opacity: 0.6;
  pointer-events: none;
}

.product-selection {
  margin-top: var(--md-spacing-sm);
}

.selection-controls {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
  width: 100%;
}

.quantity-control {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
}

.quantity-control label {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  min-width: 40px;
}

.qty-btn {
  width: 32px;
  height: 32px;
  border: 1px solid var(--md-outline);
  background: var(--md-surface);
  border-radius: var(--md-radius-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--md-on-surface);
  font-size: 18px;
  font-weight: 500;
}

.qty-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.qty-input {
  width: 60px;
  height: 32px;
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-sm);
  text-align: center;
  font-size: var(--md-body-size);
  padding: 0 var(--md-spacing-xs);
}

.package-info-wrapper {
  width: 100%;
  margin-top: var(--md-spacing-xs);
}

.package-info {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.item-total {
  font-size: var(--md-body-size);
  font-weight: 600;
  color: var(--md-primary);
  margin-top: var(--md-spacing-xs);
  display: flex;
  align-items: center;
  gap: var(--md-spacing-xs);
}

.item-total.estimated {
  color: var(--md-on-surface-variant);
}

.tooltip-container {
  position: relative;
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  padding: 4px;
  margin-left: 4px;
  border-radius: 50%;
  transition: background-color 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.tooltip-container:hover {
  background-color: var(--md-surface-variant);
}

.info-icon {
  width: 16px;
  height: 16px;
  color: var(--md-on-surface-variant);
  opacity: 0.7;
}

.delivery-options,
.payment-options {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
}

.delivery-option,
.payment-option {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
  padding: var(--md-spacing-md);
  border: 2px solid var(--md-outline-variant);
  border-radius: var(--md-radius-md);
  background: var(--md-surface);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.delivery-option:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.delivery-option.active,
.payment-option.active {
  border-color: var(--md-primary);
  background: rgba(255, 165, 0, 0.1);
}

.option-icon {
  width: 24px;
  height: 24px;
  color: var(--md-primary);
  flex-shrink: 0;
}

.option-content {
  flex: 1;
}

.option-content h4 {
  font-size: var(--md-body-size);
  font-weight: 500;
  color: var(--md-on-surface);
  margin: 0;
}

.option-check {
  width: 24px;
  height: 24px;
  color: var(--md-primary);
  flex-shrink: 0;
}

.payment-radio {
  display: none;
}

.payment-note {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin-top: var(--md-spacing-sm);
}

.pickup-location-selection {
  margin-top: var(--md-spacing-lg);
}

.selection-subtitle {
  font-size: var(--md-body-size);
  font-weight: 500;
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-md);
}

.pickup-locations {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
}

.pickup-location-card {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
  padding: var(--md-spacing-md);
  border: 2px solid var(--md-outline-variant);
  border-radius: var(--md-radius-md);
  background: var(--md-surface);
  cursor: pointer;
  transition: all 0.2s;
}

.pickup-location-card.active {
  border-color: var(--md-primary);
  background: rgba(255, 165, 0, 0.1);
}

.pickup-location-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

.location-icon {
  width: 24px;
  height: 24px;
  color: var(--md-primary);
  flex-shrink: 0;
}

.location-content {
  flex: 1;
}

.location-content h5 {
  font-size: var(--md-body-size);
  font-weight: 500;
  color: var(--md-on-surface);
  margin: 0 0 4px 0;
}

.location-content p {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin: 0;
}

.location-check {
  width: 24px;
  height: 24px;
  color: var(--md-primary);
  flex-shrink: 0;
}

.address-selection {
  margin-top: var(--md-spacing-lg);
}

.select-address-btn {
  width: 100%;
  padding: var(--md-spacing-md);
  border: 2px solid var(--md-outline-variant);
  border-radius: var(--md-radius-md);
  background: var(--md-surface);
  cursor: pointer;
  transition: all 0.2s;
}

.select-address-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.select-address-btn:not(:disabled):hover {
  border-color: var(--md-primary);
}

.btn-content {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
}

.btn-icon {
  width: 24px;
  height: 24px;
  color: var(--md-primary);
  flex-shrink: 0;
}

.btn-text {
  flex: 1;
  text-align: left;
}

.selected-address-preview {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.preview-header {
  display: flex;
  gap: var(--md-spacing-sm);
  align-items: center;
}

.preview-name {
  font-size: var(--md-body-size);
  font-weight: 500;
  color: var(--md-on-surface);
}

.preview-phone {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.preview-address {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.no-address-selected {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.no-address-selected span {
  font-size: var(--md-body-size);
  color: var(--md-on-surface);
}

.hint {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.btn-arrow {
  width: 24px;
  height: 24px;
  color: var(--md-on-surface-variant);
  flex-shrink: 0;
}

.notes-input {
  width: 100%;
  padding: var(--md-spacing-md);
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-family: inherit;
  resize: vertical;
}

.notes-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.notes-hint {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  text-align: right;
  margin-top: var(--md-spacing-xs);
}

.update-order-section {
  padding: var(--md-spacing-xl) var(--md-spacing-md);
  margin-top: var(--md-spacing-lg);
  padding-bottom: calc(var(--md-spacing-xl) + 80px + env(safe-area-inset-bottom)); /* Space for bottom nav */
}

.order-actions {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.update-order-btn,
.cancel-order-btn {
  width: 100%;
  height: 56px;
  padding: 0 var(--md-spacing-md);
  border-radius: var(--md-radius-lg);
  font-size: var(--md-body-size);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--md-elevation-2);
  border: none;
}

.update-order-btn {
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  color: white;
}

.update-order-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--md-surface-variant);
  color: var(--md-on-surface-variant);
}

.update-order-btn:not(:disabled):hover {
  transform: translateY(-2px);
  box-shadow: var(--md-elevation-4);
}

.update-order-btn:not(:disabled):active {
  transform: translateY(0);
  box-shadow: var(--md-elevation-2);
}

.cancel-order-btn {
  background: white;
  color: #C62828;
  border: 2px solid #C62828;
}

.cancel-order-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--md-surface-variant);
  color: var(--md-on-surface-variant);
  border-color: var(--md-outline-variant);
}

.cancel-order-btn:not(:disabled):hover {
  background: #C62828;
  color: white;
  transform: translateY(-2px);
  box-shadow: var(--md-elevation-4);
}

.cancel-order-btn:not(:disabled):active {
  transform: translateY(0);
  box-shadow: var(--md-elevation-2);
}

.reactivate-order-btn {
  width: 100%;
  height: 56px;
  padding: 0 var(--md-spacing-md);
  border-radius: var(--md-radius-lg);
  font-size: var(--md-body-size);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--md-elevation-2);
  border: none;
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  color: white;
}

.reactivate-order-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--md-surface-variant);
  color: var(--md-on-surface-variant);
}

.reactivate-order-btn:not(:disabled):hover {
  transform: translateY(-2px);
  box-shadow: var(--md-elevation-4);
}

.reactivate-order-btn:not(:disabled):active {
  transform: translateY(0);
  box-shadow: var(--md-elevation-2);
}

.deal-closed-note {
  text-align: center;
  font-size: var(--md-label-size);
  color: #E65100;
  margin-top: var(--md-spacing-sm);
  padding: var(--md-spacing-sm);
  background: #FFF3E0;
  border-radius: var(--md-radius-md);
}

.deal-closed-product-note {
  font-size: var(--md-label-size);
  color: #E65100;
  margin-top: var(--md-spacing-xs);
  padding: var(--md-spacing-xs) var(--md-spacing-sm);
  background: #FFF3E0;
  border-radius: var(--md-radius-sm);
  text-align: center;
}

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
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-lg);
  border-bottom: 1px solid var(--md-outline-variant);
}

.modal-header h2 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  font-weight: 500;
  margin: 0;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: var(--md-on-surface-variant);
  cursor: pointer;
  border-radius: var(--md-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn svg {
  width: 20px;
  height: 20px;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--md-spacing-lg);
}

.loading-addresses,
.no-addresses {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.empty-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto var(--md-spacing-md);
  color: var(--md-on-surface-variant);
  opacity: 0.5;
}

.addresses-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.address-card {
  display: flex;
  align-items: flex-start;
  gap: var(--md-spacing-md);
  padding: var(--md-spacing-md);
  border: 2px solid var(--md-outline-variant);
  border-radius: var(--md-radius-md);
  background: var(--md-surface);
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.address-card.active {
  border-color: var(--md-primary);
  background: rgba(255, 165, 0, 0.1);
}

.address-header {
  display: flex;
  gap: var(--md-spacing-sm);
  margin-bottom: var(--md-spacing-xs);
}

.address-name {
  font-size: var(--md-body-size);
  font-weight: 500;
  color: var(--md-on-surface);
}

.address-phone {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.address-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.address-line {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.address-instructions {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  font-style: italic;
  margin-top: 4px;
}

.address-check {
  width: 24px;
  height: 24px;
  color: var(--md-primary);
  flex-shrink: 0;
}

.add-address-btn,
.add-address-btn-secondary {
  width: 100%;
  padding: var(--md-spacing-md);
  border: 2px dashed var(--md-outline);
  border-radius: var(--md-radius-md);
  background: transparent;
  color: var(--md-primary);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: var(--md-spacing-md);
}

.add-address-btn:hover,
.add-address-btn-secondary:hover {
  border-color: var(--md-primary);
  background: rgba(255, 165, 0, 0.1);
}

/* Cancel Modal Styles */
.cancel-modal {
  max-width: 450px;
}

.cancel-warning {
  display: flex;
  gap: var(--md-spacing-md);
  padding: var(--md-spacing-lg);
  background: #FFF3E0;
  border-radius: var(--md-radius-md);
  border-left: 4px solid #FF6F00;
}

.cancel-warning svg {
  width: 48px;
  height: 48px;
  color: #FF6F00;
  flex-shrink: 0;
}

.warning-content h3 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-sm);
  font-weight: 600;
}

.warning-content p {
  font-size: var(--md-body-size);
  color: var(--md-on-surface-variant);
  margin-bottom: var(--md-spacing-xs);
}

.warning-text {
  color: #E65100 !important;
  font-weight: 500;
}

.error-message {
  padding: var(--md-spacing-md);
  background: #FFEBEE;
  color: #C62828;
  border-radius: var(--md-radius-md);
  font-size: var(--md-label-size);
  margin-top: var(--md-spacing-md);
}

.modal-footer {
  display: flex;
  gap: var(--md-spacing-md);
  padding: var(--md-spacing-lg);
  border-top: 1px solid var(--md-outline-variant);
}

.cancel-btn-secondary {
  flex: 1;
  padding: var(--md-spacing-md);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid var(--md-outline);
  background: transparent;
  color: var(--md-on-surface);
}

.cancel-btn-secondary:hover {
  background: var(--md-surface-variant);
}

.confirm-cancel-btn {
  flex: 1;
  padding: var(--md-spacing-md);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  background: #C62828;
  color: white;
}

.confirm-cancel-btn:hover:not(:disabled) {
  background: #B71C1C;
  box-shadow: 0 2px 8px rgba(198, 40, 40, 0.3);
}

.confirm-cancel-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.order-breakdown {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
  margin-top: var(--md-spacing-md);
  padding-top: var(--md-spacing-md);
  border-top: 1px solid var(--md-surface-variant);
}

.breakdown-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.breakdown-label {
  font-size: var(--md-body-size);
  color: var(--md-on-surface-variant);
}

.breakdown-amount {
  font-size: var(--md-body-size);
  font-weight: 600;
  color: var(--md-on-surface);
}

.total-row {
  margin-top: var(--md-spacing-xs);
  padding-top: var(--md-spacing-sm);
  border-top: 1px solid var(--md-surface-variant);
}

.total-label {
  font-size: var(--md-title-size);
  font-weight: 600;
  color: var(--md-on-surface);
}

.total-amount {
  font-size: var(--md-title-size);
  font-weight: 600;
  color: var(--md-primary);
}

@media (max-width: 480px) {
  .product-image {
    width: 80px;
    height: 80px;
  }
  
  .update-order-btn,
  .cancel-order-btn,
  .reactivate-order-btn {
    padding: var(--md-spacing-sm) var(--md-spacing-md);
    font-size: var(--md-label-size);
  }
}
</style>

