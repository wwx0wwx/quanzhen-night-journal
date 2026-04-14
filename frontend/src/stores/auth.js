import { defineStore } from 'pinia'

import { api, unwrap } from '../api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    loaded: false,
    isLoggedIn: false,
    isInitialized: false,
    username: null,
  }),
  actions: {
    async refresh() {
      const data = await unwrap(api.get('/auth/status'))
      this.loaded = true
      this.isLoggedIn = data.is_logged_in
      this.isInitialized = Boolean(data.system_initialized ?? data.is_initialized)
      this.username = data.username
      return data
    },
    async login(payload) {
      const data = await unwrap(api.post('/auth/login', payload))
      this.loaded = true
      this.isLoggedIn = true
      this.isInitialized = Boolean(data.system_initialized ?? data.is_initialized)
      this.username = data.username
      return data
    },
    async logout() {
      await unwrap(api.post('/auth/logout'))
      this.loaded = true
      this.isLoggedIn = false
      this.username = null
    },
  },
})
