<template>
  <section class="stack">
    <div class="hero">
      <div>
        <h1>文章管理</h1>
        <p>这里负责查看文章、手动开始写作，以及控制自动写作是暂停还是恢复。</p>
      </div>
      <div class="button-row">
        <button
          class="btn primary"
          type="button"
          :disabled="actionBusy"
          title="运行一次 AI 创作流程"
          @click="triggerTask"
        >
          {{ isTriggering ? '创作中…' : '立即创作' }}
        </button>
        <button class="btn ghost" type="button" :disabled="isLoading" @click="load">刷新列表</button>
        <RouterLink class="btn primary" to="/admin/posts/new" title="手动新建一篇文章草稿">
          新建文章
        </RouterLink>
        <button class="btn ghost" type="button" :disabled="actionBusy" @click="hibernate">
          {{ isHibernating ? '处理中…' : '立即休眠' }}
        </button>
        <button class="btn ghost" type="button" :disabled="actionBusy" @click="wakeUp">
          {{ isWakingUp ? '处理中…' : '解除休眠' }}
        </button>
      </div>
    </div>

    <form class="toolbar" @submit.prevent="load">
      <label class="field">
        <span>状态筛选</span>
        <select v-model="status" :disabled="isLoading">
          <option value="">全部</option>
          <option v-for="item in POST_STATUS_OPTIONS" :key="item" :value="item">
            {{ getStatusLabel('post', item) }}
          </option>
        </select>
      </label>
      <label class="field">
        <span>搜索</span>
        <input v-model.trim="keyword" :disabled="isLoading" placeholder="标题、slug、摘要" />
      </label>
      <label class="field">
        <span>排序</span>
        <select v-model="sort" :disabled="isLoading">
          <option value="updated_desc">最近更新优先</option>
          <option value="published_desc">最近发布优先</option>
          <option value="created_desc">最近创建优先</option>
          <option value="updated_asc">最早更新优先</option>
        </select>
      </label>
      <div class="button-row toolbar-actions">
        <button class="btn primary" type="submit" :disabled="isLoading">应用筛选</button>
        <button class="btn ghost" type="button" :disabled="isLoading" @click="resetFilters">清空</button>
      </div>
    </form>

    <div class="stack" v-if="actionError || actionSuccess">
      <div v-if="actionError" class="status-banner error">{{ actionError }}</div>
      <div v-if="actionSuccess" class="status-banner success">{{ actionSuccess }}</div>
    </div>

    <AppLoading
      v-if="isLoading"
      title="正在加载文章"
      description="正在汇总文章、审核状态和关联任务信息。"
    />

    <AppError
      v-else-if="loadError"
      title="文章列表加载失败"
      :message="loadError"
      action-label="重试"
      @retry="load"
    />

    <AppEmpty
      v-else-if="!posts.length"
      title="还没有文章"
      description="可以先手动新建一篇，或直接在这里触发一次自动生成。"
      action-label="新建文章"
      @action="router.push('/admin/posts/new')"
    />

    <template v-else>
      <div class="muted">共 {{ total }} 篇，当前显示 {{ posts.length }} 篇。</div>

      <div class="list">
        <article v-for="post in posts" :key="post.id" class="panel panel-pad stack post-card">
          <div class="split">
            <div class="stack post-card-main">
              <div class="button-row">
                <span class="tag" :class="getStatusClass('post', post.status)">
                  {{ getStatusLabel('post', post.status) }}
                </span>
                <span v-if="post.task_id" class="tag" :class="getPublishDecisionClass(post)">
                  {{ getPublishDecisionLabel(post) }}
                </span>
                <span v-if="post.review_reason" class="tag tag-warning">{{ getReviewReasonLabel(post.review_reason) }}</span>
                <span v-if="post.task_error_code" class="tag tag-danger">{{ post.task_error_code }}</span>
                <span v-if="post.qa_risk_level && post.qa_risk_level !== 'unknown'" class="tag">
                  {{ post.qa_risk_level }}
                </span>
              </div>

              <div class="stack" style="gap: 8px;">
                <RouterLink class="post-title-link" :to="`/admin/posts/${post.id}`">
                  {{ post.title || `未命名文章 #${post.id}` }}
                </RouterLink>
                <div class="muted">Slug: {{ post.slug || '-' }}</div>
              </div>

              <div class="post-summary">
                {{ post.summary || '暂无摘要，可进入编辑页补充。' }}
              </div>

              <dl class="meta-grid">
                <div>
                  <dt>来源</dt>
                  <dd>{{ post.task_id ? '自动生成' : '手动创建' }}</dd>
                </div>
                <div>
                  <dt>人格设定</dt>
                  <dd>{{ personaName(post.persona_id) }}</dd>
                </div>
                <div>
                  <dt>任务</dt>
                  <dd>
                    <RouterLink v-if="post.task_id" :to="`/admin/tasks/${post.task_id}`">#{{ post.task_id }}</RouterLink>
                    <span v-else>-</span>
                  </dd>
                </div>
                <div>
                  <dt>任务状态</dt>
                  <dd>{{ post.task_status ? getStatusLabel('task', post.task_status) : '-' }}</dd>
                </div>
                <div>
                  <dt>发布时间</dt>
                  <dd>{{ formatDateTimeWithRelative(post.published_at) }}</dd>
                </div>
                <div>
                  <dt>更新时间</dt>
                  <dd>{{ formatDateTimeWithRelative(post.updated_at) }}</dd>
                </div>
                <div>
                  <dt>排队等待</dt>
                  <dd>{{ formatDurationMs(post.queue_wait_ms) }}</dd>
                </div>
              </dl>

              <div v-if="post.task_id" class="muted">
                发布判定：{{ getPublishDecisionDescription(post) }}
              </div>

              <div v-if="post.human_approved && !post.human_approval_recorded" class="status-banner warning">
                这篇已发布稿件的人工签发路径来自历史记录推断，建议复核一次。
              </div>

              <div v-if="post.task_error_message" class="status-banner error">
                {{ post.task_error_message }}
              </div>
            </div>

            <div class="button-row post-card-actions">
              <RouterLink class="btn ghost btn-small" :to="`/admin/posts/${post.id}`">编辑</RouterLink>
              <RouterLink v-if="post.task_id" class="btn ghost btn-small" :to="`/admin/tasks/${post.task_id}`">
                查看任务
              </RouterLink>
              <button
                v-if="canPublish(post)"
                class="btn primary btn-small"
                type="button"
                :disabled="!!activeActionKey"
                @click="runAction(post, 'publish')"
              >
                {{ actionLabel(post, 'publish', '发布') }}
              </button>
              <button
                v-if="canApprove(post)"
                class="btn ghost btn-small"
                type="button"
                :disabled="!!activeActionKey"
                @click="runAction(post, 'approve')"
              >
                {{ actionLabel(post, 'approve', '审核通过') }}
              </button>
              <button
                v-if="canArchive(post)"
                class="btn ghost btn-small"
                type="button"
                :disabled="!!activeActionKey"
                @click="runAction(post, 'archive')"
              >
                {{ actionLabel(post, 'archive', '归档') }}
              </button>
            </div>
          </div>
        </article>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { api, unwrap } from '../api'
