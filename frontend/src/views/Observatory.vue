<template>
  <section class="stack">
    <AppLoading
      v-if="isLoading"
      title="正在加载观测中心"
      description="正在汇总健康状态、感知历史和系统日志。"
    />

    <AppError
      v-else-if="loadError"
      title="观测中心加载失败"
      :message="loadError"
      action-label="重新加载"
      @retry="loadAll"
    />

    <template v-else>
      <div class="stack" v-if="panelMessage">
        <div class="status-banner" :class="panelMessageType">{{ panelMessage }}</div>
      </div>

      <div class="hero">
        <div>
          <h1>观测中心</h1>
          <p>把系统健康、感知变化和系统日志收进同一个工作台，减少来回切页。</p>
        </div>
        <div class="button-row">
          <button class="btn primary" type="button" @click="loadAll">刷新全部</button>
          <button class="btn ghost" type="button" @click="setPanel('overview')">回到概览</button>
        </div>
      </div>

      <div class="panel panel-pad stack">
        <div class="segmented-tabs" role="tablist" aria-label="观测中心面板">
          <button
            v-for="panel in panels"
            :key="panel.id"
            class="segmented-tab"
            :class="{ active: activePanel === panel.id }"
            type="button"
            @click="setPanel(panel.id)"
          >
            {{ panel.label }}
          </button>
        </div>
        <div class="muted">{{ activePanelMeta.description }}</div>
      </div>

      <template v-if="activePanel === 'overview'">
        <div class="card-row">
          <StabilityGauge label="人格稳定度" :score="Number(health.persona_stability || 0)" />
          <StabilityGauge label="记忆一致性" :score="Number(health.memory_coherence || 0)" />
          <CostChart
            title="今日精力消耗"
            subtitle="模型调用费用"
            :cost="Number(health.cost?.cost || 0)"
            :limit="Number(health.cost?.limit || 1)"
          />
          <div class="metric">
            <div class="muted">最新感知</div>
            <strong>{{ current.translated_text || '暂无数据' }}</strong>
            <div class="muted">{{ latestSensoryMeta }}</div>
          </div>
        </div>

        <div class="grid two">
          <MemoryTree :memories="memories" :personas="personas" />
          <TaskTimeline :status="task.status || 'queued'" />
        </div>

        <div class="grid two">
          <div class="panel panel-pad stack">
            <div class="split">
              <div>
                <div class="section-title">最近事件</div>
                <div class="muted">展示最新进入系统的外部事件和语义归一化结果。</div>
              </div>
              <button class="btn ghost btn-small" type="button" @click="setPanel('sensory')">展开感知面板</button>
            </div>
            <AppEmpty
              v-if="!events.length"
              inline
              title="还没有事件记录"
              description="重新采样或等待外部事件进入后，这里会出现最近记录。"
            />
            <div v-else class="list">
              <div v-for="item in events.slice(0, 5)" :key="item.id" class="list-item">
                <strong>{{ item.event_type }}</strong>
                <div class="muted">{{ item.normalized_semantic || '暂无语义摘要' }}</div>
              </div>
            </div>
          </div>

          <div class="panel panel-pad stack">
            <div class="split">
              <div>
                <div class="section-title">最近日志</div>
                <div class="muted">优先看 warning / critical，快速判断是否需要排障。</div>
              </div>
              <button class="btn ghost btn-small" type="button" @click="setPanel('audit')">展开日志面板</button>
            </div>
            <AppEmpty
              v-if="!auditItems.length"
              inline
              title="当前没有日志"
              description="当前页还没有可展示的审计记录。"
            />
            <div v-else class="list">
              <div v-for="item in auditItems.slice(0, 5)" :key="item.id" class="list-item">
                <div class="split">
                  <strong>{{ item.action }}</strong>
                  <span class="tag" :class="severityClass(item.severity)">{{ item.severity }}</span>
                </div>
                <div class="muted">{{ item.timestamp }}</div>
                <div class="muted">{{ briefDetail(item.detail) }}</div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <template v-else-if="activePanel === 'sensory'">
        <div class="hero panel panel-pad observatory-inline-hero">
          <div>
            <h2>感知与事件</h2>
            <p>这里集中查看当前快照、最近历史和外部事件记录。</p>
          </div>
          <button class="btn primary" type="button" @click="runSensoryRefresh">重新采样</button>
        </div>

        <div class="grid two">
          <div class="panel panel-pad">
            <div class="section-title">当前感知</div>
            <div class="list-item">
              <strong>{{ current.translated_text || '暂无感知结果' }}</strong>
              <div class="muted">标签：{{ (current.tags || []).join(' / ') || '无' }}</div>
              <div class="muted">CPU {{ current.cpu_percent ?? '-' }} / MEM {{ current.memory_percent ?? '-' }}</div>
            </div>
          </div>
          <SensoryChart :items="history.slice(0, 12)" />
        </div>

        <div class="grid two">
          <div class="panel panel-pad">
            <div class="section-title">感知历史</div>
            <div class="list">
              <div v-for="item in history.slice(0, 10)" :key="item.id" class="list-item">
                <strong>{{ item.sampled_at }}</strong>
                <div class="muted">{{ (item.tags || []).join(' / ') || '无标签' }}</div>
              </div>
            </div>
          </div>
          <div class="panel panel-pad">
            <div class="section-title">最近事件</div>
            <div class="list">
              <div v-for="item in events.slice(0, 10)" :key="item.id" class="list-item">
                <strong>{{ item.event_type }}</strong>
                <div class="muted">{{ item.normalized_semantic || '暂无语义摘要' }}</div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <template v-else>
        <div class="hero panel panel-pad observatory-inline-hero">
          <div>
            <h2>系统日志</h2>
            <p>把筛选、翻页和导出留在这里，避免单独开一个低频页面。</p>
          </div>
          <button class="btn ghost" type="button" @click="exportCurrentAudit">导出当前结果</button>
        </div>

        <div class="panel panel-pad toolbar">
          <label class="field">
            <span>严重级别</span>
            <select v-model="auditFilters.severity">
              <option value="">全部</option>
              <option value="info">info</option>
              <option value="warning">warning</option>
              <option value="critical">critical</option>
            </select>
          </label>
          <label class="field">
            <span>动作关键字</span>
            <input v-model="auditFilters.action" placeholder="例如 task.status_change" />
          </label>
          <div class="button-row toolbar-actions">
            <button class="btn primary" type="button" @click="applyAuditFilters">筛选</button>
            <button class="btn ghost" type="button" @click="resetAuditFilters">重置</button>
          </div>
        </div>

        <AppEmpty
          v-if="!auditItems.length"
          title="还没有日志记录"
          description="当前筛选条件下没有可展示的审计日志。"
        />

        <div v-else class="list">
          <div v-for="item in auditItems" :key="item.id" class="list-item panel stack">
            <div class="split">
              <div>
                <strong>{{ item.action }}</strong>
                <div class="muted">{{ item.timestamp }}</div>
              </div>
              <div class="button-row">
                <span class="tag">{{ item.actor || 'system' }}</span>
                <span class="tag" :class="severityClass(item.severity)">{{ item.severity }}</span>
              </div>
            </div>

            <dl class="meta-grid">
              <div>
                <dt>目标</dt>
                <dd>{{ item.target_type || '-' }} #{{ item.target_id || '-' }}</dd>
              </div>
              <div>
                <dt>来源 IP</dt>
                <dd>{{ item.ip_address || '-' }}</dd>
              </div>
            </dl>

            <pre class="code-block">{{ JSON.stringify(item.detail || {}, null, 2) }}</pre>
          </div>
        </div>

        <div class="panel panel-pad split">
          <div class="muted">第 {{ auditPage }} / {{ auditTotalPages }} 页，共 {{ auditTotal }} 条</div>
          <div class="button-row">
            <button class="btn ghost btn-small" :disabled="auditPage <= 1" @click="changeAuditPage(auditPage - 1)">上一页</button>
            <button class="btn ghost btn-small" :disabled="auditPage >= auditTotalPages" @click="changeAuditPage(auditPage + 1)">下一页</button>
          </div>
        </div>
      </template>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api, unwrap } from '../api'
