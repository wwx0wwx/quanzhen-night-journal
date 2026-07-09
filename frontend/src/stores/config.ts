import { defineStore } from 'pinia'

import { api, unwrap } from '../api'

export const useConfigStore = defineStore('config', {
  state: () => ({
    items: {} as Record<string, unknown>,
  }),
  actions: {
    async load() {
      this.items = (await unwrap(api.get('/config'))) as Record<string, unknown>
      return this.items
    },
    async save(items: Record<string, unknown>) {
      await unwrap(api.put('/config', { items }))
      return this.load()
    },
  },
})
