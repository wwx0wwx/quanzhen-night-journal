import { defineStore } from 'pinia'

export type ToastKind = 'success' | 'error' | 'warning' | 'info'

export type ToastItem = {
  id: number
  kind: ToastKind
  message: string
  ttl: number
}

let seq = 1

export const useToastStore = defineStore('toast', {
  state: () => ({
    items: [] as ToastItem[],
  }),
  actions: {
    push(message: string, kind: ToastKind = 'info', ttl = 3200) {
      const id = seq++
      this.items.push({ id, kind, message, ttl })
      window.setTimeout(() => this.dismiss(id), ttl)
      return id
    },
    success(message: string, ttl?: number) {
      return this.push(message, 'success', ttl)
    },
    error(message: string, ttl?: number) {
      return this.push(message, 'error', ttl ?? 4500)
    },
    warning(message: string, ttl?: number) {
      return this.push(message, 'warning', ttl)
    },
    info(message: string, ttl?: number) {
      return this.push(message, 'info', ttl)
    },
    dismiss(id: number) {
      this.items = this.items.filter((item) => item.id !== id)
    },
    clear() {
      this.items = []
    },
  },
})
