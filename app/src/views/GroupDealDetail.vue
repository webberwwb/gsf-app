<template>
  <div class="deal-detail-page">
    <header class="page-header" :class="{ 'admin-draft-header': isAdmin && deal && deal.status === 'draft' }">
      <div class="header-center">
        <h1>团购详情</h1>
        <span v-if="isAdmin && deal && deal.status === 'draft'" class="admin-draft-badge">
          仅管理员可见
        </span>
      </div>
    </header>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="showNoDealPlaceholder" class="no-deal-placeholder">
      <div class="no-deal-icon">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z" />
        </svg>
      </div>
      <p class="no-deal-title">暂无团购</p>
      <p class="no-deal-sub">请查看产品介绍，耐心等待下次团购。</p>
    </div>
    <div v-else-if="deal" class="deal-content">
      <!-- Deal Info Section -->
      <div class="deal-info-section" :class="{ 'admin-draft-section': isAdmin && deal && deal.status === 'draft' }">
        <div v-if="isAdmin && deal && deal.status === 'draft'" class="admin-warning-banner">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="warning-icon">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div class="warning-content">
            <strong>草稿状态 - 仅管理员可见</strong>
            <p>此团购尚未对用户开放, 到开团时间会自动开放。</p>
          </div>
        </div>
        <div class="deal-header">
          <h2>{{ deal.title }}</h2>
          <span :class="['deal-badge', deal.status]">
            {{ getStatusLabel(deal.status) }}
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

      <!-- Loaded via GET /group-deals/latest (see backend for statuses) -->
      <div v-if="deal && deal.status === 'closed'" class="deal-status-notice">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="notice-icon">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div class="notice-content">
          <strong>团购已截单</strong>
          <p>已超过截单时间，商品不可再改。如需调整取货方式或支付，请前往「我的订单」操作。</p>
        </div>
      </div>
      <div v-else-if="deal && dealFulfillmentPhase" class="deal-status-notice fulfillment">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="notice-icon">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div class="notice-content">
          <strong>{{ deal.status === 'preparing' ? '正在配货' : '可以取货' }}</strong>
          <p>订单处理进度请前往「我的订单」查看。</p>
        </div>
      </div>

      <!-- Products Section -->
      <div class="products-section">
        <h3 class="section-title">可选商品</h3>
        
        <!-- Category Tabs -->
        <div v-if="visibleCategories.length > 0" class="category-tabs-sticky-container">
          <div class="category-tabs-wrapper">
            <div class="category-tabs-container">
              <div class="category-tabs" ref="categoryTabs">
                <button
                  v-for="category in visibleCategories"
                  :key="category.id"
                  :class="['category-tab', { 'active': selectedCategoryId === category.id }]"
                  @click="selectCategory(category.id)"
                >
                  {{ category.name }}
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="deal.products && deal.products.length === 0" class="empty-products">
          <p>暂无商品</p>
        </div>
        <div v-else class="products-list">
          <template v-for="group in groupedProducts" :key="group.category?.id || 'uncategorized'">
            <!-- Category Header -->
            <div v-if="group.category" class="category-header" :data-category-id="group.category.id">
              <h3>{{ group.category.name }}</h3>
            </div>
            
            <!-- Products in this category -->
            <div
              v-for="product in group.products"
              :key="product.id"
              class="product-item"
              :data-category-id="product.category_id"
            >
            <div class="product-image" @click="openProductModal(product)">
              <img v-if="getProductImage(product)" :src="getProductImage(product)" :alt="product.name" />
              <div v-else class="image-placeholder">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                </svg>
              </div>
              <!-- Sold Out Badge -->
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
              <div class="product-price-container">
                <div class="product-price">
                  <span class="price-label">团购价:</span>
                  <span v-if="product.pricing_type === 'bundled_weight'" class="price-value">
                    ${{ moneyPlain(product.pricing_data?.price_per_unit || 0) }}/{{ product.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }}
                  </span>
                  <span v-else-if="product.pricing_type === 'weight_range' || product.pricing_type === 'unit_weight'" class="price-value price-range">
                    {{ formatPriceRange(product) }}
                  </span>
                  <span v-else class="price-value">${{ formatPrice(product) }}</span>
                </div>
                
                <!-- Detailed Weight Range Pricing -->
                <div v-if="product.pricing_type === 'weight_range'" class="pricing-details-inline">
                  <div class="pricing-breakdown-compact">
                    <div class="breakdown-header" @click="togglePricingDetails(product.id)">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="info-icon-inline">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span class="breakdown-toggle-text">{{ isPricingExpanded(product.id) ? '收起' : '查看' }}价格明细</span>
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="chevron-icon" :class="{ 'expanded': isPricingExpanded(product.id) }">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                    <Transition name="expand">
                      <div v-if="isPricingExpanded(product.id)" class="weight-ranges-list">
                        <div 
                          v-for="(range, idx) in getSortedWeightRanges(product)" 
                          :key="idx"
                          class="range-item"
                        >
                          <span class="range-weight-text">{{ formatWeightRange(range, product.pricing_data?.unit) }}</span>
                          <span class="range-price-text">${{ moneyPlain(range.price || 0) }}</span>
                        </div>
                        <div class="pricing-note-inline">
                          取货时按实际重量称重结算，重量可能超出上述区间
                        </div>
                      </div>
                    </Transition>
                  </div>
                </div>
                
                <!-- Detailed Unit Weight Pricing -->
                <div v-else-if="product.pricing_type === 'unit_weight'" class="pricing-details-inline">
                  <div class="pricing-breakdown-compact">
                    <div class="breakdown-header" @click="togglePricingDetails(product.id)">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="info-icon-inline">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span class="breakdown-toggle-text">{{ isPricingExpanded(product.id) ? '收起' : '查看' }}价格计算</span>
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="chevron-icon" :class="{ 'expanded': isPricingExpanded(product.id) }">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                    <Transition name="expand">
                      <div v-if="isPricingExpanded(product.id)" class="pricing-calculation">
                        <div class="calculation-formula-inline">
                          最终价格 = 实际重量 × ${{ moneyPlain(product.pricing_data?.price_per_unit || 0) }}/{{ product.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }}
                        </div>
                        <div class="examples-list">
                          <div class="example-item">
                            <span>1 {{ product.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }}</span>
                            <span>→</span>
                            <span class="example-result">${{ moneyPlain(product.pricing_data?.price_per_unit || 0) }}</span>
                          </div>
                          <div class="example-item">
                            <span>2 {{ product.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }}</span>
                            <span>→</span>
                            <span class="example-result">${{ moneyPlain((product.pricing_data?.price_per_unit || 0) * 2) }}</span>
                          </div>
                          <div class="example-item">
                            <span>3 {{ product.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }}</span>
                            <span>→</span>
                            <span class="example-result">${{ moneyPlain((product.pricing_data?.price_per_unit || 0) * 3) }}</span>
                          </div>
                        </div>
                        <div class="pricing-note-inline">
                          取货时称重，按实际重量计算最终价格
                        </div>
                      </div>
                    </Transition>
                  </div>
                </div>
                
                <!-- Detailed Bundled Weight Pricing -->
                <div v-else-if="product.pricing_type === 'bundled_weight'" class="pricing-details-inline">
                  <div class="pricing-breakdown-compact">
                    <div class="breakdown-header" @click="togglePricingDetails(product.id)">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="info-icon-inline">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span class="breakdown-toggle-text">{{ isPricingExpanded(product.id) ? '收起' : '查看' }}价格计算</span>
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="chevron-icon" :class="{ 'expanded': isPricingExpanded(product.id) }">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                    <Transition name="expand">
                      <div v-if="isPricingExpanded(product.id)" class="pricing-calculation">
                        <div class="bundled-info-inline">
                          <div class="info-row">
                            <span class="info-label-inline">每份参考重量:</span>
                            <span class="info-value-inline">{{ product.pricing_data?.min_weight || 7 }} - {{ product.pricing_data?.max_weight || 15 }} {{ product.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }}</span>
                          </div>
                          <div class="info-row">
                            <span class="info-label-inline">单价:</span>
                            <span class="info-value-inline">${{ moneyPlain(product.pricing_data?.price_per_unit || 0) }}/{{ product.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }}</span>
                          </div>
                        </div>
                        <div class="calculation-formula-inline">
                          最终价格 = 实际重量 × ${{ moneyPlain(product.pricing_data?.price_per_unit || 0) }}/{{ product.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }}
                        </div>
                        <div class="examples-list">
                          <div class="example-item">
                            <span>{{ product.pricing_data?.min_weight || 7 }} {{ product.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }}</span>
                            <span>→</span>
                            <span class="example-result">${{ moneyPlain((product.pricing_data?.price_per_unit || 0) * (product.pricing_data?.min_weight || 7)) }}</span>
                          </div>
                          <div class="example-item">
                            <span>{{ Math.round((product.pricing_data?.min_weight || 7) + (product.pricing_data?.max_weight || 15)) / 2 }} {{ product.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }}</span>
                            <span>→</span>
                            <span class="example-result">${{ moneyPlain((product.pricing_data?.price_per_unit || 0) * Math.round(((product.pricing_data?.min_weight || 7) + (product.pricing_data?.max_weight || 15)) / 2)) }}</span>
                          </div>
                          <div class="example-item">
                            <span>{{ product.pricing_data?.max_weight || 15 }} {{ product.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }}</span>
                            <span>→</span>
                            <span class="example-result">${{ moneyPlain((product.pricing_data?.price_per_unit || 0) * (product.pricing_data?.max_weight || 15)) }}</span>
                          </div>
                        </div>
                        <div class="pricing-note-inline">
                          每份重量通常在此范围内，取货时按实际重量称重结算
                        </div>
                      </div>
                    </Transition>
                  </div>
                </div>
              </div>
              <!-- Debug: Remove after testing -->
              <!-- <div style="font-size: 10px; color: gray;">
                Type: {{ product.pricing_type }}, 
                Has ranges: {{ product.pricing_data?.ranges ? 'yes' : 'no' }},
              </div> -->

              <!-- Stock Info -->
              <!-- Only show stock when it's less than 10 (or out of stock) -->
              <div v-if="product.deal_stock_limit !== undefined && product.deal_stock_limit !== null && product.deal_stock_limit < 10" class="stock-info" :class="{ 'out-of-stock': isOutOfStock(product) }">
                <span v-if="isOutOfStock(product)">缺货</span>
                <span v-else>库存: {{ product.deal_stock_limit }} 件</span>
              </div>
              <div v-else-if="product.stock_limit !== undefined && product.stock_limit !== null && product.stock_limit === 0" class="stock-info out-of-stock">
                <span>缺货</span>
              </div>

              <!-- Product Selection Controls -->
              <div class="product-selection" :class="{ 'disabled': isOutOfStock(product) }">
                <ProductDetailsSection
                  v-if="(product.variants || []).length || product.substitute_enabled || product.substitute?.enabled"
                  :product-id="product.id"
                  :variants="product.variants || []"
                  :substitute="product.substitute_enabled || product.substitute?.enabled
                    ? (product.substitute || {
                        name: product.substitute_name,
                        description: product.substitute_description,
                        images: product.substitute_images,
                        pricing_type: product.pricing_type,
                        pricing_data: product.substitute?.pricing_data,
                        price: product.substitute_price
                      })
                    : null"
                  :variant-id="getSelection(product).variant_id"
                  :accept-substitute="getSelection(product).accept_substitute"
                  @update:variant-id="(v) => setVariantId(product, v)"
                  @update:accept-substitute="(v) => setAcceptSubstitute(product, v)"
                />
                <!-- Per Item Pricing -->
                <div v-if="product.pricing_type === 'per_item'" class="selection-controls">
                  <div class="quantity-control">
                    <button @click="decreaseQuantity(product)" :disabled="getQuantity(product) === 0 || !isOrderEditable || isOutOfStock(product)" class="qty-btn">-</button>
                    <input
                      type="number"
                      :value="getQuantity(product)"
                      @input="setQuantity(product, $event.target.value)"
                      min="0"
                      :max="product.deal_stock_limit || 999"
                      :disabled="!isOrderEditable || isOutOfStock(product)"
                      class="qty-input"
                    />
                    <button @click="increaseQuantity(product)" :disabled="(product.deal_stock_limit && getQuantity(product) >= product.deal_stock_limit) || !isOrderEditable || isOutOfStock(product)" class="qty-btn">+</button>
                  </div>
                  <div class="item-total">
                    小计: ${{ calculateItemTotal(product) }}
                  </div>
                </div>

                <!-- Weight Range Pricing -->
                <div v-else-if="product.pricing_type === 'weight_range'" class="selection-controls">
                  <div class="quantity-control">
                    <label>数量:</label>
                    <button @click="decreaseQuantity(product)" :disabled="getQuantity(product) === 0 || !isOrderEditable || isOutOfStock(product)" class="qty-btn">-</button>
                    <input
                      type="number"
                      :value="getQuantity(product)"
                      @input="setQuantity(product, $event.target.value)"
                      min="0"
                      :disabled="!isOrderEditable || isOutOfStock(product)"
                      class="qty-input"
                    />
                    <button @click="increaseQuantity(product)" :disabled="!isOrderEditable || isOutOfStock(product)" class="qty-btn">+</button>
                  </div>
                  <div class="item-total estimated">
                    <span>预估小计: ${{ calculateItemTotal(product) }}</span>
                    <div class="tooltip-container" @click.stop="showPriceInfo('价格基于最低重量估算，实际价格可能因实际重量而有所不同，取货时确认最终价格')">
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
                    <button @click="decreaseQuantity(product)" :disabled="getQuantity(product) === 0 || !isOrderEditable || isOutOfStock(product)" class="qty-btn">-</button>
                    <input
                      type="number"
                      :value="getQuantity(product)"
                      @input="setQuantity(product, $event.target.value)"
                      min="0"
                      :disabled="!isOrderEditable || isOutOfStock(product)"
                      class="qty-input"
                    />
                    <button @click="increaseQuantity(product)" :disabled="!isOrderEditable || isOutOfStock(product)" class="qty-btn">+</button>
                  </div>
                  <div class="item-total estimated">
                    <span>预估小计: ${{ calculateItemTotal(product) }}</span>
                    <div class="tooltip-container" @click="showPriceInfo('价格基于最低重量估算，实际价格可能因实际重量而有所不同，取货时确认最终价格')">
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
                    <button @click="decreaseQuantity(product)" :disabled="getQuantity(product) === 0 || !isOrderEditable || isOutOfStock(product)" class="qty-btn">-</button>
                    <input
                      type="number"
                      :value="getQuantity(product)"
                      @input="setQuantity(product, $event.target.value)"
                      min="0"
                      step="1"
                      :disabled="!isOrderEditable || isOutOfStock(product)"
                      class="qty-input"
                    />
                    <button @click="increaseQuantity(product)" :disabled="!isOrderEditable || isOutOfStock(product)" class="qty-btn">+</button>
                  </div>
                  <div class="package-info-wrapper">
                    <span class="package-info">(每份 {{ product.pricing_data?.min_weight || 7 }}-{{ product.pricing_data?.max_weight || 15 }}{{ product.pricing_data?.unit === 'kg' ? 'lb' : 'lb' }})</span>
                  </div>
                  <div class="item-total estimated">
                    <span>预估小计: {{ calculateBundledItemTotal(product) }}</span>
                    <div class="tooltip-container" @click="showPriceInfo('价格基于最低重量估算，实际价格可能因实际重量而有所不同，取货时确认最终价格')">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="info-icon">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          </template>
        </div>
      </div>
    </div>

    <!-- Fixed Bottom Bar -->
    <div v-if="deal && hasSelectedItems()" class="bottom-bar">
      <div class="total-info">
        <span class="total-label">{{ isOrderCompleted ? '最终价格' : (hasEstimatedTotal() ? '预估总计' : '总计') }}:</span>
        <span class="total-amount">${{ calculateTotal().total }}</span>
        <span v-if="hasEstimatedTotal() && !isOrderCompleted" class="estimated-note">(估算)</span>
      </div>
      <button @click="confirmOrder" class="confirm-order-btn" :disabled="!isOrderEditable">
        确认下单
      </button>
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
  </div>
