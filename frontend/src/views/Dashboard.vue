<template>
  <section class="stack">
    <AppLoading
      v-if="isLoading"
      title="正在加载总览"
      description="正在汇总最近文章、任务风险和成本信息。"
    />

    <AppError
      v-else-if="loadError"
      title="总览加载失败"
      :message="loadError"
      action-label="重新加载"
      @retry="load"
    />

    <template v-else>
      <div class="hero dashboard-hero">
        <div>
          <div class="hero-kicker">Night Watch Console</div>
          <h1>运营总览</h1>
          <p>把今夜的站点、任务、风险与生成状态收束在同一处，先看夜况是否安稳，再决定是否继续发文。</p>
        </div>
        <div class="dashboard-hero-aside">
          <span class="tag" :class="configConclusionTagClass">{{ systemState.label }}</span>
          <div class="muted">建议动作：{{ nextStep.title }}</div>
        </div>
      </div>

      <div class="panel panel-pad stack dashboard-overview-card">
        <div class="dashboard-overview-grid">
          <div class="dashboard-overview-main">
            <div class="dashboard-overview-label">今夜状态</div>
            <h2>{{ systemState.label }}</h2>
            <p>{{ systemState.description }}</p>
          </div>
          <div class="dashboard-overview-side">
            <div class="dashboard-overview-label">下一步</div>
            <strong>{{ nextStep.title }}</strong>
            <div class="muted">{{ nextStep.description }}</div>
          </div>
        </div>
      </div>

      <div class="panel panel-pad stack">
        <div class="settings-section-head">
          <div>
            <h2>站点访问状态</h2>
            <p class="muted">先确认对外入口是否稳定，再决定是否需要排查构建、域名或回源问题。</p>
          </div>
          <div class="button-row">
            <span class="tag" :class="data.domain_status.enabled ? 'tag-success' : 'tag-warning'">
              {{ data.domain_status.enabled ? '域名已启用' : '当前为 IP 模式' }}
            </span>
            <span class="tag">{{ data.domain_status.status || 'unknown' }}</span>
          </div>
        </div>

        <div class="card-row">
          <div class="metric">
            <div class="muted">绑定域名</div>
            <strong>{{ data.domain_status.domain || '未配置' }}</strong>
            <div class="muted">当前公开入口域名。</div>
          </div>
          <div class="metric">
            <div class="muted">公开地址</div>
            <strong>{{ data.domain_status.base_url || '/' }}</strong>
            <div class="muted">对外访问基准路径。</div>
          </div>
          <div class="metric">
            <div class="muted">最近检查</div>
            <strong>{{ formatCheckedAt(data.domain_status.checked_at) }}</strong>
            <div class="muted">域名诊断刷新时间。</div>
          </div>
          <div class="metric">
            <div class="muted">当日点击</div>
            <strong>{{ Number(data.click_stats.today_page_views || 0) }}</strong>
            <div class="muted">今日累计页面访问。</div>
          </div>
        </div>

        <div class="status-banner info">
          {{ data.domain_status.reason || '尚未生成站点访问诊断。' }}
        </div>
      </div>

      <div class="stack" v-if="configWarnings.length">
        <div v-for="item in configWarnings" :key="item" class="status-banner warning">{{ item }}</div>
      </div>

      <div class="card-row">
        <div class="metric dashboard-state-metric">
          <div class="muted">当前系统状态</div>
          <strong>{{ systemState.label }}</strong>
          <div class="muted">{{ systemState.description }}</div>
        </div>
        <StabilityGauge label="人格稳定度" :score="Number(data.persona_stability || 0)" />
        <StabilityGauge label="记忆一致性" :score="Number(data.memory_coherence || 0)" />
        <CostChart
          title="今日精力消耗"
          subtitle="模型调用费用"
          :cost="Number(data.cost?.cost || 0)"
          :limit="Number(data.cost?.limit || 1)"
        />
        <div class="metric dashboard-state-metric">
          <div class="muted">推荐下一步</div>
          <strong>{{ nextStep.title }}</strong>
          <div class="muted">{{ nextStep.description }}</div>
        </div>
      </div>

      <div class="card-row">
        <div class="metric">
          <div class="muted">风险任务总数</div>
          <strong>{{ totalRiskCount }}</strong>
        </div>
        <div class="metric">
          <div class="muted">失败任务</div>
          <strong>{{ data.risk_overview.failed }}</strong>
        </div>
        <div class="metric">
          <div class="muted">QA 熔断</div>
          <strong>{{ data.risk_overview.circuit_open }}</strong>
        </div>
        <div class="metric">
          <div class="muted">待人工签发</div>
          <strong>{{ data.risk_overview.waiting_human_signoff }}</strong>
        </div>
        <div class="metric">
          <div class="muted">最近任务数</div>
          <strong>{{ data.recent_tasks.length }}</strong>
        </div>
      </div>

      <div class="grid two dashboard-columns">
        <div class="panel panel-pad stack">
          <div class="section-title">近期风险提醒</div>

          <AppEmpty
            v-if="!attentionCards.length"
            inline
            title="近期没有明显风险"
            description="最近任务里没有失败、熔断或待人工签发的记录。"
          />

          <div v-else class="list">
            <RouterLink
              v-for="item in attentionCards"
              :key="`${item.kind}-${item.id}`"
              class="list-item stack"
              :to="item.kind === 'task' ? `/admin/tasks/${item.id}` : '/admin/settings'"
            >
              <div class="button-row">
                <span class="tag" :class="item.severity === 'error' ? 'tag-danger' : 'tag-warning'">
                  {{ item.severity === 'error' ? '风险' : '提醒' }}
                </span>
                <span class="tag">{{ attentionLabel(item.label) }}</span>
              </div>
              <strong>{{ item.title }}</strong>
              <div class="muted">{{ item.message }}</div>
            </RouterLink>
          </div>
        </div>

        <div class="panel panel-pad stack">
          <div class="section-title">最近任务</div>

          <AppEmpty
            v-if="!data.recent_tasks.length"
            inline
            title="还没有任务记录"
            description="触发一次生成后，这里会显示最近的任务状态和失败原因。"
          />

          <div v-else class="list">
            <RouterLink
              v-for="task in data.recent_tasks"
              :key="task.id"
              class="list-item stack"
              :to="`/admin/tasks/${task.id}`"
            >
              <div class="split">
                <strong>任务 #{{ task.id }}</strong>
                <span class="tag" :class="getStatusClass('task', task.status)">{{ getStatusLabel('task', task.status) }}</span>
              </div>
              <div class="muted">{{ formatDateTimeWithRelative(task.started_at) }}</div>
              <div class="muted">
                {{ taskPrimaryMessage(task) }}
              </div>
              <div class="button-row">
                <span class="tag" :class="getPublishDecisionClass(task)">{{ getPublishDecisionLabel(task) }}</span>
                <span v-if="task.error_code" class="tag tag-danger">{{ task.error_code }}</span>
                <span v-if="task.qa_risk_level && task.qa_risk_level !== 'unknown'" class="tag">{{ task.qa_risk_level }}</span>
                <span v-if="task.queue_wait_ms" class="tag">{{ formatDurationMs(task.queue_wait_ms) }}</span>
              </div>
            </RouterLink>
          </div>
        </div>
      </div>

      <div class="panel panel-pad stack">
        <div class="section-title">最近文章</div>

        <AppEmpty
          v-if="!data.recent_posts.length"
          inline
          title="还没有文章"
          description="去文章页手动发文或新建文章后，这里会显示最近内容。"
        />

        <div v-else class="list">
          <RouterLink
            v-for="post in data.recent_posts"
            :key="post.id"
            class="list-item stack"
            :to="`/admin/posts/${post.id}`"
          >
            <div class="split">
              <strong>{{ post.title }}</strong>
              <span class="tag" :class="getStatusClass('post', post.status)">{{ getStatusLabel('post', post.status) }}</span>
            </div>
            <div class="muted">Slug: {{ post.slug }}</div>
            <div class="muted">{{ post.summary || '暂无摘要' }}</div>
            <div class="muted">{{ formatDateTimeWithRelative(post.updated_at || post.published_at || post.created_at) }}</div>
          </RouterLink>
        </div>
      </div>
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
import { describeError } from '../utils/errors'
import { getPublishDecisionClass, getPublishDecisionDescription, getPublishDecisionLabel } from '../utils/publishDecision'
import { getStatusClass, getStatusDescription, getStatusLabel } from '../utils/statusMeta'
import { formatDateTimeWithRelative, formatDateTime, formatDurationMs } from '../utils/time'

