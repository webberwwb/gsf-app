<template>
  <div
    ref="pageRef"
    class="group-deal-detail-page"
    :class="{ 'is-pulling': showIndicator }"
    :style="{ transform: contentTransform }"
  >
    <PullToRefreshIndicator
      v-if="showIndicator"
      :height="indicatorHeight"
      :refreshing="refreshing"
      :ready-to-refresh="readyToRefresh"
      :status-text="statusText"
    />
    <div class="page-header">
      <div class="page-nav">
        <button @click="goBack" class="back-btn" aria-label="返回">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          <span class="back-label">返回</span>
        </button>
        <h1 class="page-nav-title">{{ groupDeal?.title || '团购详情' }}</h1>
        <div class="nav-spacer" aria-hidden="true"></div>
      </div>

      <div class="header-actions">
        <button @click="viewCommission" class="commission-btn" :disabled="loading || !groupDeal">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          查看分红
        </button>
        <button @click="bulkMarkDelivering" class="bulk-delivery-btn" :disabled="loading || !groupDeal || loadingBulkUpdate">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
          </svg>
          {{ loadingBulkUpdate ? '更新中...' : '批量标记配送中' }}
        </button>
        <button @click="exportOrders" class="export-btn" :disabled="loading || !groupDeal">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          导出订单
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="!groupDeal" class="error">团购活动不存在</div>
    <div v-else>
      <!-- Group Deal Info -->
      <div class="deal-info-card">
        <div class="deal-header">
          <h2>{{ groupDeal.title }}</h2>
          <div class="status-control-group">
            <span :class="['status-badge', groupDeal.status]">
              {{ getStatusLabel(groupDeal.status) }}
            </span>
            <select 
              v-model="groupDeal.status" 
              @change="handleGroupDealStatusChange"
              :disabled="updatingGroupDealStatus"
              class="status-select"
            >
              <option value="draft">草稿</option>
              <option value="upcoming">即将开始</option>
              <option value="active">进行中</option>
              <option value="closed">已截单</option>
              <option value="preparing">正在配货</option>
              <option value="ready_for_pickup">可以取货</option>
              <option value="completed">已完成</option>
            </select>
          </div>
        </div>
        
        <div v-if="groupDeal.description" class="deal-description">
          {{ groupDeal.description }}
        </div>
        
        <div class="deal-dates">
          <div class="date-item">
            <span class="date-label">下单时间:</span>
            <span class="date-value">
              {{ formatDateTime(groupDeal.order_start_date) }} - {{ formatDateTime(groupDeal.order_end_date) }}
            </span>
          </div>
          <div class="date-item">
            <span class="date-label">取货时间:</span>
            <span class="date-value">{{ formatPickupDate(groupDeal.pickup_date) }}</span>
          </div>
        </div>
      </div>

      <!-- Statistics Section -->
      <div class="statistics-section">
        <button
          v-if="narrowMobile"
          type="button"
          class="mobile-stats-toggle"
          :aria-expanded="mobileStatsSummaryOpen"
          @click="mobileStatsSummaryOpen = !mobileStatsSummaryOpen"
        >
          <span>统计汇总</span>
          <svg class="toggle-chevron" :class="{ 'is-open': mobileStatsSummaryOpen }" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        <h3 v-else class="stats-heading-desktop">统计汇总</h3>
        <div v-show="!narrowMobile || mobileStatsSummaryOpen" class="stats-grid">
          <!-- Total Orders -->
          <div class="stat-card">
            <div class="stat-icon">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-label">总订单数</div>
              <div class="stat-value">{{ statistics.totalOrders }}</div>
            </div>
          </div>

          <!-- Total Revenue (Combined Payment Status) -->
          <div class="stat-card">
            <div class="stat-icon paid-icon">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-label">总收入</div>
              <div class="stat-value">{{ statistics.totalPaidOrders }} / {{ statistics.totalOrders }}</div>
              <div class="stat-subvalue">${{ formatStatMoney(statistics.totalPaidAmount) }} / ${{ formatStatMoney(statistics.totalAmount) }}</div>
            </div>
          </div>

          <!-- Delivery vs Pickup -->
          <div class="stat-card">
            <div class="stat-icon delivery-icon">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-label">配送进度</div>
              <div class="stat-value">{{ statistics.totalShippedDelivery }} / {{ statistics.totalDelivery }}</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon pickup-icon">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-label">取货进度</div>
              <div class="stat-value">{{ statistics.totalPickedUpPickup }} / {{ statistics.totalPickup }}</div>
            </div>
          </div>

          <!-- EMT Payment -->
          <div class="stat-card">
            <div class="stat-icon emt-icon">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-label">EMT收款</div>
              <div class="stat-value">{{ statistics.emtPaidCount }} / {{ statistics.emtCount }}</div>
              <div class="stat-subvalue">${{ formatStatMoney(statistics.emtReceived) }} / ${{ formatStatMoney(statistics.emtTotal) }}</div>
            </div>
          </div>

          <!-- Cash Payment -->
          <div class="stat-card">
            <div class="stat-icon cash-icon">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-label">现金收款</div>
              <div class="stat-value">{{ statistics.cashPaidCount }} / {{ statistics.cashCount }}</div>
              <div class="stat-subvalue">${{ formatStatMoney(statistics.cashReceived) }} / ${{ formatStatMoney(statistics.cashTotal) }}</div>
            </div>
          </div>
        </div>

        <!-- Product Statistics -->
        <div v-if="statistics.productCounts.length > 0" class="product-stats-section">
          <button
            v-if="narrowMobile"
            type="button"
            class="mobile-stats-toggle product-stats-toggle"
            :aria-expanded="mobileProductStatsOpen"
            @click="mobileProductStatsOpen = !mobileProductStatsOpen"
          >
            <span>商品统计</span>
            <svg class="toggle-chevron" :class="{ 'is-open': mobileProductStatsOpen }" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <div v-show="!narrowMobile || mobileProductStatsOpen" class="product-stats-inner">
          <div class="product-stats-header" :class="{ 'product-stats-header--narrow': narrowMobile }">
            <h4 v-if="!narrowMobile">商品统计</h4>
            <button 
              v-if="selectedProductFilters.length > 0" 
              @click="clearProductFilters" 
              class="clear-filters-btn">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
              清除筛选 ({{ selectedProductFilters.length }})
            </button>
          </div>

          <div class="product-stats-controls">
            <div class="product-stats-segment" role="tablist" aria-label="商品统计分组方式">
              <button
                type="button"
                role="tab"
                :aria-selected="productStatsGroupMode === 'product'"
                :class="['segment-chip', { active: productStatsGroupMode === 'product' }]"
                @click="setProductStatsGroupMode('product')"
              >
                按商品
              </button>
              <button
                type="button"
                role="tab"
                :aria-selected="productStatsGroupMode === 'supplier'"
                :class="['segment-chip', { active: productStatsGroupMode === 'supplier' }]"
                @click="setProductStatsGroupMode('supplier')"
              >
                按供应商
              </button>
              <button
                type="button"
                role="tab"
                :aria-selected="productStatsGroupMode === 'category'"
                :class="['segment-chip', { active: productStatsGroupMode === 'category' }]"
                @click="setProductStatsGroupMode('category')"
              >
                按分类
              </button>
            </div>
          </div>

          <div
            v-if="productStatsGroupMode !== 'product' && productStatsTabs.length > 0"
            class="product-stats-chips"
            role="tablist"
            :aria-label="productStatsGroupMode === 'supplier' ? '供应商' : '分类'"
          >
            <button
              v-for="tab in productStatsTabs"
              :key="tab.key"
              type="button"
              role="tab"
              :aria-selected="activeProductStatsTab === tab.key"
              :class="['stats-chip', { active: activeProductStatsTab === tab.key }]"
              @click="activeProductStatsTab = tab.key"
            >
              <span class="stats-chip-label">{{ tab.label }}</span>
              <span class="stats-chip-badges">
                <span class="stats-chip-badge">{{ tab.productCount }} 种</span>
                <span class="stats-chip-badge stats-chip-badge--qty">{{ tab.totalQuantity }} 件</span>
              </span>
            </button>
          </div>

          <div
            v-if="visibleProductStatsSummary"
            class="product-stats-tab-summary"
          >
            <span class="product-stats-tab-summary-name">{{ visibleProductStatsSummary.label }}</span>
            <span class="product-stats-tab-summary-stats">
              {{ visibleProductStatsSummary.productCount }} 种 ·
              数量 {{ visibleProductStatsSummary.totalQuantity }} ·
              销售额 ${{ formatStatMoney(visibleProductStatsSummary.totalSalesValue) }}
            </span>
          </div>
          
          <!-- Selected Products Summary -->
          <div v-if="selectedProductFilters.length > 0" class="selected-products-summary">
            <div class="summary-header">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <h5>已选商品汇总 ({{ selectedProductFilters.length }} 个商品)</h5>
            </div>
            <div class="summary-stats-grid">
              <div class="summary-stat-card">
                <div class="summary-stat-label">总销售额</div>
                <div class="summary-stat-value">${{ formatStatMoney(selectedProductsSummary.totalSales) }}</div>
              </div>
              <div class="summary-stat-card">
                <div class="summary-stat-label">订单数量</div>
                <div class="summary-stat-value">{{ selectedProductsSummary.totalOrders }}</div>
              </div>
              <div class="summary-stat-card">
                <div class="summary-stat-label">商品总数</div>
                <div class="summary-stat-value">{{ selectedProductsSummary.totalQuantity }}</div>
              </div>
              <div class="summary-stat-card">
                <div class="summary-stat-label">平均订单额</div>
                <div class="summary-stat-value">
                  ${{ formatStatMoney(selectedProductsSummary.totalOrders > 0 ? selectedProductsSummary.totalSales / selectedProductsSummary.totalOrders : 0) }}
                </div>
              </div>
            </div>
          </div>
          
          <div v-if="visibleProductStats.length === 0" class="product-stats-empty">
            暂无商品数据
          </div>
          <div v-else class="product-stats-list">
            <div 
              v-for="productStat in visibleProductStats" 
              :key="productStat.statKey"
              :class="['product-stat-item', { active: isProductFilterActive(productStat.statKey), 'is-variant-row': productStat.variantId != null }]"
              @click="toggleProductFilter(productStat.statKey)"
            >
              <div class="product-stat-content">
                <div class="product-stat-name">{{ productStat.displayName }}</div>
                <div class="product-stat-details">
                  <div class="product-stat-value">数量: {{ productStat.totalQuantity }}</div>
                  <div class="product-stat-sales">${{ formatStatMoney(productStat.totalSalesValue) }}</div>
                </div>
              </div>
              <div v-if="isProductFilterActive(productStat.statKey)" class="product-stat-check">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
          </div>
          </div>
        </div>
      </div>

      <GroupDealFulfillmentPanel
        v-if="groupDeal?.products?.some(p => p.substitute_enabled || p.substitute?.enabled)"
        :group-deal-id="groupDeal.id"
        :products="groupDeal.products"
        :orders="orders"
        @fulfillment-updated="onFulfillmentUpdated"
      />

      <!-- Orders List -->
      <div class="orders-section">
        <div v-if="ordersStore.state.loading" class="orders-loading">
          <div class="loading-spinner">
            <svg class="spinner" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>加载订单中...</span>
          </div>
        </div>
        <template v-else>
        <div class="orders-header">
          <h3>订单列表 ({{ filteredOrders.length }}{{ hasActiveOrderFilters ? ' - 已筛选' : '' }})</h3>
          <div class="orders-header-actions">
            <div class="search-box">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="search-icon">
                <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input 
                v-model="searchQuery" 
                type="text" 
                placeholder="搜索订单 (用户名/微信/电话/订单号)"
                class="search-input"
                @input="handleSearch"
              />
              <button 
                v-if="searchQuery" 
                @click="clearSearch" 
                class="clear-search-btn"
                title="清除搜索">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div class="view-mode-toggle">
              <button 
                :class="['view-mode-btn', { active: viewMode === 'card' }]"
                @click="viewMode = 'card'"
                title="卡片视图">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                </svg>
              </button>
              <button 
                :class="['view-mode-btn', { active: viewMode === 'list' }]"
                @click="viewMode = 'list'"
                title="列表视图">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            </div>
            <button @click="findDuplicates" class="duplicates-btn" :disabled="loadingDuplicates">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" style="width: 20px; height: 20px;">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
              {{ loadingDuplicates ? '查找中...' : '查找一人多单' }}
            </button>
          </div>
        </div>
        
        <div v-if="!ordersStore.state.loading && orders.length === 0" class="empty-state">
          <p>暂无订单</p>
        </div>
        <div v-else-if="!ordersStore.state.loading">
          <!-- Order Tabs and Filters -->
          <div class="order-tabs-container">
            <div class="order-tabs">
              <button 
                :class="['tab-btn', 'pickup-tab', { active: activeOrderTab === 'pickup' }]"
                @click="activeOrderTab = 'pickup'">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                自取 ({{ filteredPickupOrders.length }})
              </button>
              <button 
                :class="['tab-btn', 'delivery-tab', { active: activeOrderTab === 'delivery' }]"
                @click="activeOrderTab = 'delivery'">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                </svg>
                配送 ({{ filteredDeliveryOrders.length }})
              </button>
              <button 
                :class="['tab-btn', 'all-tab', { active: activeOrderTab === 'all' }]"
                @click="activeOrderTab = 'all'">
                全部订单 ({{ filteredAllOrders.length }})
              </button>
            </div>
            <div class="order-filters">
              <label class="checkbox-label">
                <input type="checkbox" v-model="showCompletedOrders" class="checkbox-input">
                <span class="checkbox-text">显示已完成订单</span>
              </label>
              <select v-model="weightFilter" class="source-filter-select">
                <option value="">全部称重状态</option>
                <option value="not_weighed">未称重</option>
                <option value="weighed">已称重</option>
              </select>
              <select v-model="packingFilter" class="source-filter-select">
                <option value="">全部配货状态</option>
                <option value="not_packed">未配货</option>
                <option value="packing_complete">配货完成</option>
              </select>
              <select v-model="notesFilter" class="source-filter-select">
                <option value="">全部备注</option>
                <option value="has_notes">有备注</option>
                <option value="no_notes">无备注</option>
              </select>
              <select v-model="orderSort" class="source-filter-select">
                <option value="payment">排序: 未付款优先</option>
                <option value="weight_asc">排序: 未称重优先</option>
                <option value="weight_desc">排序: 已称重优先</option>
                <option value="packing_asc">排序: 未配货优先</option>
                <option value="packing_desc">排序: 配货完成优先</option>
              </select>
              <select v-model="userSourceFilter" class="source-filter-select">
                <option value="">全部获客渠道</option>
                <option value="花泽">花泽</option>
                <option value="default">默认</option>
              </select>
            </div>
          </div>

          <!-- Orders List -->
          <div v-if="viewMode === 'card'" class="orders-list">
            <OrderCard
              v-for="order in filteredOrders"
              :key="order.id"
              :order="order"
              :show-delete="true"
              :show-actions="false"
              :items-expanded-by-default="true"
              @click="viewOrderDetail(order)"
              @delete="deleteOrder"
              @mark-packing-complete="handleMarkPackingComplete"
            />
          </div>
          
          <!-- Orders List View -->
          <GroupDealOrderListView
            v-else
            :orders="filteredOrders"
            :loading="false"
            @order-click="viewOrderDetail"
            @mark-packing-complete="handleMarkPackingComplete"
          />
        </div>
        </template>
      </div>
      
      <!-- Order Detail Modal -->
      <OrderDetailModal
        ref="orderDetailModal"
        :show="showOrderDetail"
        :order="selectedOrder"
        :available-products="availableProducts"
        :updating-order="updatingOrder"
        :marking-complete="markingComplete"
        :update-error="updateError"
        @close="closeOrderDetail"
        @update="handleUpdateOrder"
        @mark-paid="markOrderAsPaid"
        @mark-unpaid="markOrderAsUnpaid"
        @mark-complete="markOrderComplete"
        @status-change="handleOrderStatusChange"
        @payment-method-change="handlePaymentMethodChange"
        @order-updated="handleOrderUpdated"
      @update-error="(msg) => { this.updateError = msg }"
      />

      <!-- Duplicates Modal -->
      <div v-if="showDuplicatesModal" class="modal-overlay" @click="closeDuplicatesModal">
        <div class="modal-content duplicates-modal" @click.stop>
          <div class="modal-header">
            <h2>一人多单</h2>
            <button @click="closeDuplicatesModal" class="close-btn">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div class="modal-body">
            <div v-if="duplicates.length === 0" class="empty-state">
              <p>没有找到一人多单</p>
            </div>
            <div v-else class="duplicates-list">
              <div v-for="(duplicateSet, index) in duplicates" :key="index" class="duplicate-set">
                <div class="duplicate-header">
                  <div class="user-info">
                    <strong>{{ duplicateSet.user?.nickname || '用户' }}</strong>
                    <span v-if="duplicateSet.user?.phone" class="phone">{{ duplicateSet.user.phone }}</span>
                  </div>
                  <div class="group-deal-info">
                    <span>{{ duplicateSet.group_deal?.title }}</span>
                  </div>
                </div>
                <div class="duplicate-orders">
                  <div v-for="order in duplicateSet.orders" :key="order.id" class="duplicate-order">
                    <div class="order-id">{{ order.order_number }}</div>
                    <div class="order-details">
                      <span>商品: {{ order.items?.length || 0 }}件</span>
                      <span>应付: ${{ formatDuplicateOrderDue(order) }}</span>
                      <span>状态: {{ getStatusText(order.status) }}</span>
                    </div>
                  </div>
                </div>
                <button @click="openMergeModal(duplicateSet.orders)" class="merge-btn-action">
                  合并这些订单
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Order Merge Modal -->
      <OrderMergeModal
        :show="showMergeModal"
        :orders="ordersToMerge"
        @close="closeMergeModal"
        @merged="handleOrderMerged"
      />

      <!-- Commission Breakdown Modal -->
      <CommissionBreakdownModal
        v-if="showCommissionModal && groupDeal"
        :groupDeal="groupDeal"
        @close="closeCommissionModal"
      />
    </div>
  </div>
