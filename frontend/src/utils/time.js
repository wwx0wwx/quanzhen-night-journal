const ABSOLUTE_FORMATTER = new Intl.DateTimeFormat('zh-CN', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
})

const RELATIVE_FORMATTER = new Intl.RelativeTimeFormat('zh-CN', { numeric: 'auto' })

const RELATIVE_UNITS = [
  ['day', 24 * 60 * 60 * 1000],
  ['hour', 60 * 60 * 1000],
  ['minute', 60 * 1000],
]

function parseDate(value) {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

export function formatDateTime(value) {
  const date = parseDate(value)
  return date ? ABSOLUTE_FORMATTER.format(date) : '-'
}

export function formatRelativeTime(value, now = Date.now()) {
  const date = parseDate(value)
  if (!date) return ''

  const diff = date.getTime() - now
  for (const [unit, size] of RELATIVE_UNITS) {
    if (Math.abs(diff) >= size || unit === 'minute') {
      return RELATIVE_FORMATTER.format(Math.round(diff / size), unit)
    }
  }

  return '刚刚'
}

export function formatDateTimeWithRelative(value) {
  const absolute = formatDateTime(value)
  if (absolute === '-') return absolute
  const relative = formatRelativeTime(value)
  return relative ? `${absolute} · ${relative}` : absolute
}

export function formatDurationMs(value) {
  if (value == null || value === '') return '-'
  const ms = Number(value)
  if (Number.isNaN(ms)) return '-'
  if (ms < 1000) return `${ms} ms`
  const seconds = (ms / 1000).toFixed(ms >= 10_000 ? 0 : 1)
  return `${seconds} s`
}
