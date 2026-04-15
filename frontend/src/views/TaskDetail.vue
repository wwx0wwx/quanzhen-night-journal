<template>
  <section class="stack">
    <AppLoading
      v-if="isLoading"
      title="正在加载任务"
      description="正在读取任务状态、轨迹和 Trace。"
    />

    <AppError
      v-else-if="loadError"
      title="任务加载失败"
      :message="loadError"
      action-label="重试"
      @retry="load"
    />

    <template v-else>
      <div class="hero task-hero">
        <div>
          <div class="hero-kicker">Execution Trace</div>
          <h1>任务 #{{ route.params.id }}</h1>
          <p>这里查看一次写作任务从触发到结束的全部轨迹。先判断是否稳，再决定是人工签发还是直接中止。</p>
        </div>
        <div class="button-row">
          <button class="btn primary" :disabled="actionBusy" @click="approve">
            {{ activeAction === 'approve' ? '处理中…' : '人工签发' }}
          </button>
          <button class="btn ghost" :disabled="actionBusy" @click="abort">
            {{ activeAction === 'abort' ? '处理中…' : '终止任务' }}
          </button>
        </div>
      </div>

      <div v-if="message" class="status-banner" :class="messageType">{{ message }}</div>

      <div class="grid two">
        <TaskTimeline :status="task.status || 'queued'" />

        <div class="panel panel-pad stack task-summary-card">
          <div class="section-title">任务摘要</div>
          <div class="button-row">
            <span class="tag" :class="getStatusClass('task', task.status)">{{ getStatusLabel('task', task.status) }}</span>
            <span class="tag" :class="getPublishDecisionClass(task)">{{ getPublishDecisionLabel(task) }}</span>
            <span v-if="task.error_code" class="tag tag-danger">{{ task.error_code }}</span>
          </div>
          <dl class="meta-grid">
            <div>
              <dt>来源</dt>
              <dd>{{ task.trigger_source || 'manual' }}</dd>
            </div>
            <div>
                  <dt>人格设定</dt>
              <dd>{{ task.persona_id ? `#${task.persona_id}` : '-' }}</dd>
            </div>
            <div>
              <dt>关联文章</dt>
              <dd>
                <RouterLink v-if="task.post_id" :to="`/admin/posts/${task.post_id}`">#{{ task.post_id }}</RouterLink>
                <span v-else>-</span>
              </dd>
            </div>
            <div>
              <dt>开始时间</dt>
              <dd>{{ formatDateTimeWithRelative(task.started_at) }}</dd>
            </div>
            <div>
              <dt>结束时间</dt>
              <dd>{{ formatDateTimeWithRelative(task.finished_at) }}</dd>
            </div>
            <div>
              <dt>排队等待</dt>
              <dd>{{ formatDurationMs(task.queue_wait_ms) }}</dd>
            </div>
          </dl>
          <div class="muted">{{ taskPrimaryMessage }}</div>
        </div>
      </div>

      <div v-if="task.error_message" class="status-banner error">
        {{ task.error_message }}
      </div>

      <details class="panel panel-pad trace-panel">
        <summary class="trace-summary">
          <span class="section-title">Trace JSON</span>
          <span class="muted">默认折叠，只在排查问题时展开。</span>
        </summary>
        <pre>{{ traceText }}</pre>
      </details>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'

import { api, unwrap } from '../api'
import AppError from '../components/AppError.vue'
import AppLoading from '../components/AppLoading.vue'
import TaskTimeline from '../components/TaskTimeline.vue'
import { describeError } from '../utils/errors'
import { getPublishDecisionClass, getPublishDecisionDescription, getPublishDecisionLabel } from '../utils/publishDecision'
import { getStatusClass, getStatusDescription, getStatusLabel } from '../utils/statusMeta'
import { formatDateTimeWithRelative, formatDurationMs } from '../utils/time'

const route = useRoute()
const task = reactive({})
const isLoading = ref(true)
const loadError = ref('')
const activeAction = ref('')
const message = ref('')
const messageType = ref('info')

const actionBusy = computed(() => !!activeAction.value)
const traceText = computed(() => JSON.stringify(task.trace || {}, null, 2))
const taskPrimaryMessage = computed(() => {
  if (task.error_message) return task.error_message
  if (task.error_code) return task.error_code
  if (task.publish_decision_path && !['manual_post', 'pending'].includes(task.publish_decision_path)) {
    return getPublishDecisionDescription(task)
  }
  return getStatusDescription('task', task.status)
})

async function load() {
  isLoading.value = true
  loadError.value = ''

  try {
    Object.assign(task, await unwrap(api.get(`/tasks/${route.params.id}`)))
  } catch (error) {
    loadError.value = describeError(error, '任务加载失败，请稍后重试。')
  } finally {
    isLoading.value = false
  }
}

async function approve() {
  if (activeAction.value) return
  if (!window.confirm('确认人工签发这个任务，并允许它继续发布？')) return

  activeAction.value = 'approve'
  message.value = ''
  try {
    await unwrap(api.post(`/tasks/${route.params.id}/approve`, { publish_immediately: true }))
    messageType.value = 'success'
    message.value = '任务已人工签发。'
    await load()
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, '人工签发失败。')
  } finally {
    activeAction.value = ''
  }
}

async function abort() {
  if (activeAction.value) return
  if (!window.confirm('确认终止这个任务？终止后需要重新触发。')) return

  activeAction.value = 'abort'
  message.value = ''
  try {
    await unwrap(api.post(`/tasks/${route.params.id}/abort`))
    messageType.value = 'success'
    message.value = '任务已终止。'
    await load()
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, '终止任务失败。')
  } finally {
    activeAction.value = ''
  }
}

onMounted(load)
</script>

<style scoped>
.task-hero {
  align-items: end;
}

.task-summary-card {
  background:
    linear-gradient(180deg, rgba(232, 238, 245, 0.03), transparent 100%),
    rgba(10, 14, 21, 0.76);
}
</style>
