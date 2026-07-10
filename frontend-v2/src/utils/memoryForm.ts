export const MEMORY_LEVEL_OPTIONS = [
  { value: 'L0', label: 'L0 核心' },
  { value: 'L1', label: 'L1 阶段' },
  { value: 'L2', label: 'L2 近期' },
  { value: 'L3', label: 'L3 碎片' },
]

export function levelLabel(level) {
  return MEMORY_LEVEL_OPTIONS.find((item) => item.value === level)?.label || level || '-'
}

export function reviewStatusLabel(status) {
  if (status === 'reviewed') return '已复核'
  if (status === 'promoted') return '已提升'
  if (status === 'unreviewed') return '未复核'
  return status || '-'
}

export function parseTags(text) {
  return String(text || '')
    .split(/[,，\s]+/)
    .map((item) => item.trim())
    .filter(Boolean)
}

export function normalizeTags(tags) {
  if (Array.isArray(tags)) return tags
  return parseTags(tags)
}

export function formatScore(value) {
  if (value == null || value === '') return '-'
  const num = Number(value)
  if (Number.isNaN(num)) return String(value)
  return num.toFixed(3)
}

export function createEmptyMemoryForm(personaId = 1) {
  return {
    persona_id: personaId,
    level: 'L2',
    content: '',
    summary: '',
    tags: [],
    source: 'hand_written',
    weight: 1,
    review_status: 'unreviewed',
    decay_strategy: 'standard',
    is_core: false,
  }
}
