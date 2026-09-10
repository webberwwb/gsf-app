<template>
  <Teleport to="body">
    <div v-if="src" class="lightbox" role="dialog" aria-modal="true" aria-label="查看照片" @click="$emit('close')">
      <img :src="src" alt="送达照片" @click.stop />
      <button type="button" class="close-btn" @click="$emit('close')">关闭</button>
    </div>
  </Teleport>
</template>

<script>
export default {
  name: 'ImageLightbox',
  props: {
    src: {
      type: String,
      default: ''
    }
  },
  emits: ['close']
}
</script>

<style scoped>
.lightbox {
  position: fixed;
  inset: 0;
  z-index: 12000;
  background: rgba(0, 0, 0, 0.88);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1.25rem;
  padding-bottom: calc(1.25rem + env(safe-area-inset-bottom));
}
.lightbox img {
  max-width: 100%;
  max-height: calc(100vh - 7rem);
  object-fit: contain;
  border-radius: 8px;
}
.close-btn {
  margin-top: 1rem;
  min-height: 44px;
  min-width: 120px;
  border: none;
  border-radius: 8px;
  background: #fff;
  color: #1c1b16;
  font-weight: 600;
  cursor: pointer;
}
</style>
