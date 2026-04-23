<template>
  <section class="stack">
    <div class="hero tasks-hero">
      <div>
        <div class="hero-kicker">Execution Ledger</div>
        <h1>任务列表</h1>
        <p>所有写作任务的运行记录。从这里查看执行状态、排查异常、进入单条任务的 Trace 详情。</p>
      </div>
      <div class="button-row">
        <button class="btn ghost" type="button" :disabled="isLoading" @click="load">刷新列表</button>
      </div>
    </div>

    <form class="panel panel-pad toolbar tasks-toolbar" @submit.prevent="load">
      <label class="field">
        <span>状态筛选</span>
        <select v-model="status" :disabled="isLoading">
          <option value="">全部</option>
          <option v-for="item in TASK_STATUS_OPTIONS" :key="item" :value="item">
            {{ getStatusLabel('task', item) }}
          </option>
        </select>
      </label>
      <div class="button-row toolbar-actions">
        <button class="btn primary" type="submit" :disabled="isLoading">应用筛选</button>
        <button class="btn ghost" type="button" :disabled="isLoading" @click="resetFilters">清空</button>
      </div>
    </form>

    <AppLoading
      v-if="isLoading"
      title="正在加载任务"
      description="正在汇总任务执行记录与关联文章状态。"
    />

    <AppError
      v-else-if="loadError"
      title="任务列表加载失败"
      :message="loadError"
      action-label="重试"
      @retry="load"
    />

    <AppEmpty
      v-else-if="!tasks.length"
      title="还没有任务记录"
      description="触发一次自动创作或手动创建文章后，任务会出现在这里。"
    />

    <template v-else>
      <div class="panel panel-pad tasks-ledger-meta">
        <div>
          <div class="hero-kicker">Ledger Count</div>
          <strong>共 {{ total }} 条，第 {{ page }} / {{ totalPages }} 页，当前显示 {{ tasks.length }} 条。</strong>
        </div>
      </div>

      <div class="list">
        <article v-for="task in tasks" :key="task.id" class="panel panel-pad stack task-card">
          <div class="split">
            <div class="stack task-card-main">
              <div class="button-row">
                <span class="tag" :class="getStatusClass('task', task.status)">
                  {{ getStatusLabel('task', task.status) }}
                </span>
                <span class="tag" :class="getPublishDecisionClass(task)">
                  {{ getPublishDecisionLabel(task) }}
                </span>
                <span v-if="task.error_code" class="tag tag-danger">{{ task.error_code }}</span>
              </div>

              <div class="stack" style="gap: 4px;">
                <div class="task-card-kicker">任务 #{{ task.id }}</div>
                <div class="muted">{{ getStatusDescription('task', task.status) }}</div>
              </div>

              <dl class="meta-grid">
                <div>
                  <dt>来源</dt>
                  <dd>{{ task.trigger_source || '-' }}</dd>
                </div>
                <div>
                  <dt>人格</dt>
                  <dd>{{ task.persona_id ? `#${task.persona_id}` : '-' }}</dd>
                </div>
                <div>
                  <dt>文章</dt>
                  <dd>
                    <RouterLink v-if="task.post_id" :to="`/admin/posts/${task.post_id}`">#{{ task.post_id }}</RouterLink>
                    <span v-else>-</span>
                  </dd>
                </div>
                <div>
                  <dt>开始</dt>
                  <dd>{{ formatDateTimeWithRelative(task.started_at) }}</dd>
                </div>
                <div>
                  <dt>结束</dt>
                  <dd>{{ formatDateTimeWithRelative(task.finished_at) }}</dd>
                </div>
                <div>
                  <dt>排队</dt>
                  <dd>{{ formatDurationMs(task.queue_wait_ms) }}</dd>
                </div>
              </dl>

              <div v-if="task.error_message" class="status-banner error">{{ task.error_message }}</div>
            </div>

            <div class="button-row task-card-actions">
              <div class="task-card-actions-label">操作</div>
              <RouterLink class="btn ghost btn-small" :to="`/admin/tasks/${task.id}`">查看详情</RouterLink>
              <RouterLink v-if="task.post_id" class="btn ghost btn-small" :to="`/admin/posts/${task.post_id}`">查看文章</RouterLink>
            </div>
          </div>
        </article>
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
import { computed, onMounted, ref } from 'vue'

import { api, unwrap } from '../api'
import AppEmpty from '../components/AppEmpty.vue'
import AppError from '../components/AppError.vue'
import AppLoading from '../components/AppLoading.vue'
import { describeError } from '../utils/errors'
import { getPublishDecisionClass, getPublishDecisionLabel } from '../utils/publishDecision'
import { getStatusClass, getStatusDescription, getStatusLabel } from '../utils/statusMeta'
import { formatDateTimeWithRelative, formatDurationMs } from '../utils/time'

const TASK_STATUS_OPTIONS = [
  'queued', 'preparing_context', 'generating', 'qa_checking',
  'rewrite_pending', 'waiting_human_signoff', 'ready_to_publish',
  'publishing', 'published', 'failed', 'circuit_open', 'aborted', 'draft_saved',
]

const tasks = ref([])
const total = ref(0)
const status = ref('')
const page = ref(1)
const pageSize = 20
const isLoading = ref(true)
const loadError = ref('')

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

function resetFilters() {
  status.value = ''
  page.value = 1
  load()
}

async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    const data = await unwrap(api.get('/tasks', {
      params: {
        status: status.value || undefined,
        page: page.value,
        page_size: pageSize,
      },
    }))
    tasks.value = data.items || []
    total.value = data.total || 0
  } catch (error) {
    loadError.value = describeError(error, '加载任务列表失败，请稍后重试。')
  } finally {
    isLoading.value = false
  }
}

function changePage(nextPage) {
  if (nextPage < 1 || nextPage > totalPages.value) return
  page.value = nextPage
  load()
}

onMounted(load)
</script>

<style scoped>
.tasks-hero {
  align-items: end;
}

.tasks-toolbar {
  margin-bottom: 4px;
}

.tasks-ledger-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.tasks-ledger-meta strong {
  display: block;
  font-family: var(--font-display);
  font-size: 1.08rem;
  letter-spacing: 0.06em;
}

.task-card {
  background:
    linear-gradient(180deg, rgba(232, 238, 245, 0.035), transparent 100%),
    linear-gradient(145deg, rgba(13, 17, 24, 0.94), rgba(8, 11, 17, 0.98));
}

.task-card-kicker,
.task-card-actions-label {
  color: var(--accent-soft);
  font-size: 0.72rem;
  letter-spacing: 0.24em;
  text-transform: uppercase;
}

.task-card-actions {
  min-width: 138px;
  flex-direction: column;
  align-items: stretch;
}
</style>