import AppEmpty from '../components/AppEmpty.vue'
import AppError from '../components/AppError.vue'
import AppLoading from '../components/AppLoading.vue'
import { describeError } from '../utils/errors'
import { getPublishDecisionClass, getPublishDecisionDescription, getPublishDecisionLabel } from '../utils/publishDecision'
import { POST_STATUS_OPTIONS, getReviewReasonLabel, getStatusClass, getStatusLabel } from '../utils/statusMeta'
import { formatDateTimeWithRelative, formatDurationMs } from '../utils/time'

const router = useRouter()
const posts = ref([])
const total = ref(0)
const status = ref('')
const keyword = ref('')
const sort = ref('updated_desc')
const personas = ref([])
const isLoading = ref(true)
const loadError = ref('')
const activeActionKey = ref('')
const actionError = ref('')
const actionSuccess = ref('')
const isTriggering = ref(false)
const isHibernating = ref(false)
const isWakingUp = ref(false)

const actionBusy = computed(() => !!activeActionKey.value || isTriggering.value || isHibernating.value || isWakingUp.value)

function personaName(personaId) {
  if (!personaId) return '未指定'
  return personas.value.find((item) => item.id === personaId)?.name || `#${personaId}`
}

function canPublish(post) {
  return ['draft', 'approved', 'pending_review', 'publish_failed'].includes(post.status)
}

