import { tGlobal } from '../i18n'

const DOW_MAP = { sun: 0, mon: 1, tue: 2, wed: 3, thu: 4, fri: 5, sat: 6 }
const DOW_REVERSE = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']

export function getFreqLabels() {
  return [
    { value: 'daily', label: tGlobal('cron.daily') },
    { value: 'mon', label: tGlobal('cron.mon') },
    { value: 'tue', label: tGlobal('cron.tue') },
    { value: 'wed', label: tGlobal('cron.wed') },
    { value: 'thu', label: tGlobal('cron.thu') },
    { value: 'fri', label: tGlobal('cron.fri') },
    { value: 'sat', label: tGlobal('cron.sat') },
    { value: 'sun', label: tGlobal('cron.sun') },
    { value: 'monthly-1', label: tGlobal('cron.monthly1') },
    { value: 'monthly-15', label: tGlobal('cron.monthly15') },
  ]
}

/** @deprecated use getFreqLabels() for i18n-aware labels */
export const FREQ_LABELS = [
  { value: 'daily', label: '每天' },
  { value: 'mon', label: '每周一' },
  { value: 'tue', label: '每周二' },
  { value: 'wed', label: '每周三' },
  { value: 'thu', label: '每周四' },
  { value: 'fri', label: '每周五' },
  { value: 'sat', label: '每周六' },
  { value: 'sun', label: '每周日' },
  { value: 'monthly-1', label: '每月 1 日' },
  { value: 'monthly-15', label: '每月 15 日' },
]

export function parseCron(expr: string | null | undefined) {
  if (!expr || typeof expr !== 'string') return null
  const parts = expr.trim().split(/\s+/)
  if (parts.length !== 5) return null

  const [minute, hour, dom, month, dow] = parts
  const m = Number(minute)
  const h = Number(hour)
  if (!Number.isInteger(m) || !Number.isInteger(h)) return null
  if (m < 0 || m > 59 || h < 0 || h > 23) return null
  if (month !== '*') return null

  const time = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`

  if (dom === '*' && dow === '*') return { frequency: 'daily', time }
  if (dom === '*' && /^\d$/.test(dow)) {
    const d = Number(dow)
    if (d >= 0 && d <= 6) return { frequency: DOW_REVERSE[d], time }
  }
  if (dow === '*' && /^\d+$/.test(dom)) {
    const d = Number(dom)
    if (d === 1 || d === 15) return { frequency: `monthly-${d}`, time }
  }

  return null
}

export function buildCron(frequency: string, time: string) {
  const [hStr, mStr] = (time || '00:00').split(':')
  const h = Number(hStr) || 0
  const m = Number(mStr) || 0

  if (frequency === 'daily') return `${m} ${h} * * *`
  if (frequency in DOW_MAP) return `${m} ${h} * * ${DOW_MAP[frequency as keyof typeof DOW_MAP]}`
  if (frequency.startsWith('monthly-')) {
    const dom = frequency.split('-')[1]
    return `${m} ${h} ${dom} * *`
  }
  return `${m} ${h} * * *`
}

function formatTime(minute: string, hour: string) {
  const h = Number(hour)
  const m = Number(minute)
  if (!Number.isInteger(h) || !Number.isInteger(m)) return `${hour}:${minute}`
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
}

export function cronToHuman(expr: string | null | undefined) {
  if (!expr || typeof expr !== 'string') return ''
  const parts = expr.trim().split(/\s+/)
  if (parts.length !== 5) return expr

  const [minute, hour, dom, , dow] = parts
  const time = formatTime(minute, hour)
  const parsed = parseCron(expr)
  if (parsed) {
    const label = getFreqLabels().find((item) => item.value === parsed.frequency)?.label || parsed.frequency
    return `${label} ${parsed.time}`
  }

  if (minute === '*' && hour === '*' && dom === '*' && dow === '*') {
    return expr
  }

  return `${time} (${expr})`
}
