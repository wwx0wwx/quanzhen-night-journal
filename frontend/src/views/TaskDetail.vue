<template>
  <section class="stack">
    <AppLoading
      v-if="isLoading"
      :title="t('tasks.loadingTitle')"
      :description="t('tasks.loadingDesc')"
    />

    <AppError
      v-else-if="loadError"
      :title="t('tasks.loadError')"
      :message="loadError"
      :action-label="t('common.retry')"
      @retry="load"
    />

    <template v-else>
      <div class="hero task-hero">
        <div>
          <h1>{{ t('taskDetail.title', { id: route.params.id }) }}</h1>
          <p>{{ t('taskDetail.subtitle') }}</p>
        </div>
        <div class="button-row">
          <button
            v-if="task.status === 'waiting_human_signoff'"
            class="btn primary"
            :disabled="actionBusy"
            data-tooltip="确认高风险内容安全后放行发布"
            @click="approve"
          >
            {{ activeAction === 'approve' ? t('common.busy') : t('taskDetail.approve') }}
          </button>
          <button
            v-if="canAbort"
            class="btn ghost"
            :disabled="actionBusy"
            data-tooltip="强制中止当前任务，需重新触发才能继续"
            @click="abort"
          >
            {{ activeAction === 'abort' ? t('common.busy') : t('taskDetail.abort') }}
          </button>
          <button
            v-if="isFailedOrCircuitOpen"
            class="btn ghost"
            :disabled="actionBusy"
            data-tooltip="标记为已知悉，总览页将不再提示此任务"
            @click="dismiss"
          >
            {{ activeAction === 'dismiss' ? t('common.busy') : t('taskDetail.dismiss') }}
          </button>
          <button
            v-if="isFailedOrCircuitOpen"
            class="btn ghost"
            :disabled="actionBusy"
            data-tooltip="用同一角色设定重新写一次"
            @click="retry"
          >
            {{ activeAction === 'retry' ? t('common.busy') : t('taskDetail.retry') }}
          </button>
        </div>
      </div>

      <div
        v-if="message"
        class="status-banner"
        :class="messageType"
      >
        {{ message }}
      </div>

      <div class="grid two">
        <TaskTimeline :status="task.status || 'queued'" />

        <div class="panel panel-pad stack task-summary-card">
          <div class="section-title">
            {{ t('taskDetail.summary') }}
          </div>
          <div class="button-row">
            <span
              class="tag"
              :class="getStatusClass('task', task.status)"
            >{{
              getStatusLabel('task', task.status)
            }}</span>
            <span
              v-if="showPublishDecision"
              class="tag"
              :class="getPublishDecisionClass(task)"
            >{{
              getPublishDecisionLabel(task)
            }}</span>
            <span
              v-if="task.error_code"
              class="tag tag-danger"
            >{{
              describeErrorCode(task.error_code) || task.error_code
            }}</span>
          </div>
          <dl class="meta-grid">
            <div>
              <dt>{{ t('taskDetail.source') }}</dt>
              <dd>{{ task.trigger_source || 'manual' }}</dd>
            </div>
            <div>
              <dt>{{ t('posts.persona') }}</dt>
              <dd>{{ task.persona_id ? `#${task.persona_id}` : '-' }}</dd>
            </div>
            <div>
              <dt>{{ t('taskDetail.post') }}</dt>
              <dd>
                <RouterLink
                  v-if="task.post_id"
                  :to="`/admin/posts/${task.post_id}`"
                >
                  #{{ task.post_id }}
                </RouterLink>
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
          <div class="muted">
            {{ taskPrimaryMessage }}
          </div>
        </div>
      </div>

      <div
        v-if="task.error_message"
        class="status-banner error"
      >
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
import { useI18n } from 'vue-i18n'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { confirmAction } from '../composables/useConfirm'
const { t } = useI18n()

import { api, unwrap } from '../api'
import AppError from '../components/AppError.vue'
import AppLoading from '../components/AppLoading.vue'
import TaskTimeline from '../components/TaskTimeline.vue'
import { describeError, describeErrorCode } from '../utils/errors'
import {
  getPublishDecisionClass,
  getPublishDecisionDescription,
  getPublishDecisionLabel,
} from '../utils/publishDecision'
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
const TERMINAL_STATES = ['published', 'failed', 'circuit_open', 'aborted', 'draft_saved']
const isFailedOrCircuitOpen = computed(() => ['failed', 'circuit_open'].includes(task.status) && !task.acknowledged_at)
const canAbort = computed(() => !TERMINAL_STATES.includes(task.status))
const showPublishDecision = computed(() => {
  const path = task.publish_decision_path
  if (!path || path === 'pending') return false
  if (path === 'blocked' && TERMINAL_STATES.includes(task.status)) return false
  return true
})
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
  const ok = await confirmAction({
    title: t('signoff.approve'),
    message: t('confirm.danger'),
    confirmLabel: t('signoff.approve'),
    danger: true,
  })
  if (!ok) return
  return approveInner()
}
async function approveInner() {
  if (activeAction.value) return

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

async function dismiss() {
  if (activeAction.value) return
  activeAction.value = 'dismiss'
  message.value = ''
  try {
    await unwrap(api.post(`/tasks/${route.params.id}/dismiss`))
    messageType.value = 'success'
    message.value = '已标记为已知悉，总览页将不再提示此任务。'
    await load()
  } catch (err) {
    messageType.value = 'error'
    message.value = describeError(err, '操作失败。')
  } finally {
    activeAction.value = ''
  }
}

async function retry() {
  if (activeAction.value) return
  activeAction.value = 'retry'
  message.value = ''
  try {
    const payload = task.persona_id ? { persona_id: task.persona_id } : {}
    const result = await unwrap(api.post('/tasks/trigger', payload))
    messageType.value = 'success'
    message.value = `已重新触发任务 #${result.id}。`
  } catch (err) {
    messageType.value = 'error'
    message.value = describeError(err, '重新触发失败。')
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
  background: var(--panel);
}
</style>
