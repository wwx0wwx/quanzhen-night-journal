<template>
  <section class="stack">
    <AppLoading
      v-if="isLoading"
      title="正在加载首页"
      description="正在汇总发文状态、待办和最近文章。"
    />

    <AppError
      v-else-if="loadError"
      title="首页加载失败"
      :message="loadError"
      action-label="重新加载"
      @retry="load"
    />

    <template v-else>
      <div class="page-header">
        <div>
          <h1>首页</h1>
          <p>一眼看清：现在能不能发文、有没有需要你处理的事。</p>
        </div>
        <div class="page-header-actions">
          <button
            class="btn ghost btn-small"
            type="button"
            :disabled="isLoading"
            @click="load"
          >
            刷新
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
              立即写一篇
            </RouterLink>
            <RouterLink
              v-if="Number(data.risk_overview.waiting_human_signoff || 0) > 0"
              class="btn ghost"
              to="/admin/tasks?status=waiting_human_signoff"
            >
              查看待确认（{{ data.risk_overview.waiting_human_signoff }}）
            </RouterLink>
            <RouterLink
              v-else
              class="btn ghost"
              to="/admin/tasks"
            >
              查看发文任务
            </RouterLink>
            <RouterLink
              class="btn ghost"
              to="/admin/settings"
            >
              检查设置
            </RouterLink>
          </div>
        </div>
        <div class="status-hero-side">
          <div class="muted">建议下一步</div>
          <strong>{{ nextStep.title }}</strong>
          <div class="muted">
            {{ nextStep.description }}
          </div>
        </div>
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
          <div class="muted">待你处理</div>
          <strong>{{ pendingRiskCount }}</strong>
          <div class="muted">失败 / 待确认 / 质量拦截</div>
        </div>
        <div class="metric">
          <div class="muted">失败任务</div>
          <strong>{{ unackedFailed }}</strong>
        </div>
        <div class="metric">
          <div class="muted">待人工确认</div>
          <strong>{{ data.risk_overview.waiting_human_signoff }}</strong>
        </div>
        <div class="metric">
          <div class="muted">今日费用</div>
          <strong>{{ Number(data.cost?.cost || 0).toFixed(4) }}</strong>
          <div class="muted">限额 {{ Number(data.cost?.limit || 0) }}</div>
        </div>
      </div>

      <div class="grid two dashboard-columns">
        <div class="panel panel-pad stack">
          <div class="split">
            <div class="section-title">待办（最多 5 条）</div>
            <button
              v-if="hasFailedAttention"
              class="btn ghost btn-small"
              :disabled="dismissBusy"
              @click="dismissAll"
            >
              {{ dismissBusy ? '处理中…' : '全部已知悉' }}
            </button>
          </div>

          <AppEmpty
            v-if="!attentionCards.length"
            inline
            title="目前没有需要处理的事"
            description="没有失败任务、质量拦截或待确认文稿。"
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
                  {{ item.severity === 'error' ? '需要处理' : '提醒' }}
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
                  忽略
                </button>
                <button
                  class="btn ghost btn-small"
                  :disabled="dismissBusy"
                  @click="retryTask(item.personaId)"
                >
                  重试
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="panel panel-pad stack">
          <div class="section-title">最近文章</div>

          <AppEmpty
            v-if="!data.recent_posts.length"
            inline
            title="还没有文章"
            description="点「立即写一篇」或去文章页新建，就会出现在这里。"
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
                {{ post.summary || '暂无摘要' }}
              </div>
              <div class="muted">
                {{ formatDateTimeWithRelative(post.updated_at || post.published_at || post.created_at) }}
              </div>
            </RouterLink>
          </div>
        </div>
      </div>

      <div class="panel panel-pad stack">
        <div class="section-title">最近任务</div>
        <AppEmpty
          v-if="!data.recent_tasks.length"
          inline
          title="还没有任务记录"
          description="触发一次自动写作后，这里会显示进度。"
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
              <strong>任务 #{{ task.id }}</strong>
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
          <span>系统健康与域名（一般不用看）</span>
          <span
            class="tag"
            :class="healthStatusClass"
          >{{ healthStatusLabel }}</span>
        </summary>
        <div class="collapsible-body stack">
          <div class="split">
            <p class="muted" style="margin: 0">
              服务、数据库、调度、构建与模型连通性。域名配置是否就绪不代表读者一定能打开。
            </p>
            <button
              class="btn ghost btn-small"
              type="button"
              :disabled="healthProbe.busy"
              @click="probeHealth"
            >
              {{ healthProbe.busy ? '自检中…' : '重新自检' }}
            </button>
          </div>

          <div class="card-row">
            <div
              v-for="item in healthCards"
              :key="item.key"
              class="metric"
            >
              <div class="muted">{{ item.label }}</div>
              <strong>{{ item.statusLabel }}</strong>
              <div class="muted">{{ item.detail }}</div>
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
              <div class="muted">绑定域名</div>
              <strong>{{ data.domain_status.domain || '未配置' }}</strong>
            </div>
            <div class="metric">
              <div class="muted">博客基准地址</div>
              <strong>{{ data.domain_status.base_url || '/' }}</strong>
            </div>
            <div class="metric">
              <div class="muted">今日访问</div>
              <strong>{{ Number(data.click_stats.today_page_views || 0) }}</strong>
            </div>
            <div class="metric">
              <div class="muted">域名状态</div>
              <strong>{{ data.domain_status.enabled ? '已启用' : '未公开' }}</strong>
            </div>
          </div>

          <div class="status-banner info">
            {{ data.domain_status.reason || '尚未生成域名配置诊断。' }}
          </div>

          <div class="split">
            <button
              v-if="data.domain_status.enabled"
              class="btn ghost btn-small"
              :disabled="blogProbe.busy"
              @click="probeBlog"
            >
              {{ blogProbe.busy ? '检测中…' : '检测公网是否能打开' }}
            </button>
            <span
              v-else
              class="muted"
            >未启用域名，无需检测公网。</span>
            <span
              v-if="blogProbe.done"
              class="tag"
              :class="blogProbe.reachable ? 'tag-success' : 'tag-danger'"
            >
              {{ blogProbe.reachable ? '可达' : '不可达' }}
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
              label="角色稳定度"
              :score="Number(data.persona_stability || 0)"
            />
            <StabilityGauge
              label="记忆一致性"
              :score="Number(data.memory_coherence || 0)"
            />
            <CostChart
              title="今日模型费用"
              subtitle="相对日限额"
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

