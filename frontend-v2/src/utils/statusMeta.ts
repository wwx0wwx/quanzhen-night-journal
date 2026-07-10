const POST_STATUS_META = {
  draft: { label: '草稿', description: '尚未进入审核或发布流程。', className: '' },
  pending_review: { label: '待审核', description: '内容已生成或保存，等待进一步确认。', className: 'tag-warning' },
  approved: { label: '已通过', description: '内容已审核通过，可以发布。', className: 'tag-success' },
  publishing: { label: '发布中', description: '系统正在写入前台站点。', className: 'tag-warning' },
  published: { label: '已发布', description: '文章已经对前台读者可见。', className: 'tag-success' },
  publish_failed: { label: '发布失败', description: '发布阶段出错，需要人工处理。', className: 'tag-danger' },
  archived: { label: '已归档', description: '文章已退出主列表，仅作历史保留。', className: '' },
}

const TASK_STATUS_META = {
  queued: { label: '排队中', description: '任务已经创建，等待开始。', className: '' },
  preparing_context: { label: '准备上下文', description: '正在收集记忆、配置和上下文。', className: '' },
  generating: { label: '生成正文', description: '模型正在写作。', className: '' },
  qa_checking: { label: '质量检查', description: '正在执行 QA 审核。', className: '' },
  rewrite_pending: { label: '待重写', description: '上一次结果未通过，准备重写。', className: 'tag-warning' },
  waiting_human_signoff: { label: '待人工签发', description: '高风险稿件需要人工确认。', className: 'tag-warning' },
  ready_to_publish: { label: '待发布', description: '审核完成，可以进入发布。', className: 'tag-success' },
  publishing: { label: '发布中', description: '系统正在推送到前台站点。', className: 'tag-warning' },
  published: { label: '已发布', description: '任务已完成并成功发布。', className: 'tag-success' },
  failed: { label: '失败', description: '任务执行失败。', className: 'tag-danger' },
  circuit_open: { label: '熔断', description: '连续质量问题触发熔断，需人工处理。', className: 'tag-danger' },
  aborted: { label: '已终止', description: '任务被人工终止。', className: 'tag-danger' },
  draft_saved: { label: '已存草稿', description: '任务未继续发布，但内容已保留。', className: 'tag-warning' },
}

const REVIEW_REASON_META = {
  waiting_human_signoff: '待人工签发',
  qa_circuit_open: 'QA 熔断待处理',
  manual_update: '人工修改',
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

function getMeta(map, key, fallbackLabel = '未知状态') {
  return map[key] || { label: key || fallbackLabel, description: '状态信息暂未定义。', className: '' }
}

export function getPostStatusMeta(status) {
  return getMeta(POST_STATUS_META, status, '未知文章状态')
}

export function getTaskStatusMeta(status) {
  return getMeta(TASK_STATUS_META, status, '未知任务状态')
}

export function getStatusLabel(kind, status) {
  return kind === 'task' ? getTaskStatusMeta(status).label : getPostStatusMeta(status).label
}

export function getStatusClass(kind, status) {
  return kind === 'task' ? getTaskStatusMeta(status).className : getPostStatusMeta(status).className
}

export function getStatusDescription(kind, status) {
  return kind === 'task' ? getTaskStatusMeta(status).description : getPostStatusMeta(status).description
}

export function getReviewReasonLabel(reason) {
  if (!reason) return ''
  return REVIEW_REASON_META[reason] || reason
}