</template>

<script>
import { ref, getCurrentInstance } from 'vue'
import apiClient from '../api/client'
import { formatDateTimeEST_CN, formatPickupDateTime_CN } from '../utils/date'
import { useModal } from '../composables/useModal'
import { usePullToRefresh } from '../composables/usePullToRefresh'
import { useOrdersStore } from '../stores/orders'
import { usePageHeader } from '../stores/pageHeader'
import OrderCard from '../components/OrderCard.vue'
import GroupDealOrderListView from '../components/GroupDealOrderListView.vue'
import OrderDetailModal from '../components/OrderDetailModal.vue'
import OrderMergeModal from '../components/OrderMergeModal.vue'
import CommissionBreakdownModal from '../components/CommissionBreakdownModal.vue'
import GroupDealFulfillmentPanel from '../components/GroupDealFulfillmentPanel.vue'
import PullToRefreshIndicator from '../components/PullToRefreshIndicator.vue'
import { orderHasMissingFinalWeight, statusChangeWarnsIfMissingFinalWeight } from '../utils/orderWeightValidation'
import { orderAmountDueNumber, formatOrderMoney2, orderFinalTotalNumber, orderStoreCreditAppliedNumber } from '../utils/orderPricing'
import { calculateOrderPoints } from '../utils/orderPoints'
import { resolveOrderLineTotal } from '../utils/orderItemPricing'
import { loadGroupDealOrderPrefs, saveGroupDealOrderPrefs } from '../utils/groupDealOrderPrefs'

const PACKING_COMPLETE_STATUSES = ['packing_complete', 'ready_for_pickup', 'out_for_delivery', 'delivering', 'completed']

