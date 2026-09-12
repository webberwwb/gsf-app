export default {
  data() {
    return {
      showConsentModal: false,
      consentSaving: false,
      consentError: '',
      consentModalMode: 'agree',
      deliveryGatePending: false,
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
      if (!this.hasCardOnFile) {
        this.deliveryGatePending = true
        this.startCardSetup()
        return
      }
      this.applyDeliveryAfterGate()
    },
    acceptDeliveryConsent() {
      this.orderDeliveryConsented = true
      this.showConsentModal = false
      this.consentError = ''
      if (!this.hasCardOnFile) {
        this.deliveryGatePending = true
        this.startCardSetup()
        return
      }
      this.applyDeliveryAfterGate()
    },
    cancelDeliveryConsent() {
      this.showConsentModal = false
      this.consentError = ''
      if (this.consentModalMode === 'view') return
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
      if (this.orderDeliveryConsented && this.hasCardOnFile) {
        this.applyDeliveryAfterGate()
      } else {
        this.stayPickupAfterGate()
      }
    },
    enforceDeliveryEligibility() {
      if (this.deliveryGatePending || this.showConsentModal) return
      if (this.deliveryMethod !== 'delivery') return
      if (this.orderDeliveryConsented && this.hasCardOnFile) return
      this.stayPickupAfterGate()
    }
  }
}
