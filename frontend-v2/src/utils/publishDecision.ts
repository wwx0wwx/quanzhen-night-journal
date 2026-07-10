const DECISION_META = {
  qa_auto_passed: {
    label: 'QA 自动通过',
    description: 'QA 已自动允许发布。',
    className: 'tag-success',
  },
  human_approved: {
    label: '人工签发',
    description: '高风险稿件已由人工签发后允许发布。',
    className: 'tag-warning',
  },
  human_approved_legacy_inferred: {
    label: '人工签发（历史推断）',
    description: '该发布路径来自历史记录推断，建议复核一次。',
    className: 'tag-warning',
  },
  waiting_human_signoff: {
    label: '待人工签发',
    description: '高风险稿件仍在等待人工签发。',
    className: 'tag-warning',
  },
  blocked: {
    label: '已阻断',
    description: '当前任务未满足发布条件。',
    className: 'tag-danger',
  },
  manual_post: {
    label: '手动文章',
    description: '这篇文章不走自动 QA 决策链。',
    className: '',
  },
  pending: {
    label: '待判定',
    description: '发布结论尚未形成。',
    className: '',
  },
}

export function getPublishDecisionMeta(item) {
  const path = item?.publish_decision_path || 'pending'
  return DECISION_META[path] || DECISION_META.pending
}

export function getPublishDecisionLabel(item) {
  return getPublishDecisionMeta(item).label
}

export function getPublishDecisionDescription(item) {
  return getPublishDecisionMeta(item).description
}

export function getPublishDecisionClass(item) {
  return getPublishDecisionMeta(item).className
}
