import i18n, { tGlobal } from '../i18n'

function asArray(help: string | string[] | undefined): string[] {
  if (!help) return []
  return Array.isArray(help) ? help : [help]
}

function flatSettingsValue(key: string): string | undefined {
  const prefix = 'settingsFields.'
  if (!key.startsWith(prefix)) return undefined
  const rest = key.slice(prefix.length)
  const parts = rest.split('.')
  for (let split = parts.length - 1; split >= 1; split -= 1) {
    const fieldKey = parts.slice(0, split).join('.')
    const propPath = parts.slice(split)
    const messages = i18n.global.getLocaleMessage(i18n.global.locale.value) as Record<string, unknown>
    let value = (messages.settingsFields as Record<string, unknown> | undefined)?.[fieldKey]
    for (const prop of propPath) {
      if (!value || typeof value !== 'object') return undefined
      value = (value as Record<string, unknown>)[prop]
    }
    if (typeof value === 'string') return value
  }
  return undefined
}

function tr(key: string, fallback?: string) {
  const flat = flatSettingsValue(key)
  if (flat) return flat
  if (!i18n.global.te(key)) return fallback
  const value = tGlobal(key)
  return value !== key ? value : fallback
}

/** Translate a settings field label/help/placeholder by config key, with Chinese fallback. */
export function translateField(field: {
  key: string
  label?: string
  help?: string | string[]
  placeholder?: string
  options?: Array<{ value: string; label: string }>
}) {
  const base = `settingsFields.${field.key}`
  const helpArr = asArray(field.help)
  let help: string | string[] | undefined = field.help
  if (helpArr.length === 1) {
    help = tr(`${base}.help`, helpArr[0])
  } else if (helpArr.length > 1) {
    help = helpArr.map((text, index) => tr(`${base}.help${index}`, text) || text)
  }

  const options = (field.options || []).map((opt) => ({
    ...opt,
    label: tr(`${base}.opt.${opt.value}`, opt.label) || opt.label,
  }))

  return {
    ...field,
    label: tr(`${base}.label`, field.label) || field.label,
    placeholder: tr(`${base}.placeholder`, field.placeholder) || field.placeholder,
    help,
    options: options.length ? options : field.options,
  }
}
