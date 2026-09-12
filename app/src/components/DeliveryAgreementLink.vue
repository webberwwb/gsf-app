<template>
  <p class="delivery-agreement-footnote">
    <button type="button" class="delivery-agreement-link" @click.stop="$emit('open')">
      查看配送协议
    </button>
  </p>
</template>

<script>
export default {
  name: 'DeliveryAgreementLink',
  emits: ['open']
}
</script>

<style scoped>
.delivery-agreement-footnote {
  margin: 6px 0 0;
  font-size: 0.75rem;
  line-height: 1.45;
  color: var(--md-on-surface-variant);
}

.delivery-agreement-link {
  display: inline-block;
  padding: 2px 0;
  border: none;
  background: none;
  color: var(--md-on-surface-variant);
  font-size: inherit;
  line-height: inherit;
  text-decoration: underline;
  text-underline-offset: 3px;
  cursor: pointer;
}
</style>
