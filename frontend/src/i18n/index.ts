import { createI18n } from 'vue-i18n'

import en from './locales/en'
import zhCN from './locales/zh-CN'

export const LOCALE_STORAGE_KEY = 'qz-admin-locale'
export type AppLocale = 'zh-CN' | 'en'

export const SUPPORTED_LOCALES: { code: AppLocale; label: string; short: string }[] = [
  { code: 'zh-CN', label: '中文', short: '中' },
  { code: 'en', label: 'English', short: 'EN' },
]

export function detectLocale(): AppLocale {
  if (typeof window === 'undefined') return 'zh-CN'
  const saved = window.localStorage.getItem(LOCALE_STORAGE_KEY)
  if (saved === 'en' || saved === 'zh-CN') return saved
  // Product default: Chinese (ignore browser language for first visit)
  return 'zh-CN'
}

export function setStoredLocale(locale: AppLocale) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(LOCALE_STORAGE_KEY, locale)
  document.documentElement.setAttribute('lang', locale === 'zh-CN' ? 'zh-CN' : 'en')
}

const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: detectLocale(),
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    en,
  },
})

if (typeof document !== 'undefined') {
  document.documentElement.setAttribute('lang', i18n.global.locale.value === 'zh-CN' ? 'zh-CN' : 'en')
}

export function tGlobal(key: string, params?: Record<string, unknown>): string {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return i18n.global.t(key, params as any) as string
}

export function setLocale(locale: AppLocale) {
  i18n.global.locale.value = locale
  setStoredLocale(locale)
}

export default i18n
