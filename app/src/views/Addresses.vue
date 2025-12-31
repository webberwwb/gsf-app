<template>
  <div class="addresses-page">
    <header class="page-header">
      <button @click="$router.back()" class="back-btn">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <div class="header-center">
        <h1>配送地址</h1>
      </div>
      <div class="header-spacer"></div>
    </header>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="addresses.length === 0" class="empty-state">
      <div class="empty-icon">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      </div>
      <h2>暂无地址</h2>
      <p>添加您的第一个配送地址</p>
      <button @click="openAddModal" class="add-first-btn">添加地址</button>
    </div>
    <div v-else class="addresses-list">
      <div v-for="address in addresses" :key="address.id" class="address-card" :class="{ 'default': address.is_default }">
        <div class="address-header">
          <div class="address-info">
            <span class="recipient-name">{{ address.recipient_name }}</span>
            <span class="recipient-phone">{{ address.phone }}</span>
            <span v-if="address.is_default" class="default-badge">默认</span>
          </div>
          <div class="address-actions">
            <button @click="editAddress(address)" class="edit-btn">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button @click="deleteAddress(address.id)" class="delete-btn">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
        <div class="address-details">
          <p class="address-line">{{ address.address_line1 }}</p>
          <p v-if="address.address_line2" class="address-line">{{ address.address_line2 }}</p>
          <p class="address-line">{{ address.city }}, {{ address.postal_code }}</p>
          <p v-if="address.delivery_instructions" class="delivery-instructions">
            <span class="instructions-label">配送说明：</span>{{ address.delivery_instructions }}
          </p>
        </div>
        <div v-if="!address.is_default" class="address-footer">
          <button @click="setDefaultAddress(address.id)" class="set-default-btn">设为默认</button>
        </div>
      </div>
    </div>

    <!-- Floating Add Button -->
    <button @click="openAddModal" class="floating-add-btn">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
      </svg>
    </button>

    <!-- Address Form Modal -->
    <AddressForm
      :show="showModal"
      :address="editingAddress"
      @close="closeModal"
      @saved="handleAddressSaved"
    />
  </div>
</template>

<script>
import apiClient from '../api/client'
import AddressForm from '../components/AddressForm.vue'
import { useModal } from '../composables/useModal'

export default {
  name: 'Addresses',
  components: {
    AddressForm
  },
  setup() {
    const { confirm, success, error } = useModal()
    return { confirm, success, error }
  },
  data() {
    return {
      loading: true,
      error: null,
      addresses: [],
      showModal: false,
      editingAddress: null
    }
  },
  mounted() {
    this.loadAddresses()
  },
  methods: {
    async loadAddresses() {
      this.loading = true
      this.error = null
      try {
        const response = await apiClient.get('/addresses')
        this.addresses = response.data.addresses || []
      } catch (error) {
        this.error = error.response?.data?.message || error.response?.data?.error || '加载地址失败'
        console.error('Failed to load addresses:', error)
      } finally {
        this.loading = false
      }
    },
    openAddModal() {
      this.editingAddress = null
      this.showModal = true
    },
    editAddress(address) {
      this.editingAddress = address
      this.showModal = true
    },
    closeModal() {
      this.showModal = false
      this.editingAddress = null
    },
    async handleAddressSaved() {
      await this.loadAddresses()
      this.closeModal()
    },
    async deleteAddress(addressId) {
      const confirmed = await this.confirm('确定要删除这个地址吗？', {
        type: 'warning'
      })
      if (!confirmed) {
        return
      }

      try {
        await apiClient.delete(`/addresses/${addressId}`)
        await this.success('地址已删除')
        await this.loadAddresses()
      } catch (error) {
        await this.error(error.response?.data?.message || error.response?.data?.error || '删除失败')
        console.error('Delete address error:', error)
      }
    },
    async setDefaultAddress(addressId) {
      try {
        await apiClient.post(`/addresses/${addressId}/set-default`)
        await this.success('默认地址已设置')
        await this.loadAddresses()
      } catch (error) {
        await this.error(error.response?.data?.message || error.response?.data?.error || '设置默认地址失败')
        console.error('Set default address error:', error)
      }
    }
  }
}
</script>

<style scoped>
.addresses-page {
  min-height: 100vh;
  background: var(--md-background);
  padding-bottom: calc(80px + env(safe-area-inset-bottom)); /* Space for bottom nav */
}

.page-header {
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-2);
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: calc(var(--md-spacing-lg) + env(safe-area-inset-top));
  padding-left: var(--md-spacing-md);
  padding-right: var(--md-spacing-md);
}