import { api, unwrap } from '../api'
import AppEmpty from '../components/AppEmpty.vue'
import AppError from '../components/AppError.vue'
import AppLoading from '../components/AppLoading.vue'
import CostChart from '../components/CostChart.vue'
import StabilityGauge from '../components/StabilityGauge.vue'
import { describeError, describeErrorCode } from '../utils/errors'
import {
  getPublishDecisionDescription,
} from '../utils/publishDecision'
import { getStatusClass, getStatusDescription, getStatusLabel } from '../utils/statusMeta'
import { formatDateTimeWithRelative, formatDateTime } from '../utils/time'
import {
  buildHealthCards,
  createDashboardState,
  deriveNextStep,
  deriveSystemState,
} from '../utils/dashboardHealth'

const data = reactive(createDashboardState())
const health = reactive({ status: 'unknown', checks: {} })
const isLoading = ref(true)
const loadError = ref('')
const hasLoadedOnce = ref(false)
const dismissBusy = ref(false)
const blogProbe = reactive({ busy: false, done: false, reachable: false, reason: '' })
const healthProbe = reactive({ busy: false, error: '' })
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
  if (!data.config_status.system_initialized) warnings.push('系统还没完成初始化，请先走完设置向导。')
  if (!data.config_status.llm_ready) warnings.push('AI 模型还没配好，自动写作会失败。请到「系统设置」填写。')
  if (!data.config_status.embedding_ready) warnings.push('记忆检索还没配好，找记忆和去重会变弱。')
  if (!data.config_status.domain_enabled) warnings.push('还没配置域名：读者看不到博客，但后台仍可正常使用。')
  return warnings
})

const healthStatusLabel = computed(() => {
  if (health.status === 'ok') return '运行正常'
  if (health.status === 'degraded') return '部分降级'
  if (health.status === 'error') return '存在错误'
  return '尚未自检'
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
      title: `任务 #${item.task_id}`,
      message: describeErrorCode(item.label) || item.message,
      personaId: task?.persona_id,
    }
  })

  if (!data.config_status.llm_ready) {
    cards.push({
      kind: 'settings',
      id: 'llm',
      severity: 'warning',
      label: '配置缺口',
      title: 'AI 模型尚未就绪',
      message: '请到系统设置填写接口地址、密钥和模型名称。',
    })
  }
  if (!data.config_status.embedding_ready) {
    cards.push({
      kind: 'settings',
      id: 'embedding',
      severity: 'warning',
      label: '配置缺口',
      title: '记忆检索尚未就绪',
      message: '请到系统设置补齐向量服务配置。',
    })
  }

  return cards.slice(0, 6)
})

const hasFailedAttention = computed(() => attentionCards.value.some((c) => c.kind === 'task' && c.severity === 'error'))

function attentionLabel(label) {
  if (label === 'legacy_publish_decision') return '历史签发待复核'
  if (label === 'waiting_human_signoff') return '待人工确认'
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
    blogProbe.reason = '探测请求失败，请稍后重试。'
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
    healthProbe.error = describeError(error, '运行自检失败，请稍后重试。')
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
        healthProbe.error = describeError(error, '运行自检失败，请稍后重试。')
        return { status: 'unknown', checks: {} }
      }),
    ])
    Object.assign(data, createDashboardState(), result)
    Object.assign(health, { status: 'unknown', checks: {} }, healthResult)
    hasLoadedOnce.value = true
    loadError.value = ''
  } catch (error) {
    loadError.value = describeError(error, '加载首页失败，请稍后重试。')
  } finally {
    if (showLoading) isLoading.value = false
  }
}

onMounted(load)
</script>
