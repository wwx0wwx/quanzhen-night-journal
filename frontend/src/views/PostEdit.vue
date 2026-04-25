<template>
  <section class="stack">
    <AppLoading
      v-if="isLoading"
      title="正在加载文章"
      description="正在读取正文、元信息和修订历史。"
    />

    <AppError
      v-else-if="loadError"
      title="文章加载失败"
      :message="loadError"
      action-label="重试"
      @retry="load"
    />

    <template v-else>
      <div class="hero editor-hero">
        <div>
          <div class="hero-kicker">Manuscript Workbench</div>
          <h1>{{ isNew ? '新建文章' : `编辑文章 #${route.params.id}` }}</h1>
          <p>正文、元信息、版本和发布动作都在这张工作台上完成。保持语言冷静、结构清晰，再决定是否送它进入前台。</p>
        </div>
        <div class="button-row">
          <button class="btn primary" :disabled="actionBusy" data-tooltip="仅保存当前内容为草稿，不改变发布状态" @click="save">
            {{ isSaving ? '保存中…' : '保存' }}
          </button>
          <button v-if="!isNew" class="btn ghost" :disabled="actionBusy" data-tooltip="将文章直接发布到博客站点" @click="runWorkflowAction('publish')">
            {{ activeAction === 'publish' ? '发布中…' : '发布' }}
          </button>
          <button v-if="!isNew" class="btn ghost" :disabled="actionBusy" data-tooltip="标记内容已审核，但暂不发布" @click="runWorkflowAction('approve')">
            {{ activeAction === 'approve' ? '处理中…' : '审核通过' }}
          </button>
          <button v-if="!isNew" class="btn ghost" :disabled="actionBusy" data-tooltip="将文章从博客站点移除并归档" @click="runWorkflowAction('archive')">
            {{ activeAction === 'archive' ? '处理中…' : '归档' }}
          </button>
        </div>
      </div>

      <div v-if="message" class="status-banner" :class="messageType">{{ message }}</div>

      <div class="grid two editor-layout">
        <div class="panel panel-pad stack editor-panel">
          <label class="field">
            <span>标题</span>
            <input v-model="form.title" placeholder="给这篇文章一个清晰标题" />
          </label>
          <label class="field">
            <span>Slug</span>
            <input v-model="form.slug" placeholder="留空时会自动生成" />
          </label>
          <label class="field">
            <span>摘要</span>
            <textarea v-model="form.summary" placeholder="为空时系统会根据正文自动提取。"></textarea>
          </label>
          <label class="field">
            <span>状态</span>
            <select v-model="form.status">
              <option v-for="item in POST_STATUS_OPTIONS" :key="item" :value="item">
                {{ getStatusLabel('post', item) }}
              </option>
            </select>
          </label>
          <label class="field">
            <span>正文 Markdown</span>
            <textarea v-model="form.content_markdown" class="editor-textarea" placeholder="在这里编辑正文 Markdown。"></textarea>
          </label>
        </div>

        <div class="stack">
          <div class="panel panel-pad stack editor-info-card">
            <div class="section-title">文章信息</div>
            <dl class="meta-grid">
              <div>
                <dt>当前状态</dt>
                <dd>{{ getStatusLabel('post', form.status) }}</dd>
              </div>
              <div>
                <dt>文章来源</dt>
                <dd>{{ post.task_id ? '自动生成稿' : '手动创建' }}</dd>
              </div>
              <div>
                <dt>最近修改</dt>
                <dd>{{ formatDateTimeWithRelative(post.updated_at) }}</dd>
              </div>
              <div>
                <dt>发布时间</dt>
                <dd>{{ formatDateTimeWithRelative(post.published_at) }}</dd>
              </div>
              <div>
                <dt>当前版本</dt>
                <dd>#{{ post.revision || 1 }}</dd>
              </div>
            </dl>
          </div>

          <div class="panel panel-pad stack editor-preview-card">
            <div class="section-title">Markdown 预览</div>
            <div v-if="form.summary" class="status-banner info">{{ form.summary }}</div>
            <article class="preview-content" v-html="previewHtml"></article>
          </div>

          <div v-if="!isNew" class="panel panel-pad stack">
            <div class="split">
              <div>
                <div class="section-title">修订历史</div>
                <div class="muted">可查看旧版本内容，并按需回滚。</div>
              </div>
              <button class="btn ghost btn-small" type="button" :disabled="isRevisionsLoading" @click="loadRevisions">
                {{ isRevisionsLoading ? '刷新中…' : '刷新' }}
              </button>
            </div>

            <AppEmpty
              v-if="!revisions.length && !isRevisionsLoading"
              inline
              title="还没有修订记录"
              description="首次修改后，这里会记录历史版本。"
            />

            <div v-else class="list revision-list">
              <div
                v-for="revision in revisions"
                :key="revision.id"
                class="list-item revision-card"
                :class="{ active: selectedRevisionId === revision.id }"
              >
                <div class="split">
                  <div class="stack" style="gap: 6px;">
                    <strong>版本 #{{ revision.revision }}</strong>
                    <div class="muted">{{ formatDateTimeWithRelative(revision.created_at) }}</div>
                    <div class="muted">{{ revision.change_reason || '未记录原因' }}</div>
                  </div>
                  <div class="button-row">
                    <button class="btn ghost btn-small" type="button" @click="selectedRevisionId = revision.id">查看内容</button>
                    <button class="btn ghost btn-small" type="button" :disabled="activeAction === `revert:${revision.revision}`" @click="revertRevision(revision)">
                      {{ activeAction === `revert:${revision.revision}` ? '回滚中…' : '回滚到此版' }}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="selectedRevision" class="stack">
              <div class="section-title">版本 #{{ selectedRevision.revision }} 内容</div>
              <pre>{{ selectedRevision.content_markdown }}</pre>
            </div>
          </div>

          <DigitalStamp :stamp="post.digital_stamp" />
        </div>
      </div>
    </template>
  </section>