</template>

<script>
import apiClient from '../api/client'
import { useCheckoutStore } from '../stores/checkout'
import { useAuthStore } from '../stores/auth'
import { formatDateEST_CN, formatDateTimeEST_CN, formatPickupDateTime_CN } from '../utils/date'
import { useModal } from '../composables/useModal'
import ProductDetailModal from '../components/ProductDetailModal.vue'
import Modal from '../components/Modal.vue'
import ProductDetailsSection from '../components/ProductDetailsSection.vue'
import {
  estimateLinePrice,
  estimateSelectionTotal,
  isSelectionComplete,
  getSelectionIncompleteMessage
} from '../utils/orderItemPricing'
import {
  formatMoney,
  formatMoneyDisplay,
  formatProductListPrice,
  formatProductPriceRange,
  roundMoney
} from '../utils/productPriceDisplay'

export default {
  name: 'GroupDealDetail',
  components: {
    ProductDetailModal,
    Modal,
    ProductDetailsSection
  },
  data() {
    return {
      loading: true,
      error: null,
      deal: null,
      selectedItems: {}, // { productId: { quantity } }
      showProductModal: false,
      selectedProduct: null,
      showPriceInfoModal: false,
      priceInfoMessage: '',
      expandedPricing: {}, // Track which products have expanded pricing details
      categories: [],
      selectedCategoryId: null,
      stickyOriginalTop: null // Store original position of sticky container
    }
  },
  setup() {
    const checkoutStore = useCheckoutStore()
    const authStore = useAuthStore()
    const { warning, error: showError } = useModal()
    return { checkoutStore, authStore, warning, showError }
  },
  computed: {
    isAuthenticated() {
      return this.authStore.isAuthenticated
    },
    isAdmin() {
      return this.authStore.isAdmin
    },
    dealFulfillmentPhase() {
      return this.deal && ['preparing', 'ready_for_pickup'].includes(this.deal.status)
    },
    isOrderEditable() {
      if (!this.deal) return false
      if (this.deal.status === 'active') return true
      // Admins can place test orders on draft deals (draft is admin-only in the API)
      if (this.isAdmin && this.deal.status === 'draft') return true
      return false
    },
    showNoDealPlaceholder() {
      return !this.loading && !this.error && !this.deal
    },
    filteredProducts() {
      // Always show all products, no filtering
      if (!this.deal || !this.deal.products) return []
      return this.deal.products
    },
    groupedProducts() {
      // Group products by category for display with headers
      if (!this.deal || !this.deal.products || !this.categories) return []
      
      const groups = []
      
      // First, add products that have categories
      this.visibleCategories.forEach(category => {
        const categoryProducts = this.deal.products.filter(p => p.category_id === category.id)
        if (categoryProducts.length > 0) {
          groups.push({
            category: category,
            products: categoryProducts
          })
        }
      })
      
      // Then, add products without category (if any)
      const uncategorizedProducts = this.deal.products.filter(p => !p.category_id)
      if (uncategorizedProducts.length > 0) {
        groups.push({
          category: null,
          products: uncategorizedProducts
        })
      }
      
      return groups
    },
    visibleCategories() {
      if (!this.deal || !this.deal.products || !this.categories) return []
      
      // Only show categories that have at least one product in this group deal
      return this.categories.filter(category => {
        return this.deal.products.some(product => product.category_id === category.id)
      })
    }
  },
    async mounted() {
    if (!this.authStore.token) {
      this.authStore.loadFromStorage()
    }
    await this.loadDeal()
    await this.loadCategories()
    
    // Setup scroll indicator detection
    this.$nextTick(() => {
      this.setupScrollIndicators()
      this.setupStickyFallback()
      this.setupScrollSpy()
    })
  },
  beforeUnmount() {
    // Cleanup scroll listener
    if (this.$refs.categoryTabs) {
      const container = this.$refs.categoryTabs.parentElement
      container?.removeEventListener('scroll', this.updateScrollIndicators)
      window.removeEventListener('resize', this.updateScrollIndicators)
    }
    // Cleanup sticky fallback
    window.removeEventListener('scroll', this.handleStickyScroll)
    // Cleanup scroll spy
    window.removeEventListener('scroll', this.handleScrollSpy)
  },
  methods: {
    async loadDeal() {
      this.loading = true
      this.error = null
      this.deal = null
      this.selectedItems = {}
      try {
        const response = await apiClient.get('/group-deals/latest')
        this.deal = response.data.deal
        if (this.deal && this.deal.products) {
          this.deal.products.forEach(product => {
            this.selectedItems[product.id] = {
              quantity: 0
            }
          })
        }
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || '加载团购详情失败'
        console.error('Failed to load deal:', error)
      } finally {
        this.loading = false
      }
    },
    async loadCategories() {
      try {
        const response = await apiClient.get('/product-categories')
        this.categories = response.data.categories || []
      } catch (error) {
        console.error('Failed to load categories:', error)
      }
    },
    selectCategory(categoryId) {
      this.selectedCategoryId = categoryId
      
      // Scroll to the category section
      this.$nextTick(() => {
        // Find the category header for this category
        const categoryHeader = document.querySelector(`.category-header[data-category-id="${categoryId}"]`)
        
        if (categoryHeader) {
          // Calculate dynamic offset based on actual header and tab heights
          const header = document.querySelector('.page-header')
          const stickyContainer = document.querySelector('.category-tabs-sticky-container')
          
          let offset = 140 // Default fallback
          if (header && stickyContainer) {
            const headerHeight = header.offsetHeight
            const tabsHeight = stickyContainer.offsetHeight
            offset = headerHeight + tabsHeight + 10 // 10px padding
          }
          
          const elementPosition = categoryHeader.getBoundingClientRect().top
          const offsetPosition = elementPosition + window.pageYOffset - offset
          
          window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
          })
        }
      })
    },
    setupScrollIndicators() {
      const container = this.$refs.categoryTabs?.parentElement
      if (!container) return
      
      this.updateScrollIndicators()
      container.addEventListener('scroll', this.updateScrollIndicators)
      
      // Also update on window resize
      window.addEventListener('resize', this.updateScrollIndicators)
    },
    setupStickyFallback() {
      // Check if we're in iOS PWA standalone mode
      const isStandalone = window.matchMedia('(display-mode: standalone)').matches || 
                          window.navigator.standalone === true
      const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream
      
      // Only apply fallback if needed (iOS PWA)
      if (isIOS && isStandalone) {
        // Wait for content to load then store initial position
        setTimeout(() => {
          const stickyContainer = document.querySelector('.category-tabs-sticky-container')
          if (stickyContainer) {
            // Store the initial offset from top of document
            this.stickyOriginalTop = stickyContainer.offsetTop
          }
          window.addEventListener('scroll', this.handleStickyScroll, { passive: true })
          this.handleStickyScroll()
        }, 500)
      }
    },
    handleStickyScroll() {
      const stickyContainer = document.querySelector('.category-tabs-sticky-container')
      const header = document.querySelector('.page-header')
      const productsSection = document.querySelector('.products-section')
      const dealContent = document.querySelector('.deal-content')
      
      if (!stickyContainer || !header || !productsSection || !dealContent) return
      
      // If we haven't stored the original position yet, store it now
      if (this.stickyOriginalTop === null) {
        this.stickyOriginalTop = stickyContainer.offsetTop
      }
      
      const headerHeight = header.offsetHeight
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop
      
      // Get the deal-content padding (margin from screen edge)
      const dealContentPadding = 24 // Adjusted to match visual spacing
      
      // Get the products section dimensions
      const productsSectionLeft = productsSection.offsetLeft
      const productsSectionWidth = productsSection.offsetWidth
      
      // The sticky container has negative margin to extend to edges of products section
      // We want it to stay within the deal-content bounds
      const leftPosition = dealContentPadding
      const width = window.innerWidth - (dealContentPadding * 2)
      
      // If we've scrolled past where the sticky container originally was
      if (scrollTop >= (this.stickyOriginalTop - headerHeight)) {
        // Create a placeholder to prevent layout shift if it doesn't exist
        let placeholder = stickyContainer.previousElementSibling
        if (!placeholder || !placeholder.classList.contains('sticky-placeholder')) {
          placeholder = document.createElement('div')
          placeholder.className = 'sticky-placeholder'
          placeholder.style.height = `${stickyContainer.offsetHeight}px`
          placeholder.style.marginBottom = `${getComputedStyle(stickyContainer).marginBottom}`
          stickyContainer.parentNode.insertBefore(placeholder, stickyContainer)
        }
        
        stickyContainer.style.position = 'fixed'
        stickyContainer.style.top = `${headerHeight + 5}px`
        stickyContainer.style.left = `${leftPosition}px`
        stickyContainer.style.right = 'auto'
        stickyContainer.style.width = `${width}px`
        stickyContainer.style.zIndex = '100'
        stickyContainer.style.margin = '0'
        stickyContainer.style.boxSizing = 'border-box'
      } else {
        // Remove placeholder when unsticking
        const placeholder = stickyContainer.previousElementSibling
        if (placeholder && placeholder.classList.contains('sticky-placeholder')) {
          placeholder.remove()
        }
        
        // Reset to normal flow - explicitly set all values
        stickyContainer.style.position = ''
        stickyContainer.style.top = ''
        stickyContainer.style.left = ''
        stickyContainer.style.right = ''
        stickyContainer.style.width = ''
        stickyContainer.style.zIndex = ''
        stickyContainer.style.margin = ''
        stickyContainer.style.boxSizing = ''
      }
    },
    setupScrollSpy() {
      window.addEventListener('scroll', this.handleScrollSpy, { passive: true })
      // Initial call
      this.handleScrollSpy()
    },
    handleScrollSpy() {
      // Throttle the scroll spy for performance
      if (this._scrollSpyTimeout) return
      
      this._scrollSpyTimeout = setTimeout(() => {
        this._scrollSpyTimeout = null
        
        const header = document.querySelector('.page-header')
        const stickyContainer = document.querySelector('.category-tabs-sticky-container')
        
        if (!header || !stickyContainer) return
        
        const headerHeight = header.offsetHeight
        const tabsHeight = stickyContainer.offsetHeight
        const offset = headerHeight + tabsHeight + 20 // Offset from top where we check
        
        // Get all category headers
        const categoryHeaders = document.querySelectorAll('.category-header[data-category-id]')
        
        if (categoryHeaders.length === 0) return
        
        // Find which category is currently in view
        let currentCategoryId = null
        
        for (const categoryHeader of categoryHeaders) {
          const rect = categoryHeader.getBoundingClientRect()
          
          // If the category header is above the offset point, it's the active one
          if (rect.top <= offset) {
            currentCategoryId = categoryHeader.getAttribute('data-category-id')
          } else {
            // Once we find one that's below, stop
            break
          }
        }
        
        // Update selected category if changed
        if (currentCategoryId && this.selectedCategoryId !== parseInt(currentCategoryId)) {
          this.selectedCategoryId = parseInt(currentCategoryId)
          
          // Auto-scroll the tab bar to show the active tab
          this.$nextTick(() => {
            this.scrollTabIntoView(parseInt(currentCategoryId))
          })
        }
      }, 100) // 100ms throttle
    },
    scrollTabIntoView(categoryId) {
      const tabsContainer = this.$refs.categoryTabs?.parentElement
      if (!tabsContainer) return
      
      // Find the active tab button
      const activeTab = tabsContainer.querySelector(`.category-tab[class*="active"]`)
      if (!activeTab) return
      
      // Get positions relative to the scroll container
      const containerScrollLeft = tabsContainer.scrollLeft
      const tabOffsetLeft = activeTab.offsetLeft
      const tabWidth = activeTab.offsetWidth
      const containerWidth = tabsContainer.clientWidth
      
      // Calculate visible range
      const visibleStart = containerScrollLeft
      const visibleEnd = containerScrollLeft + containerWidth
      const tabStart = tabOffsetLeft
      const tabEnd = tabOffsetLeft + tabWidth
      
      // Check if tab is out of view
      const isOutOfViewLeft = tabStart < visibleStart
      const isOutOfViewRight = tabEnd > visibleEnd
      
      // Only scroll if the tab is out of view
      if (isOutOfViewLeft) {
        // Tab is off to the left - scroll to show it with some padding
        const targetScrollLeft = Math.max(0, tabOffsetLeft - 20) // 20px padding, don't go below 0
        tabsContainer.scrollTo({
          left: targetScrollLeft,
          behavior: 'smooth'
        })
      } else if (isOutOfViewRight) {
        // Tab is off to the right - scroll to show it with some padding
        const targetScrollLeft = tabOffsetLeft - containerWidth + tabWidth + 20 // 20px padding from right
        tabsContainer.scrollTo({
          left: targetScrollLeft,
          behavior: 'smooth'
        })
      }
      // If tab is already visible, don't scroll
    },
    updateScrollIndicators() {
      const container = this.$refs.categoryTabs?.parentElement
      const wrapper = container?.parentElement
      if (!container) return
      
      const canScrollLeft = container.scrollLeft > 10
      const canScrollRight = container.scrollLeft < container.scrollWidth - container.clientWidth - 10
      
      if (canScrollLeft) {
        container.classList.add('can-scroll-left')
      } else {
        container.classList.remove('can-scroll-left')
      }
      
      if (canScrollRight) {
        container.classList.add('can-scroll-right')
      } else {
        container.classList.remove('can-scroll-right')
      }
      
      // Hide animation hint after user scrolls
      if (container.scrollLeft > 0 && wrapper) {
        wrapper.classList.add('user-has-scrolled')
      }
    },
    formatDate(dateString) {
      // This shows date only, not datetime
      return formatDateEST_CN(dateString)
    },
    formatDateTime(dateString) {
      return formatDateTimeEST_CN(dateString)
    },
    formatPickupDate(dateString) {
      return formatPickupDateTime_CN(dateString)
    },
    formatPrice(product) {
      return formatProductListPrice(product)
    },
    formatPriceRange(product) {
      return formatProductPriceRange(product)
    },
    money(value) {
      return formatMoneyDisplay(value)
    },
    moneyPlain(value) {
      return formatMoney(value)
    },
    getStatusLabel(status) {
      const labels = {
        draft: '草稿',
        active: '进行中',
        closed: '已截单',
        preparing: '正在配货',
        ready_for_pickup: '可以取货'
      }
      return labels[status] || status
    },
    isOrderCompleted() {
      return false // This is for the deal detail page, not order completion
    },
    getQuantity(product) {
      return this.selectedItems[product.id]?.quantity || 0
    },
    setQuantity(product, value) {
      // Check if product is out of stock
      if (this.isOutOfStock(product)) {
        return
      }
      
      const qty = parseInt(value) || 0
      const maxQty = product.deal_stock_limit || 999
      const finalQty = Math.max(0, Math.min(qty, maxQty))

      if (finalQty > 0) {
        const selection = this.getSelection(product)
        if (!isSelectionComplete(product, selection)) {
          this.warning(getSelectionIncompleteMessage(product, selection))
          return
        }
      }

      if (!this.selectedItems[product.id]) {
        this.selectedItems[product.id] = { quantity: 0, variant_id: null, accept_substitute: null }
      }
      this.selectedItems[product.id].quantity = finalQty
    },
    increaseQuantity(product) {
      if (this.isOutOfStock(product)) {
        return
      }
      const selection = this.getSelection(product)
      if (!isSelectionComplete(product, selection)) {
        this.warning(getSelectionIncompleteMessage(product, selection))
        return
      }

      const current = this.getQuantity(product)
      const maxQty = product.deal_stock_limit || 999
      this.setQuantity(product, Math.min(current + 1, maxQty))
    },
    isOutOfStock(product) {
      if (!product) return false
      
      // Check deal_stock_limit (deal-specific inventory)
      // null or undefined means unlimited stock, only 0 means out of stock
      if (product.deal_stock_limit !== undefined && product.deal_stock_limit !== null) {
        return product.deal_stock_limit === 0
      }
      
      return false // No stock limit means unlimited stock
    },
    decreaseQuantity(product) {
      const current = this.getQuantity(product)
      this.setQuantity(product, Math.max(current - 1, 0))
    },
    getSelection(product) {
      if (!this.selectedItems[product.id]) {
        this.selectedItems[product.id] = { quantity: 0, variant_id: null, accept_substitute: null }
      }
      return this.selectedItems[product.id]
    },
    setVariantId(product, variantId) {
      this.getSelection(product).variant_id = variantId
    },
    setAcceptSubstitute(product, value) {
      this.getSelection(product).accept_substitute = value
    },
    calculateItemTotal(product) {
      const quantity = this.getQuantity(product)
      if (quantity === 0) return '0.00'
      const sel = this.getSelection(product)
      const { totalPrice } = estimateLinePrice(product, {
        quantity,
        variant_id: sel.variant_id
      })
      return formatMoney(totalPrice)
    },
    calculateBundledItemTotal(product) {
      const quantity = this.getQuantity(product)
      if (quantity === 0) return '$0.00'
      const sel = this.getSelection(product)
      const total = estimateSelectionTotal(product, quantity, { variant_id: sel.variant_id })
      return formatMoneyDisplay(total)
    },
    calculateTotal() {
      if (!this.deal || !this.deal.products) return '0.00'
      
      let total = 0
      let hasEstimatedItems = false
      this.deal.products.forEach(product => {
        const itemTotal = parseFloat(this.calculateItemTotal(product))
        total += itemTotal
        if (itemTotal > 0 && (product.pricing_type === 'weight_range' || product.pricing_type === 'unit_weight' || product.pricing_type === 'bundled_weight')) {
          hasEstimatedItems = true
        }
      })
      return { total: formatMoney(total), hasEstimated: hasEstimatedItems }
    },
    hasSelectedItems() {
      return Object.values(this.selectedItems).some(item => item.quantity > 0)
    },
    hasEstimatedTotal() {
      const result = this.calculateTotal()
      return result.hasEstimated
    },
    async confirmOrder() {
      const orderItems = []
      
      for (const product of this.deal.products) {
        const selection = this.selectedItems[product.id]
        if (!selection || selection.quantity <= 0) continue

        if (!isSelectionComplete(product, selection)) {
          await this.warning(getSelectionIncompleteMessage(product, selection))
          return
        }

        const variant = (product.variants || []).find((v) => v.id === selection.variant_id)
        const { totalPrice } = estimateLinePrice(product, {
          quantity: selection.quantity,
          variant_id: selection.variant_id
        })
        const isEstimated = ['weight_range', 'unit_weight', 'bundled_weight'].includes(product.pricing_type)

        orderItems.push({
          product_id: product.id,
          quantity: selection.quantity,
          pricing_type: product.pricing_type,
          variant_id: selection.variant_id || undefined,
          variant_name: variant?.name || undefined,
          accept_substitute: selection.accept_substitute,
          estimated_price: formatMoney(totalPrice),
          is_estimated: isEstimated,
          counts_toward_free_shipping: product.counts_toward_free_shipping !== false
        })
      }
      
      if (orderItems.length === 0) {
        await this.warning('请至少选择一个商品')
        return
      }
      
      // Store data in Pinia store for checkout page
      this.checkoutStore.setDeal(this.deal)
      this.checkoutStore.setOrderItems(orderItems)
      
      // Clear existing order data - always create new order
      this.checkoutStore.setExistingOrder(null, null, null)
      
      // Navigate to checkout page - it will use the store data
      this.$router.push('/checkout')
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
      // Support both old single image format and new multiple images format
      if (product.images && Array.isArray(product.images) && product.images.length > 0) {
        return product.images[0]
      }
      if (product.image) {
        return product.image
      }
      return null
    },
    togglePricingDetails(productId) {
      this.expandedPricing[productId] = !this.expandedPricing[productId]
    },
    isPricingExpanded(productId) {
      return this.expandedPricing[productId] || false
    },
    getSortedWeightRanges(product) {
      if (!product.pricing_data?.ranges) return []
      return [...product.pricing_data.ranges].sort((a, b) => (a.min || 0) - (b.min || 0))
    },
    formatWeightRange(range, unit = 'lb') {
      const displayUnit = unit === 'kg' ? 'lb' : 'lb'
      if (range.max === null || range.max === undefined) {
        return `${range.min}+ ${displayUnit}`
      }
      return `${range.min} - ${range.max} ${displayUnit}`
    }
  }
}
</script>