.back-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  padding: var(--md-spacing-xs);
  cursor: pointer;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--md-radius-sm);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
  width: 40px;
  height: 40px;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.back-btn svg {
  width: 24px;
  height: 24px;
  color: white;
}

.header-spacer {
  width: 40px;
  flex-shrink: 0;
}

.header-center {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--md-spacing-sm);
}

.header-logo {
  width: 32px;
  height: 32px;
  object-fit: contain;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.15));
}

.page-header h1 {
  font-size: var(--md-headline-size);
  color: white;
  font-weight: 500;
  text-align: center;
  letter-spacing: -0.5px;
  margin: 0;
}

.loading, .error {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--md-spacing-xl);
  text-align: center;
  min-height: 50vh;
}

.empty-icon {
  width: 80px;
  height: 80px;
  color: var(--md-on-surface-variant);
  opacity: 0.5;
  margin-bottom: var(--md-spacing-md);
}

.empty-icon svg {
  width: 100%;
  height: 100%;
}

.empty-state h2 {
  font-size: var(--md-title-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-sm);
}

.empty-state p {
  font-size: var(--md-body-size);
  color: var(--md-on-surface-variant);
  margin-bottom: var(--md-spacing-md);
}

.add-first-btn {
  padding: var(--md-spacing-md) var(--md-spacing-lg);
  background: var(--md-primary);
  color: white;
  border: none;
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--md-elevation-2);
}

.add-first-btn:hover {
  background: #FF7F00;
  box-shadow: var(--md-elevation-3);
  transform: translateY(-2px);
}

.addresses-list {
  padding: var(--md-spacing-md);
  max-width: 600px;
  margin: 0 auto;
}

.address-card {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-md);
  margin-bottom: var(--md-spacing-md);
  box-shadow: var(--md-elevation-1);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid transparent;
}

.address-card:hover {
  box-shadow: var(--md-elevation-2);
}

.address-card.default {
  border-color: var(--md-primary);
  background: linear-gradient(to bottom, rgba(255, 140, 0, 0.05), var(--md-surface));
}

.address-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--md-spacing-sm);
  padding-bottom: var(--md-spacing-sm);
  border-bottom: 1px solid var(--md-outline-variant);
}

.address-info {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--md-spacing-sm);
  flex: 1;
}

.recipient-name {
  font-size: var(--md-body-size);
  font-weight: 600;
  color: var(--md-on-surface);
}

.recipient-phone {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.default-badge {
  padding: 0.125rem 0.5rem;
  background: var(--md-primary);
  color: white;
  border-radius: var(--md-radius-xl);
  font-size: var(--md-label-size);
  font-weight: 500;
}

.address-actions {
  display: flex;
  gap: var(--md-spacing-xs);
}

.edit-btn, .delete-btn {
  background: transparent;
  border: none;
  padding: var(--md-spacing-xs);
  cursor: pointer;
  color: var(--md-on-surface-variant);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--md-radius-sm);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  width: 32px;
  height: 32px;
}

.edit-btn:hover {
  background: var(--md-primary-variant);
  color: var(--md-primary);
}

.delete-btn:hover {
  background: #FFEBEE;
  color: #C62828;
}

.edit-btn svg, .delete-btn svg {
  width: 18px;
  height: 18px;
}

.address-details {
  margin-bottom: var(--md-spacing-sm);
}

.address-line {
  font-size: var(--md-body-size);
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-xs);
  line-height: 1.5;
}

.delivery-instructions {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin-top: var(--md-spacing-sm);
  padding-top: var(--md-spacing-sm);
  border-top: 1px solid var(--md-outline-variant);
}

.instructions-label {
  font-weight: 500;
  color: var(--md-on-surface);
}

.address-footer {
  padding-top: var(--md-spacing-sm);
  border-top: 1px solid var(--md-outline-variant);
}

.set-default-btn {
  padding: var(--md-spacing-xs) var(--md-spacing-md);
  background: transparent;
  color: var(--md-primary);
  border: 1px solid var(--md-primary);
  border-radius: var(--md-radius-md);
  font-size: var(--md-label-size);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.set-default-btn:hover {
  background: var(--md-primary);
  color: white;
}

.floating-add-btn {
  position: fixed;
  bottom: calc(80px + env(safe-area-inset-bottom) + var(--md-spacing-md));
  right: var(--md-spacing-md);
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--md-primary);
  color: white;
  border: none;
  box-shadow: var(--md-elevation-4);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 99;
}

.floating-add-btn:hover {
  background: #FF7F00;
  box-shadow: var(--md-elevation-6);
  transform: scale(1.1);
}

.floating-add-btn:active {
  transform: scale(0.95);
}

.floating-add-btn svg {
  width: 24px;
  height: 24px;
}
</style>

