import { reactive } from 'vue'

const state = reactive({
  title: null,
  onBack: null
})

export function usePageHeader() {
  const setTitle = (title) => {
    state.title = title || null
  }

  const setBackHandler = (handler) => {
    state.onBack = typeof handler === 'function' ? handler : null
  }

  const reset = () => {
    state.title = null
    state.onBack = null
  }

  return {
    state,
    setTitle,
    setBackHandler,
    reset
  }
}
