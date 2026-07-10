import { reactive } from 'vue'

type ConfirmOptions = {
  title?: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  danger?: boolean
}

type ConfirmState = {
  open: boolean
  title: string
  message: string
  confirmLabel: string
  cancelLabel: string
  danger: boolean
  resolve: ((ok: boolean) => void) | null
}

const state = reactive<ConfirmState>({
  open: false,
  title: '',
  message: '',
  confirmLabel: '',
  cancelLabel: '',
  danger: false,
  resolve: null,
})

export function useConfirmState() {
  return state
}

export function confirmAction(options: ConfirmOptions): Promise<boolean> {
  return new Promise((resolve) => {
    if (state.open && state.resolve) {
      state.resolve(false)
    }
    state.open = true
    state.title = options.title || ''
    state.message = options.message
    state.confirmLabel = options.confirmLabel || ''
    state.cancelLabel = options.cancelLabel || ''
    state.danger = Boolean(options.danger)
    state.resolve = resolve
  })
}

export function resolveConfirm(ok: boolean) {
  const fn = state.resolve
  state.open = false
  state.resolve = null
  fn?.(ok)
}
