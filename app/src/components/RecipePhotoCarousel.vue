<template>
  <div class="photo-frame" :class="{ 'has-pages': images.length > 1 }">
    <div class="stage">
      <div ref="scroller" class="scroller" @scroll.passive="onScroll">
        <img v-for="(image, index) in images" :key="index" :src="image" :alt="alt" draggable="false" />
      </div>
      <slot />
      <template v-if="images.length > 1">
        <button type="button" class="carousel-btn prev" aria-label="上一张" @click.stop="step(-1)">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <button type="button" class="carousel-btn next" aria-label="下一张" @click.stop="step(1)">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </button>
        <div class="carousel-indicator">{{ active + 1 }} / {{ images.length }}</div>
      </template>
    </div>
    <div v-if="images.length > 1" class="carousel-thumbnails">
      <button
        v-for="(image, index) in images"
        :key="index"
        type="button"
        class="thumbnail"
        :class="{ active: index === active }"
        :aria-label="`第 ${index + 1} 张，共 ${images.length} 张`"
        :aria-current="index === active ? 'true' : undefined"
        @click.stop="go(index)"
      >
        <img :src="image" alt="" draggable="false" />
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RecipePhotoCarousel',
  props: {
    images: { type: Array, default: () => [] },
    alt: { type: String, default: '' }
  },
  data() {
    return { active: 0 }
  },
  watch: {
    images() {
      this.active = 0
      this.$nextTick(() => {
        if (this.$refs.scroller) this.$refs.scroller.scrollLeft = 0
      })
    }
  },
  methods: {
    onScroll(event) {
      const el = event.target
      const width = el.clientWidth || 1
      const index = Math.round(el.scrollLeft / width)
      this.active = Math.min(this.images.length - 1, Math.max(0, index))
    },
    step(direction) {
      if (!this.images.length) return
      const next = (this.active + direction + this.images.length) % this.images.length
      this.go(next)
    },
    go(index) {
      const el = this.$refs.scroller
      if (!el) return
      this.active = index
      el.scrollTo({ left: index * el.clientWidth, behavior: 'smooth' })
    }
  }
}
</script>

<style scoped>
.photo-frame {
  width: 100%;
  background: #FFF6EA;
}
.stage {
  position: relative;
  width: 100%;
  height: var(--recipe-photo-h, 52vw);
  overflow: hidden;
  background: #FFF6EA;
}
.scroller {
  display: flex;
  width: 100%;
  height: 100%;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-x: contain;
}
.scroller::-webkit-scrollbar { display: none; }
.scroller img {
  flex: 0 0 100%;
  width: 100%;
  height: 100%;
  object-fit: cover;
  scroll-snap-align: start;
  background: #FFF6EA;
  pointer-events: none;
}
.photo-frame.has-pages ::v-slotted(.photo-facts) {
  padding-bottom: 2.15rem;
}
.carousel-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 3;
  width: 40px;
  height: 40px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  color: #374151;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  cursor: pointer;
}
.carousel-btn svg {
  width: 20px;
  height: 20px;
}
.carousel-btn.prev { left: 12px; }
.carousel-btn.next { right: 12px; }
.carousel-indicator {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 3;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.2;
  pointer-events: none;
}
.carousel-thumbnails {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 8px;
  scrollbar-width: thin;
}
.carousel-thumbnails::-webkit-scrollbar { height: 4px; }
.carousel-thumbnails::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 2px;
}
.thumbnail {
  flex-shrink: 0;
  width: 60px;
  height: 60px;
  padding: 0;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid transparent;
  background: #FFF6EA;
  opacity: 0.6;
  cursor: pointer;
}
.thumbnail.active {
  opacity: 1;
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}
.thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  pointer-events: none;
}
</style>