</template>

<script setup>
import DOMPurify from 'dompurify'
import MarkdownIt from 'markdown-it'
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'

import { api, unwrap } from '../api'
import AppEmpty from '../components/AppEmpty.vue'
import AppError from '../components/AppError.vue'
import AppLoading from '../components/AppLoading.vue'
import DigitalStamp from '../components/DigitalStamp.vue'
import { describeError } from '../utils/errors'
import { POST_STATUS_OPTIONS, getStatusLabel } from '../utils/statusMeta'
import { formatDateTimeWithRelative } from '../utils/time'

const route = useRoute()
const router = useRouter()
const markdown = new MarkdownIt({ html: false, linkify: true, breaks: true })

const isNew = computed(() => !route.params.id)
const post = reactive({})
const form = reactive({
  title: '',
  slug: '',
  summary: '',
  content_markdown: '',
  front_matter: {},
  status: 'draft',
  persona_id: null,
  publish_target: 'hugo',
})
const revisions = ref([])
const selectedRevisionId = ref(null)
const isLoading = ref(true)
const isRevisionsLoading = ref(false)
const loadError = ref('')
const isSaving = ref(false)
const formDirty = ref(false)
const activeAction = ref('')
const message = ref('')
const messageType = ref('info')

const actionBusy = computed(() => isSaving.value || !!activeAction.value)
const previewHtml = computed(() => DOMPurify.sanitize(markdown.render(form.content_markdown || '还没有正文内容。')))
const selectedRevision = computed(() => revisions.value.find((item) => item.id === selectedRevisionId.value) || null)

function applyPost(data) {
  Object.assign(post, data)
  Object.assign(form, {
    title: data.title || '',
    slug: data.slug || '',
    summary: data.summary || '',
    content_markdown: data.content_markdown || '',
    front_matter: data.front_matter || {},
    status: data.status || 'draft',
    persona_id: data.persona_id ?? null,
    publish_target: data.publish_target || 'hugo',
  })
}

async function loadRevisions() {
  if (isNew.value) return
  isRevisionsLoading.value = true
  try {
    revisions.value = await unwrap(api.get(`/posts/${route.params.id}/revisions`))
    selectedRevisionId.value = revisions.value[0]?.id || null
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, '修订历史加载失败。')
  } finally {
    isRevisionsLoading.value = false
  }
}

async function load() {
  isLoading.value = true
  loadError.value = ''
  message.value = ''

  try {
    if (isNew.value) {
      Object.assign(post, { revision: 1, published_at: '', updated_at: '', task_id: null })
      revisions.value = []
      selectedRevisionId.value = null
      return
    }

    const data = await unwrap(api.get(`/posts/${route.params.id}`))
    applyPost(data)
    await loadRevisions()
  } catch (error) {
    loadError.value = describeError(error, '加载文章失败，请稍后重试。')
  } finally {
    isLoading.value = false
  }
}

async function save() {
  if (isSaving.value) return

  isSaving.value = true
  message.value = ''
  try {
    if (isNew.value) {
      const data = await unwrap(api.post('/posts', form))
      applyPost(data)
      messageType.value = 'success'
      message.value = '文章已创建。'
      await router.replace(`/admin/posts/${data.id}`)
      await load()
      return
    }

    const data = await unwrap(api.put(`/posts/${route.params.id}`, form))
    applyPost(data)
    messageType.value = 'success'
    message.value = '文章已保存。'
    formDirty.value = false
    await loadRevisions()
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, '保存文章失败。')
  } finally {
    isSaving.value = false
  }
}

function actionLabel(action) {
  if (action === 'publish') return '发布'
  if (action === 'approve') return '审核通过'
  return '归档'
}

async function runWorkflowAction(action) {
  if (activeAction.value) return
  if (!window.confirm(`确认${actionLabel(action)}这篇文章？`)) return

  activeAction.value = action
  message.value = ''
  try {
    const data = await unwrap(api.post(`/posts/${route.params.id}/${action}`))
    applyPost(data)
    messageType.value = 'success'
    message.value = `文章已${actionLabel(action)}。`
    await loadRevisions()
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, `${actionLabel(action)}失败。`)
  } finally {
    activeAction.value = ''
  }
}

async function revertRevision(revision) {
  if (activeAction.value) return
  if (!window.confirm(`确认回滚到版本 #${revision.revision}？当前正文会被覆盖。`)) return

  activeAction.value = `revert:${revision.revision}`
  message.value = ''
  try {
    const data = await unwrap(api.post(`/posts/${route.params.id}/revert/${revision.revision}`))
    applyPost(data)
    messageType.value = 'success'
    message.value = `已回滚到版本 #${revision.revision}。`
    await loadRevisions()
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, '回滚失败。')
  } finally {
    activeAction.value = ''
  }
}

onMounted(async () => {
  await load()
  await nextTick()
  watch(form, () => { formDirty.value = true }, { deep: true })
})

onBeforeRouteLeave(() => {
  if (formDirty.value) {
    return window.confirm('有未保存的修改，确定要离开吗？')
  }
})
</script>

<style scoped>
.editor-hero {
  align-items: end;
}

.editor-info-card,
.editor-preview-card {
  background: var(--panel);
}
</style>