export default {
  name: 'GroupDealDetail',
  components: {
    OrderCard,
    GroupDealOrderListView,
    OrderDetailModal,
    OrderMergeModal,
    CommissionBreakdownModal,
    GroupDealFulfillmentPanel,
    PullToRefreshIndicator
  },
  setup() {
    const instance = getCurrentInstance()
    const pageRef = ref(null)
    const { confirm, success, error: showError } = useModal()
    const ordersStore = useOrdersStore()
    const {
      showIndicator,
      indicatorHeight,
      contentTransform,
      statusText,
      readyToRefresh,
      refreshing
    } = usePullToRefresh({
      hostRef: pageRef,
      onRefresh: () => instance?.proxy?.refreshPage?.(),
      isEnabled: () => {
        const vm = instance?.proxy
        if (!vm) return false
        return !vm.showOrderDetail && !vm.showDuplicatesModal && !vm.showMergeModal && !vm.showCommissionModal
      }
    })
    return {
      pageRef,
      showIndicator,
      indicatorHeight,
      contentTransform,
      statusText,
      readyToRefresh,
      refreshing,
      confirm,
      success,
      showError,
      ordersStore
    }
  },
  async beforeRouteLeave(to, from, next) {
    if (this.showOrderDetail && this.$refs.orderDetailModal?.hasUnsavedChanges) {
      const ok = await this.confirm(
        '您有未保存的订单修改（含称重、商品、备注等）。确定离开此页吗？未保存的修改将丢失。',
        { type: 'warning', title: '未保存的修改' }
      )
      if (!ok) return next(false)
    }
    next()
  },
  data() {
    const orderPrefs = loadGroupDealOrderPrefs()
    return {
      loading: true,
      error: null,
      groupDeal: null,
      showOrderDetail: false,
      selectedOrder: null,
      availableProducts: [],
      updatingOrder: false,
      updateError: null,
      markingComplete: false,
      updatingGroupDealStatus: false,
      activeOrderTab: orderPrefs.activeOrderTab,
      selectedProductFilters: [],
      searchQuery: '',
      showCompletedOrders: orderPrefs.showCompletedOrders,
      weightFilter: orderPrefs.weightFilter,
      packingFilter: orderPrefs.packingFilter,
      notesFilter: orderPrefs.notesFilter,
      orderSort: orderPrefs.orderSort,
      userSourceFilter: orderPrefs.userSourceFilter,
      // Duplicate orders
      loadingDuplicates: false,
      showDuplicatesModal: false,
      duplicates: [],
      showMergeModal: false,
      ordersToMerge: [],
      // Bulk update
      loadingBulkUpdate: false,
      // Commission
      showCommissionModal: false,
      // View mode
      viewMode: orderPrefs.viewMode, // 'card' or 'list'
      narrowMobile: false,
      mobileStatsSummaryOpen: true,
      mobileProductStatsOpen: true,
      productStatsGroupMode: 'product',
      activeProductStatsTab: null
    }
  },
  watch: {
    productStatsTabs: {
      handler(tabs) {
        if (this.productStatsGroupMode === 'product') {
          this.activeProductStatsTab = null
          return
        }
        if (!tabs?.length) {
          this.activeProductStatsTab = null
          return
        }
        if (!tabs.some((tab) => tab.key === this.activeProductStatsTab)) {
          this.activeProductStatsTab = tabs[0].key
        }
      },
      immediate: true
    }
  },
  created() {
    if (typeof window !== 'undefined') {
      const narrow = window.innerWidth <= 767
      this.narrowMobile = narrow
      if (narrow) {
        this.mobileStatsSummaryOpen = false
        this.mobileProductStatsOpen = false
      }
    }
  },
  watch: {
    orderListPrefs: {
      deep: true,
      handler(prefs) {
        saveGroupDealOrderPrefs(prefs)
      }
    }
  },
  computed: {
    orderListPrefs() {
      return {
        activeOrderTab: this.activeOrderTab,
        showCompletedOrders: this.showCompletedOrders,
        weightFilter: this.weightFilter,
        packingFilter: this.packingFilter,
        notesFilter: this.notesFilter,
        orderSort: this.orderSort,
        userSourceFilter: this.userSourceFilter,
        viewMode: this.viewMode
      }
    },
    orders() {
      let orders = this.ordersStore.state.orders
      
      // Filter out completed orders by default unless checkbox is checked
      if (!this.showCompletedOrders) {
        orders = orders.filter(order => order.status !== 'completed')
      }
      
      return orders
    },
    filteredOrders() {
      let orders = []
      
      // First filter by tab
      switch (this.activeOrderTab) {
        case 'all':
          orders = this.orders
          break
        case 'delivery':
          orders = this.deliveryOrders
          break
        case 'pickup':
          orders = this.pickupOrders
          break
        default:
          orders = this.orders
      }
      
      // Then filter by selected products (if any)
      if (this.selectedProductFilters.length > 0) {
        orders = orders.filter(order => {
          if (!order.items || !Array.isArray(order.items)) {
            return false
          }
          // Check if order contains ANY of the selected products
          return order.items.some((item) => this.itemMatchesProductFilter(item))
        })
      }
      
      // Then filter by search query (if any)
      if (this.searchQuery && this.searchQuery.trim()) {
        const query = this.searchQuery.trim().toLowerCase()
        orders = orders.filter(order => {
          // Search by username
          const username = (order.user?.nickname || '').toLowerCase()
          if (username.includes(query)) return true
          
          // Search by wechat name
          const wechat = (order.user?.wechat || '').toLowerCase()
          if (wechat.includes(query)) return true
          
          // Search by phone number
          const phone = (order.user?.phone || '').toLowerCase()
          if (phone.includes(query)) return true
          
          // Search by order number
          const orderNumber = (order.order_number || '').toLowerCase()
          if (orderNumber.includes(query)) return true
          
          return false
        })
      }
      
      // Then filter by user source (if any)
      if (this.userSourceFilter) {
        orders = orders.filter(order => {
          const userSource = order.user?.user_source || 'default'
          return userSource === this.userSourceFilter
        })
      }

      // Filter by weight state
      if (this.weightFilter === 'not_weighed') {
        orders = orders.filter(order => orderHasMissingFinalWeight(order))
      } else if (this.weightFilter === 'weighed') {
        orders = orders.filter(order => !orderHasMissingFinalWeight(order))
      }

      // Filter by packing state
      if (this.packingFilter === 'not_packed') {
        orders = orders.filter(order => !this.isOrderPackingComplete(order))
      } else if (this.packingFilter === 'packing_complete') {
        orders = orders.filter(order => this.isOrderPackingComplete(order))
      }

      // Filter by order notes
      if (this.notesFilter === 'has_notes') {
        orders = orders.filter(order => this.orderHasNotes(order))
      } else if (this.notesFilter === 'no_notes') {
        orders = orders.filter(order => !this.orderHasNotes(order))
      }
      
      orders.sort((a, b) => this.compareOrdersForSort(a, b))
      
      return orders
    },
    hasActiveOrderFilters() {
      return this.selectedProductFilters.length > 0
        || !!this.searchQuery?.trim()
        || !!this.userSourceFilter
        || !!this.weightFilter
        || !!this.packingFilter
        || !!this.notesFilter
    },
    filteredAllOrders() {
      return this.applyProductFilter(this.orders)
    },
    filteredDeliveryOrders() {
      return this.applyProductFilter(this.deliveryOrders)
    },
    filteredPickupOrders() {
      return this.applyProductFilter(this.pickupOrders)
    },
    deliveryOrders() {
      return this.orders.filter(order => order.delivery_method === 'delivery')
    },
    pickupOrders() {
      return this.orders.filter(order => order.delivery_method === 'pickup')
    },
    statistics() {
      // Use all orders from store, not filtered ones
      const allOrders = this.ordersStore.state.orders || []
      
      if (!allOrders || allOrders.length === 0) {
        return {
          totalOrders: 0,
          totalAmount: 0,
          totalPaidOrders: 0,
          totalPaidAmount: 0,
          totalUnpaidOrders: 0,
          totalUnpaidAmount: 0,
          totalDelivery: 0,
          totalPickup: 0,
          totalShippedOrPickedUp: 0,
          totalShippedDelivery: 0,
          totalPickedUpPickup: 0,
          productCounts: [],
          emtTotal: 0,
          emtReceived: 0,
          emtCount: 0,
          emtPaidCount: 0,
          cashTotal: 0,
          cashReceived: 0,
          cashCount: 0,
          cashPaidCount: 0
        }
      }

      let totalAmount = 0
      let totalPaidOrders = 0
      let totalPaidAmount = 0
      let totalUnpaidOrders = 0
      let totalUnpaidAmount = 0
      let totalDelivery = 0
      let totalPickup = 0
      let totalShippedOrPickedUp = 0
      let totalShippedDelivery = 0
      let totalPickedUpPickup = 0
      
      // Payment method tracking
      let emtTotal = 0
      let emtReceived = 0
      let emtCount = 0
      let emtPaidCount = 0
      let cashTotal = 0
      let cashReceived = 0
      let cashCount = 0
      let cashPaidCount = 0
      
      const productCountsMap = new Map()
      const dealProducts = this.groupDeal?.products || []
      const productById = new Map(dealProducts.map((p) => [p.id, p]))

      allOrders.forEach(order => {
        const orderTotal = orderFinalTotalNumber(order)
        totalAmount += orderTotal

        // Payment status
        if (order.payment_status === 'paid') {
          totalPaidOrders++
          totalPaidAmount += orderTotal
        } else {
          totalUnpaidOrders++
          totalUnpaidAmount += orderTotal
        }
        
        // Payment method breakdown
        const paymentMethod = order.payment_method
        const isPaid = order.payment_status === 'paid'
        
        if (paymentMethod === 'emt' || paymentMethod === 'etransfer') {
          emtTotal += orderTotal
          emtCount++
          if (isPaid) {
            emtReceived += orderTotal
            emtPaidCount++
          }
        } else if (paymentMethod === 'cash') {
          cashTotal += orderTotal
          cashCount++
          if (isPaid) {
            cashReceived += orderTotal
            cashPaidCount++
          }
        }

        // Delivery method and shipped/picked up status
        if (order.delivery_method === 'delivery') {
          totalDelivery++
          // Check if delivery order is shipped
          if (order.status === 'out_for_delivery' || order.status === 'delivering' || order.status === 'completed') {
            totalShippedDelivery++
          }
        } else if (order.delivery_method === 'pickup') {
          totalPickup++
          // Check if pickup order is picked up
          if (order.status === 'ready_for_pickup' || order.status === 'completed') {
            totalPickedUpPickup++
          }
        }

        // Shipped/Picked Up status (combined)
        // For delivery: out_for_delivery, delivering, or completed
        // For pickup: ready_for_pickup or completed
        const isShippedOrPickedUp = 
          (order.delivery_method === 'delivery' && 
           (order.status === 'out_for_delivery' || order.status === 'delivering' || order.status === 'completed')) ||
          (order.delivery_method === 'pickup' && 
           (order.status === 'ready_for_pickup' || order.status === 'completed'))
        
        if (isShippedOrPickedUp) {
          totalShippedOrPickedUp++
        }

        // Product counts - need to fetch full order details for items
        // For now, we'll calculate from orders that have items loaded
        if (order.items && Array.isArray(order.items)) {
          order.items.forEach(item => {
            const productId = item.product?.id || item.product_id
            if (!productId) return

            const catalogProduct = productById.get(productId) || item.product
            const productName = catalogProduct?.name || item.product?.name || 'Unknown Product'
            const hasVariants = ((catalogProduct?.variants || item.product?.variants) || []).length > 0
            const variantId = hasVariants ? (item.variant_id ?? null) : null
            const statKey = this.productStatKey(productId, variantId, hasVariants)
            const variantName = hasVariants
              ? this.variantLabelForItem(catalogProduct || item.product, item)
              : null
            const displayName = variantName ? `${productName} · ${variantName}` : productName
            const quantity = item.quantity || 0
            const itemSalesValue = this.computeItemSalesValue(item)
            const supplier = catalogProduct?.supplier
            const category = catalogProduct?.category

            if (productCountsMap.has(statKey)) {
              const existing = productCountsMap.get(statKey)
              existing.totalQuantity += quantity
              existing.totalSalesValue += itemSalesValue
            } else {
              productCountsMap.set(statKey, {
                statKey,
                productId,
                variantId,
                productName,
                variantName,
                displayName,
                supplierId: supplier?.id ?? null,
                supplierName: supplier?.name || '未分配供应商',
                categoryId: category?.id ?? null,
                categoryName: category?.name || '未分配分类',
                totalQuantity: quantity,
                totalSalesValue: itemSalesValue
              })
            }
          })
        }
      })

      // Convert map to array and sort by product name
      const productCounts = Array.from(productCountsMap.values()).sort((a, b) => {
        const nameCmp = a.productName.localeCompare(b.productName)
        if (nameCmp !== 0) return nameCmp
        const aVar = a.variantName || ''
        const bVar = b.variantName || ''
        return aVar.localeCompare(bVar)
      })

      return {
        totalOrders: allOrders.length,
        totalAmount,
        totalPaidOrders,
        totalPaidAmount,
        totalUnpaidOrders,
        totalUnpaidAmount,
        totalDelivery,
        totalPickup,
        totalShippedOrPickedUp,
        totalShippedDelivery,
        totalPickedUpPickup,
        productCounts,
        // Payment method breakdown
        emtTotal,
        emtReceived,
        emtCount,
        emtPaidCount,
        cashTotal,
        cashReceived,
        cashCount,
        cashPaidCount
      }
    },
    selectedProductsSummary() {
      // Calculate summary statistics for selected products
      if (this.selectedProductFilters.length === 0) {
        return {
          totalSales: 0,
          totalOrders: 0,
          totalQuantity: 0
        }
      }
      
      // Get selected product statistics
      const selectedProducts = this.statistics.productCounts.filter((p) =>
        this.selectedProductFilters.includes(p.statKey)
      )
      
      const totalSales = selectedProducts.reduce((sum, p) => sum + p.totalSalesValue, 0)
      const totalQuantity = selectedProducts.reduce((sum, p) => sum + p.totalQuantity, 0)
      
      // Count unique orders containing selected products
      const ordersWithSelectedProducts = this.applyProductFilter(this.ordersStore.state.orders || [])
      const totalOrders = ordersWithSelectedProducts.length
      
      return {
        totalSales,
        totalOrders,
        totalQuantity
      }
    },
    productStatsTabs() {
      const stats = this.statistics.productCounts
      const mode = this.productStatsGroupMode
      if (mode === 'product' || !stats.length) return []

      const meta = mode === 'supplier'
        ? { idKey: 'supplierId', nameKey: 'supplierName' }
        : { idKey: 'categoryId', nameKey: 'categoryName' }

      const groups = new Map()
      stats.forEach((stat) => {
        const id = stat[meta.idKey]
        const key = id == null ? 'none' : String(id)
        const label = stat[meta.nameKey]
        if (groups.has(key)) {
          const group = groups.get(key)
          group.totalQuantity += stat.totalQuantity
          group.totalSalesValue += stat.totalSalesValue
          group.productCount += 1
        } else {
          groups.set(key, {
            key,
            label,
            totalQuantity: stat.totalQuantity,
            totalSalesValue: stat.totalSalesValue,
            productCount: 1
          })
        }
      })

      return Array.from(groups.values()).sort((a, b) => a.label.localeCompare(b.label, 'zh-CN'))
    },
    visibleProductStats() {
      const stats = this.statistics.productCounts
      if (this.productStatsGroupMode === 'product') return stats
      if (!this.activeProductStatsTab) return stats

      const idKey = this.productStatsGroupMode === 'supplier' ? 'supplierId' : 'categoryId'
      return stats.filter((stat) => {
        const id = stat[idKey]
        const key = id == null ? 'none' : String(id)
        return key === this.activeProductStatsTab
      })
    },
    visibleProductStatsSummary() {
      const stats = this.visibleProductStats
      if (!stats.length) return null

      let label = '全部商品'
      if (this.productStatsGroupMode === 'supplier' || this.productStatsGroupMode === 'category') {
        const tab = this.productStatsTabs.find((t) => t.key === this.activeProductStatsTab)
        label = tab?.label || label
      }

      return {
        label,
        productCount: stats.length,
        totalQuantity: stats.reduce((sum, stat) => sum + stat.totalQuantity, 0),
        totalSalesValue: stats.reduce((sum, stat) => sum + stat.totalSalesValue, 0)
      }
    }
  },
  mounted() {
    const pageHeader = usePageHeader()
    this._pageHeader = pageHeader
    pageHeader.setBackHandler(() => this.goBack())
    this.fetchGroupDealDetail()
    if (typeof window !== 'undefined') {
      window.addEventListener('resize', this.syncNarrowMobile, { passive: true })
    }
  },
  beforeUnmount() {
    this._pageHeader?.reset()
    if (typeof window !== 'undefined') {
      window.removeEventListener('resize', this.syncNarrowMobile)
    }
  },
  methods: {
    formatStatMoney(value) {
      return formatOrderMoney2(value)
    },
    syncNarrowMobile() {
      if (typeof window === 'undefined') return
      const n = window.innerWidth <= 767
      if (n === this.narrowMobile) return
      this.narrowMobile = n
      if (n) {
        this.mobileStatsSummaryOpen = false
        this.mobileProductStatsOpen = false
      } else {
        this.mobileStatsSummaryOpen = true
        this.mobileProductStatsOpen = true
      }
    },
    applyProductFilter(orders) {
      if (this.selectedProductFilters.length === 0) {
        return orders
      }
      
      return orders.filter(order => {
        if (!order.items || !Array.isArray(order.items)) {
          return false
        }
        // Check if order contains ANY of the selected products
        return order.items.some((item) => this.itemMatchesProductFilter(item))
      })
    },
    isOrderPackingComplete(order) {
      return PACKING_COMPLETE_STATUSES.includes(order?.status)
    },
    orderHasNotes(order) {
      return !!(order?.notes && String(order.notes).trim())
    },
    compareOrdersForSort(a, b) {
      const sortKey = this.orderSort || 'payment'

      if (sortKey === 'weight_asc' || sortKey === 'weight_desc') {
        const aMissing = orderHasMissingFinalWeight(a) ? 1 : 0
        const bMissing = orderHasMissingFinalWeight(b) ? 1 : 0
        const diff = sortKey === 'weight_asc' ? aMissing - bMissing : bMissing - aMissing
        if (diff !== 0) return diff
      } else if (sortKey === 'packing_asc' || sortKey === 'packing_desc') {
        const aComplete = this.isOrderPackingComplete(a) ? 1 : 0
        const bComplete = this.isOrderPackingComplete(b) ? 1 : 0
        const diff = sortKey === 'packing_asc' ? aComplete - bComplete : bComplete - aComplete
        if (diff !== 0) return diff
      }

      const aPaid = a.payment_status === 'paid' ? 1 : 0
      const bPaid = b.payment_status === 'paid' ? 1 : 0
      return aPaid - bPaid
    },
    productStatKey(productId, variantId, hasVariants) {
      if (!hasVariants) return String(productId)
      const vid = variantId == null ? 'none' : String(variantId)
      return `${productId}:${vid}`
    },
    parseProductStatKey(statKey) {
      const s = String(statKey)
      if (!s.includes(':')) {
        return { productId: s, variantId: null, hasVariants: false }
      }
      const [productId, variantPart] = s.split(':')
      return {
        productId,
        variantId: variantPart === 'none' ? null : variantPart,
        hasVariants: true
      }
    },
    variantLabelForItem(product, item) {
      if (item.variant_name) return item.variant_name
      if (item.variant?.name) return item.variant.name
      const vid = item.variant_id
      if (vid != null) {
        const v = (product?.variants || []).find((x) => x.id === vid || String(x.id) === String(vid))
        if (v?.name) return v.name
        return '未知规格'
      }
      return '（未选规格）'
    },
    computeItemSalesValue(item) {
      return resolveOrderLineTotal(item)
    },
    itemMatchesProductFilter(item) {
      const productId = item.product?.id || item.product_id
      if (!productId) return false
      return this.selectedProductFilters.some((statKey) => {
        const parsed = this.parseProductStatKey(statKey)
        if (String(parsed.productId) !== String(productId)) return false
        if (!parsed.hasVariants) return true
        const itemVid = item.variant_id == null ? null : String(item.variant_id)
        const filterVid = parsed.variantId == null ? null : String(parsed.variantId)
        return itemVid === filterVid
      })
    },
    toggleProductFilter(statKey) {
      const index = this.selectedProductFilters.indexOf(statKey)
      if (index >= 0) {
        this.selectedProductFilters.splice(index, 1)
      } else {
        this.selectedProductFilters.push(statKey)
      }
    },
    isProductFilterActive(statKey) {
      return this.selectedProductFilters.includes(statKey)
    },
    clearProductFilters() {
      this.selectedProductFilters = []
    },
    setProductStatsGroupMode(mode) {
      if (this.productStatsGroupMode === mode) return
      this.productStatsGroupMode = mode
      if (mode === 'product') {
        this.activeProductStatsTab = null
        return
      }
      const tabs = this.productStatsTabs
      this.activeProductStatsTab = tabs.length ? tabs[0].key : null
    },
    handleSearch() {
      // Search is handled by computed property filteredOrders
      // This method can be used for debouncing if needed in the future
    },
    clearSearch() {
      this.searchQuery = ''
    },
    async fetchGroupDealDetail() {
      try {
        this.loading = true
        this.error = null
        const dealId = this.$route.params.id
        
        // Fetch group deal first (fast)
        const dealResponse = await apiClient.get(`/admin/group-deals/${dealId}`)
        this.groupDeal = dealResponse.data.group_deal
        // Store previous status for change detection
        if (this.groupDeal) {
          this.groupDeal._previousStatus = this.groupDeal.status
          this._pageHeader?.setTitle(this.groupDeal.title)
        }
        
        // Show the page immediately with group deal info
        this.loading = false
        
        // Fetch orders in parallel (slow, but page is already visible)
        this.fetchOrders(dealId)
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || error.message || 'Failed to load group deal'
        console.error('Failed to fetch group deal detail:', error)
        this.loading = false
      }
    },
    async refreshPage() {
      const dealId = this.$route.params.id
      if (!dealId) return

      try {
        this.error = null
        const dealResponse = await apiClient.get(`/admin/group-deals/${dealId}`)
        this.groupDeal = dealResponse.data.group_deal
        if (this.groupDeal) {
          this.groupDeal._previousStatus = this.groupDeal.status
          this._pageHeader?.setTitle(this.groupDeal.title)
        }
        await this.fetchOrders(dealId)
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || error.message || 'Failed to refresh group deal'
        console.error('Failed to refresh group deal detail:', error)
      }
    },
    async fetchOrders(dealId) {
      try {
        this.ordersStore.setLoading(true)
        
        // Fetch orders for this group deal with items included (excluding cancelled orders)
        const ordersResponse = await apiClient.get('/admin/orders', {
          params: {
            group_deal_id: dealId,
            per_page: 1000
          }
        })
        
        // Filter out cancelled orders
        const orders = (ordersResponse.data.orders || []).filter(order => order.status !== 'cancelled')
        
        // Ensure all orders have items array (even if empty)
        orders.forEach(order => {
          if (!order.items) {
            order.items = []
          }
        })
        
        // Update store
        this.ordersStore.setOrders(orders)
      } catch (error) {
        console.error('Failed to fetch orders:', error)
        this.ordersStore.setError(error.response?.data?.message || error.response?.data?.error || 'Failed to load orders')
      } finally {
        this.ordersStore.setLoading(false)
      }
    },
    async onFulfillmentUpdated() {
      if (this.groupDeal?.id) {
        await this.fetchOrders(this.groupDeal.id)
      }
    },
    goBack() {
      this.$router.push('/group-deals')
    },
    viewCommission() {
      this.showCommissionModal = true
    },
    closeCommissionModal() {
      this.showCommissionModal = false
    },
    exportOrders() {
      try {
        if (!this.groupDeal || !this.orders || this.orders.length === 0) {
          this.showError('没有订单可导出')
          return
        }

        // Get all unique products across all orders
        const allProducts = new Set()
        this.orders.forEach(order => {
          if (order.items && order.items.length > 0) {
            order.items.forEach(item => {
              const productName = item.product?.name || 'Unknown'
              allProducts.add(productName)
            })
          }
        })
        const productColumns = Array.from(allProducts).sort()

        // Build CSV header
        const headers = [
          '订单号',
          '用户姓名',
          '电话',
          '微信',
          '配送方式',
          '地址/取货点',
          ...productColumns,
          '备注',
          '订单金额(含调整)',
          '代金券',
          '应付金额',
          '付款状态',
          '付款方式'
        ]

        // Build CSV rows
        const rows = this.orders.map(order => {
          // Get product quantities
          const productQuantities = {}
          if (order.items && order.items.length > 0) {
            order.items.forEach(item => {
              const productName = item.product?.name || 'Unknown'
              productQuantities[productName] = item.quantity || 0
            })
          }

          // Delivery method and location
          const deliveryMethod = order.delivery_method === 'delivery' ? '配送' : '自取'
          let location = ''
          if (order.delivery_method === 'delivery' && order.address) {
            const parts = []
            if (order.address.address_line1) parts.push(order.address.address_line1)
            if (order.address.address_line2) parts.push(order.address.address_line2)
            if (order.address.city) parts.push(order.address.city)
            if (order.address.postal_code) parts.push(order.address.postal_code)
            location = parts.join(', ')
          } else if (order.delivery_method === 'pickup') {
            const locationMap = {
              'markham': '万锦',
              'northyork': '北约克',
              'scarborough': '士嘉堡',
              'downtown': '市中心'
            }
            location = locationMap[order.pickup_location] || order.pickup_location || ''
          }

          // Payment status and method
          const paymentStatusMap = {
            'unpaid': '未付款',
            'paid': '已付款',
            'failed': '支付失败',
            'refunded': '已退款'
          }
          const paymentMethodMap = {
            'cash': '现金',
            'emt': 'EMT',
            'wechat': '微信支付',
            'alipay': '支付宝'
          }

          const row = [
            order.order_number || '',
            order.user?.nickname || order.user?.phone || '',
            order.user?.phone || '',
            order.user?.wechat || '',
            deliveryMethod,
            location,
            ...productColumns.map(product => productQuantities[product] || ''),
            order.notes || '',
            `$${formatOrderMoney2(orderFinalTotalNumber(order))}`,
            orderStoreCreditAppliedNumber(order) > 0
              ? `$${formatOrderMoney2(orderStoreCreditAppliedNumber(order))}`
              : '',
            `$${formatOrderMoney2(orderAmountDueNumber(order))}`,
            paymentStatusMap[order.payment_status] || order.payment_status || '',
            paymentMethodMap[order.payment_method] || order.payment_method || ''
          ]

          return row
        })

        // Convert to CSV string with proper escaping
        const csvContent = [headers, ...rows]
          .map(row => 
            row.map(cell => {
              // Convert to string and escape quotes
              const cellStr = String(cell || '')
              // If cell contains comma, quote, or newline, wrap in quotes and escape quotes
              if (cellStr.includes(',') || cellStr.includes('"') || cellStr.includes('\n')) {
                return `"${cellStr.replace(/"/g, '""')}"`
              }
              return cellStr
            }).join(',')
          )
          .join('\n')

        // Add BOM for proper UTF-8 encoding in Excel
        const BOM = '\uFEFF'
        const csvWithBOM = BOM + csvContent

        // Create and download file
        const blob = new Blob([csvWithBOM], { type: 'text/csv;charset=utf-8;' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${this.groupDeal.title}_订单_${new Date().toISOString().split('T')[0]}.csv`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)

        this.success('订单导出成功')
      } catch (error) {
        this.showError('导出订单失败: ' + (error.message || 'Unknown error'))
        console.error('Export orders error:', error)
      }
    },
    async handleGroupDealStatusChange() {
      if (!this.groupDeal) return
      
      const newStatus = this.groupDeal.status
      const oldStatus = this.groupDeal._previousStatus || this.groupDeal.status
      
      // Don't update if status hasn't changed
      if (newStatus === oldStatus) {
        return
      }
      
      const statusText = this.getStatusLabel(newStatus)
      const confirmed = await this.confirm(`确认将团购状态改为 "${statusText}"?\n\n此操作将自动更新相关订单状态。`)
      if (!confirmed) {
        // Revert the status change
        this.groupDeal.status = oldStatus
        return
      }
      
      this.updatingGroupDealStatus = true
      try {
        const response = await apiClient.put(`/admin/group-deals/${this.groupDeal.id}/status`, { 
          status: newStatus 
        })
        
        // Update group deal with response data
        this.groupDeal = response.data.group_deal
        // Update previous status
        this.groupDeal._previousStatus = this.groupDeal.status
        
        // Refresh orders list to show updated order statuses
        await this.fetchGroupDealDetail()
        
        const ordersUpdated = response.data.orders_updated || 0
        if (ordersUpdated > 0) {
          await this.success(`团购状态已更新为: ${statusText}\n已更新 ${ordersUpdated} 个订单状态`)
        } else {
          await this.success(`团购状态已更新为: ${statusText}`)
        }
      } catch (error) {
        // Revert the status change on error
        this.groupDeal.status = oldStatus
        const errorMsg = error.response?.data?.message || error.response?.data?.error || '更新失败'
        await this.showError(`更新失败: ${errorMsg}`)
        console.error('Failed to update group deal status:', error)
      } finally {
        this.updatingGroupDealStatus = false
      }
    },
    getStatusLabel(status) {
      const labels = {
        'draft': '草稿',
        'upcoming': '即将开始',
        'active': '进行中',
        'closed': '已截单',
        'preparing': '准备中',
        'ready_for_pickup': '可以取货',
        'completed': '已完成'
      }
      return labels[status] || status
    },
    getStatusText(status) {
      const labels = {
        'submitted': '已提交',
        'confirmed': '已确认',
        'preparing': '配货中',
        'ready_for_pickup': '可取货',
        'out_for_delivery': '配送中',
        'delivering': '配送中',
        'completed': '已完成',
        'cancelled': '已取消'
      }
      return labels[status] || status
    },
    formatDuplicateOrderDue(order) {
      return formatOrderMoney2(orderAmountDueNumber(order))
    },
    getPaymentStatusText(status) {
      const labels = {
        'unpaid': '未付款',
        'paid': '已付款',
        'failed': '支付失败',
        'refunded': '已退款'
      }
      return labels[status] || status
    },
    formatDateTime(dateString) {
      return formatDateTimeEST_CN(dateString) || 'N/A'
    },
    formatPickupDate(dateString) {
      return formatPickupDateTime_CN(dateString) || 'N/A'
    },
    formatAddress(address) {
      if (!address) return ''
      const parts = [
        address.address_line1,
        address.address_line2,
        address.city,
        address.postal_code
      ].filter(Boolean)
      return parts.join(', ')
    },
    async viewOrderDetail(order) {
      try {
        // Fetch full order details
        const response = await apiClient.get(`/admin/orders/${order.id}`)
        this.selectedOrder = response.data.order
        
        console.log('[viewOrderDetail] Fetched order:', this.selectedOrder)
        console.log('[viewOrderDetail] Order user_id:', this.selectedOrder.user_id)
        console.log('[viewOrderDetail] Order user:', this.selectedOrder.user)
        
        // Use products from already-loaded group deal (no need for another API call)
        // Products are already available in this.groupDeal.products from fetchGroupDealDetail()
        if (this.groupDeal && this.groupDeal.products && Array.isArray(this.groupDeal.products)) {
          this.availableProducts = this.groupDeal.products
        } else {
          // Fallback: only load if group deal data is not available
          await this.loadAvailableProducts()
        }
        
        this.showOrderDetail = true
        this.updateError = null
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Failed to load order details'
        await this.showError(`加载失败: ${errorMsg}`)
        console.error('Failed to load order details:', error)
      }
    },
    async loadAvailableProducts() {
      // Fallback method - only called if groupDeal.products is not available
      if (!this.selectedOrder?.group_deal_id) return
      
      try {
        const response = await apiClient.get(`/admin/group-deals/${this.selectedOrder.group_deal_id}`)
        this.availableProducts = response.data.group_deal?.products || []
      } catch (error) {
        console.error('Failed to load products:', error)
        this.availableProducts = []
      }
    },
    closeOrderDetail() {
      this.showOrderDetail = false
      this.selectedOrder = null
      this.availableProducts = []
      this.updateError = null
    },
    async deleteOrder(orderId) {
      const confirmed = await this.confirm(
        '确认删除此订单? 订单将被软删除，不会在列表中显示，但数据仍保留在数据库中。此操作无法撤销。',
        {
          type: 'warning',
          title: '确认删除'
        }
      )
      if (!confirmed) {
        return
      }

      try {
        await apiClient.delete(`/admin/orders/${orderId}`)

        const orders = this.ordersStore.state.orders.filter((o) => o.id !== orderId)
        this.ordersStore.setOrders(orders)

        if (this.selectedOrder?.id === orderId) {
          this.closeOrderDetail()
        }

        await this.success('订单已删除')
      } catch (error) {
        const errorMsg =
          error.response?.data?.message ||
          error.response?.data?.error ||
          'Failed to delete order'
        await this.error(`删除失败: ${errorMsg}`)
        console.error('Failed to delete order:', error)
      }
    },
    async handleUpdateOrder(orderId, updateData) {
      this.updatingOrder = true
      this.updateError = null
      
      try {
        const response = await apiClient.put(`/admin/orders/${orderId}/update`, updateData)
        const updatedOrder = response.data.order
        
        // Update store and local state
        this.ordersStore.updateOrder(updatedOrder)
        this.selectedOrder = updatedOrder
        
        await this.success('订单已更新')
        
        // Don't close the modal - keep it open so admin can continue editing
      } catch (error) {
        this.updateError = error.response?.data?.message || error.response?.data?.error || '更新失败'
        await this.error(`更新失败: ${this.updateError}`)
        console.error('Failed to update order:', error)
      } finally {
        this.updatingOrder = false
      }
    },
    handleOrderUpdated(order) {
      this.selectedOrder = order
      this.ordersStore.updateOrder(order)
    },
    orderNeedsFinalWeightAttention(order) {
      if (!order) return false
      if (this.showOrderDetail && this.selectedOrder?.id === order.id && this.$refs.orderDetailModal) {
        return this.$refs.orderDetailModal.hasMissingFinalWeight
      }
      return orderHasMissingFinalWeight(order)
    },
    async handleOrderStatusChange(orderId, newStatus) {
      if (!this.selectedOrder || !newStatus) {
        return
      }
      
      if (newStatus === this.selectedOrder.status) {
        return
      }
      
      const statusText = this.getStatusText(newStatus)

      if (statusChangeWarnsIfMissingFinalWeight(newStatus) && this.orderNeedsFinalWeightAttention(this.selectedOrder)) {
        const proceed = await this.confirm(
          `此订单仍有按重计价商品未填写有效实际重量（或总重量）。确定仍要将状态改为「${statusText}」吗？\n\n若已在详情中填写重量，请先点击「更新订单」保存后再改状态。`,
          { type: 'warning', title: '缺少最终重量' }
        )
        if (!proceed) {
          return
        }
      }

      const confirmed = await this.confirm(`确认将订单状态改为 "${statusText}"?`)
      if (!confirmed) {
        return
      }
      
      try {
        const response = await apiClient.put(`/admin/orders/${orderId}/status`, { status: newStatus })
        const updatedOrder = response.data.order
        
        // Update store and local state
        this.ordersStore.updateOrder(updatedOrder)
        this.selectedOrder = updatedOrder
        
        await this.success(`订单状态已更新为: ${statusText}`)
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Failed to update status'
        await this.error(`更新失败: ${errorMsg}`)
        console.error('Failed to update order status:', error)
      }
    },
    async handleMarkPackingComplete(order) {
      if (!order || order.status !== 'preparing') {
        return
      }
      
      const confirmed = await this.confirm(`确认将订单 #${order.order_number} 标记为配货完成?`)
      if (!confirmed) {
        return
      }
      
      try {
        const response = await apiClient.put(`/admin/orders/${order.id}/status`, { status: 'packing_complete' })
        const updatedOrder = response.data.order
        
        // Update store
        this.ordersStore.updateOrder(updatedOrder)
        
        await this.success('订单已标记为配货完成')
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Failed to update status'
        await this.showError(`更新失败: ${errorMsg}`)
        console.error('Failed to mark packing complete:', error)
      }
    },
    async handlePaymentMethodChange(paymentMethod) {
      // Auto-mark as paid when cash is selected and order is unpaid
      // Don't trigger for cancelled or completed orders
      if (paymentMethod === 'cash' && 
          this.selectedOrder && 
          this.selectedOrder.payment_status === 'unpaid' &&
          this.selectedOrder.status !== 'cancelled' &&
          this.selectedOrder.status !== 'completed') {
        await this.markOrderAsPaid('cash')
      }
    },
    async markOrderAsPaid(data) {
      // Handle different data formats for backward compatibility
      let orderId
      let paymentMethod = 'etransfer'
      
      if (typeof data === 'object' && data !== null) {
        // New format: { orderId, paymentMethod }
        if (data.orderId) {
          orderId = data.orderId
          paymentMethod = data.paymentMethod || 'etransfer'
        } else if (data.id) {
          // Old format: order object (for backward compatibility)
          orderId = data.id
          paymentMethod = data.payment_method || 'etransfer'
        } else {
          return
        }
      } else if (typeof data === 'string') {
        // Old format: paymentMethod string
        paymentMethod = data
        if (!this.selectedOrder) return
        orderId = this.selectedOrder.id
      } else {
        return
      }
      
      // Find the order to mark as paid
      const orderToMark = this.selectedOrder?.id === orderId 
        ? this.selectedOrder 
        : this.orders.find(o => o.id === orderId)
      
      if (!orderToMark || orderToMark.payment_status === 'paid') {
        return
      }

      if (this.orderNeedsFinalWeightAttention(orderToMark)) {
        const proceed = await this.confirm(
          '此订单仍有按重计价商品未填写有效实际重量（或总重量）。确定仍要标记为已付款吗？\n\n金额与积分将按当前已保存的数据结算；若刚在详情里填写了重量，请先点击「更新订单」。',
          { type: 'warning', title: '缺少最终重量' }
        )
        if (!proceed) {
          return
        }
      }
      
      const amount = formatOrderMoney2(orderAmountDueNumber(orderToMark))
      const pointsToEarn = calculateOrderPoints(orderToMark)
      
      const confirmed = await this.confirm(`确认标记订单 #${orderToMark.order_number} 为已付款?\n\n应付金额: $${amount}\n将获得积分: ${pointsToEarn} 分\n\n支付后订单将自动完成。`)
      if (!confirmed) {
        return
      }
      
      try {
        const response = await apiClient.put(`/admin/orders/${orderId}/payment`, { 
          payment_status: 'paid',
          payment_method: paymentMethod
        })
        
        const updatedOrder = response.data.order
        
        // Update store and local state
        this.ordersStore.updateOrder(updatedOrder)
        if (this.selectedOrder && this.selectedOrder.id === updatedOrder.id) {
          this.selectedOrder = updatedOrder
        }
        
        const pointsAwarded = response.data.points_awarded || 0
        const paymentMethodLabel = paymentMethod === 'cash' ? '现金' : '电子转账'
        await this.success(`订单已标记为已付款（${paymentMethodLabel}）\n积分: ${pointsAwarded} 分已发放\n订单状态: 订单完成`)
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Failed to update payment status'
        await this.error(`更新失败: ${errorMsg}`)
        console.error('Failed to mark as paid:', error)
      }
    },
    async markOrderAsUnpaid(data) {
      // Handle different data formats
      let orderId
      
      if (typeof data === 'object' && data !== null) {
        if (data.orderId) {
          orderId = data.orderId
        } else if (data.id) {
          orderId = data.id
        } else {
          return
        }
      } else {
        if (!this.selectedOrder) return
        orderId = this.selectedOrder.id
      }
      
      // Find the order to mark as unpaid
      const orderToMark = this.selectedOrder?.id === orderId 
        ? this.selectedOrder 
        : this.orders.find(o => o.id === orderId)
      
      if (!orderToMark || orderToMark.payment_status !== 'paid') {
        return
      }
      
      const amount = formatOrderMoney2(orderFinalTotalNumber(orderToMark))
      
      const confirmed = await this.confirm(`确认标记订单 #${orderToMark.order_number} 为未付款?\n\n金额: $${amount}\n\n此操作将撤销已发放的积分。`)
      if (!confirmed) {
        return
      }
      
      try {
        const response = await apiClient.put(`/admin/orders/${orderId}/payment`, { 
          payment_status: 'unpaid'
        })
        
        const updatedOrder = response.data.order
        
        // Update store and local state
        this.ordersStore.updateOrder(updatedOrder)
        if (this.selectedOrder && this.selectedOrder.id === updatedOrder.id) {
          this.selectedOrder = updatedOrder
        }
        
        await this.success(`订单已标记为未付款`)
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Failed to update payment status'
        await this.error(`更新失败: ${errorMsg}`)
        console.error('Failed to mark as unpaid:', error)
      }
    },
    async markOrderComplete() {
      if (!this.selectedOrder || this.selectedOrder.status === 'completed') {
        return
      }

      if (this.orderNeedsFinalWeightAttention(this.selectedOrder)) {
        const proceed = await this.confirm(
          '此订单仍有按重计价商品未填写有效实际重量（或总重量）。确定仍要标记为已完成吗？\n\n建议先点击「更新订单」保存称重后再完成。',
          { type: 'warning', title: '缺少最终重量' }
        )
        if (!proceed) {
          return
        }
      }
      
      let confirmMsg = `确认标记订单 #${this.selectedOrder.order_number} 为已完成?`
      if (this.selectedOrder.payment_status === 'unpaid') {
        const pts = calculateOrderPoints(this.selectedOrder)
        confirmMsg += `\n\n注意：订单仍为「未付款」，不会发放积分（预计 ${pts} 分）。\n请先点击「标记已付款」发放积分。`
      }
      const confirmed = await this.confirm(confirmMsg, { type: 'warning' })
      if (!confirmed) {
        return
      }
      
      this.markingComplete = true
      try {
        const response = await apiClient.put(`/admin/orders/${this.selectedOrder.id}/status`, { status: 'completed' })
        const updatedOrder = response.data.order
        
        // Update store and local state
        this.ordersStore.updateOrder(updatedOrder)
        this.selectedOrder = updatedOrder
        
        let successMsg = '订单已标记为已完成'
        if (response.data.points_notice || updatedOrder.payment_status === 'unpaid') {
          successMsg += '\n积分未发放：请标记为「已付款」后才会计入用户积分。'
        }
        await this.success(successMsg)
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Failed to update status'
        await this.error(`更新失败: ${errorMsg}`)
        console.error('Failed to mark order complete:', error)
      } finally {
        this.markingComplete = false
      }
    },
    
    async findDuplicates() {
      this.loadingDuplicates = true
      try {
        const params = {
          group_deal_id: this.groupDeal.id
        }
        
        const response = await apiClient.get('/admin/orders/duplicates', { params })
        this.duplicates = response.data.duplicate_sets || []
        this.showDuplicatesModal = true
        
        if (this.duplicates.length === 0) {
          await this.success('没有找到一人多单')
        } else {
          await this.success(`找到 ${this.duplicates.length} 组一人多单`)
        }
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || '查找失败'
        await this.showError(`查找失败: ${errorMsg}`)
        console.error('Failed to find duplicates:', error)
      } finally {
        this.loadingDuplicates = false
      }
    },
    
    closeDuplicatesModal() {
      this.showDuplicatesModal = false
    },
    
    openMergeModal(orders) {
      this.ordersToMerge = orders
      this.showMergeModal = true
      this.showDuplicatesModal = false
    },
    
    closeMergeModal() {
      this.showMergeModal = false
      this.ordersToMerge = []
    },
    
    async handleOrderMerged(mergedOrder) {
      await this.success('订单合并成功')
      // Refresh group deal and orders - we need full refresh for merge as it affects multiple orders
      await this.fetchGroupDealDetail()
      // Optionally refresh duplicates if modal is still open
      if (this.showDuplicatesModal) {
        await this.findDuplicates()
      }
    },

    async bulkMarkDelivering() {
      if (!this.groupDeal) {
        return
      }

      // Count delivery orders that will be updated
      const deliveryOrders = this.orders.filter(order => 
        order.delivery_method === 'delivery' && 
        order.status !== 'out_for_delivery' &&
        order.status !== 'completed' &&
        order.status !== 'cancelled'
      )
      
      if (deliveryOrders.length === 0) {
        await this.error('当前团购没有可更新的配送订单')
        return
      }
      
      const confirmed = await this.confirm(
        `确认将"${this.groupDeal.title}"的所有配送订单标记为"正在配送"？\n\n将更新 ${deliveryOrders.length} 个配送订单\n\n此操作将更新该团购下所有符合条件的配送订单。`,
        { type: 'warning', title: '批量更新确认' }
      )
      
      if (!confirmed) {
        return
      }
      
      this.loadingBulkUpdate = true
      try {
        const params = {
          status: 'out_for_delivery',
          delivery_method: 'delivery',
          group_deal_id: this.groupDeal.id
        }
        
        const response = await apiClient.post('/admin/orders/bulk-update-status', params)
        
        const updatedCount = response.data.updated_count || 0
        await this.success(`成功更新 ${updatedCount} 个订单为"正在配送"`)
        
        // Refresh group deal and orders
        await this.fetchGroupDealDetail()
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.response?.data?.error || '批量更新失败'
        await this.error(`更新失败: ${errorMsg}`)
        console.error('Failed to bulk update orders:', error)
      } finally {
        this.loadingBulkUpdate = false
      }
    },

    getStatusText(status) {
      const statusMap = {
        'submitted': '已提交订单',
        'confirmed': '已确认订单',
        'preparing': '正在配货',
        'packing_complete': '配货完成',
        'ready_for_pickup': '可以取货',
        'out_for_delivery': '正在配送',
        'delivering': '正在配送',
        'completed': '订单完成',
        'cancelled': '已取消'
      }
      return statusMap[status] || status
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
.group-deal-detail-page {
  max-width: 1200px;
  transition: transform 0.2s ease;
  will-change: transform;
}

.group-deal-detail-page.is-pulling {
  transition: none;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--md-spacing-md);
  margin-bottom: var(--md-spacing-lg);
}

.page-nav {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  min-width: 0;
}

.page-nav-title,
.nav-spacer {
  display: none;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  padding: var(--md-spacing-xs) var(--md-spacing-sm);
  background: transparent;
  color: rgba(0, 0, 0, 0.87);
  border: none;
  border-radius: var(--md-radius-sm);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
}

.back-btn svg {
  width: 20px;
  height: 20px;
}

.back-btn:hover {
  background: rgba(0, 0, 0, 0.06);
}

.header-actions {
  display: flex;
  gap: var(--md-spacing-md);
}

.bulk-delivery-btn {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  background: #E1F5FE;
  color: #0277BD;
  border: 1px solid rgba(2, 119, 189, 0.2);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--md-elevation-2);
  position: relative;
  overflow: hidden;
}

.bulk-delivery-btn svg {
  width: 20px;
  height: 20px;
}

.bulk-delivery-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(2, 119, 189, 0.1);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s, opacity 0.3s;
  opacity: 0;
}

.bulk-delivery-btn:hover:not(:disabled) {
  background: #B3E5FC;
  border-color: rgba(2, 119, 189, 0.4);
  box-shadow: var(--md-elevation-3);
  transform: translateY(-2px);
}

.bulk-delivery-btn:active:not(:disabled) {
  background: #81D4FA;
  transform: translateY(0);
}

.bulk-delivery-btn:active:not(:disabled)::before {
  width: 300px;
  height: 300px;
  opacity: 1;
  transition: width 0s, height 0s, opacity 0.3s;
}

.bulk-delivery-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.export-btn {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  background: var(--md-primary);
  color: white;
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--md-elevation-2);
}

.export-btn svg {
  width: 20px;
  height: 20px;
}

.export-btn:hover:not(:disabled) {
  background: #FF7F00;
  box-shadow: var(--md-elevation-3);
  transform: translateY(-2px);
}

.export-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.commission-btn {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  background: linear-gradient(135deg, #9c27b0 0%, #7b1fa2 100%);
  color: white;
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition-fast);
}

.commission-btn svg {
  width: 20px;
  height: 20px;
}

.commission-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #7b1fa2 0%, #6a1b9a 100%);
  box-shadow: var(--md-elevation-3);
  transform: translateY(-2px);
}

.commission-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading, .error, .empty-state {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.deal-info-card {
  background: #FFFFFF;
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  margin-bottom: var(--md-spacing-lg);
}

.deal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--md-spacing-md);
}

