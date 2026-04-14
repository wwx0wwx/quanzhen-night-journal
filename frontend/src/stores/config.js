import { defineStore } from 'pinia'

import { api, unwrap } from '../api'

export const useConfigStore = defineStore('config', {
  state: () => ({
    items: {},
  }),
  actions: {
    async load() {
      this.items = await unwrap(api.get('/config'))
      return this.items
    },
    async save(items) {
      await unwrap(api.put('/config', { items }))
      return this.load()
    },
  },
})
