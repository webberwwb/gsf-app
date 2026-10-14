import { getBackendOrigin } from '../config/api'

export function recipeShareUrl(recipeId) {
  return `${getBackendOrigin()}/share/recipes/${recipeId}`
}

export async function shareRecipe(recipe) {
  const url = recipeShareUrl(recipe.id)
  const payload = { title: recipe.title, text: recipe.title, url }
  if (typeof navigator !== 'undefined' && navigator.share) {
    await navigator.share(payload)
    return 'shared'
  }
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(url)
    return 'copied'
  }
  return url
}
