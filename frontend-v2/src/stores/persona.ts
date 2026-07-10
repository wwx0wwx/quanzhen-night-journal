import { defineStore } from 'pinia'

import { api, unwrap } from '../api'

export type PersonaSummary = {
  id: number
  name?: string
  [key: string]: unknown
}

export const usePersonaStore = defineStore('persona', {
  state: () => ({
    items: [] as PersonaSummary[],
  }),
  actions: {
    async load() {
      this.items = (await unwrap(api.get('/personas'))) as PersonaSummary[]
      return this.items
    },
    async remove(id: number) {
      await unwrap(api.delete(`/personas/${id}`))
      this.items = this.items.filter((item) => item.id !== id)
      return this.items
    },
  },
})