function createDashboardState() {
  return {
    recent_posts: [],
    recent_tasks: [],
    cost: { cost: 0, limit: 1 },
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
    risk_overview: { failed: 0, circuit_open: 0, waiting_human_signoff: 0 },
    attention_items: [],
    config_status: {
      system_initialized: false,
      llm_ready: false,
      embedding_ready: false,
      domain_enabled: false,
    },
  }
}

const data = reactive(createDashboardState())
const isLoading = ref(true)
const loadError = ref('')
const hasLoadedOnce = ref(false)
const totalRiskCount = computed(
  () => Number(data.risk_overview.failed || 0) + Number(data.risk_overview.circuit_open || 0) + Number(data.risk_overview.waiting_human_signoff || 0),
)
const configConclusionTagClass = computed(() => {
  if (!data.config_status.system_initialized || !data.config_status.llm_ready) return 'tag-danger'
  if (Number(data.risk_overview.failed || 0) > 0 || Number(data.risk_overview.circuit_open || 0) > 0 || Number(data.risk_overview.waiting_human_signoff || 0) > 0) {
    return 'tag-warning'
  }
  return 'tag-success'
})

const systemState = computed(() => {
  if (!data.config_status.system_initialized) {
    return { label: '尚未初始化', description: '请先完成初始化与基础配置。' }
  }
  if (!data.config_status.llm_ready) {
    return { label: '无法自动发文', description: '大脑接入尚未配置完成，自动生成会直接失败。' }
  }
  if (Number(data.risk_overview.waiting_human_signoff || 0) > 0 || Number(data.risk_overview.circuit_open || 0) > 0) {
    return { label: '可降级发文', description: '系统可运行，但存在待签发或熔断风险。' }
  }
  if (Number(data.risk_overview.failed || 0) > 0) {
    return { label: '需先排错', description: '最近已有失败任务，建议先检查原因。' }
  }
  return { label: '可正常发文', description: '当前配置和近期任务状态允许继续发文。' }
})

