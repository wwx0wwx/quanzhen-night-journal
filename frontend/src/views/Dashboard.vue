<template>
  <section class="stack">
    <AppLoading
      v-if="isLoading"
      :title="t('dashboard.loadingTitle')"
      :description="t('dashboard.loadingDesc')"
    />

    <AppError
      v-else-if="loadError"
      :title="t('dashboard.loadError')"
      :message="loadError"
      :action-label="t('common.refresh')"
      @retry="load"
    />

    <template v-else>
      <div class="page-header">
        <div>
          <h1>{{ t('dashboard.title') }}</h1>
          <p>{{ t('dashboard.subtitle') }}</p>
        </div>
        <div class="page-header-actions">
          <button
            class="btn ghost btn-small"
            type="button"
            :disabled="isLoading"
            @click="load"
          >
            {{ t('common.refresh') }}
          </button>
        </div>
      </div>

      <div class="status-hero">
        <div class="status-hero-main">
          <span
            class="tag"
            :class="configConclusionTagClass"
          >{{ systemState.label }}</span>
          <h2>{{ systemState.label }}</h2>
          <p>{{ systemState.description }}</p>
          <div
            class="quick-actions"
            style="margin-top: 16px"
          >
            <RouterLink
              class="btn primary"
              to="/admin/posts"
            >
              {{ t('dashboard.writeNow') }}
            </RouterLink>
            <RouterLink
              v-if="Number(data.risk_overview.waiting_human_signoff || 0) > 0"
              class="btn ghost"
              to="/admin/tasks?status=waiting_human_signoff"
            >
              {{ t('dashboard.viewPending', { n: data.risk_overview.waiting_human_signoff }) }}
            </RouterLink>
            <RouterLink
              v-else
              class="btn ghost"
              to="/admin/tasks"
            >
              {{ t('dashboard.viewTasks') }}
            </RouterLink>
            <RouterLink
              class="btn ghost"
              to="/admin/settings"
            >
              {{ t('dashboard.checkSettings') }}
            </RouterLink>
          </div>
        </div>
        <div class="status-hero-side">
          <div class="muted">
            {{ t('dashboard.nextStep') }}
          </div>
          <strong>{{ nextStep.title }}</strong>
          <div class="muted">
            {{ nextStep.description }}
          </div>
        </div>
      </div>


      <SignoffQueue
        v-if="signoffTasks && signoffTasks.length"
        :items="signoffTasks"
        :busy-id="signoffBusyId"
        @approve="approveSignoff"
      />

      <div
        v-if="costHint"
        class="status-banner"
        :class="costHintClass"
      >
        {{ costHint }}
      </div>

      <div
        v-if="configWarnings.length"
        class="stack"
      >
        <div
          v-for="item in configWarnings"
          :key="item"
          class="status-banner warning"
        >
          {{ item }}
        </div>
      </div>

      <div class="card-row">
        <div class="metric">
          <div class="muted">
            {{ t('dashboard.pending') }}
          </div>
          <strong>{{ pendingRiskCount }}</strong>
          <div class="muted">
            {{ t('dashboard.pendingHint') }}
          </div>
        </div>
        <div class="metric">
          <div class="muted">
            {{ t('dashboard.failedTasks') }}
          </div>
          <strong>{{ unackedFailed }}</strong>
        </div>
        <div class="metric">
          <div class="muted">
            {{ t('dashboard.waitingSignoff') }}
          </div>
          <strong>{{ data.risk_overview.waiting_human_signoff }}</strong>
        </div>
        <div class="metric">
          <div class="muted">
            {{ t('dashboard.todayCost') }}
          </div>
          <strong>{{ Number(data.cost?.cost || 0).toFixed(4) }}</strong>
          <div class="muted">
            {{ t('dashboard.budgetLimit', { n: Number(data.cost?.limit || 0) }) }}
          </div>
        </div>
      </div>

      <div class="grid two dashboard-columns">
        <div class="panel panel-pad stack">
          <div class="split">
            <div class="section-title">
              {{ t('dashboard.todos') }}
            </div>
            <button
              v-if="hasFailedAttention"
              class="btn ghost btn-small"
              :disabled="dismissBusy"
              @click="dismissAll"
            >
              {{ dismissBusy ? t('common.busy') : t('dashboard.dismissAll') }}
            </button>
          </div>

          <AppEmpty
            v-if="!attentionCards.length"
            inline
            :title="t('dashboard.noTodosTitle')"
            :description="t('dashboard.noTodosDesc')"
          />

          <div
            v-else
            class="list"
          >
            <div
              v-for="item in attentionCards.slice(0, 5)"
              :key="`${item.kind}-${item.id}`"
              class="list-item stack"
            >
              <div class="button-row">
                <span
                  class="tag"
                  :class="item.severity === 'error' ? 'tag-danger' : 'tag-warning'"
                >
                  {{ item.severity === 'error' ? t('dashboard.needAction') : t('dashboard.reminder') }}
                </span>
                <span class="tag">{{ attentionLabel(item.label) }}</span>
              </div>
              <RouterLink :to="item.kind === 'task' ? `/admin/tasks/${item.id}` : '/admin/settings'">
                <strong>{{ item.title }}</strong>
              </RouterLink>
              <div class="muted">
                {{ item.message }}
              </div>
              <div
                v-if="item.kind === 'task' && item.severity === 'error'"
                class="button-row"
              >
                <button
                  class="btn ghost btn-small"
                  :disabled="dismissBusy"
                  @click="dismissTask(item.id)"
                >
                  {{ t('dashboard.ignore') }}
                </button>
                <button
                  class="btn ghost btn-small"
                  :disabled="dismissBusy"
                  @click="retryTask(item.personaId)"
                >
                  {{ t('dashboard.retryTask') }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="panel panel-pad stack">
          <div class="section-title">
            {{ t('dashboard.recentPosts') }}
          </div>

          <AppEmpty
            v-if="!data.recent_posts.length"
            inline
            :title="t('dashboard.noPostsTitle')"
            :description="t('dashboard.noPostsDesc')"
          />

          <div
            v-else
            class="list"
          >
            <RouterLink
              v-for="post in data.recent_posts.slice(0, 5)"
              :key="post.id"
              class="list-item stack"
              :to="`/admin/posts/${post.id}`"
            >
              <div class="split">
                <strong>{{ post.title }}</strong>
                <span
                  class="tag"
                  :class="getStatusClass('post', post.status)"
                >{{ getStatusLabel('post', post.status) }}</span>
              </div>
              <div class="muted">
                {{ post.summary || t('dashboard.noSummary') }}
              </div>
              <div class="muted">
                {{ formatDateTimeWithRelative(post.updated_at || post.published_at || post.created_at) }}
              </div>
            </RouterLink>
          </div>
        </div>
      </div>

      <div class="panel panel-pad stack">
        <div class="section-title">
          {{ t('dashboard.recentTasks') }}
        </div>
        <AppEmpty
          v-if="!data.recent_tasks.length"
          inline
          :title="t('dashboard.noTasksTitle')"
          :description="t('dashboard.noTasksDesc')"
        />
        <div
          v-else
          class="list"
        >
          <RouterLink
            v-for="task in data.recent_tasks.slice(0, 5)"
            :key="task.id"
            class="list-item stack"
            :to="`/admin/tasks/${task.id}`"
          >
            <div class="split">
              <strong>{{ t('dashboard.taskN', { id: task.id }) }}</strong>
              <span
                class="tag"
                :class="getStatusClass('task', task.status)"
              >{{ getStatusLabel('task', task.status) }}</span>
            </div>
            <div class="muted">
              {{ formatDateTimeWithRelative(task.started_at) }}
            </div>
            <div class="muted">
              {{ taskPrimaryMessage(task) }}
            </div>
          </RouterLink>
        </div>
      </div>

      <details class="panel collapsible-panel">
        <summary>
          <span>{{ t('dashboard.healthFold') }}</span>
          <span
            class="tag"
            :class="healthStatusClass"
          >{{ healthStatusLabel }}</span>
        </summary>
        <div class="collapsible-body stack">
          <div class="split">
            <p
              class="muted"
              style="margin: 0"
            >
              {{ t('dashboard.healthHint') }}
            </p>
            <button
              class="btn ghost btn-small"
              type="button"
              :disabled="healthProbe.busy"
              @click="probeHealth"
            >
              {{ healthProbe.busy ? t('dashboard.rechecking') : t('dashboard.recheck') }}
            </button>
          </div>

          <div class="card-row">
            <div
              v-for="item in healthCards"
              :key="item.key"
              class="metric"
            >
              <div class="muted">
                {{ item.label }}
              </div>
              <strong>{{ item.statusLabel }}</strong>
              <div class="muted">
                {{ item.detail }}
              </div>
            </div>
          </div>

          <div
            v-if="healthProbe.error"
            class="status-banner warning"
          >
            {{ healthProbe.error }}
          </div>

          <div class="card-row">
            <div class="metric">
              <div class="muted">
                {{ t('dashboard.boundDomain') }}
              </div>
              <strong>{{ data.domain_status.domain || t('dashboard.notConfigured') }}</strong>
            </div>
            <div class="metric">
              <div class="muted">
                {{ t('dashboard.blogBaseUrl') }}
              </div>
              <strong>{{ data.domain_status.base_url || '/' }}</strong>
            </div>
            <div class="metric">
              <div class="muted">
                {{ t('dashboard.todayViews') }}
              </div>
              <strong>{{ Number(data.click_stats.today_page_views || 0) }}</strong>
            </div>
            <div class="metric">
              <div class="muted">
                {{ t('dashboard.domainStatus') }}
              </div>
              <strong>{{ data.domain_status.enabled ? t('dashboard.domainEnabled') : t('dashboard.domainPrivate') }}</strong>
            </div>
          </div>

          <div class="status-banner info">
            {{ data.domain_status.reason || t('dashboard.domainNoDiag') }}
          </div>

          <div class="split">
            <button
              v-if="data.domain_status.enabled"
              class="btn ghost btn-small"
              :disabled="blogProbe.busy"
              @click="probeBlog"
            >
              {{ blogProbe.busy ? t('dashboard.probing') : t('dashboard.probeBlog') }}
            </button>
            <span
              v-else
              class="muted"
            >{{ t('dashboard.noDomainProbe') }}</span>
            <span
              v-if="blogProbe.done"
              class="tag"
              :class="blogProbe.reachable ? 'tag-success' : 'tag-danger'"
            >
              {{ blogProbe.reachable ? t('dashboard.reachable') : t('dashboard.unreachable') }}
            </span>
          </div>
          <div
            v-if="blogProbe.done"
            class="status-banner"
            :class="blogProbe.reachable ? 'success' : 'error'"
          >
            {{ blogProbe.reason }}
          </div>

          <div class="card-row">
            <StabilityGauge
              :label="t('dashboard.personaStability')"
              :score="Number(data.persona_stability || 0)"
            />
            <StabilityGauge
              :label="t('dashboard.memoryCoherence')"
              :score="Number(data.memory_coherence || 0)"
            />
            <CostChart
              :title="t('dashboard.costTitle')"
              :subtitle="t('dashboard.costSubtitle')"
              :cost="Number(data.cost?.cost || 0)"
              :limit="Number(data.cost?.limit || 1)"
            />
          </div>
        </div>
      </details>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { api, unwrap } from '../api'
import AppEmpty from '../components/AppEmpty.vue'
import AppError from '../components/AppError.vue'
import AppLoading from '../components/AppLoading.vue'
import CostChart from '../components/CostChart.vue'
import StabilityGauge from '../components/StabilityGauge.vue'
import SignoffQueue from '../components/SignoffQueue.vue'
import { useToastStore } from '../stores/toast'
import { describeError, describeErrorCode } from '../utils/errors'
import {
  getPublishDecisionDescription,
} from '../utils/publishDecision'
import { getStatusClass, getStatusDescription, getStatusLabel } from '../utils/statusMeta'
import { formatDateTimeWithRelative } from '../utils/time'
import {
  buildHealthCards,
  createDashboardState,
  deriveNextStep,
  deriveSystemState,
} from '../utils/dashboardHealth'

const { t } = useI18n()
const toast = useToastStore()
const data = reactive(createDashboardState())
const health = reactive({ status: 'unknown', checks: {} })
const isLoading = ref(true)
const loadError = ref('')
const hasLoadedOnce = ref(false)
const dismissBusy = ref(false)
const signoffBusyId = ref(null)
const blogProbe = reactive({ busy: false, done: false, reachable: false, reason: '' })
const healthProbe = reactive({ busy: false, error: '' })

const signoffTasks = computed(() =>
  (data.recent_tasks || []).filter((task) => task.status === 'waiting_human_signoff'),
)
const costHint = computed(() => {
  const cost = Number(data.cost?.cost || 0)
  const limit = Number(data.cost?.limit || data.cost?.budget || 0)
  if (!limit || limit >= 99999) return ''
  const ratio = cost / limit
  if (ratio >= 1) return t('cost.overLimit')
  if (ratio >= 0.8) return t('cost.nearLimit')
  const remain = Math.max(0, Math.floor((limit - cost) / 0.05))
  return t('cost.remaining', { n: remain })
})
const costHintClass = computed(() => {
  const cost = Number(data.cost?.cost || 0)
  const limit = Number(data.cost?.limit || data.cost?.budget || 0)
  if (!limit || limit >= 99999) return 'info'
  const ratio = cost / limit
  if (ratio >= 1) return 'error'
  if (ratio >= 0.8) return 'warning'
  return 'info'
})

async function approveSignoff(task) {
  if (signoffBusyId.value) return
  signoffBusyId.value = task.id
  try {
    await unwrap(api.post(`/tasks/${task.id}/approve`))
    toast.success(t('toast.approved'))
    await load(false)
  } catch (error) {
    toast.error(describeError(error))
  } finally {
    signoffBusyId.value = null
  }
}
const pendingRiskCount = computed(
  () => unackedFailed.value + unackedCircuitOpen.value + Number(data.risk_overview.waiting_human_signoff || 0),
)
const unackedFailed = computed(
  () => Number(data.risk_overview.failed || 0) - Number(data.risk_overview.failed_acknowledged || 0),
)
const unackedCircuitOpen = computed(
  () => Number(data.risk_overview.circuit_open || 0) - Number(data.risk_overview.circuit_open_acknowledged || 0),
)
const configConclusionTagClass = computed(() => {
  if (!data.config_status.system_initialized || !data.config_status.llm_ready) return 'tag-danger'
  if (
    unackedFailed.value > 0 ||
    unackedCircuitOpen.value > 0 ||
    Number(data.risk_overview.waiting_human_signoff || 0) > 0
  ) {
    return 'tag-warning'
  }
  return 'tag-success'
})

const systemState = computed(() =>
  deriveSystemState({
    systemInitialized: data.config_status.system_initialized,
    llmReady: data.config_status.llm_ready,
    waitingHuman: Number(data.risk_overview.waiting_human_signoff || 0),
    unackedCircuitOpen: unackedCircuitOpen.value,
    unackedFailed: unackedFailed.value,
  }),
)

const nextStep = computed(() =>
  deriveNextStep({
    systemInitialized: data.config_status.system_initialized,
    llmReady: data.config_status.llm_ready,
    embeddingReady: data.config_status.embedding_ready,
    waitingHuman: Number(data.risk_overview.waiting_human_signoff || 0),
    unackedCircuitOpen: unackedCircuitOpen.value,
    unackedFailed: unackedFailed.value,
  }),
)

const configWarnings = computed(() => {
  const warnings = []
  if (!data.config_status.system_initialized) warnings.push(t('dashboard.warnUninit'))
  if (!data.config_status.llm_ready) warnings.push(t('dashboard.warnLlm'))
  if (!data.config_status.embedding_ready) warnings.push(t('dashboard.warnEmbed'))
  if (!data.config_status.domain_enabled) warnings.push(t('dashboard.warnDomain'))
  return warnings
})

const healthStatusLabel = computed(() => {
  if (health.status === 'ok') return t('dashboard.healthOk')
  if (health.status === 'degraded') return t('dashboard.healthDegraded')
  if (health.status === 'error') return t('dashboard.healthError')
  return t('dashboard.healthUnknown')
})

const healthStatusClass = computed(() => {
  if (health.status === 'ok') return 'tag-success'
  if (health.status === 'error') return 'tag-danger'
  return 'tag-warning'
})

const healthCards = computed(() => buildHealthCards(health.checks || {}))

const attentionCards = computed(() => {
  const taskIndex = Object.fromEntries(data.recent_tasks.map((t) => [t.id, t]))
  const cards = data.attention_items.map((item) => {
    const task = taskIndex[item.task_id]
    return {
      kind: 'task',
      id: item.task_id,
      severity: item.severity,
      label: item.label,
      title: t('dashboard.taskN', { id: item.task_id }),
      message: describeErrorCode(item.label) || item.message,
      personaId: task?.persona_id,
    }
  })

  if (!data.config_status.llm_ready) {
    cards.push({
      kind: 'settings',
      id: 'llm',
      severity: 'warning',
      label: t('dashboard.configGap'),
      title: t('dashboard.gapLlmTitle'),
      message: t('dashboard.gapLlmMsg'),
    })
  }
  if (!data.config_status.embedding_ready) {
    cards.push({
      kind: 'settings',
      id: 'embedding',
      severity: 'warning',
      label: t('dashboard.configGap'),
      title: t('dashboard.gapEmbedTitle'),
      message: t('dashboard.gapEmbedMsg'),
    })
  }

  return cards.slice(0, 6)
})

const hasFailedAttention = computed(() => attentionCards.value.some((c) => c.kind === 'task' && c.severity === 'error'))

function attentionLabel(label) {
  if (label === 'legacy_publish_decision') return t('dashboard.legacySignoff')
  if (label === 'waiting_human_signoff') return t('dashboard.waitingHuman')
  return describeErrorCode(label) || label
}

function taskPrimaryMessage(task) {
  if (task.error_message) return task.error_message
  if (task.error_code) return describeErrorCode(task.error_code) || task.error_code
  if (task.publish_decision_path && !['manual_post', 'pending', 'blocked'].includes(task.publish_decision_path)) {
    return getPublishDecisionDescription(task)
  }
  return getStatusDescription('task', task.status)
}

async function dismissTask(taskId) {
  if (dismissBusy.value) return
  dismissBusy.value = true
  try {
    await unwrap(api.post(`/tasks/${taskId}/dismiss`))
    await load(false)
  } catch {
    /* ignore */
  } finally {
    dismissBusy.value = false
  }
}

async function dismissAll() {
  if (dismissBusy.value) return
  dismissBusy.value = true
  try {
    await unwrap(api.post('/tasks/dismiss-all'))
    await load(false)
  } catch {
    /* ignore */
  } finally {
    dismissBusy.value = false
  }
}

async function retryTask(personaId) {
  if (dismissBusy.value) return
  dismissBusy.value = true
  try {
    const payload = personaId ? { persona_id: personaId } : {}
    await unwrap(api.post('/tasks/trigger', payload))
    await load(false)
  } catch {
    /* ignore */
  } finally {
    dismissBusy.value = false
  }
}

async function probeBlog() {
  if (blogProbe.busy) return
  blogProbe.busy = true
  blogProbe.done = false
  try {
    const result = await unwrap(api.post('/dashboard/probe-blog'))
    blogProbe.reachable = !!result.reachable
    blogProbe.reason = result.reason || ''
    blogProbe.done = true
  } catch {
    blogProbe.reachable = false
    blogProbe.reason = t('dashboard.probeFail')
    blogProbe.done = true
  } finally {
    blogProbe.busy = false
  }
}

async function probeHealth() {
  if (healthProbe.busy) return
  healthProbe.busy = true
  healthProbe.error = ''
  try {
    const result = await unwrap(api.get('/health/system', { params: { probe_external: true } }))
    Object.assign(health, { status: 'unknown', checks: {} }, result)
  } catch (error) {
    healthProbe.error = describeError(error, t('dashboard.healthFail'))
  } finally {
    healthProbe.busy = false
  }
}

async function load(showLoading = !hasLoadedOnce.value) {
  if (showLoading) isLoading.value = true
  if (!hasLoadedOnce.value) loadError.value = ''

  try {
    const [result, healthResult] = await Promise.all([
      unwrap(api.get('/dashboard')),
      unwrap(api.get('/health/system', { params: { probe_external: true } })).catch((error) => {
        healthProbe.error = describeError(error, t('dashboard.healthFail'))
        return { status: 'unknown', checks: {} }
      }),
    ])
    Object.assign(data, createDashboardState(), result)
    Object.assign(health, { status: 'unknown', checks: {} }, healthResult)
    hasLoadedOnce.value = true
    loadError.value = ''
  } catch (error) {
    loadError.value = describeError(error, t('dashboard.loadErrorFallback'))
  } finally {
    if (showLoading) isLoading.value = false
  }
}

onMounted(load)
</script>
