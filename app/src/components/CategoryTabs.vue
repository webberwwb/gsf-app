<template>
  <div
    class="category-tabs-sticky-container"
    :class="{ 'no-bleed': !bleed }"
    :style="stickyTop ? { top: stickyTop } : null"
  >
    <div class="category-tabs-wrapper" ref="wrapper">
      <div class="category-tabs-container" ref="scroller">
        <div class="category-tabs">
          <button
            v-if="showDiscount"
            type="button"
            class="category-tab discount-tab"
            :class="{ active: selectedId === 'discount' }"
            @click="selectCategory('discount')"
          >
            折扣
          </button>
          <button
            v-for="category in categories"
            :key="category.id"
            type="button"
            :class="['category-tab', { active: selectedId === category.id }]"
            @click="selectCategory(category.id)"
          >
            {{ category.name }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CategoryTabs',
  props: {
    categories: {
      type: Array,
      default: () => []
    },
    showDiscount: {
      type: Boolean,
      default: false
    },
    headerSelector: {
      type: String,
      default: '.page-header'
    },
    stickyTop: {
      type: String,
      default: null
    },
    bleed: {
      type: Boolean,
      default: true
    },
    pinOnIos: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      selectedId: null,
      stickyOriginalTop: null,
      pinLeft: null,
      pinWidth: null
    }
  },
  watch: {
    categories() {
      this.$nextTick(() => this.updateScrollIndicators())
    },
    showDiscount() {
      this.$nextTick(() => this.updateScrollIndicators())
    },
    selectedId() {
      this.$nextTick(() => this.scrollTabIntoView())
    }
  },
  mounted() {
    this.setupScrollIndicators()
    this.setupScrollSpy()
    if (this.pinOnIos) this.setupIosPin()
  },
  beforeUnmount() {
    this.$refs.scroller?.removeEventListener('scroll', this.updateScrollIndicators)
    window.removeEventListener('resize', this.updateScrollIndicators)
    window.removeEventListener('scroll', this.handleScrollSpy)
    window.removeEventListener('scroll', this.handleIosPin)
    if (this._scrollSpyTimeout) {
      clearTimeout(this._scrollSpyTimeout)
      this._scrollSpyTimeout = null
    }
    this.clearScrollLock()
    this.clearPinPlaceholder()
  },
  methods: {
    normalizeCategoryId(id) {
      if (id == null || id === '') return null
      if (id === 'discount') return 'discount'
      const n = parseInt(id, 10)
      return Number.isNaN(n) ? id : n
    },
    selectCategory(categoryId) {
      const normalized = this.normalizeCategoryId(categoryId)
      this.selectedId = normalized
      this._scrollLockId = normalized
      this.$nextTick(() => this.scrollToSection(categoryId))
    },
    scrollToSection(categoryId) {
      const categoryHeader = document.querySelector(`.category-header[data-category-id="${categoryId}"]`)
      if (!categoryHeader) {
        this.releaseScrollLock()
        return
      }

      const header = document.querySelector(this.headerSelector)
      const tabsHeight = this.$el?.offsetHeight || 0
      let offset = 140
      if (header) {
        offset = header.offsetHeight + tabsHeight + 10
      }

      const top = categoryHeader.getBoundingClientRect().top + window.pageYOffset - offset
      this._scrollTargetY = top
      if (Math.abs((window.pageYOffset || 0) - top) <= 2) {
        this.releaseScrollLock()
        return
      }
      this.armScrollLock()
      window.scrollTo({ top, behavior: 'smooth' })
    },
    armScrollLock() {
      this.clearScrollLock()
      this._releaseOnUser = (event) => {
        if (event.type === 'keydown') {
          const scrolls = ['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End', ' ']
          if (!scrolls.includes(event.key)) return
        }
        const tabs = this.$refs.scroller
        if (tabs && event.target && tabs.contains(event.target)) return
        this.releaseScrollLock()
      }
      window.addEventListener('wheel', this._releaseOnUser, { passive: true })
      window.addEventListener('touchstart', this._releaseOnUser, { passive: true })
      window.addEventListener('keydown', this._releaseOnUser)
      this._onScrollEnd = (event) => {
        const target = event.target
        if (target !== document && target !== document.documentElement && target !== document.body) return
        this.releaseScrollLock()
      }
      window.addEventListener('scrollend', this._onScrollEnd)
      this._scrollLockTimer = setTimeout(() => this.releaseScrollLock(), 4000)
    },
    releaseScrollLock() {
      this._scrollLockId = null
      this._scrollTargetY = null
      this.clearScrollLock()
    },
    clearScrollLock() {
      if (this._releaseOnUser) {
        window.removeEventListener('wheel', this._releaseOnUser)
        window.removeEventListener('touchstart', this._releaseOnUser)
        window.removeEventListener('keydown', this._releaseOnUser)
        this._releaseOnUser = null
      }
      if (this._onScrollEnd) {
        window.removeEventListener('scrollend', this._onScrollEnd)
        this._onScrollEnd = null
      }
      if (this._scrollLockTimer) {
        clearTimeout(this._scrollLockTimer)
        this._scrollLockTimer = null
      }
    },
    setupScrollIndicators() {
      const container = this.$refs.scroller
      if (!container) return
      this.updateScrollIndicators()
      container.addEventListener('scroll', this.updateScrollIndicators)
      window.addEventListener('resize', this.updateScrollIndicators)
    },
    updateScrollIndicators() {
      const container = this.$refs.scroller
      const wrapper = this.$refs.wrapper
      if (!container) return

      const canScrollLeft = container.scrollLeft > 10
      const canScrollRight = container.scrollLeft < container.scrollWidth - container.clientWidth - 10
      container.classList.toggle('can-scroll-left', canScrollLeft)
      container.classList.toggle('can-scroll-right', canScrollRight)
      if (container.scrollLeft > 0 && wrapper) {
        wrapper.classList.add('user-has-scrolled')
      }
    },
    setupScrollSpy() {
      window.addEventListener('scroll', this.handleScrollSpy, { passive: true })
      this.handleScrollSpy()
    },
    handleScrollSpy() {
      if (this._scrollSpyTimeout) return
      this._scrollSpyTimeout = setTimeout(() => {
        this._scrollSpyTimeout = null

        if (this._scrollLockId != null) {
          const y = window.pageYOffset || 0
          if (this._scrollTargetY != null && Math.abs(y - this._scrollTargetY) <= 2) {
            this.releaseScrollLock()
          } else {
            return
          }
        }

        const header = document.querySelector(this.headerSelector)
        const stickyContainer = this.$el
        if (!header || !stickyContainer) return

        const offset = header.offsetHeight + stickyContainer.offsetHeight + 20
        const categoryHeaders = document.querySelectorAll('.category-header[data-category-id]')
        if (categoryHeaders.length === 0) return

        let currentCategoryId = null
        for (const categoryHeader of categoryHeaders) {
          if (categoryHeader.getBoundingClientRect().top <= offset) {
            currentCategoryId = categoryHeader.getAttribute('data-category-id')
          } else {
            break
          }
        }

        const normalizedId = this.normalizeCategoryId(currentCategoryId)
        if (normalizedId != null && this.selectedId !== normalizedId) {
          this.selectedId = normalizedId
        }
      }, 100)
    },
    scrollTabIntoView() {
      const tabsContainer = this.$refs.scroller
      if (!tabsContainer) return

      const activeTab = tabsContainer.querySelector('.category-tab.active')
      if (!activeTab) return

      const containerScrollLeft = tabsContainer.scrollLeft
      const tabOffsetLeft = activeTab.offsetLeft
      const tabWidth = activeTab.offsetWidth
      const containerWidth = tabsContainer.clientWidth
      const visibleStart = containerScrollLeft
      const visibleEnd = containerScrollLeft + containerWidth
      const tabStart = tabOffsetLeft
      const tabEnd = tabOffsetLeft + tabWidth

      if (tabStart < visibleStart) {
        tabsContainer.scrollTo({
          left: Math.max(0, tabOffsetLeft - 20),
          behavior: 'smooth'
        })
      } else if (tabEnd > visibleEnd) {
        tabsContainer.scrollTo({
          left: tabOffsetLeft - containerWidth + tabWidth + 20,
          behavior: 'smooth'
        })
      }
    },
    setupIosPin() {
      const isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
        window.navigator.standalone === true
      const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream
      if (!isIOS || !isStandalone) return

      setTimeout(() => {
        if (!this.$el) return
        this.stickyOriginalTop = this.$el.offsetTop
        window.addEventListener('scroll', this.handleIosPin, { passive: true })
        this.handleIosPin()
      }, 500)
    },
    handleIosPin() {
      const el = this.$el
      const header = document.querySelector(this.headerSelector)
      if (!el || !header) return

      if (this.stickyOriginalTop == null) {
        this.stickyOriginalTop = el.offsetTop
      }

      const headerHeight = header.offsetHeight
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop
      const shouldPin = scrollTop >= (this.stickyOriginalTop - headerHeight)

      if (shouldPin) {
        if (this.pinLeft == null) {
          const rect = el.getBoundingClientRect()
          this.pinLeft = rect.left
          this.pinWidth = rect.width
        }
        let placeholder = el.previousElementSibling
        if (!placeholder || !placeholder.classList.contains('sticky-placeholder')) {
          placeholder = document.createElement('div')
          placeholder.className = 'sticky-placeholder'
          placeholder.style.height = `${el.offsetHeight}px`
          el.parentNode.insertBefore(placeholder, el)
        }
        el.style.position = 'fixed'
        el.style.top = `${headerHeight}px`
        el.style.left = `${this.pinLeft}px`
        el.style.right = 'auto'
        el.style.width = `${this.pinWidth}px`
        el.style.zIndex = '150'
        el.style.margin = '0'
        el.style.boxSizing = 'border-box'
      } else {
        this.clearPinPlaceholder()
        this.pinLeft = null
        this.pinWidth = null
        el.style.position = ''
        el.style.top = ''
        el.style.left = ''
        el.style.right = ''
        el.style.width = ''
        el.style.zIndex = ''
        el.style.margin = ''
        el.style.boxSizing = ''
      }
    },
    clearPinPlaceholder() {
      const el = this.$el
      const placeholder = el?.previousElementSibling
      if (placeholder && placeholder.classList.contains('sticky-placeholder')) {
        placeholder.remove()
      }
    }
  }
}
</script>

<style scoped>
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

.category-tabs-sticky-container.no-bleed {
  margin-left: calc(-1 * var(--md-spacing-md));
  margin-right: calc(-1 * var(--md-spacing-md));
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

.category-tab.discount-tab {
  background: #FFEBEE;
  color: #E53935;
}

.category-tab.discount-tab:hover {
  background: #FFCDD2;
}

.category-tab.discount-tab.active {
  background: #FF4444;
  color: #fff;
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
</style>
