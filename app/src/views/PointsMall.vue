<template>
  <div class="points-mall-page">
    <header class="page-header">
      <button @click="$router.back()" class="back-btn">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1>积分商城</h1>
      <div class="header-spacer"></div>
    </header>

    <main class="page-content">
      <div class="coming-soon-container">
        <div class="icon-wrapper">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2>即将上线</h2>
        <p class="description">
          通过购买产品或邀请朋友下单即可获得积分，未来可以在积分商城兑换精美礼品！
        </p>
        <p class="sub-description">
          更多精彩内容，敬请期待！
        </p>
      </div>
    </main>
  </div>
</template>

<script>
export default {
  name: 'PointsMall'
}
</script>

<style scoped>
.points-mall-page {
  min-height: 100vh;
  background: var(--md-background);
  padding-bottom: 80px; /* Space for bottom nav */
}

.page-header {
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-2);
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: calc(var(--md-spacing-lg) + env(safe-area-inset-top));
  padding-left: var(--md-spacing-md);
  padding-right: var(--md-spacing-md);
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

.page-header h1 {
  font-size: var(--md-headline-size);
  color: white;
  font-weight: 500;
  flex: 1;
  text-align: center;
  letter-spacing: -0.5px;
  margin: 0;
}

.page-content {
  padding: var(--md-spacing-xl);
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 200px);
}

.coming-soon-container {
  text-align: center;
  max-width: 500px;
  padding: var(--md-spacing-xl);
}

.icon-wrapper {
  width: 120px;
  height: 120px;
  margin: 0 auto var(--md-spacing-xl);
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(255, 140, 0, 0.1) 0%, rgba(255, 215, 0, 0.1) 100%);
  border-radius: 50%;
  color: var(--md-primary);
}

.icon-wrapper svg {
  width: 64px;
  height: 64px;
}

.coming-soon-container h2 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-lg);
  font-weight: 500;
}

.description {
  font-size: var(--md-body-size);
  color: var(--md-on-surface-variant);
  line-height: 1.8;
  margin-bottom: var(--md-spacing-md);
}

.sub-description {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  opacity: 0.8;
  font-style: italic;
}

@media (max-width: 480px) {
  .page-content {
    padding: var(--md-spacing-lg);
  }
  
  .coming-soon-container {
    padding: var(--md-spacing-lg);
  }
  
  .icon-wrapper {
    width: 100px;
    height: 100px;
  }
  
  .icon-wrapper svg {
    width: 48px;
    height: 48px;
  }
}
</style>