<style scoped>
.deal-detail-page {
  min-height: 100vh;
  background: var(--md-background);
  padding-bottom: calc(80px + env(safe-area-inset-bottom)); /* Space for bottom nav */
}

.page-header {
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  padding: var(--md-spacing-lg);
  padding-top: calc(var(--md-spacing-lg) + env(safe-area-inset-top));
  box-shadow: var(--md-elevation-2);
  position: -webkit-sticky;
  position: sticky;
  top: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-center {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--md-spacing-sm);
  flex-wrap: wrap;
}

.header-logo {
  width: 32px;
  height: 32px;
  object-fit: contain;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.15));
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

.no-deal-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: var(--md-spacing-xl);
  min-height: 45vh;
  color: var(--md-on-surface-variant);
}

.no-deal-icon {
  width: 72px;
  height: 72px;
  opacity: 0.35;
  margin-bottom: var(--md-spacing-md);
}

.no-deal-icon svg {
  width: 100%;
  height: 100%;
}

.no-deal-title {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  font-weight: 500;
  margin: 0 0 var(--md-spacing-xs);
}

.no-deal-sub {
  font-size: var(--md-body-size);
  margin: 0;
  opacity: 0.85;
}

.deal-content {
  padding: var(--md-spacing-md);
  padding-bottom: 150px;
}

