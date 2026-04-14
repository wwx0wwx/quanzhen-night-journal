import { defineStore } from 'pinia'

import { api, unwrap } from '../api'

export const usePersonaStore = defineStore('persona', {
  state: () => ({
    items: [],
  }),
  actions: {
    async load() {
      this.items = await unwrap(api.get('/personas'))
      return this.items
    },
    async remove(id) {
      await unwrap(api.delete(`/personas/${id}`))
      this.items = this.items.filter((item) => item.id !== id)
      return this.items
    },
  },
})
