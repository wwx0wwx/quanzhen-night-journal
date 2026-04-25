<template>
  <section class="stack">
    <div class="hero posts-hero">
      <div>
        <div class="hero-kicker">Manuscript Registry</div>
        <h1>文章管理</h1>
        <p>这里像夜间卷宗台一样整理稿件、生成任务与发布动作，先判断每篇稿件的状态，再决定是否继续推进。</p>
      </div>
      <div class="button-row posts-hero-actions">
        <button
          class="btn primary"
          type="button"
          :disabled="actionBusy"
          data-tooltip="运行一次 AI 创作流程"
          @click="triggerTask"
        >
          {{ isTriggering ? '创作中…' : '立即创作' }}
        </button>
        <button class="btn ghost" type="button" :disabled="isLoading" @click="load">刷新列表</button>
        <RouterLink class="btn primary" to="/admin/posts/new" data-tooltip="手动新建一篇文章草稿">
          新建文章
        </RouterLink>
        <button class="btn ghost" type="button" :disabled="actionBusy" data-tooltip="暂停自动创作，不再触发定时任务" @click="hibernate">
          {{ isHibernating ? '处理中…' : '立即休眠' }}
        </button>
        <button class="btn ghost" type="button" :disabled="actionBusy" data-tooltip="恢复自动创作调度" @click="wakeUp">
          {{ isWakingUp ? '处理中…' : '解除休眠' }}
        </button>
      </div>
    </div>

    <form class="panel panel-pad toolbar posts-toolbar" @submit.prevent="load">
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
      <div class="panel panel-pad posts-ledger-meta">
        <div>
          <div class="hero-kicker">Registry Count</div>
          <strong>共 {{ total }} 篇，第 {{ page }} / {{ totalPages }} 页，当前显示 {{ posts.length }} 篇。</strong>
        </div>
        <div class="muted">主操作优先处理“待审核 / 可发布 / 失败待排查”的稿件，其余状态可延后整理。</div>
      </div>

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

              <div class="stack post-card-heading" style="gap: 8px;">
                <div class="post-card-kicker">卷宗 #{{ post.id }}</div>
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
              <div class="post-card-actions-label">处置动作</div>
              <RouterLink class="btn ghost btn-small" :to="`/admin/posts/${post.id}`">编辑</RouterLink>
              <RouterLink v-if="post.task_id" class="btn ghost btn-small" :to="`/admin/tasks/${post.task_id}`">
                查看任务
              </RouterLink>
              <button
                v-if="canPublish(post)"
                class="btn primary btn-small"
                type="button"
                :disabled="!!activeActionKey"
                data-tooltip="将文章直接发布到博客站点"
                @click="runAction(post, 'publish')"
              >
                {{ actionLabel(post, 'publish', '发布') }}
              </button>
              <button
                v-if="canApprove(post)"
                class="btn ghost btn-small"
                type="button"
                :disabled="!!activeActionKey"
                data-tooltip="标记内容已审核，但暂不发布"
                @click="runAction(post, 'approve')"
              >
                {{ actionLabel(post, 'approve', '审核通过') }}
              </button>
              <button
                v-if="canArchive(post)"
                class="btn ghost btn-small"
                type="button"
                :disabled="!!activeActionKey"
                data-tooltip="将文章从博客站点移除并归档"
                @click="runAction(post, 'archive')"
              >
                {{ actionLabel(post, 'archive', '归档') }}
              </button>
            </div>
          </div>
        </article>
      </div>

      <div class="panel panel-pad split">
        <div class="muted">第 {{ page }} / {{ totalPages }} 页，共 {{ total }} 篇</div>
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
const page = ref(1)
const pageSize = 20
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
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

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
  page.value = 1
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
          page: page.value,
          page_size: pageSize,
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

function changePage(nextPage) {
  if (nextPage < 1 || nextPage > totalPages.value) return
  page.value = nextPage
  load()
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

<style scoped>
.posts-hero {
  align-items: end;
}

.posts-hero-actions {
  justify-content: flex-end;
}

.posts-toolbar {
  margin-bottom: 4px;
}

.posts-ledger-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.posts-ledger-meta strong {
  display: block;
  font-family: var(--font-display);
  font-size: 1.08rem;
  letter-spacing: 0.06em;
}

.post-card {
  background: var(--panel-strong);
}

.post-card-heading {
  position: relative;
}

.post-card-kicker,
.post-card-actions-label {
  color: var(--accent-soft);
  font-size: 0.72rem;
  letter-spacing: 0.24em;
  text-transform: uppercase;
}

.post-card-actions {
  min-width: 138px;
  flex-direction: column;
  align-items: stretch;
}

.post-title-link {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.post-summary {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

@media (max-width: 900px) {
  .posts-hero-actions,
  .posts-ledger-meta {
    justify-content: flex-start;
  }
}
</style>
