<template>
  <div v-if="show" class="consent-overlay" @click.self="onCancel">
    <div class="consent-sheet" role="dialog" aria-labelledby="consent-title" aria-modal="true">
      <div class="consent-header">
        <h3 id="consent-title">{{ title }}</h3>
        <button type="button" class="consent-close" aria-label="关闭" @click="onCancel">×</button>
      </div>

      <div class="consent-body" ref="bodyEl">
        <p class="consent-intro">{{ intro }}</p>
        <section v-for="section in sections" :key="section.title" class="consent-section">
          <h4>{{ section.title }}</h4>
          <p v-for="(para, idx) in section.paragraphs" :key="'p-' + idx">{{ para }}</p>
          <ul v-if="section.bullets?.length">
            <li v-for="(item, idx) in section.bullets" :key="'b-' + idx">{{ item }}</li>
          </ul>
          <p v-for="(para, idx) in (section.afterBullets || [])" :key="'a-' + idx">{{ para }}</p>
        </section>
        <p class="consent-closing">{{ closing }}</p>
      </div>

      <div class="consent-footer">
        <label class="consent-check">
          <input v-model="agreed" type="checkbox" />
          <span>{{ checkboxLabel }}</span>
        </label>
        <p v-if="error" class="consent-error">{{ error }}</p>
        <div class="consent-actions">
          <button type="button" class="consent-btn consent-btn-cancel" :disabled="saving" @click="onCancel">
            取消
          </button>
          <button
            type="button"
            class="consent-btn consent-btn-confirm"
            :disabled="!agreed || saving"
            @click="$emit('accept')"
          >
            {{ saving ? '提交中...' : '同意并继续' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {
  DELIVERY_CONSENT_TITLE,
  DELIVERY_CONSENT_INTRO,
  DELIVERY_CONSENT_SECTIONS,
  DELIVERY_CONSENT_CLOSING,
  DELIVERY_CONSENT_CHECKBOX
} from '../utils/deliveryConsent'

export default {
  name: 'DeliveryConsentModal',
  props: {
    show: { type: Boolean, default: false },
    saving: { type: Boolean, default: false },
    error: { type: String, default: '' }
  },
  emits: ['accept', 'cancel'],
  data() {
    return {
      agreed: false,
      title: DELIVERY_CONSENT_TITLE,
      intro: DELIVERY_CONSENT_INTRO,
      sections: DELIVERY_CONSENT_SECTIONS,
      closing: DELIVERY_CONSENT_CLOSING,
      checkboxLabel: DELIVERY_CONSENT_CHECKBOX
    }
  },
  watch: {
    show(open) {
      if (open) {
        this.agreed = false
        this.$nextTick(() => {
          if (this.$refs.bodyEl) this.$refs.bodyEl.scrollTop = 0
        })
      }
    }
  },
  methods: {
    onCancel() {
      if (this.saving) return
      this.$emit('cancel')
    }
  }
}
</script>

<style scoped>
.consent-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 1300;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.consent-sheet {
  width: 100%;
  max-width: 480px;
  max-height: min(92vh, 780px);
  background: var(--md-surface);
  border-radius: var(--md-radius-lg) var(--md-radius-lg) 0 0;
  box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.consent-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 16px 12px;
  border-bottom: 1px solid var(--md-surface-variant);
  flex-shrink: 0;
}

.consent-header h3 {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--md-on-surface);
}

.consent-close {
  border: none;
  background: transparent;
  font-size: 1.6rem;
  line-height: 1;
  color: var(--md-on-surface-variant);
  padding: 0 4px;
}

.consent-body {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding: 16px;
  font-size: 0.875rem;
  line-height: 1.65;
  color: var(--md-on-surface);
}

.consent-intro,
.consent-closing {
  margin: 0 0 16px;
  color: var(--md-on-surface-variant);
}

.consent-section {
  margin-bottom: 18px;
}

.consent-section h4 {
  margin: 0 0 8px;
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--md-primary);
}

.consent-section p {
  margin: 0 0 8px;
}

.consent-section ul {
  margin: 0 0 8px;
  padding-left: 1.15rem;
}

.consent-section li {
  margin-bottom: 4px;
}

.consent-footer {
  flex-shrink: 0;
  padding: 12px 16px calc(12px + env(safe-area-inset-bottom));
  border-top: 1px solid var(--md-surface-variant);
  background: var(--md-surface);
}

.consent-check {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 0.8125rem;
  line-height: 1.5;
  color: var(--md-on-surface);
}

.consent-check input {
  margin-top: 3px;
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  accent-color: var(--md-primary);
}

.consent-error {
  margin: 8px 0 0;
  font-size: 0.8125rem;
  color: #c62828;
}

.consent-actions {
  display: flex;
  gap: 10px;
  margin-top: 12px;
}

.consent-btn {
  flex: 1;
  padding: 12px 16px;
  border: none;
  border-radius: var(--md-radius-md);
  font-size: 0.9375rem;
  font-weight: 600;
}

.consent-btn-cancel {
  background: var(--md-surface-variant);
  color: var(--md-on-surface);
}

.consent-btn-confirm {
  background: var(--md-primary);
  color: #fff;
}

.consent-btn-confirm:disabled {
  opacity: 0.45;
}
</style>
