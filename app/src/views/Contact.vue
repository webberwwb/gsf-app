<template>
  <div class="contact-page">
    <header class="page-header">
      <h1>联系我们</h1>
    </header>

    <main class="page-content">
      <p class="intro">添加微信或关注小红书，欢迎随时联系我们。</p>

      <section class="contact-card">
        <div class="card-heading">
          <span class="brand-icon wechat-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M8.4 4C4.7 4 1.7 6.7 1.7 10c0 1.9 1.1 3.6 2.8 4.7L3.8 17l2.9-1.4c.5.1 1.1.2 1.7.2.2 0 .4 0 .6 0C8.4 15.2 8 14.1 8 13c0-3.3 3.1-6 7-6 .2 0 .4 0 .6 0C14.5 4.8 11.6 4 8.4 4zm9.6 5c-3.3 0-6 2.2-6 5s2.7 5 6 5c.5 0 1-.1 1.4-.2L22 20l-.9-2.2c1.2-1.1 1.9-2.4 1.9-3.8 0-2.8-2.7-5-6-5z" />
            </svg>
          </span>
          <h2>微信</h2>
        </div>

        <div class="id-row">
          <div>
            <p class="id-label">微信号</p>
            <p class="id-value">Grainstory</p>
          </div>
          <button type="button" class="copy-btn" @click="copyWechatId">复制</button>
        </div>

        <div class="qr-wrap">
          <img
            src="/images/wechat-qr.png"
            alt="微信二维码 Grainstory"
            class="qr-image"
          />
        </div>
        <p class="hint">打开微信扫一扫添加，或长按保存二维码</p>
      </section>

      <a
        class="contact-card xhs-card"
        href="https://www.rednote.com/user/profile/663fa6330000000003030ee6"
        target="_blank"
        rel="noopener noreferrer"
      >
        <div class="card-heading">
          <span class="brand-icon xhs-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </span>
          <h2>小红书</h2>
        </div>
        <div class="xhs-row">
          <div>
            <p class="id-label">账号</p>
            <p class="id-value xhs-name">谷语农庄</p>
          </div>
          <span class="open-link">打开主页 ›</span>
        </div>
      </a>
    </main>
  </div>
</template>

<script>
import { useModal } from '../composables/useModal'

export default {
  name: 'Contact',
  setup() {
    const { success, error: showError } = useModal()
    return { success, showError }
  },
  methods: {
    async copyWechatId() {
      try {
        await navigator.clipboard.writeText('Grainstory')
        await this.success('已复制微信号 Grainstory', { title: '完成' })
      } catch (_) {
        await this.showError('复制失败，请手动复制 Grainstory')
      }
    }
  }
}
</script>

<style scoped>
.contact-page {
  min-height: 100vh;
  background: var(--md-background);
  padding-bottom: calc(80px + env(safe-area-inset-bottom));
}

.page-header {
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  padding: var(--md-spacing-lg);
  padding-top: calc(var(--md-spacing-lg) + env(safe-area-inset-top));
  box-shadow: var(--md-elevation-2);
  position: sticky;
  top: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
}

.page-header h1 {
  font-size: var(--md-headline-size);
  color: white;
  font-weight: 500;
  letter-spacing: -0.5px;
  margin: 0;
}

.page-content {
  padding: var(--md-spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.intro {
  margin: 0;
  color: var(--md-on-surface-variant);
  font-size: var(--md-body-size);
  text-align: center;
}

.contact-card {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.card-heading {
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
}

.card-heading h2 {
  margin: 0;
  font-size: var(--md-title-size);
  font-weight: 600;
  color: var(--md-on-surface);
}

.brand-icon {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.brand-icon svg {
  width: 18px;
  height: 18px;
}

.wechat-icon {
  background: #07C160;
  color: white;
}

.xhs-icon {
  background: #FF2442;
  color: white;
}

.id-row,
.xhs-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--md-spacing-md);
}

.id-label {
  margin: 0;
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.id-value {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--md-on-surface);
  letter-spacing: 0.02em;
}

.copy-btn {
  background: var(--md-primary);
  color: white;
  border: none;
  border-radius: var(--md-radius-sm);
  padding: 0.4rem 0.75rem;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  flex-shrink: 0;
}

.qr-wrap {
  display: flex;
  justify-content: center;
  padding: var(--md-spacing-sm) 0;
}

.qr-image {
  width: 220px;
  height: 220px;
  max-width: 100%;
  object-fit: contain;
  background: white;
  border-radius: var(--md-radius-md);
}

.hint {
  margin: 0;
  text-align: center;
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.xhs-card {
  text-decoration: none;
  color: inherit;
  transition: box-shadow 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.xhs-card:hover,
.xhs-card:focus-visible {
  box-shadow: var(--md-elevation-2);
}

.xhs-name {
  color: #FF2442;
}

.open-link {
  font-size: var(--md-label-size);
  font-weight: 500;
  color: var(--md-primary);
  flex-shrink: 0;
}
</style>