import AppEmpty from '../components/AppEmpty.vue'
import AppError from '../components/AppError.vue'
import AppLoading from '../components/AppLoading.vue'
import CostChart from '../components/CostChart.vue'
import MemoryTree from '../components/MemoryTree.vue'
import SensoryChart from '../components/SensoryChart.vue'
import StabilityGauge from '../components/StabilityGauge.vue'
import TaskTimeline from '../components/TaskTimeline.vue'
import { describeError } from '../utils/errors'

const route = useRoute()
const router = useRouter()

const panels = [
  { id: 'overview', label: '概览', description: '保留最常用的健康、任务和最近信号，适合日常巡检。' },
  { id: 'sensory', label: '感知与事件', description: '查看当前感知、历史采样和外部事件，不再单独拆页。' },
  { id: 'audit', label: '系统日志', description: '筛选审计日志、翻页和导出，作为观察类低频能力收纳。' },
]

const health = reactive({})
const current = reactive({})
const task = reactive({})
const personas = ref([])
const memories = ref([])
const history = ref([])
const events = ref([])
const auditItems = ref([])
const auditTotal = ref(0)
const auditPage = ref(1)
const auditPageSize = 20
const panelMessage = ref('')
const panelMessageType = ref('info')
const auditFilters = reactive({
  severity: '',
  action: '',
})
const isLoading = ref(true)
const loadError = ref('')

