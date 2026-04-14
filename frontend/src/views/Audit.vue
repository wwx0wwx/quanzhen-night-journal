<template>
  <section class="stack">
    <AppLoading
      v-if="isLoading"
      title="正在加载系统日志"
      description="正在获取审计日志与筛选结果。"
    />

    <AppError
      v-else-if="loadError"
      title="系统日志加载失败"
      :message="loadError"
      action-label="重新加载"
      @retry="load"
    />

    <template v-else>
      <div class="hero">
        <div>
          <h1>系统日志</h1>
          <p>查看审计记录、筛选严重级别，并导出当前筛选结果。</p>
        </div>
        <div class="button-row">
          <button class="btn ghost" :disabled="isLoading" @click="exportCurrent">导出当前结果</button>
        </div>
      </div>

      <div class="panel panel-pad toolbar">
        <label class="field">
          <span>严重级别</span>
          <select v-model="filters.severity">
            <option value="">全部</option>
            <option value="info">info</option>
            <option value="warning">warning</option>
            <option value="critical">critical</option>
          </select>
        </label>
        <label class="field">
          <span>动作关键字</span>
          <input v-model="filters.action" placeholder="例如 task.status_change" />
        </label>
        <div class="button-row">
          <button class="btn primary" :disabled="isLoading" @click="applyFilters">筛选</button>
          <button class="btn ghost" :disabled="isLoading" @click="resetFilters">重置</button>
        </div>
      </div>

      <AppEmpty
        v-if="!items.length"
        title="还没有日志记录"
        description="当前筛选条件下没有可展示的审计日志。"
      />

      <div v-else class="list">
        <div v-for="item in items" :key="item.id" class="list-item panel stack">
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
              <dt>加工后事件</dt>
              <dd class="processed-event">{{ item.processed_event || '-' }}</dd>
            </div>
            <div>
              <dt>来源 IP</dt>
              <dd>{{ item.ip_address || '-' }}</dd>
            </div>
          </dl>

          <pre class="code-block">{{ prettyDetail(item.detail) }}</pre>
        </div>
      </div>

      <div class="panel panel-pad split">
        <div class="muted">第 {{ page }} / {{ totalPages }} 页，共 {{ total }} 条</div>
        <div class="button-row">
          <button class="btn ghost btn-small" :disabled="page <= 1 || isLoading" @click="changePage(page - 1)">上一页</button>
          <button class="btn ghost btn-small" :disabled="page >= totalPages || isLoading" @click="changePage(page + 1)">下一页</button>
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
import { describeError } from '../utils/errors'

const filters = reactive({
  severity: '',
  action: '',
})
const items = ref([])
const isLoading = ref(true)
const loadError = ref('')
const page = ref(1)
const pageSize = 20
const total = ref(0)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

function severityClass(severity) {
  if (severity === 'critical') return 'tag-danger'
  if (severity === 'warning') return 'tag-warning'
  return 'tag-success'
}

function prettyDetail(detail) {
  return JSON.stringify(detail || {}, null, 2)
}

async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    const params = {
      page: page.value,
      page_size: pageSize,
    }
    if (filters.severity) params.severity = filters.severity
    if (filters.action) params.action = filters.action
    const data = await unwrap(api.get('/audit', { params }))
    items.value = data.items || []
    total.value = Number(data.total || 0)
  } catch (error) {
    loadError.value = describeError(error, '加载系统日志失败。')
  } finally {
    isLoading.value = false
  }
}

function applyFilters() {
  page.value = 1
  load()
}

function resetFilters() {
  filters.severity = ''
  filters.action = ''
  page.value = 1
  load()
}

function changePage(nextPage) {
  if (nextPage < 1 || nextPage > totalPages.value) return
  page.value = nextPage
  load()
}

function exportCurrent() {
  const blob = new Blob([JSON.stringify(items.value, null, 2)], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `audit-page-${page.value}.json`
  link.click()
  URL.revokeObjectURL(url)
}

onMounted(load)
</script>

<style scoped>
.processed-event {
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
