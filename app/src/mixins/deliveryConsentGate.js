import apiClient from '../api/client'
import { hasDeliveryConsent } from '../utils/deliveryConsent'

export default {
  data() {
    return {
      showConsentModal: false,
      consentSaving: false,
      consentError: '',
      deliveryGatePending: false
    }
  },
  computed: {
    hasDeliveryConsent() {
      return hasDeliveryConsent(this.currentUser)
    }
  },
  methods: {
    async requestDelivery() {
      if (!this.hasDeliveryConsent) {
        this.consentError = ''
        this.showConsentModal = true
        return
      }
      if (!this.hasCardOnFile) {
        this.deliveryGatePending = true
        this.startCardSetup()
        return
      }
      this.applyDeliveryAfterGate()
    },
    async acceptDeliveryConsent() {
      this.consentSaving = true
      this.consentError = ''
      try {
        const { data } = await apiClient.post('/auth/me/delivery-consent')
        if (data.user) {
          this.authStore.setUser(data.user)
        }
        this.showConsentModal = false
        if (!this.hasCardOnFile) {
          this.deliveryGatePending = true
          this.startCardSetup()
          return
        }
        this.applyDeliveryAfterGate()
      } catch (e) {
        this.consentError = e.response?.data?.error || e.response?.data?.message || '提交失败，请重试'
      } finally {
        this.consentSaving = false
      }
    },
    cancelDeliveryConsent() {
      this.showConsentModal = false
      this.consentError = ''
      this.stayPickupAfterGate()
    },
    onCardSetupClosed() {
      if (this.deliveryGatePending && !this.hasCardOnFile) {
        this.deliveryGatePending = false
        this.stayPickupAfterGate()
      }
    },
    onCardSavedForGate() {
      if (!this.deliveryGatePending) return
      this.deliveryGatePending = false
      if (this.hasDeliveryConsent && this.hasCardOnFile) {
        this.applyDeliveryAfterGate()
      } else {
        this.stayPickupAfterGate()
      }
    },
    enforceDeliveryEligibility() {
      if (this.deliveryGatePending || this.showConsentModal) return
      if (this.deliveryMethod !== 'delivery') return
      if (this.hasDeliveryConsent && this.hasCardOnFile) return
      this.stayPickupAfterGate()
    }
  }
}