const nextStep = computed(() => {
  if (!data.config_status.system_initialized) {
    return { title: '先完成初始化', description: '先补齐管理员密码、站点信息和大脑接入配置。' }
  }
  if (!data.config_status.llm_ready) {
    return { title: '先补齐大脑接入配置', description: '去设置页填入接口地址、访问密钥和模型名称。' }
  }
  if (!data.config_status.embedding_ready) {
    return { title: '补齐记忆检索配置', description: '避免检索、去重和相似度判断退化。' }
  }
  if (Number(data.risk_overview.waiting_human_signoff || 0) > 0) {
    return { title: '先审阅待签发稿件', description: '优先检查高风险稿件，再决定是否发布。' }
  }
  if (Number(data.risk_overview.failed || 0) > 0 || Number(data.risk_overview.circuit_open || 0) > 0) {
    return { title: '先排查失败任务', description: '先看失败任务和熔断原因，再继续发文。' }
  }
  return { title: '可以开始今晚写作', description: '当前系统状态稳定，可以触发新的写作任务。' }
})

const configWarnings = computed(() => {
  const warnings = []
  if (!data.config_status.system_initialized) warnings.push('系统尚未完成初始化。')
  if (!data.config_status.llm_ready) warnings.push('大脑接入配置未完成，自动写作会失败。')
  if (!data.config_status.embedding_ready) warnings.push('记忆检索配置未完成，检索与去重会退化。')
  if (!data.config_status.domain_enabled) warnings.push('当前仍处于 IP 模式或域名未启用。')
  return warnings
})

