const DAY_NAMES = ['日', '一', '二', '三', '四', '五', '六']

export function cronToHuman(expr) {
  if (!expr || typeof expr !== 'string') return ''
  const parts = expr.trim().split(/\s+/)
  if (parts.length !== 5) return expr

  const [minute, hour, dom, _month, dow] = parts
  const time = formatTime(minute, hour)

  if (minute === '*' && hour === '*' && dom === '*' && dow === '*') {
    return '每分钟'
  }

  if (hour === '*' && dom === '*' && dow === '*') {
    if (minute.startsWith('*/')) {
      const n = Number(minute.slice(2))
      return n > 0 ? `每 ${n} 分钟` : expr
    }
    return `每小时的第 ${minute} 分钟`
  }

  if (dom === '*' && dow === '*') {
    if (hour.startsWith('*/')) {
      const n = Number(hour.slice(2))
      return n > 0 ? `每 ${n} 小时` : expr
    }
    return time ? `每天 ${time}` : expr
  }

  if (dom === '*' && dow !== '*') {
    const dayDesc = parseDow(dow)
    if (!dayDesc) return time ? `Cron: ${expr}` : expr
    return time ? `${dayDesc} ${time}` : `${dayDesc}`
  }

  if (dow === '*' && dom !== '*') {
    const d = Number(dom)
    if (Number.isInteger(d) && d >= 1 && d <= 31) {
      return time ? `每月 ${d} 日 ${time}` : `每月 ${d} 日`
    }
  }

  return expr
}

function formatTime(minute, hour) {
  const m = Number(minute)
  const h = Number(hour)
  if (!Number.isInteger(m) || !Number.isInteger(h)) return ''
  if (m < 0 || m > 59 || h < 0 || h > 23) return ''
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
}

function parseDow(dow) {
  if (dow === '*') return null

  if (/^\d$/.test(dow)) {
    const d = Number(dow)
    if (d >= 0 && d <= 6) return `每周${DAY_NAMES[d]}`
    return null
  }

  if (/^\d-\d$/.test(dow)) {
    const [a, b] = dow.split('-').map(Number)
    if (a >= 0 && a <= 6 && b >= 0 && b <= 6) {
      if (a === 1 && b === 5) return '工作日（周一至周五）'
      return `每周${DAY_NAMES[a]}至周${DAY_NAMES[b]}`
    }
    return null
  }

  if (/^[\d,]+$/.test(dow)) {
    const days = dow.split(',').map(Number)
    if (days.every((d) => d >= 0 && d <= 6)) {
      return days.map((d) => `周${DAY_NAMES[d]}`).join('、')
    }
    return null
  }

  return null
}
