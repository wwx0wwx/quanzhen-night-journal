import { tGlobal } from '../i18n'

const DECISION_CLASS: Record<string, string> = {
  qa_auto_passed: 'tag-success',
  human_approved: 'tag-warning',
  human_approved_legacy_inferred: 'tag-warning',
  waiting_human_signoff: 'tag-warning',
  blocked: 'tag-danger',
  manual_post: '',
  pending: '',
}

function keyOf(path?: string | null) {
  return path && DECISION_CLASS[path] !== undefined ? path : 'pending'
}

export function getPublishDecisionMeta(item: { publish_decision_path?: string | null } | null | undefined) {
  const path = keyOf(item?.publish_decision_path)
  return {
    label: tGlobal(`decision.${path}.label`),
    description: tGlobal(`decision.${path}.description`),
    className: DECISION_CLASS[path] || '',
  }
}

export function getPublishDecisionLabel(item: { publish_decision_path?: string | null } | null | undefined) {
  return getPublishDecisionMeta(item).label
}

export function getPublishDecisionDescription(item: { publish_decision_path?: string | null } | null | undefined) {
  return getPublishDecisionMeta(item).description
}

export function getPublishDecisionClass(item: { publish_decision_path?: string | null } | null | undefined) {
  return getPublishDecisionMeta(item).className
}
