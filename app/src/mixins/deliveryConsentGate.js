export default {
  data() {
    return {
      showConsentModal: false,
      consentSaving: false,
      consentError: '',
      consentModalMode: 'agree',
      orderDeliveryConsented: false
    }
  },
  computed: {
    hasDeliveryConsent() {
      return this.orderDeliveryConsented
    },
    consentViewOnly() {
      return this.consentModalMode === 'view'
    }
  },
  methods: {
    seedConsentIfExistingDelivery() {
      if (this.deliveryMethod === 'delivery') {
        this.orderDeliveryConsented = true
      }
    },
    openDeliveryAgreement() {
      this.consentError = ''
      this.consentModalMode = 'view'
      this.showConsentModal = true
    },
    requestDelivery() {
      if (!this.orderDeliveryConsented) {
        this.consentError = ''
        this.consentModalMode = 'agree'
        this.showConsentModal = true
        return
      }
      this.applyDeliveryAfterGate()
    },
    acceptDeliveryConsent() {
      this.orderDeliveryConsented = true
      this.showConsentModal = false
      this.consentError = ''
      this.applyDeliveryAfterGate()
    },
    cancelDeliveryConsent() {
      this.showConsentModal = false
      this.consentError = ''
      if (this.consentModalMode === 'view') return
      this.stayPickupAfterGate()
    },
    onCardSetupClosed() {},
    onCardSavedForGate() {},
    enforceDeliveryEligibility() {
      if (this.showConsentModal) return
      if (this.deliveryMethod !== 'delivery') return
      if (this.orderDeliveryConsented) return
      this.stayPickupAfterGate()
    }
  }
}
