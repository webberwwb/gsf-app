import { ref } from 'vue'

const modalState = ref({
  show: false,
  type: 'info',
  title: '',
  message: '',
  confirmText: '确定',
  cancelText: '取消',
  showCancel: false,
  showClose: true,
  icon: true,
  closeOnOverlay: true,
  onConfirm: null,
  onCancel: null
})

export function useModal() {
  const showModal = (options) => {
    return new Promise((resolve) => {
      modalState.value = {
        show: true,
        type: options.type || 'info',
        title: options.title || '',
        message: options.message || '',
        confirmText: options.confirmText || '确定',
        cancelText: options.cancelText || '取消',
        showCancel: options.showCancel !== undefined ? options.showCancel : false,
        showClose: options.showClose !== undefined ? options.showClose : true,
        icon: options.icon !== undefined ? options.icon : true,
        closeOnOverlay: options.closeOnOverlay !== undefined ? options.closeOnOverlay : true,
        onConfirm: () => {
          modalState.value.show = false
          resolve(true)
        },
        onCancel: () => {
          modalState.value.show = false
          resolve(false)
        }
      }
    })
  }

  const alert = (message, options = {}) => {
    return showModal({
      type: options.type || 'info',
      title: options.title || '',
      message,
      confirmText: options.confirmText || '确定',
      showCancel: false,
      icon: options.icon,
      ...options
    })
  }

  const confirm = (message, options = {}) => {
    return showModal({
      type: 'confirm',
      title: options.title || '确认',
      message,
      confirmText: options.confirmText || '确定',
      cancelText: options.cancelText || '取消',
      showCancel: true,
      icon: options.icon,
      ...options
    })
  }

  const success = (message, options = {}) => {
    return showModal({
      type: 'success',
      title: options.title || '成功',
      message,
      confirmText: options.confirmText || '确定',
      showCancel: false,
      ...options
    })
  }

  const error = (message, options = {}) => {
    return showModal({
      type: 'error',
      title: options.title || '错误',
      message,
      confirmText: options.confirmText || '确定',
      showCancel: false,
      ...options
    })
  }

  const warning = (message, options = {}) => {
    return showModal({
      type: 'warning',
      title: options.title || '警告',
      message,
      confirmText: options.confirmText || '确定',
      showCancel: false,
      ...options
    })
  }

  const closeModal = () => {
    if (modalState.value.onCancel) {
      modalState.value.onCancel()
    }
    modalState.value.show = false
  }

  return {
    modalState,
    showModal,
    alert,
    confirm,
    success,
    error,
    warning,
    closeModal
  }
}