const attentionCards = computed(() => {
  const cards = data.attention_items.map((item) => ({
    kind: 'task',
    id: item.task_id,
    severity: item.severity,
    label: item.label,
    title: `任务 #${item.task_id}`,
    message: item.message,
  }))

  if (!data.config_status.llm_ready) {
    cards.push({
      kind: 'settings',
      id: 'llm',
      severity: 'warning',
      label: '配置缺口',
      title: '大脑接入尚未就绪',
      message: '请在设置页补齐接口地址、访问密钥和模型名称。',
    })
  }
  if (!data.config_status.embedding_ready) {
    cards.push({
      kind: 'settings',
      id: 'embedding',
      severity: 'warning',
      label: '配置缺口',
      title: '记忆检索尚未就绪',
      message: '请在设置页补齐向量服务配置，避免检索和去重退化。',
    })
  }

  return cards.slice(0, 6)
})

function taskTagClass(status) {
  return getStatusClass('task', status)
}

function taskSummary(status) {
  return getStatusDescription('task', status)
}

function attentionLabel(label) {
  if (label === 'legacy_publish_decision') return '历史签发待复核'
  if (label === 'waiting_human_signoff') return '待人工签发'
  return label
}

function formatCheckedAt(value) {
  return formatDateTime(value)
}

function taskPrimaryMessage(task) {
  if (task.error_message) return task.error_message
  if (task.error_code) return task.error_code
  if (task.publish_decision_path && !['manual_post', 'pending'].includes(task.publish_decision_path)) {
    return getPublishDecisionDescription(task)
  }
  return taskSummary(task.status)
}

async function load(showLoading = !hasLoadedOnce.value) {
  if (showLoading) isLoading.value = true
  if (!hasLoadedOnce.value) loadError.value = ''

  try {
    const result = await unwrap(api.get('/dashboard'))
    Object.assign(data, createDashboardState(), result)
    hasLoadedOnce.value = true
    loadError.value = ''
  } catch (error) {
    loadError.value = describeError(error, '加载总览失败，请稍后重试。')
  } finally {
    if (showLoading) isLoading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.dashboard-hero {
  align-items: end;
}

.dashboard-hero-aside {
  display: grid;
  gap: 10px;
  justify-items: end;
  text-align: right;
}

.dashboard-overview-card {
  gap: 22px;
}

.dashboard-overview-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(300px, 0.8fr);
  gap: 20px;
  align-items: stretch;
}

.dashboard-overview-main,
.dashboard-overview-side {
  position: relative;
  display: grid;
  gap: 12px;
  padding: 24px;
  border-radius: 16px;
  border: 1px solid rgba(155, 176, 198, 0.14);
  background:
    linear-gradient(180deg, rgba(220, 230, 240, 0.04), transparent 100%),
    rgba(12, 16, 24, 0.62);
}

.dashboard-overview-main::before,
.dashboard-overview-side::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: inherit;
  background:
    radial-gradient(circle at top right, rgba(216, 229, 240, 0.08), transparent 22%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.02), transparent 40%);
}

.dashboard-overview-main h2,
.dashboard-overview-side strong {
  margin: 0;
  font-family: var(--font-display);
  letter-spacing: 0.08em;
}

.dashboard-overview-main h2 {
  font-size: clamp(1.6rem, 2.8vw, 2.4rem);
}

.dashboard-overview-main p,
.dashboard-overview-side .muted {
  margin: 0;
  line-height: 1.8;
}

.dashboard-overview-label {
  color: var(--accent-soft);
  font-size: 0.76rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
}

.dashboard-overview-side strong {
  font-size: 1.14rem;
}

.dashboard-state-metric strong {
  font-size: 1.58rem;
}

@media (max-width: 960px) {
  .dashboard-hero-aside {
    justify-items: start;
    text-align: left;
  }

  .dashboard-overview-grid {
    grid-template-columns: 1fr;
  }
}
</style>
