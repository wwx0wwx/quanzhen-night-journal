import { tGlobal } from '../i18n'

const CODE_KEYS: Record<number, string> = {
  1001: 'errors.codes.1001',
  1002: 'errors.codes.1002',
  2001: 'errors.codes.2001',
  3001: 'errors.codes.3001',
  3003: 'errors.codes.3003',
  4001: 'errors.codes.4001',
}

const RAW_MESSAGE_KEYS: Record<string, string> = {
  not_authenticated: 'errors.raw.not_authenticated',
  token_invalid: 'errors.raw.token_invalid',
  user_not_found: 'errors.raw.user_not_found',
  request_failed: 'errors.raw.request_failed',
  llm_not_configured: 'errors.raw.llm_not_configured',
  no_active_persona: 'errors.raw.no_active_persona',
}

const ERROR_CODE_KEYS: Record<string, string> = {
  container_restart: 'errors.labels.container_restart',
  invalid_model_output: 'errors.labels.invalid_model_output',
  qa_circuit_open: 'errors.labels.qa_circuit_open',
  budget_exhausted: 'errors.labels.budget_exhausted',
  publish_failed: 'errors.labels.publish_failed',
  task_aborted: 'errors.labels.task_aborted',
  llm_request_failed: 'errors.labels.llm_request_failed',
  llm_timeout: 'errors.labels.llm_timeout',
  embedding_failed: 'errors.labels.embedding_failed',
}

export function describeErrorCode(code?: string | null): string {
  if (!code) return ''
  const key = ERROR_CODE_KEYS[code]
  return key ? tGlobal(key) : code
}

type ErrorLike = {
  code?: number | string
  message?: string
  response?: { data?: { code?: number; message?: string } }
  responseData?: { code?: number; message?: string }
}

export function describeError(error: unknown, fallback?: string): string {
  const fb = fallback || tGlobal('errors.fallback')
  const err = (error || {}) as ErrorLike
  const code = err?.response?.data?.code ?? err?.responseData?.code ?? err?.code
  if (typeof code === 'number' && CODE_KEYS[code]) {
    return tGlobal(CODE_KEYS[code])
  }

  const message = err?.response?.data?.message || err?.responseData?.message || err?.message || ''
  if (!message) {
    return fb
  }
  if (RAW_MESSAGE_KEYS[message]) {
    return tGlobal(RAW_MESSAGE_KEYS[message])
  }
  if (/database is locked/i.test(message)) {
    return tGlobal('errors.dbLocked')
  }
  if (/timeout/i.test(message)) {
    return tGlobal('errors.timeout')
  }
  if (/network error/i.test(message)) {
    return tGlobal('errors.network')
  }
  if (/^llm_/.test(message)) {
    return tGlobal('errors.llmGeneric')
  }
  if (/[一-龥]/.test(message)) {
    return message
  }
  return fb
}