.deal-header h2 {
  font-size: var(--md-headline-size);
  color: var(--md-on-surface);
  font-weight: 500;
  margin: 0;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: var(--md-radius-xl);
  font-size: var(--md-label-size);
  font-weight: 500;
}

.status-badge.draft {
  background: #F5F5F5;
  color: #757575;
}

.status-badge.upcoming {
  background: #E3F2FD;
  color: #1976D2;
}

.status-badge.active {
  background: #E8F5E9;
  color: #2E7D32;
}

.status-badge.closed {
  background: #FFF3E0;
  color: #F57C00;
}

.status-badge.preparing {
  background: #F3E5F5;
  color: #7B1FA2;
}

.status-badge.ready_for_pickup {
  background: #E8F5E9;
  color: #2E7D32;
}

.status-badge.completed {
  background: #F3E5F5;
  color: #7B1FA2;
}

.status-control-group {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
}

.status-select {
  padding: var(--md-spacing-xs) var(--md-spacing-sm);
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-sm);
  font-size: var(--md-label-size);
  background: var(--md-surface);
  color: var(--md-on-surface);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.status-select:focus {
  outline: none;
  border-color: var(--md-primary);
  border-width: 2px;
}

.status-select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.status-select:hover:not(:disabled) {
  border-color: var(--md-primary);
  background: rgba(255, 140, 0, 0.05);
}

