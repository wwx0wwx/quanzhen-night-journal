import { tGlobal } from '../i18n'

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
  if (status === 'ok') return tGlobal('health.ok')
  if (status === 'warning') return tGlobal('health.warning')
  if (status === 'error') return tGlobal('health.error')
  return tGlobal('health.unknown')
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
  if (!check.configured) {
    return tGlobal('health.missing', {
      items: (check.missing || []).join(', ') || tGlobal('health.missingConfig'),
    })
  }
  const reachability = check.reachability || {}
  if (reachability.status === 'ok') return tGlobal('health.modelsOk', { code: reachability.http_status })
  if (reachability.status === 'skipped') return tGlobal('health.probeSkipped')
  return reachability.detail || tGlobal('health.probeError')
}

export function domainHealthDetail(check?: HealthCheck): string {
  if (!check) return '-'
  if (!check.enabled) return check.reason || tGlobal('health.domainDisabled')
  const reachability = check.blog_reachability || {}
  if (reachability.status === 'ok') return tGlobal('health.publicHttp', { code: reachability.http_status })
  return check.reason || reachability.detail || tGlobal('health.publicUnknown')
}

export function diskDetail(check?: HealthCheck): string {
  if (!check) return '-'
  const ratio = Number(check.free_ratio || 0) * 100
  return tGlobal('health.freeRatio', { n: ratio.toFixed(1) })
}

export function buildHealthCards(checks: Record<string, HealthCheck | undefined> = {}): HealthCard[] {
  return [
    buildHealthCard('api', tGlobal('health.api'), checks.api, tGlobal('health.apiDetail')),
    buildHealthCard(
      'database',
      tGlobal('health.database'),
      checks.database,
      tGlobal('health.encoding', { enc: checks.database?.encoding || '-' }),
    ),
    buildHealthCard(
      'scheduler',
      tGlobal('health.scheduler'),
      checks.scheduler,
      checks.scheduler
        ? checks.scheduler.running
          ? tGlobal('health.schedulerRunning', { n: checks.scheduler.job_count || 0 })
          : tGlobal('health.schedulerStopped', { n: checks.scheduler.job_count || 0 })
        : '-',
    ),
    buildHealthCard(
      'hugo_build',
      tGlobal('health.hugo'),
      checks.hugo_build,
      checks.hugo_build?.built_at || checks.hugo_build?.detail || '-',
    ),
    buildHealthCard('llm', tGlobal('health.llm'), checks.llm, providerDetail(checks.llm)),
    buildHealthCard('embedding', tGlobal('health.embedding'), checks.embedding, providerDetail(checks.embedding)),
    buildHealthCard('domain', tGlobal('health.domain'), checks.domain, domainHealthDetail(checks.domain)),
    buildHealthCard('disk', tGlobal('health.disk'), checks.disk, diskDetail(checks.disk)),
  ]
}

export type DashboardState = {
  recent_posts: unknown[]
  recent_tasks: Array<{ id: number; persona_id?: number }>
  cost: { cost: number; budget: number; limit?: number }
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
    return {
      label: tGlobal('systemState.notInit.label'),
      description: tGlobal('systemState.notInit.description'),
    }
  }
  if (!input.llmReady) {
    return {
      label: tGlobal('systemState.notReady.label'),
      description: tGlobal('systemState.notReady.description'),
    }
  }
  if (input.waitingHuman > 0 || input.unackedCircuitOpen > 0) {
    return {
      label: tGlobal('systemState.attention.label'),
      description: tGlobal('systemState.attention.description'),
    }
  }
  if (input.unackedFailed > 0) {
    return {
      label: tGlobal('systemState.attention.label'),
      description: tGlobal('systemState.attention.description'),
    }
  }
  return {
    label: tGlobal('systemState.ok.label'),
    description: tGlobal('systemState.ok.description'),
  }
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
    return {
      title: tGlobal('nextStep.setup.title'),
      description: tGlobal('nextStep.setup.description'),
    }
  }
  if (!input.llmReady) {
    return {
      title: tGlobal('nextStep.llm.title'),
      description: tGlobal('nextStep.llm.description'),
    }
  }
  if (input.waitingHuman > 0) {
    return {
      title: tGlobal('nextStep.signoff.title'),
      description: tGlobal('nextStep.signoff.description'),
    }
  }
  if (input.unackedFailed > 0 || input.unackedCircuitOpen > 0) {
    return {
      title: tGlobal('nextStep.failed.title'),
      description: tGlobal('nextStep.failed.description'),
    }
  }
  return {
    title: tGlobal('nextStep.write.title'),
    description: tGlobal('nextStep.write.description'),
  }
}
