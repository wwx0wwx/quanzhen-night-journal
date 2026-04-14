const FIRST_LOGIN_KEY = 'qz_admin_seen_settings'

function canUseStorage() {
  return typeof window !== 'undefined' && Boolean(window.localStorage)
}

export function shouldOpenSettingsAfterLogin() {
  if (!canUseStorage()) return false
  return window.localStorage.getItem(FIRST_LOGIN_KEY) !== '1'
}

export function markSettingsAsSeen() {
  if (!canUseStorage()) return
  window.localStorage.setItem(FIRST_LOGIN_KEY, '1')
}

export function getPostLoginRoute(isInitialized) {
  if (!isInitialized) return '/admin/setup'
  if (shouldOpenSettingsAfterLogin()) {
    markSettingsAsSeen()
    return '/admin/settings'
  }
  return '/admin/'
}
