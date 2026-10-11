import apiClient from '../api/client'

export const ORDER_UPDATE_TIMEOUT_MS = 10000

export function orderUpdateErrorMessage(error) {
  if (isOrderUpdateTimeout(error)) {
    return '更新超时。已填写的重量还在，请再点一次「更新订单」。'
  }
  const serverMessage = error?.response?.data?.message || error?.response?.data?.error
  if (serverMessage) return `${serverMessage} 已填写的重量还在，请再点一次「更新订单」。`
  return '更新失败。已填写的重量还在，请再点一次「更新订单」。'
}

export function isOrderUpdateTimeout(error) {
  return error?.code === 'ECONNABORTED'
    || error?.code === 'ERR_CANCELED'
    || error?.name === 'CanceledError'
    || error?.message === 'ORDER_UPDATE_TIMEOUT'
}

export function putOrderWeights(orderId, items) {
  return putWithTimeout(`/admin/orders/${orderId}/update-weights`, { items })
}

export function putOrderUpdate(orderId, updateData) {
  return putWithTimeout(`/admin/orders/${orderId}/update`, updateData)
}

function putWithTimeout(url, body) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), ORDER_UPDATE_TIMEOUT_MS)
  const request = apiClient.put(url, body, {
    signal: controller.signal,
    timeout: ORDER_UPDATE_TIMEOUT_MS,
  })
  return withTimeout(request, ORDER_UPDATE_TIMEOUT_MS).finally(() => clearTimeout(timer))
}

function withTimeout(promise, ms) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(Object.assign(new Error('ORDER_UPDATE_TIMEOUT'), { code: 'ECONNABORTED' }))
    }, ms)
    promise.then(
      (value) => {
        clearTimeout(timer)
        resolve(value)
      },
      (error) => {
        clearTimeout(timer)
        reject(error)
      },
    )
  })
}
