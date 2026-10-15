import { defineStore } from 'pinia'
import apiClient from '../api/client'

export const useFeatureStore = defineStore('features', {
  state: () => ({
    flags: {},
    loaded: false,
    pending: null,
    generation: 0
  }),

  actions: {
    isEnabled(name) {
      return this.loaded && !!this.flags[name]
    },

    load() {
      if (this.pending) return this.pending
      const generation = this.generation
      this.pending = apiClient.get('/features')
        .then((response) => {
          if (generation !== this.generation) return
          this.flags = response.data || {}
        })
        .catch(() => {
          if (generation !== this.generation) return
          this.flags = {}
        })
        .finally(() => {
          if (generation === this.generation) {
            this.loaded = true
            this.pending = null
          }
        })
      return this.pending
    },

    reload() {
      this.generation += 1
      this.pending = null
      this.loaded = false
      this.flags = {}
      return this.load()
    },

    async whenReady() {
      while (!this.loaded) {
        await (this.pending || this.load())
      }
    }
  }
})