.deal-description {
  color: var(--md-on-surface-variant);
  margin-bottom: var(--md-spacing-md);
  line-height: 1.5;
}

.deal-dates {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
  padding: var(--md-spacing-md);
  background: var(--md-surface-variant);
  border-radius: var(--md-radius-md);
}

.date-item {
  display: flex;
  gap: var(--md-spacing-sm);
}

.date-label {
  font-weight: 500;
  color: var(--md-on-surface-variant);
  min-width: 80px;
}

.date-value {
  color: var(--md-on-surface);
}

.statistics-section {
  background: #FFFFFF;
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  margin-bottom: var(--md-spacing-lg);
}

.statistics-section h3 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-lg);
  font-weight: 500;
}

.stats-heading-desktop {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-lg);
  font-weight: 500;
}

.mobile-stats-toggle {
  display: none;
}

.toggle-chevron {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
  transition: transform 0.2s ease;
  color: var(--md-on-surface-variant);
}

.toggle-chevron.is-open {
  transform: rotate(180deg);
}

.product-stats-header--narrow {
  justify-content: flex-end;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--md-spacing-md);
  margin-bottom: var(--md-spacing-lg);
}

.stat-card {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
  padding: var(--md-spacing-md);
  background: var(--md-surface-variant);
  border-radius: var(--md-radius-md);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.stat-card:hover {
  background: rgba(0, 0, 0, 0.04);
  transform: translateY(-2px);
  box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--md-radius-md);
  background: rgba(255, 140, 0, 0.1);
  color: var(--md-primary);
  flex-shrink: 0;
}

