import { defineStore } from 'pinia'

import { api, unwrap } from '../api'

export type AuthStatus = {
  is_logged_in: boolean
  system_initialized?: boolean
  is_initialized?: boolean
  username?: string | null
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    loaded: false,
    isLoggedIn: false,
    isInitialized: false,
    username: null as string | null,
  }),
  actions: {
    async refresh() {
      const data = await unwrap<AuthStatus>(api.get('/auth/status'))
      this.loaded = true
      this.isLoggedIn = data.is_logged_in
      this.isInitialized = Boolean(data.system_initialized ?? data.is_initialized)
      this.username = data.username ?? null
      return data
    },
    async login(payload: { username: string; password: string }) {
      const data = await unwrap<AuthStatus>(api.post('/auth/login', payload))
      this.loaded = true
      this.isLoggedIn = true
      this.isInitialized = Boolean(data.system_initialized ?? data.is_initialized)
      this.username = data.username ?? null
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