function canApprove(post) {
  return ['draft', 'pending_review'].includes(post.status)
}

function canArchive(post) {
  return post.status !== 'archived'
}

function actionLabel(post, action, idleLabel) {
  return activeActionKey.value === `${action}:${post.id}` ? `${idleLabel}中…` : idleLabel
}

function resetFilters() {
  status.value = ''
  keyword.value = ''
  sort.value = 'updated_desc'
  load()
}

function confirmMessage(post, action) {
  if (action === 'publish') return `确认发布《${post.title}》？`
  if (action === 'approve') return `确认将《${post.title}》标记为审核通过？`
  return `确认归档《${post.title}》？归档后它会退出主列表。`
}

async function load() {
  isLoading.value = true
  loadError.value = ''

  try {
    const [postData, personaData] = await Promise.all([
      unwrap(api.get('/posts', {
        params: {
          status: status.value || undefined,
          q: keyword.value || undefined,
          sort: sort.value,
          page_size: 100,
        },
      })),
      personas.value.length ? Promise.resolve(personas.value) : unwrap(api.get('/personas')),
    ])
    posts.value = postData.items || []
    total.value = postData.total || 0
    personas.value = personaData || []
  } catch (error) {
    loadError.value = describeError(error, '加载文章列表失败，请稍后重试。')
  } finally {
    isLoading.value = false
  }
}

async function runAction(post, action) {
  if (actionBusy.value) return
  if (!window.confirm(confirmMessage(post, action))) return

  actionError.value = ''
  actionSuccess.value = ''
  activeActionKey.value = `${action}:${post.id}`

  try {
    await unwrap(api.post(`/posts/${post.id}/${action}`))
    const label = action === 'publish' ? '发布' : action === 'approve' ? '审核通过' : '归档'
    actionSuccess.value = `文章《${post.title}》已${label}。`
    await load()
  } catch (error) {
    actionError.value = describeError(error, '文章操作失败，请稍后重试。')
  } finally {
    activeActionKey.value = ''
  }
}

async function triggerTask() {
  if (actionBusy.value) return

  actionError.value = ''
  actionSuccess.value = ''
  isTriggering.value = true
  try {
    const result = await unwrap(api.post('/tasks/trigger', { trigger_source: 'manual', semantic_hint: '请开始今晚的写作' }))
    actionSuccess.value = `写作任务 #${result.id} 已开始。`
    await load()
  } catch (error) {
    actionError.value = describeError(error, '触发任务失败，请稍后重试。')
  } finally {
    isTriggering.value = false
  }
}

async function hibernate() {
  if (actionBusy.value) return

  actionError.value = ''
  actionSuccess.value = ''
  isHibernating.value = true
  try {
    await unwrap(api.post('/cost/hibernate'))
    actionSuccess.value = '系统已进入休眠，自动写作会先暂停。'
  } catch (error) {
    actionError.value = describeError(error, '进入休眠失败，请稍后重试。')
  } finally {
    isHibernating.value = false
  }
}

async function wakeUp() {
  if (actionBusy.value) return

  actionError.value = ''
  actionSuccess.value = ''
  isWakingUp.value = true
  try {
    await unwrap(api.post('/cost/wake-up'))
    actionSuccess.value = '系统已恢复写作。'
  } catch (error) {
    actionError.value = describeError(error, '解除休眠失败，请稍后重试。')
  } finally {
    isWakingUp.value = false
  }
}

onMounted(load)
</script>