.stat-icon svg {
  width: 24px;
  height: 24px;
}

.stat-icon.amount-icon {
  background: rgba(76, 175, 80, 0.1);
  color: #4CAF50;
}

.stat-icon.paid-icon {
  background: rgba(76, 175, 80, 0.1);
  color: #4CAF50;
}

.stat-icon.unpaid-icon {
  background: rgba(255, 152, 0, 0.1);
  color: #FF9800;
}

.stat-icon.delivery-icon {
  background: rgba(33, 150, 243, 0.1);
  color: #2196F3;
}

.stat-icon.pickup-icon {
  background: rgba(156, 39, 176, 0.1);
  color: #9C27B0;
}

.stat-icon.shipped-icon {
  background: rgba(0, 150, 136, 0.1);
  color: #009688;
}

.stat-icon.emt-icon {
  background: rgba(63, 81, 181, 0.1);
  color: #3F51B5;
}

.stat-icon.cash-icon {
  background: rgba(255, 152, 0, 0.1);
  color: #FF9800;
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-label {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin-bottom: var(--md-spacing-xs);
  font-weight: 500;
}

.stat-value {
  font-size: var(--md-headline-size);
  color: var(--md-on-surface);
  font-weight: 600;
  line-height: 1.2;
}

.stat-subvalue {
  font-size: var(--md-body-size);
  color: var(--md-on-surface-variant);
  margin-top: 2px;
}

.product-stats-section {
  margin-top: var(--md-spacing-lg);
  padding-top: var(--md-spacing-lg);
  border-top: 1px solid rgba(0, 0, 0, 0.12);
}

.product-stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--md-spacing-md);
}

