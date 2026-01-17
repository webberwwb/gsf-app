import { reactive } from 'vue'

const state = reactive({
  orders: [],
  currentOrder: null,
  groupDeal: null,
  loading: false,
  error: null
})

export function useOrdersStore() {
  const updateOrder = (updatedOrder) => {
    // Update order in the orders list
    const index = state.orders.findIndex(o => o.id === updatedOrder.id)
    if (index >= 0) {
      // Preserve reactivity by updating properties individually
      Object.assign(state.orders[index], updatedOrder)
    }
    
    // Update current order if it matches
    if (state.currentOrder && state.currentOrder.id === updatedOrder.id) {
      Object.assign(state.currentOrder, updatedOrder)
    }
  }

  const updateOrderInList = (orderId, updates) => {
    const index = state.orders.findIndex(o => o.id === orderId)
    if (index >= 0) {
      Object.assign(state.orders[index], updates)
    }
    
    if (state.currentOrder && state.currentOrder.id === orderId) {
      Object.assign(state.currentOrder, updates)
    }
  }

  const setOrders = (orders) => {
    state.orders = orders
  }

  const setCurrentOrder = (order) => {
    state.currentOrder = order
  }

  const setGroupDeal = (groupDeal) => {
    state.groupDeal = groupDeal
  }

  const setLoading = (loading) => {
    state.loading = loading
  }

  const setError = (error) => {
    state.error = error
  }

  return {
    state,
    updateOrder,
    updateOrderInList,
    setOrders,
    setCurrentOrder,
    setGroupDeal,
    setLoading,
    setError
  }
}