.deal-info-section {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  margin-bottom: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.deal-info-section:hover {
  box-shadow: var(--md-elevation-2);
}

.deal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--md-spacing-md);
  gap: var(--md-spacing-sm);
  flex-wrap: wrap;
}

@media (max-width: 480px) {
  .deal-header h2 {
    font-size: var(--md-title-size);
  }
  
  .deal-badge {
    font-size: 0.75rem;
    padding: 4px 8px;
  }
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
  box-shadow: 0 2px 4px rgba(255, 68, 68, 0.3);
}

.deal-badge.closed {
  background: #FFF3E0;
  color: #F57C00;
  box-shadow: 0 2px 4px rgba(245, 124, 0, 0.3);
}

.deal-badge.preparing {
  background: #E3F2FD;
  color: #1565C0;
}

.deal-badge.ready_for_pickup {
  background: #E8F5E9;
  color: #2E7D32;
}

.deal-badge.draft {
  background: #E0E0E0;
  color: #616161;
  box-shadow: 0 2px 4px rgba(97, 97, 97, 0.2);
}

.page-header.admin-draft-header {
  background: linear-gradient(135deg, #9C27B0 0%, #673AB7 100%);
}

.admin-draft-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border-radius: var(--md-radius-xl);
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.5px;
  margin-left: var(--md-spacing-sm);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.deal-info-section.admin-draft-section {
  border: 2px dashed #9C27B0;
  background: linear-gradient(135deg, rgba(156, 39, 176, 0.03) 0%, rgba(103, 58, 183, 0.03) 100%);
}

.admin-warning-banner {
  display: flex;
  align-items: flex-start;
  gap: var(--md-spacing-md);
  padding: var(--md-spacing-md);
  background: linear-gradient(135deg, rgba(156, 39, 176, 0.1) 0%, rgba(103, 58, 183, 0.1) 100%);
  border: 2px solid #9C27B0;
  border-radius: var(--md-radius-md);
  margin-bottom: var(--md-spacing-lg);
}

.warning-icon {
  width: 24px;
  height: 24px;
  color: #9C27B0;
  flex-shrink: 0;
  margin-top: 2px;
}

.warning-content {
  flex: 1;
}

.warning-content strong {
  display: block;
  color: #6A1B9A;
  font-size: var(--md-body-size);
  margin-bottom: var(--md-spacing-xs);
}

.warning-content p {
  color: #7B1FA2;
  font-size: var(--md-label-size);
  line-height: 1.5;
  margin: 0;
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

@media (max-width: 480px) {
  .date-row {
    gap: var(--md-spacing-sm);
  }
  
  .date-value {
    font-size: 0.75rem;
  }
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

.products-section {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.products-section:hover {
  box-shadow: var(--md-elevation-2);
}

.section-title {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-md);
  font-weight: 500;
}

.category-tabs-sticky-container {
  position: -webkit-sticky;
  position: sticky;
  top: 85px;
  z-index: 100;
  margin: 0 calc(-1 * var(--md-spacing-lg));
  margin-bottom: var(--md-spacing-lg);
  background: var(--md-surface);
  box-sizing: border-box;
}

.category-tabs-sticky-container::before {
  content: '';
  position: absolute;
  top: -5px;
  left: 0;
  right: 0;
  height: 5px;
  background: var(--md-surface);
  z-index: -1;
}

.category-tabs-wrapper {
  background: var(--md-surface);
  padding: var(--md-spacing-lg) var(--md-spacing-lg);
  padding-top: calc(var(--md-spacing-lg) + 5px);
  padding-bottom: var(--md-spacing-md);
  box-shadow: none;
  position: relative;
  overflow: hidden;
  box-sizing: border-box;
}

.category-tabs-wrapper::before {
  display: none;
}

/* Hide animation when user has scrolled */
.category-tabs-wrapper.user-has-scrolled::before {
  display: none;
}

.category-tabs-wrapper::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--md-outline-variant);
  opacity: 0.3;
}

.category-tabs-container {
  position: relative;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  scroll-behavior: smooth;
}

.category-tabs-container::-webkit-scrollbar {
  display: none;
}

.scroll-indicator {
  display: none;
}

.category-tabs {
  display: flex;
  gap: var(--md-spacing-sm);
  min-width: min-content;
  padding-bottom: var(--md-spacing-xs);
  padding-left: 2px;
  padding-right: 2px;
}

.category-tab {
  flex-shrink: 0;
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  border: none;
  background: var(--md-surface-variant);
  color: var(--md-on-surface-variant);
  border-radius: var(--md-radius-md);
  font-size: var(--md-label-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
  position: relative;
  -webkit-tap-highlight-color: transparent;
  min-height: 44px;
  display: flex;
  align-items: center;
  overflow: visible;
}

.category-tab:hover {
  background: var(--md-outline-variant);
}

.category-tab.active {
  background: var(--md-primary);
  color: white;
}

.category-tab:active {
  transform: scale(0.96);
}

@media (max-width: 480px) {
  .category-tab {
    padding: var(--md-spacing-xs) var(--md-spacing-md);
    font-size: 0.8125rem;
  }
  
  .category-tabs-sticky-container {
    top: 85px;
    margin-left: calc(-1 * var(--md-spacing-md));
    margin-right: calc(-1 * var(--md-spacing-md));
  }
  
  .category-tabs-wrapper {
    padding: var(--md-spacing-sm) var(--md-spacing-md);
  }
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

.category-header {
  margin-top: var(--md-spacing-lg);
  margin-bottom: var(--md-spacing-md);
  padding-bottom: var(--md-spacing-sm);
  border-bottom: 2px solid var(--md-primary);
}

.category-header:first-child {
  margin-top: 0;
}

.category-header h3 {
  font-size: var(--md-title-size);
  color: var(--md-primary);
  font-weight: 600;
  margin: 0;
}

.product-item {
  display: flex;
  gap: var(--md-spacing-md);
  padding-bottom: var(--md-spacing-lg);
  border-bottom: 1px solid var(--md-surface-variant);
  flex-wrap: wrap;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
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
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.product-image:hover {
  transform: scale(1.05);
  box-shadow: var(--md-elevation-2);
}

@media (max-width: 480px) {
  .product-image {
    width: 80px;
    height: 80px;
  }
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
  transition: color 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  margin: 0;
}

.product-name:hover {
  color: var(--md-primary);
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
  transition: color 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: pre-line;
}

.product-description-preview:hover {
  color: var(--md-on-surface);
}

.package-info-wrapper {
  width: 100%;
  margin-top: var(--md-spacing-xs);
}

.package-info {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  white-space: normal;
}

.product-price-container {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
  width: 100%;
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

.price-value.price-range {
  white-space: nowrap;
}

.pricing-details-inline {
  width: 100%;
  margin-top: 4px;
}

.pricing-breakdown-compact {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.breakdown-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

.breakdown-header:hover {
  background: #f3f4f6;
}

.breakdown-header:active {
  background: #e5e7eb;
}

.info-icon-inline {
  width: 16px;
  height: 16px;
  color: #6b7280;
  flex-shrink: 0;
}

.breakdown-toggle-text {
  font-size: 13px;
  color: #374151;
  font-weight: 500;
  flex: 1;
}

.chevron-icon {
  width: 16px;
  height: 16px;
  color: #6b7280;
  flex-shrink: 0;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.chevron-icon.expanded {
  transform: rotate(180deg);
}

.weight-ranges-list,
.pricing-calculation {
  padding: 12px;
  background: white;
  border-top: 1px solid #e5e7eb;
}

.range-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  background: #f9fafb;
  border-radius: 6px;
  margin-bottom: 6px;
  border: 1px solid #e5e7eb;
}

.range-item:last-of-type {
  margin-bottom: 8px;
}

.range-weight-text {
  font-size: 13px;
  color: #374151;
  font-weight: 500;
}

.range-price-text {
  font-size: 15px;
  font-weight: 700;
  color: #FF4444;
}

.calculation-formula-inline {
  padding: 10px 12px;
  background: #f9fafb;
  border-radius: 6px;
  font-size: 13px;
  color: #374151;
  font-weight: 500;
  margin-bottom: 8px;
  border: 1px solid #e5e7eb;
  font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
}

.bundled-info-inline {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 8px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.info-label-inline {
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
}

.info-value-inline {
  font-size: 14px;
  color: #111827;
  font-weight: 600;
}

.examples-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 8px;
}

.example-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background: #f9fafb;
  border-radius: 6px;
  font-size: 13px;
  color: #374151;
  border: 1px solid #e5e7eb;
}

.example-item span:first-child {
  font-weight: 500;
  min-width: 50px;
}

.example-item span:nth-child(2) {
  color: #9ca3af;
  font-weight: 600;
}

.example-result {
  font-weight: 700;
  color: #FF4444;
  margin-left: auto;
  font-size: 14px;
}

.pricing-note-inline {
  font-size: 12px;
  color: #92400e;
  background: #fffbeb;
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid #fde68a;
  line-height: 1.4;
}

.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
}

.expand-enter-to,
.expand-leave-from {
  opacity: 1;
  max-height: 500px;
}

.original-price {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  text-decoration: line-through;
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
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.9;
    transform: scale(1.02);
  }
}


.product-selection.disabled {
  opacity: 0.6;
  pointer-events: none;
}

.product-selection.disabled .quantity-control {
  opacity: 0.5;
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

@media (max-width: 480px) {
  .selection-controls {
    gap: var(--md-spacing-xs);
    flex-direction: column;
  }
  
  .quantity-control {
    flex-wrap: wrap;
    gap: var(--md-spacing-xs);
  }
  
  .quantity-control label {
    min-width: auto;
    width: 100%;
  }
  
  .package-info-wrapper {
    margin-top: 2px;
  }
  
  .package-info {
    font-size: 0.75rem;
    line-height: 1.4;
  }
  
  .item-total {
    width: 100%;
    text-align: left;
    flex-wrap: wrap;
  }
  
  .item-total.estimated {
    flex-direction: row;
    align-items: center;
    gap: var(--md-spacing-xs);
  }
  
  .price-value.price-range {
    font-size: 0.9rem;
    line-height: 1.4;
  }
  
  .product-item {
    padding: var(--md-spacing-md);
  }
  
  .product-details {
    gap: var(--md-spacing-sm);
  }
  
  .product-price {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .price-value {
    font-size: 1rem;
  }
  
  .tooltip-container {
    padding: 8px;
    margin-left: 6px;
  }
  
  .info-icon {
    width: 18px;
    height: 18px;
  }
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

.qty-btn:not(:disabled):hover {
  background: var(--md-surface-variant);
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

.weight-input-group {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  flex-wrap: wrap;
}

@media (max-width: 480px) {
  .weight-input-group {
    width: 100%;
  }
  
  .weight-input-group label {
    min-width: 60px;
    font-size: 0.8rem;
  }
  
  .weight-input {
    flex: 1;
    min-width: 80px;
  }
}

.weight-input-group label {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  min-width: 80px;
}

.weight-input {
  flex: 1;
  max-width: 120px;
  height: 32px;
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-sm);
  padding: 0 var(--md-spacing-sm);
  font-size: var(--md-body-size);
}

.unit-label {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  min-width: 30px;
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
  -webkit-tap-highlight-color: transparent;
}

.tooltip-container:hover {
  background-color: var(--md-surface-variant);
}

.tooltip-container:active {
  background-color: var(--md-outline-variant);
}

.info-icon {
  width: 16px;
  height: 16px;
  color: var(--md-on-surface-variant);
  flex-shrink: 0;
  opacity: 0.7;
  transition: opacity 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.tooltip-container:hover .info-icon,
.tooltip-container:active .info-icon {
  opacity: 1;
}


.bottom-bar {
  position: fixed;
  bottom: calc(80px + env(safe-area-inset-bottom)); /* Above bottom nav */
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.95);
  padding: var(--md-spacing-md);
  box-shadow: var(--md-elevation-4);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--md-spacing-md);
  z-index: 99;
  padding-bottom: calc(var(--md-spacing-md) + env(safe-area-inset-bottom));
}

.total-info {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-xs);
}

.total-label {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  display: flex;
  align-items: center;
  gap: var(--md-spacing-xs);
}

.total-amount {
  font-size: var(--md-headline-size);
  font-weight: 600;
  color: var(--md-primary);
}

.estimated-note {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  font-weight: 400;
  margin-left: var(--md-spacing-xs);
}

.confirm-order-btn {
  flex: 1;
  max-width: 200px;
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  background: var(--md-primary);
  color: white;
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
}

.confirm-order-btn:disabled {
  background: #4CAF50;
  cursor: default;
  opacity: 1;
}

@media (max-width: 480px) {
  .confirm-order-btn {
    padding: var(--md-spacing-sm) var(--md-spacing-md);
    font-size: var(--md-label-size);
  }
  
  .total-amount {
    font-size: var(--md-title-size);
  }
}

.confirm-order-btn:hover:not(:disabled) {
  background: #FF7F00;
  box-shadow: var(--md-elevation-2);
}

.deal-status-notice {
  display: flex;
  align-items: flex-start;
  gap: var(--md-spacing-md);
  padding: var(--md-spacing-md);
  background: linear-gradient(135deg, rgba(255, 152, 0, 0.1) 0%, rgba(245, 124, 0, 0.1) 100%);
  border: 2px solid #FF9800;
  border-radius: var(--md-radius-md);
  margin-bottom: var(--md-spacing-lg);
}

.deal-status-notice .notice-icon {
  width: 24px;
  height: 24px;
  color: #F57C00;
  flex-shrink: 0;
  margin-top: 2px;
}

.deal-status-notice .notice-content {
  flex: 1;
}

.deal-status-notice .notice-content strong {
  display: block;
  color: #E65100;
  font-size: var(--md-body-size);
  margin-bottom: var(--md-spacing-xs);
}

.deal-status-notice .notice-content p {
  color: #F57C00;
  font-size: var(--md-label-size);
  line-height: 1.5;
  margin: 0;
}

.deal-status-notice.fulfillment {
  border-color: #1565C0;
  background: linear-gradient(135deg, rgba(21, 101, 192, 0.06) 0%, rgba(46, 125, 50, 0.05) 100%);
}
.deal-status-notice.fulfillment .notice-icon {
  color: #1565C0;
}
.deal-status-notice.fulfillment .notice-content strong {
  color: #0D47A1;
}
.deal-status-notice.fulfillment .notice-content p {
  color: #1565C0;
}
</style>

