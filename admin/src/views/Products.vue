<template>
  <div class="products-page">
    <!-- Tab Navigation -->
    <div class="tabs-container">
      <button 
        :class="['tab', { active: activeTab === 'products' }]"
        @click="activeTab = 'products'"
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
        </svg>
        <span>商品列表</span>
      </button>
      <button 
        :class="['tab', { active: activeTab === 'categories' }]"
        @click="activeTab = 'categories'"
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
        </svg>
        <span>分类管理</span>
      </button>
      <button 
        :class="['tab', { active: activeTab === 'assignment' }]"
        @click="activeTab = 'assignment'"
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
        <span>批量分配</span>
      </button>
    </div>

    <!-- Products Tab -->
    <div v-show="activeTab === 'products'" class="tab-content">
      <ProductsTab />
    </div>

    <!-- Categories Tab -->
    <div v-show="activeTab === 'categories'" class="tab-content">
      <CategoriesTab />
    </div>

    <!-- Assignment Tab -->
    <div v-show="activeTab === 'assignment'" class="tab-content">
      <AssignmentTab />
    </div>
  </div>
</template>

<script>
import ProductsTab from '../components/ProductsTab.vue'
import CategoriesTab from '../components/CategoriesTab.vue'
import AssignmentTab from '../components/AssignmentTab.vue'

export default {
  name: 'Products',
  components: {
    ProductsTab,
    CategoriesTab,
    AssignmentTab
  },
  data() {
    return {
      activeTab: 'products'
    }
  }
}
</script>

<style scoped>
.products-page {
  max-width: 1400px;
}

.tabs-container {
  display: flex;
  gap: var(--md-spacing-xs);
  margin-bottom: var(--md-spacing-lg);
  background: var(--md-surface);
  padding: var(--md-spacing-sm);
  border-radius: var(--md-radius-lg);
  box-shadow: var(--md-elevation-1);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.tab {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  border: none;
  background: transparent;
  color: var(--md-on-surface-variant);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
  flex-shrink: 0;
}

.tab svg {
  width: 20px;
  height: 20px;
}

.tab:hover:not(.active) {
  background: var(--md-surface-variant);
}

.tab.active {
  background: var(--md-primary);
  color: white;
  box-shadow: var(--md-elevation-2);
}

.tab.active:hover {
  filter: brightness(0.94);
}

.tab-content {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 768px) {
  .tab {
    padding: var(--md-spacing-sm) var(--md-spacing-md);
    font-size: var(--md-label-size);
  }
  
  .tab svg {
    width: 18px;
    height: 18px;
  }
}
</style>
