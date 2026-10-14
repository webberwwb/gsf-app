<template>
  <RecipeDetailPanel :recipe-id="$route.params.id" />
</template>

<script>
import RecipeDetailPanel from '../components/RecipeDetailPanel.vue'

export default {
  name: 'RecipeDetail',
  components: { RecipeDetailPanel }
}
</script>
