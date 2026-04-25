const CODE_MESSAGES = {
  1001: '请求参数无效，请检查后重试。',
  1002: '请求的内容不存在或已被删除。',
  2001: '登录已失效或账号密码错误，请重新确认。',
  3001: '系统尚未初始化，请先完成初始化配置。',
  3003: '系统已经初始化，不能重复执行初始化。',
  4001: '发布失败，请检查发布链路后重试。',
}

const RAW_MESSAGE_MAP = {
  not_authenticated: '登录已失效，请重新登录。',
  token_invalid: '登录状态无效，请重新登录。',
  user_not_found: '当前用户不存在，请重新登录。',
  request_failed: '请求失败，请稍后重试。',
  llm_not_configured: '大脑接入尚未配置完整，请先检查设置页。',
  no_active_persona: '当前没有启用中的人格设定，请先检查人格设置。',
}

const ERROR_CODE_LABELS = {
  container_restart: '系统重启导致任务中断',
  invalid_model_output: '模型输出格式异常',
  qa_circuit_open: '质量检查多次未通过',
  budget_exhausted: '当日/当月预算已用完',
  publish_failed: '文章发布到博客失败',
  task_aborted: '任务已被手动终止',
  llm_request_failed: '大脑接入请求失败',
  llm_timeout: '大脑接入请求超时',
  embedding_failed: '记忆检索请求失败',
}

export function describeErrorCode(code) {
  if (!code) return ''
  return ERROR_CODE_LABELS[code] || code
}

export function describeError(error, fallback = '请求失败，请稍后重试。') {
  const code = error?.response?.data?.code ?? error?.responseData?.code ?? error?.code
  if (code && CODE_MESSAGES[code]) {
    return CODE_MESSAGES[code]
  }

  const message = error?.response?.data?.message || error?.responseData?.message || error?.message || ''
  if (!message) {
    return fallback
  }
  if (RAW_MESSAGE_MAP[message]) {
    return RAW_MESSAGE_MAP[message]
  }
  if (/database is locked/i.test(message)) {
    return '系统正在处理其他写入，请稍后重试。'
  }
  if (/timeout/i.test(message)) {
    return '请求超时，请稍后重试。'
  }
  if (/network error/i.test(message)) {
    return '网络异常，请检查连接后重试。'
  }
  if (/^llm_/.test(message)) {
    return '大脑接入请求失败，请检查模型配置或稍后重试。'
  }
  if (/[一-龥]/.test(message)) {
    return message
  }
  return fallback
}
