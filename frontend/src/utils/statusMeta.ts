import { tGlobal } from '../i18n'

const POST_STATUS_CLASS: Record<string, string> = {
  draft: '',
  pending_review: 'tag-warning',
  approved: 'tag-success',
  publishing: 'tag-warning',
  published: 'tag-success',
  publish_failed: 'tag-danger',
  archived: '',
}

const TASK_STATUS_CLASS: Record<string, string> = {
  queued: '',
  preparing_context: '',
  generating: '',
  qa_checking: '',
  rewrite_pending: 'tag-warning',
  waiting_human_signoff: 'tag-warning',
  ready_to_publish: 'tag-success',
  publishing: 'tag-warning',
  published: 'tag-success',
  failed: 'tag-danger',
  circuit_open: 'tag-danger',
  aborted: 'tag-danger',
  draft_saved: 'tag-warning',
}

const REVIEW_REASON_KEYS: Record<string, string> = {
  waiting_human_signoff: 'status.review.waiting_human_signoff',
  qa_circuit_open: 'status.review.qa_circuit_open',
  manual_update: 'status.review.manual_update',
}

export const POST_STATUS_OPTIONS = ['draft', 'pending_review', 'approved', 'published', 'publish_failed', 'archived']

export const TASK_TIMELINE_ORDER = [
  'queued',
  'preparing_context',
  'generating',
  'qa_checking',
  'rewrite_pending',
  'waiting_human_signoff',
  'ready_to_publish',
  'publishing',
  'published',
]

export const TASK_STATUS_OPTIONS = [
  'queued',
  'preparing_context',
  'generating',
  'qa_checking',
  'rewrite_pending',
  'waiting_human_signoff',
  'ready_to_publish',
  'publishing',
  'published',
  'failed',
  'circuit_open',
  'aborted',
  'draft_saved',
]

function postKey(status?: string | null) {
  return status && POST_STATUS_CLASS[status] !== undefined ? status : 'unknown'
}

function taskKey(status?: string | null) {
  return status && TASK_STATUS_CLASS[status] !== undefined ? status : 'unknown'
}

export function getPostStatusMeta(status?: string | null) {
  const key = postKey(status)
  return {
    label: tGlobal(`status.post.${key}.label`),
    description: tGlobal(`status.post.${key}.description`),
    className: POST_STATUS_CLASS[status || ''] || '',
  }
}

export function getTaskStatusMeta(status?: string | null) {
  const key = taskKey(status)
  return {
    label: tGlobal(`status.task.${key}.label`),
    description: tGlobal(`status.task.${key}.description`),
    className: TASK_STATUS_CLASS[status || ''] || '',
  }
}

export function getStatusLabel(kind: string, status?: string | null) {
  return kind === 'task' ? getTaskStatusMeta(status).label : getPostStatusMeta(status).label
}

export function getStatusClass(kind: string, status?: string | null) {
  return kind === 'task' ? getTaskStatusMeta(status).className : getPostStatusMeta(status).className
}

export function getStatusDescription(kind: string, status?: string | null) {
  return kind === 'task' ? getTaskStatusMeta(status).description : getPostStatusMeta(status).description
}

export function getReviewReasonLabel(reason?: string | null) {
  if (!reason) return ''
  const key = REVIEW_REASON_KEYS[reason]
  return key ? tGlobal(key) : reason
}
