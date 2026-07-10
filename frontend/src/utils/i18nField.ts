import { tGlobal } from '../i18n'

function asArray(help: string | string[] | undefined): string[] {
  if (!help) return []
  return Array.isArray(help) ? help : [help]
}

function tr(key: string, fallback?: string) {
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