.product-stats-section h4 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin: 0;
  font-weight: 500;
}

.product-stats-controls {
  margin-bottom: var(--md-spacing-md);
}

.product-stats-segment {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 3px;
  padding: 3px;
  background: rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 999px;
}

.segment-chip {
  padding: 0.4rem 0.85rem;
  background: transparent;
  color: var(--md-on-surface-variant);
  border: none;
  border-radius: 999px;
  font-size: 0.8125rem;
  font-weight: 500;
  line-height: 1.2;
  cursor: pointer;
  transition: color 0.15s, background 0.15s, box-shadow 0.15s;
  white-space: nowrap;
}

.segment-chip:hover:not(.active) {
  color: var(--md-on-surface);
  background: rgba(255, 255, 255, 0.55);
}

.segment-chip.active {
  background: #fff;
  color: var(--md-primary);
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}

.product-stats-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: var(--md-spacing-md);
}

.stats-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  max-width: 100%;
  padding: 0.35rem 0.45rem 0.35rem 0.75rem;
  background: #fff;
  color: var(--md-on-surface);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 999px;
  font-size: 0.8125rem;
  font-weight: 500;
  line-height: 1.25;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s, box-shadow 0.15s, color 0.15s;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.stats-chip:hover:not(.active) {
  border-color: rgba(255, 140, 0, 0.45);
  background: rgba(255, 140, 0, 0.04);
}

.stats-chip.active {
  border-color: var(--md-primary);
  background: rgba(255, 140, 0, 0.12);
  color: #c2410c;
  font-weight: 600;
  box-shadow: 0 1px 4px rgba(255, 140, 0, 0.2);
}

.stats-chip-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stats-chip-badges {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  flex-shrink: 0;
}

.stats-chip-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  font-size: 0.625rem;
  font-weight: 600;
  letter-spacing: 0.01em;
  color: var(--md-on-surface-variant);
  background: rgba(0, 0, 0, 0.06);
}

.stats-chip-badge--qty {
  color: #9a3412;
  background: rgba(255, 140, 0, 0.14);
}

.stats-chip.active .stats-chip-badge {
  color: #9a3412;
  background: rgba(255, 140, 0, 0.18);
}

.stats-chip.active .stats-chip-badge--qty {
  color: #fff;
  background: var(--md-primary);
}

.product-stats-tab-summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--md-spacing-sm) var(--md-spacing-md);
  margin-bottom: var(--md-spacing-md);
  padding: 0.55rem 0.85rem;
  background: linear-gradient(135deg, rgba(255, 140, 0, 0.08) 0%, rgba(255, 140, 0, 0.02) 100%);
  border-radius: 999px;
  border: 1px solid rgba(255, 140, 0, 0.22);
}

.product-stats-tab-summary-name {
  font-size: var(--md-body-size);
  font-weight: 600;
  color: var(--md-on-surface);
}

.product-stats-tab-summary-stats {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  font-weight: 500;
}

.product-stats-empty {
  padding: var(--md-spacing-lg);
  text-align: center;
  color: var(--md-on-surface-variant);
  font-size: var(--md-body-size);
}

.clear-filters-btn {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  background: #F44336;
  color: white;
  border: none;
  border-radius: var(--md-radius-sm);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.clear-filters-btn svg {
  width: 16px;
  height: 16px;
}

.clear-filters-btn:hover {
  background: #D32F2F;
  transform: translateY(-1px);
  box-shadow: 0px 2px 4px rgba(244, 67, 54, 0.3);
}

.selected-products-summary {
  margin-bottom: var(--md-spacing-lg);
  padding: var(--md-spacing-lg);
  background: linear-gradient(135deg, rgba(255, 140, 0, 0.08) 0%, rgba(255, 140, 0, 0.02) 100%);
  border: 2px solid rgba(255, 140, 0, 0.3);
  border-radius: var(--md-radius-lg);
  box-shadow: 0px 2px 8px rgba(255, 140, 0, 0.15);
}

.summary-header {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  margin-bottom: var(--md-spacing-md);
  padding-bottom: var(--md-spacing-sm);
  border-bottom: 2px solid rgba(255, 140, 0, 0.2);
}

.summary-header svg {
  width: 24px;
  height: 24px;
  color: var(--md-primary);
}

.summary-header h5 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin: 0;
  font-weight: 600;
}

.summary-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--md-spacing-md);
}

.summary-stat-card {
  background: white;
  padding: var(--md-spacing-md);
  border-radius: var(--md-radius-md);
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.summary-stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.15);
}

.summary-stat-label {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin-bottom: var(--md-spacing-xs);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.summary-stat-value {
  font-size: 1.5rem;
  color: var(--md-primary);
  font-weight: 700;
  line-height: 1.2;
}

.product-stats-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: var(--md-spacing-sm);
}

.product-stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  background: rgba(0, 0, 0, 0.02);
  border-radius: var(--md-radius-sm);
  border: 2px solid rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  user-select: none;
}

.product-stat-item:hover {
  background: rgba(255, 140, 0, 0.08);
  border-color: var(--md-primary);
  transform: translateY(-2px);
  box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
}

.product-stat-item.active {
  background: rgba(255, 140, 0, 0.15);
  border-color: var(--md-primary);
  box-shadow: 0px 2px 4px rgba(255, 140, 0, 0.3);
}

.product-stat-item.is-variant-row .product-stat-name {
  padding-left: 0.35rem;
}

.product-stat-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex: 1;
  gap: var(--md-spacing-md);
}

.product-stat-name {
  font-size: 0.8125rem;
  color: var(--md-on-surface);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.3;
  word-break: break-word;
}

.product-stat-details {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.product-stat-value {
  font-size: 0.75rem;
  color: var(--md-on-surface-variant);
  font-weight: 500;
  white-space: nowrap;
}

.product-stat-sales {
  font-size: 0.875rem;
  color: var(--md-primary);
  font-weight: 600;
  white-space: nowrap;
}

.product-stat-check {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  margin-left: var(--md-spacing-sm);
  background: var(--md-primary);
  border-radius: 50%;
  color: white;
}

.product-stat-check svg {
  width: 16px;
  height: 16px;
}

.orders-section {
  margin-top: var(--md-spacing-lg);
}

.orders-section h3 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-md);
}

.order-tabs-container {
  margin-bottom: var(--md-spacing-lg);
  background: #FFFFFF;
  padding: var(--md-spacing-md);
  border-radius: var(--md-radius-lg);
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
}

.order-tabs {
  display: flex;
  gap: var(--md-spacing-sm);
  flex-wrap: wrap;
  margin-bottom: var(--md-spacing-md);
}

.order-filters {
  display: flex;
  gap: var(--md-spacing-md);
  padding-top: var(--md-spacing-md);
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  align-items: center;
  flex-wrap: wrap;
}

.source-filter-select {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: 1px solid var(--md-outline);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  background: var(--md-surface);
  color: var(--md-on-surface);
  cursor: pointer;
  transition: var(--transition-fast);
}

.source-filter-select:hover {
  border-color: var(--md-primary);
}

.source-filter-select:focus {
  outline: none;
  border-color: var(--md-primary);
  border-width: 2px;
  box-shadow: 0 0 0 4px rgba(255, 140, 0, 0.12);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  cursor: pointer;
  user-select: none;
  padding: var(--md-spacing-xs) var(--md-spacing-sm);
  border-radius: var(--md-radius-sm);
  transition: all 0.2s;
}

.checkbox-label:hover {
  background: rgba(0, 0, 0, 0.03);
}

.checkbox-input {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--md-primary);
}

.checkbox-text {
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.7);
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  background: var(--md-surface-variant);
  color: var(--md-on-surface);
  border: 2px solid transparent;
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
}

.tab-btn svg {
  width: 20px;
  height: 20px;
}

.tab-btn:hover {
  background: rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.tab-btn.active {
  background: #FFFFFF;
  font-weight: 600;
  box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
}

.tab-btn.delivery-tab.active {
  border-color: #4CAF50;
  color: #4CAF50;
}

.tab-btn.pickup-tab.active {
  border-color: #FF8C00;
  color: #FF8C00;
}

.tab-btn.all-tab.active {
  border-color: #607D8B;
  color: #607D8B;
}

.orders-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--md-spacing-md);
  margin-top: var(--md-spacing-md);
}

@media (max-width: 1024px) {
  .orders-list {
    grid-template-columns: 1fr;
  }
}


/* Orders header with duplicate button */
.orders-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--md-spacing-md);
  gap: var(--md-spacing-md);
  flex-wrap: wrap;
}

.orders-header h3 {
  margin: 0;
}

.orders-header-actions {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-md);
  flex-wrap: wrap;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
  background: #FFFFFF;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 24px;
  padding: 8px 16px;
  min-width: 300px;
  transition: all 0.2s;
}

.search-box:focus-within {
  border-color: var(--md-primary);
  box-shadow: 0px 2px 4px rgba(255, 140, 0, 0.2);
}

.search-icon {
  width: 18px;
  height: 18px;
  color: rgba(0, 0, 0, 0.6);
  flex-shrink: 0;
  margin-right: 8px;
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 0.875rem;
  color: rgba(0, 0, 0, 0.87);
  padding: 0;
}

.search-input::placeholder {
  color: rgba(0, 0, 0, 0.4);
}

.clear-search-btn {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: rgba(0, 0, 0, 0.6);
  cursor: pointer;
  border-radius: 50%;
  padding: 0;
  margin-left: 8px;
  transition: all 0.2s;
}

.clear-search-btn:hover {
  background: rgba(0, 0, 0, 0.08);
  color: rgba(0, 0, 0, 0.87);
}

.clear-search-btn svg {
  width: 14px;
  height: 14px;
}

/* View Mode Toggle */
.view-mode-toggle {
  display: flex;
  gap: 4px;
  background: #FFFFFF;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 24px;
  padding: 4px;
}

.view-mode-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: transparent;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s;
  color: rgba(0, 0, 0, 0.6);
}

.view-mode-btn svg {
  width: 20px;
  height: 20px;
}

.view-mode-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  color: rgba(0, 0, 0, 0.87);
}

.view-mode-btn.active {
  background: var(--md-primary);
  color: white;
  box-shadow: 0px 2px 4px rgba(255, 140, 0, 0.3);
}

/* Duplicates button */
.duplicates-btn {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-xs);
  padding: 10px 20px;
  border: 1px solid rgba(156, 39, 176, 0.2);
  border-radius: 24px;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.1px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  background: #F3E5F5;
  color: #7B1FA2;
  min-height: 40px;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  white-space: nowrap;
}

.duplicates-btn:hover:not(:disabled) {
  background: #E1BEE7;
  border-color: rgba(123, 31, 162, 0.4);
  box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.16), 0px 3px 6px rgba(0, 0, 0, 0.23);
  transform: translateY(-1px);
}

.duplicates-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Duplicates Modal */
.duplicates-modal {
  max-width: 1000px;
}