const activePanel = computed(() => {
  const panel = String(route.query.panel || 'overview')
  return panels.some((item) => item.id === panel) ? panel : 'overview'
})

const activePanelMeta = computed(() => panels.find((item) => item.id === activePanel.value) || panels[0])
const latestSensoryMeta = computed(() => {
  const tags = (current.tags || []).join(' / ')
  if (!tags && current.cpu_percent == null && current.memory_percent == null) return '最近还没有感知数据。'
  return `标签 ${tags || '无'}，CPU ${current.cpu_percent ?? '-'} / MEM ${current.memory_percent ?? '-'}`
})
const auditTotalPages = computed(() => Math.max(1, Math.ceil(auditTotal.value / auditPageSize)))

function setPanel(panel) {
  const query = panel === 'overview' ? {} : { panel }
  router.replace({ path: '/admin/observatory', query })
}

function severityClass(severity) {
  if (severity === 'critical') return 'tag-danger'
  if (severity === 'warning') return 'tag-warning'
  return 'tag-success'
}

function briefDetail(detail) {
  const text = JSON.stringify(detail || {})
  return text.length > 88 ? `${text.slice(0, 88)}...` : text
}

async function refreshOverviewData() {
  const [healthData, memoryData, personaData, taskData] = await Promise.all([
    unwrap(api.get('/health/dashboard')),
    unwrap(api.get('/memories', { params: { page_size: 100 } })),
    unwrap(api.get('/personas')),
    unwrap(api.get('/tasks')),
  ])
  Object.assign(health, healthData)
  memories.value = memoryData.items || []
  personas.value = personaData || []
  Object.assign(task, (taskData.items || [])[0] || {})
}

async function refreshSensory() {
  const [currentData, historyData, eventData] = await Promise.all([
    unwrap(api.get('/sensory/current')),
    unwrap(api.get('/sensory/history')),
    unwrap(api.get('/events')),
  ])
  Object.assign(current, currentData)
  history.value = historyData || []
  events.value = eventData.items || []
}

async function loadAudit() {
  const params = {
    page: auditPage.value,
    page_size: auditPageSize,
  }
  if (auditFilters.severity) params.severity = auditFilters.severity
  if (auditFilters.action) params.action = auditFilters.action

  const data = await unwrap(api.get('/audit', { params }))
  auditItems.value = data.items || []
  auditTotal.value = Number(data.total || 0)
}

async function loadAll() {
  isLoading.value = true
  loadError.value = ''
  panelMessage.value = ''
  try {
    await Promise.all([refreshOverviewData(), refreshSensory(), loadAudit()])
  } catch (error) {
    loadError.value = describeError(error, '加载观测中心失败，请稍后重试。')
  } finally {
    isLoading.value = false
  }
}

async function runAuditLoad(fallback) {
  try {
    panelMessage.value = ''
    await loadAudit()
  } catch (error) {
    panelMessageType.value = 'error'
    panelMessage.value = describeError(error, fallback)
  }
}

async function runSensoryRefresh() {
  try {
    panelMessage.value = ''
    await refreshSensory()
    panelMessageType.value = 'success'
    panelMessage.value = '感知与事件已刷新。'
  } catch (error) {
    panelMessageType.value = 'error'
    panelMessage.value = describeError(error, '刷新感知与事件失败。')
  }
}

function applyAuditFilters() {
  auditPage.value = 1
  runAuditLoad('加载筛选后的系统日志失败。')
}

function resetAuditFilters() {
  auditFilters.severity = ''
  auditFilters.action = ''
  auditPage.value = 1
  runAuditLoad('重置系统日志筛选失败。')
}

function changeAuditPage(nextPage) {
  if (nextPage < 1 || nextPage > auditTotalPages.value) return
  auditPage.value = nextPage
  runAuditLoad('切换系统日志页码失败。')
}

function exportCurrentAudit() {
  const blob = new Blob([JSON.stringify(auditItems.value, null, 2)], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `observatory-audit-page-${auditPage.value}.json`
  link.click()
  URL.revokeObjectURL(url)
}

watch(() => route.query.panel, (value) => {
  const panel = String(value || 'overview')
  if (!panels.some((item) => item.id === panel)) {
    setPanel('overview')
  }
})

onMounted(loadAll)
</script>
