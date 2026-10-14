<template>
  <button
    v-if="count > 0"
    type="button"
    class="recipe-entry"
    :aria-label="`查看菜谱，${count} 道`"
    @click.stop="$emit('open', productId)"
  >
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" aria-hidden="true">
      <path stroke-linecap="round" stroke-linejoin="round" d="M4 11h16" />
      <path stroke-linecap="round" stroke-linejoin="round" d="M6 11a6 6 0 0012 0" />
      <path stroke-linecap="round" stroke-linejoin="round" d="M8 7.5c.7.9 1.6.9 2.3 0 .7-.9 1.6-.9 2.3 0 .7.9 1.6.9 2.3 0" />
    </svg>
    <span class="label">查看菜谱（{{ count }}）</span>
    <span class="new-badge">new</span>
  </button>
</template>

<script>
export default {
  name: 'RecipeProductEntry',
  props: {
    productId: { type: [Number, String], required: true },
    count: { type: Number, default: 0 }
  },
  emits: ['open']
}
</script>

<style scoped>
.recipe-entry {
  display: inline-flex;
  align-items: center;
  gap: 0.28rem;
  margin-top: 0.35rem;
  padding: 0;
  border: none;
  background: none;
  color: var(--md-primary);
  line-height: 1;
}
.recipe-entry svg {
  width: 18px;
  height: 18px;
  flex: none;
}
.label {
  font-size: 0.78rem;
  font-weight: 600;
}
.new-badge {
  padding: 0.08rem 0.32rem;
  border-radius: 999px;
  background: #E25B4A;
  color: white;
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  line-height: 1.2;
  text-transform: lowercase;
}
</style>