.duplicates-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-lg);
}

.duplicate-set {
  background: #FFFFFF;
  border-radius: 12px;
  padding: var(--md-spacing-md);
  box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
  border: 2px solid #F3E5F5;
}

.duplicate-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--md-spacing-md);
  padding-bottom: var(--md-spacing-sm);
  border-bottom: 2px solid #7B1FA2;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-info strong {
  font-size: 1rem;
  color: rgba(0, 0, 0, 0.87);
}

.user-info .phone {
  font-size: 0.875rem;
  color: rgba(0, 0, 0, 0.6);
}

.group-deal-info {
  font-size: 0.875rem;
  color: #7B1FA2;
  font-weight: 500;
}

.duplicate-orders {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-sm);
  margin-bottom: var(--md-spacing-md);
}

.duplicate-order {
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  background: #F5F5F5;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.duplicate-order .order-id {
  font-family: 'Courier New', monospace;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.87);
  margin-bottom: 4px;
}

.duplicate-order .order-details {
  display: flex;
  gap: var(--md-spacing-md);
  font-size: 0.875rem;
  color: rgba(0, 0, 0, 0.6);
}

.merge-btn-action {
  width: 100%;
  padding: 10px 24px;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.1px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(123, 31, 162, 0.2);
  background: #F3E5F5;
  color: #7B1FA2;
  min-height: 40px;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
}

.merge-btn-action:hover {
  background: #E1BEE7;
  border-color: rgba(123, 31, 162, 0.4);
  box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.16), 0px 3px 6px rgba(0, 0, 0, 0.23);
  transform: translateY(-1px);
}

.merge-btn-action:active {
  background: #CE93D8;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  transform: translateY(0);
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
  background: #FFFFFF;
  border-radius: 24px;
  max-width: 800px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0px 11px 15px -7px rgba(0, 0, 0, 0.2), 0px 24px 38px 3px rgba(0, 0, 0, 0.14), 0px 9px 46px 8px rgba(0, 0, 0, 0.12);
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  padding-top: calc(var(--md-spacing-md) + env(safe-area-inset-top));
  background: linear-gradient(135deg, #FF8C00 0%, #FFA500 100%);
  border-bottom: 1px solid rgba(255, 165, 0, 0.2);
  border-radius: 24px 24px 0 0;
  position: relative;
}

/* Extend background color into safe area */
.modal-header::before {
  content: '';
  position: absolute;
  top: calc(-1 * env(safe-area-inset-top));
  left: 0;
  right: 0;
  height: env(safe-area-inset-top);
  background: linear-gradient(135deg, #FF8C00 0%, #FFA500 100%);
  border-radius: 24px 24px 0 0;
}

.modal-header h2 {
  font-size: 1.25rem;
  color: rgba(0, 0, 0, 0.9);
  font-weight: 600;
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
  padding: 0;
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
  padding: var(--md-spacing-lg);
  background: #FAFAFA;
}

/* Loading Spinner */
.loading-section,
.orders-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: var(--md-spacing-xl);
  background: linear-gradient(135deg, rgba(255, 140, 0, 0.03) 0%, rgba(255, 165, 0, 0.05) 100%);
  border-radius: var(--md-radius-lg);
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24);
  min-height: 200px;
  position: relative;
  overflow: hidden;
}

.loading-section::before,
.orders-loading::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 140, 0, 0.1), transparent);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% {
    left: -100%;
  }
  100% {
    left: 100%;
  }
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--md-spacing-md);
  position: relative;
  z-index: 1;
  animation: fadeInUp 0.4s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.spinner {
  width: 56px;
  height: 56px;
  color: var(--md-primary);
  animation: spin 1s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite;
  filter: drop-shadow(0 2px 4px rgba(255, 140, 0, 0.2));
}

@keyframes spin {
  0% {
    transform: rotate(0deg) scale(1);
  }
  50% {
    transform: rotate(180deg) scale(1.1);
  }
  100% {
    transform: rotate(360deg) scale(1);
  }
}

.spinner circle {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.3;
  }
  50% {
    opacity: 1;
  }
}

.spinner path {
  animation: dash 1.5s ease-in-out infinite;
}

@keyframes dash {
  0% {
    stroke-dasharray: 1, 150;
    stroke-dashoffset: 0;
  }
  50% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -35;
  }
  100% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -124;
  }
}

.loading-spinner span {
  font-size: 0.9375rem;
  color: var(--md-primary);
  font-weight: 600;
  letter-spacing: 0.3px;
  animation: pulse-text 1.5s ease-in-out infinite;
}

@keyframes pulse-text {
  0%, 100% {
    opacity: 0.7;
  }
  50% {
    opacity: 1;
  }
}

/* Laptop Responsive Styles */
@media (max-width: 1366px) {
  .group-deal-detail-page {
    padding: var(--md-spacing-md);
  }
  
  .header-actions {
    gap: 6px;
  }
  
  .edit-btn,
  .delete-btn,
  .view-orders-btn {
    padding: 8px 16px;
    font-size: 0.875rem;
  }
  
  .product-card {
    padding: var(--md-spacing-md);
  }
  
  .product-image {
    height: 140px;
  }
  
  .product-name {
    font-size: 1rem;
  }
  
  .summary-stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--md-spacing-sm);
  }
  
  .summary-stat-value {
    font-size: 1.25rem;
  }
}

/* Mobile Responsive Styles */
@media (max-width: 767px) {
  .group-deal-detail-page {
    padding: var(--md-spacing-sm);
  }
  
  .selected-products-summary {
    padding: var(--md-spacing-md);
  }
  
  .summary-header h5 {
    font-size: 0.9375rem;
  }
  
  .summary-stats-grid {
    grid-template-columns: 1fr;
    gap: var(--md-spacing-sm);
  }
  
  .summary-stat-card {
    padding: var(--md-spacing-sm) var(--md-spacing-md);
  }
  
  .summary-stat-value {
    font-size: 1.125rem;
  }
  
  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: var(--md-spacing-sm);
    margin-left: calc(-1 * var(--md-spacing-sm));
    margin-right: calc(-1 * var(--md-spacing-sm));
    margin-top: calc(-1 * var(--md-spacing-sm));
    margin-bottom: var(--md-spacing-md);
  }

  .page-nav {
    display: none;
  }

  .deal-header h2 {
    display: none;
  }

  .header-actions {
    flex-direction: column;
    width: 100%;
    gap: var(--md-spacing-sm);
    padding: 0 var(--md-spacing-sm);
  }
  
  .commission-btn,
  .bulk-delivery-btn,
  .export-btn {
    width: 100%;
    justify-content: center;
    font-size: 0.875rem;
    padding: var(--md-spacing-sm) var(--md-spacing-md);
  }
  
  .commission-btn svg,
  .bulk-delivery-btn svg,
  .export-btn svg {
    width: 18px;
    height: 18px;
  }
  
  .deal-info-card {
    padding: var(--md-spacing-md);
  }
  
  .deal-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--md-spacing-sm);
  }
  
  .deal-header h2 {
    font-size: 1.25rem;
  }
  
  .status-control-group {
    width: 100%;
    flex-direction: column;
    align-items: stretch;
    gap: var(--md-spacing-sm);
  }
  
  .status-select {
    width: 100%;
  }
  
  .deal-dates {
    flex-direction: column;
    gap: var(--md-spacing-sm);
  }
  
  .date-item {
    flex-direction: column;
    gap: var(--md-spacing-xs);
  }
  
  .date-label {
    font-size: 0.75rem;
  }
  
  .date-value {
    font-size: 0.875rem;
  }
  
  .statistics-section {
    padding: var(--md-spacing-md);
  }
  
  .statistics-section h3 {
    font-size: 1rem;
    margin-bottom: var(--md-spacing-sm);
  }

  .stats-heading-desktop {
    font-size: 1rem;
    margin-bottom: var(--md-spacing-sm);
  }

  .mobile-stats-toggle {
    display: flex;
    width: 100%;
    align-items: center;
    justify-content: space-between;
    gap: var(--md-spacing-sm);
    padding: var(--md-spacing-md);
    margin: 0 0 var(--md-spacing-md) 0;
    background: var(--md-surface-variant);
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: var(--md-radius-md);
    font-size: 1rem;
    font-weight: 600;
    color: var(--md-on-surface);
    cursor: pointer;
    text-align: left;
    -webkit-tap-highlight-color: transparent;
  }

  .mobile-stats-toggle.product-stats-toggle {
    margin-top: 0;
    margin-bottom: var(--md-spacing-md);
  }

  .product-stats-segment {
    display: flex;
    width: 100%;
  }

  .segment-chip {
    flex: 1;
    min-width: 0;
    padding: 0.45rem 0.35rem;
    font-size: 0.75rem;
    text-align: center;
  }

  .product-stats-chips {
    gap: 0.4rem;
  }

  .stats-chip {
    font-size: 0.75rem;
    padding: 0.3rem 0.35rem 0.3rem 0.65rem;
  }

  .stats-chip-label {
    max-width: 8rem;
  }

  .product-stats-tab-summary {
    border-radius: var(--md-radius-md);
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
    gap: var(--md-spacing-sm);
  }
  
  .stat-card {
    padding: var(--md-spacing-md);
  }
  
  .stat-icon {
    width: 36px;
    height: 36px;
  }
  
  .stat-icon svg {
    width: 18px;
    height: 18px;
  }
  
  .stat-label {
    font-size: 0.75rem;
  }
  
  .stat-value {
    font-size: 1.25rem;
  }
  
  .products-section {
    padding: var(--md-spacing-md);
  }
  
  .products-section h3 {
    font-size: 1rem;
  }
  
  .products-grid-section {
    grid-template-columns: 1fr;
    gap: var(--md-spacing-sm);
  }
  
  .product-card {
    padding: var(--md-spacing-sm);
  }
  
  .product-image {
    height: 120px;
  }
  
  .product-name {
    font-size: 0.875rem;
  }
  
  .orders-section {
    padding: var(--md-spacing-md);
  }
  
  .orders-section h3 {
    font-size: 1rem;
  }

  .orders-header {
    flex-direction: column;
    align-items: stretch;
  }

  .orders-header-actions {
    flex-direction: column;
    align-items: stretch;
    width: 100%;
  }

  .search-box {
    min-width: 0;
    width: 100%;
    box-sizing: border-box;
  }

  .view-mode-toggle {
    display: flex;
    justify-content: center;
    width: 100%;
  }

  .duplicates-btn {
    width: 100%;
    justify-content: center;
  }

  .order-filters {
    flex-direction: column;
    align-items: stretch;
    gap: var(--md-spacing-sm);
  }

  .source-filter-select {
    width: 100%;
    box-sizing: border-box;
  }
  
  .order-tabs {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    flex-wrap: nowrap;
    gap: var(--md-spacing-xs);
    padding-bottom: var(--md-spacing-xs);
    margin-bottom: var(--md-spacing-sm);
  }
  
  .tab-btn {
    white-space: nowrap;
    font-size: 0.75rem;
    padding: var(--md-spacing-xs) var(--md-spacing-sm);
    flex-shrink: 0;
  }
  
  .orders-list-view {
    padding: 0;
  }
  
  .modal-overlay {
    padding: var(--md-spacing-xs);
  }
  
  .modal-content {
    max-width: 100%;
    max-height: 95vh;
    border-radius: var(--md-radius-md);
  }
  
  .modal-header {
    padding: var(--md-spacing-md);
  }
  
  .modal-header h2 {
    font-size: 1rem;
  }
  
  .modal-body {
    padding: var(--md-spacing-md);
  }
}

/* Extra small mobile */
@media (max-width: 360px) {
  .deal-header h2 {
    font-size: 1.125rem;
  }
  
  .stat-value {
    font-size: 1.125rem;
  }
  
  .commission-btn,
  .bulk-delivery-btn,
  .export-btn {
    font-size: 0.8125rem;
    padding: var(--md-spacing-xs) var(--md-spacing-sm);
  }
  
  .tab-btn {
    font-size: 0.6875rem;
    padding: 6px var(--md-spacing-xs);
  }
}

</style>

