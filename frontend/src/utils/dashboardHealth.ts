export type HealthCheck = {
  status?: string
  configured?: boolean
  missing?: string[]
  encoding?: string
  running?: boolean
  job_count?: number
  built_at?: string
  detail?: string
  signal?: string
  reason?: string
  enabled?: boolean
  free_ratio?: number
  reachability?: {
    status?: string
    http_status?: number
    detail?: string
  }
  blog_reachability?: {
    status?: string
    http_status?: number
    detail?: string
  }
}

export type HealthCard = {
  key: string
  label: string
  status: string
  statusLabel: string
  detail: string
}

export function statusLabel(status?: string): string {
  if (status === 'ok') return '正常'
  if (status === 'warning') return '警告'
  if (status === 'error') return '错误'
  return '未知'
}

export function buildHealthCard(
  key: string,
  label: string,
  check: HealthCheck | undefined,
  fallbackDetail: string,
): HealthCard {
  return {
    key,
    label,
    status: check?.status || 'unknown',
    statusLabel: statusLabel(check?.status),
    detail: fallbackDetail || '-',
  }
}

export function providerDetail(check?: HealthCheck): string {
  if (!check) return '-'
  if (!check.configured) return `缺少 ${(check.missing || []).join(', ') || '配置'}`
  const reachability = check.reachability || {}
  if (reachability.status === 'ok') return `/models HTTP ${reachability.http_status}`
  if (reachability.status === 'skipped') return '未执行外部探测'
  return reachability.detail || '外部探测异常'
}

export function domainHealthDetail(check?: HealthCheck): string {
  if (!check) return '-'
  if (!check.enabled) return check.reason || '未启用域名'
  const reachability = check.blog_reachability || {}
  if (reachability.status === 'ok') return `公网 HTTP ${reachability.http_status}`
  return check.reason || reachability.detail || '公网状态未知'
}

export function diskDetail(check?: HealthCheck): string {
  if (!check) return '-'
  const ratio = Number(check.free_ratio || 0) * 100
  return `剩余 ${ratio.toFixed(1)}%`
}

export function buildHealthCards(checks: Record<string, HealthCheck | undefined> = {}): HealthCard[] {
  return [
    buildHealthCard('api', 'API 服务', checks.api, '核心接口响应状态。'),
    buildHealthCard('database', '数据库', checks.database, `编码 ${checks.database?.encoding || '-'}`),
    buildHealthCard(
      'scheduler',
      '调度器',
      checks.scheduler,
      checks.scheduler
        ? `${checks.scheduler.running ? '运行中' : '未运行'} · ${checks.scheduler.job_count || 0} 个任务`
        : '-',
    ),
    buildHealthCard(
      'hugo_build',
      'Hugo 构建',
      checks.hugo_build,
      checks.hugo_build?.built_at || checks.hugo_build?.detail || '-',
    ),
    buildHealthCard('llm', '大脑接入', checks.llm, providerDetail(checks.llm)),
    buildHealthCard('embedding', '记忆检索', checks.embedding, providerDetail(checks.embedding)),
    buildHealthCard('domain', '公网入口', checks.domain, domainHealthDetail(checks.domain)),
    buildHealthCard('disk', '磁盘', checks.disk, diskDetail(checks.disk)),
  ]
}

export type DashboardState = {
  recent_posts: unknown[]
  recent_tasks: Array<{ id: number; persona_id?: number }>
  cost: { cost: number; budget: number }
  click_stats: { today_page_views: number }
  domain_status: {
    domain: string
    enabled: boolean
    status: string
    reason: string
    checked_at: string
    base_url: string
  }
  persona_stability: number
  memory_coherence: number
  risk_overview: {
    failed: number
    circuit_open: number
    waiting_human_signoff: number
    failed_acknowledged: number
    circuit_open_acknowledged: number
  }
  attention_items: Array<{
    task_id: number
    severity: string
    label: string
    message: string
  }>
  config_status: {
    system_initialized: boolean
    llm_ready: boolean
    embedding_ready: boolean
    domain_enabled: boolean
  }
}

export function createDashboardState(): DashboardState {
  return {
    recent_posts: [],
    recent_tasks: [],
    cost: { cost: 0, budget: 1 },
    click_stats: { today_page_views: 0 },
    domain_status: {
      domain: '',
      enabled: false,
      status: 'disabled',
      reason: '',
      checked_at: '',
      base_url: '/',
    },
    persona_stability: 0,
    memory_coherence: 0,
    risk_overview: {
      failed: 0,
      circuit_open: 0,
      waiting_human_signoff: 0,
      failed_acknowledged: 0,
      circuit_open_acknowledged: 0,
    },
    attention_items: [],
    config_status: {
      system_initialized: false,
      llm_ready: false,
      embedding_ready: false,
      domain_enabled: false,
    },
  }
}

export function deriveSystemState(input: {
  systemInitialized: boolean
  llmReady: boolean
  waitingHuman: number
  unackedCircuitOpen: number
  unackedFailed: number
}): { label: string; description: string } {
  if (!input.systemInitialized) {
    return { label: '尚未初始化', description: '请先完成初始化与基础配置。' }
  }
  if (!input.llmReady) {
    return { label: '无法自动发文', description: '大脑接入尚未配置完成，自动生成会直接失败。' }
  }
  if (input.waitingHuman > 0 || input.unackedCircuitOpen > 0) {
    return { label: '可降级发文', description: '系统可运行，但存在待签发或熔断风险。' }
  }
  if (input.unackedFailed > 0) {
    return { label: '需先排错', description: '最近已有失败任务，建议先检查原因。' }
  }
  return { label: '可正常发文', description: '当前配置和近期任务状态允许继续发文。' }
}

export function deriveNextStep(input: {
  systemInitialized: boolean
  llmReady: boolean
  embeddingReady: boolean
  waitingHuman: number
  unackedCircuitOpen: number
  unackedFailed: number
}): { title: string; description: string } {
  if (!input.systemInitialized) {
    return { title: '先完成初始化', description: '先补齐管理员密码、站点信息和大脑接入配置。' }
  }
  if (!input.llmReady) {
    return { title: '先补齐大脑接入配置', description: '去设置页填入接口地址、访问密钥和模型名称。' }
  }
  if (!input.embeddingReady) {
    return { title: '补齐记忆检索配置', description: '避免检索、去重和相似度判断退化。' }
  }
  if (input.waitingHuman > 0) {
    return { title: '先审阅待签发稿件', description: '优先检查高风险稿件，再决定是否发布。' }
  }
  if (input.unackedFailed > 0 || input.unackedCircuitOpen > 0) {
    return { title: '先排查失败任务', description: '先看失败任务和熔断原因，再继续发文。' }
  }
  return { title: '可以开始今晚写作', description: '当前系统状态稳定，可以触发新的写作任务。' }
}
