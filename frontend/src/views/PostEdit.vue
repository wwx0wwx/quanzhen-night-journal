<template>
  <section class="stack">
    <AppLoading
      v-if="isLoading"
      :title="t('postEdit.loadingTitle')"
      :description="t('postEdit.loadingDesc')"
    />

    <AppError
      v-else-if="loadError"
      :title="t('postEdit.loadError')"
      :message="loadError"
      :action-label="t('common.retry')"
      @retry="load"
    />

    <template v-else>
      <div class="hero editor-hero">
        <div>
          <h1>{{ isNew ? t('postEdit.newTitle') : t('postEdit.editTitle', { id: route.params.id }) }}</h1>
          <p>{{ t('postEdit.subtitle') }}</p>
        </div>
        <div class="button-row">
          <button
            class="btn primary"
            :disabled="actionBusy"
            :data-tooltip="t('postEdit.tooltips.save')"
            @click="save"
          >
            {{ isSaving ? t('common.saving') : t('common.save') }}
          </button>
          <button
            v-if="!isNew"
            class="btn ghost"
            :disabled="actionBusy"
            :data-tooltip="t('postEdit.tooltips.publish')"
            @click="runWorkflowAction('publish')"
          >
            {{ activeAction === 'publish' ? t('postEdit.publishing') : t('postEdit.actions.publish') }}
          </button>
          <button
            v-if="!isNew"
            class="btn ghost"
            :disabled="actionBusy"
            :data-tooltip="t('postEdit.tooltips.approve')"
            @click="runWorkflowAction('approve')"
          >
            {{ activeAction === 'approve' ? t('common.busy') : t('postEdit.actions.approve') }}
          </button>
          <button
            v-if="!isNew"
            class="btn ghost"
            :disabled="actionBusy"
            :data-tooltip="t('postEdit.tooltips.archive')"
            @click="runWorkflowAction('archive')"
          >
            {{ activeAction === 'archive' ? t('common.busy') : t('postEdit.actions.archive') }}
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

      <div class="grid two editor-layout">
        <div class="panel panel-pad stack editor-panel">
          <label class="field">
            <span>{{ t('postEdit.fields.title') }}</span>
            <input
              v-model="form.title"
              :placeholder="t('postEdit.placeholders.title')"
            >
          </label>
          <label class="field">
            <span>Slug</span>
            <input
              v-model="form.slug"
              :placeholder="t('postEdit.placeholders.slug')"
            >
          </label>
          <label class="field">
            <span>{{ t('postEdit.fields.summary') }}</span>
            <textarea
              v-model="form.summary"
              :placeholder="t('postEdit.placeholders.summary')"
            />
          </label>
          <label class="field">
            <span>{{ t('common.status') }}</span>
            <select v-model="form.status">
              <option
                v-for="item in POST_STATUS_OPTIONS"
                :key="item"
                :value="item"
              >
                {{ getStatusLabel('post', item) }}
              </option>
            </select>
          </label>
          <label class="field">
            <span>{{ t('postEdit.fields.body') }}</span>
            <textarea
              v-model="form.content_markdown"
              class="editor-textarea"
              :placeholder="t('postEdit.placeholders.body')"
            />
          </label>
        </div>

        <div class="stack">
          <div class="panel panel-pad stack editor-info-card">
            <div class="section-title">
              {{ t('postEdit.infoTitle') }}
            </div>
            <dl class="meta-grid">
              <div>
                <dt>{{ t('postEdit.meta.status') }}</dt>
                <dd>{{ getStatusLabel('post', form.status) }}</dd>
              </div>
              <div>
                <dt>{{ t('postEdit.meta.source') }}</dt>
                <dd>{{ post.task_id ? t('postEdit.source.auto') : t('postEdit.source.manual') }}</dd>
              </div>
              <div>
                <dt>{{ t('postEdit.meta.updated') }}</dt>
                <dd>{{ formatDateTimeWithRelative(post.updated_at) }}</dd>
              </div>
              <div>
                <dt>{{ t('postEdit.meta.published') }}</dt>
                <dd>{{ formatDateTimeWithRelative(post.published_at) }}</dd>
              </div>
              <div>
                <dt>{{ t('postEdit.meta.revision') }}</dt>
                <dd>#{{ post.revision || 1 }}</dd>
              </div>
            </dl>
          </div>

          <div class="panel panel-pad stack editor-preview-card">
            <div class="section-title">
              {{ t('postEdit.previewTitle') }}
            </div>
            <div
              v-if="form.summary"
              class="status-banner info"
            >
              {{ form.summary }}
            </div>
            <article
              class="preview-content"
              v-html="previewHtml"
            />
          </div>

          <div
            v-if="!isNew"
            class="panel panel-pad stack"
          >
            <div class="split">
              <div>
                <div class="section-title">
                  {{ t('postEdit.revisionsTitle') }}
                </div>
                <div class="muted">
                  {{ t('postEdit.revisionsDesc') }}
                </div>
              </div>
              <button
                class="btn ghost btn-small"
                type="button"
                :disabled="isRevisionsLoading"
                @click="loadRevisions"
              >
                {{ isRevisionsLoading ? t('postEdit.refreshing') : t('common.refresh') }}
              </button>
            </div>

            <AppEmpty
              v-if="!revisions.length && !isRevisionsLoading"
              inline
              :title="t('postEdit.emptyRevisionsTitle')"
              :description="t('postEdit.emptyRevisionsDesc')"
            />

            <div
              v-else
              class="list revision-list"
            >
              <div
                v-for="revision in revisions"
                :key="revision.id"
                class="list-item revision-card"
                :class="{ active: selectedRevisionId === revision.id }"
              >
                <div class="split">
                  <div
                    class="stack"
                    style="gap: 6px"
                  >
                    <strong>{{ t('postEdit.revisionN', { n: revision.revision }) }}</strong>
                    <div class="muted">
                      {{ formatDateTimeWithRelative(revision.created_at) }}
                    </div>
                    <div class="muted">
                      {{ revision.change_reason || t('postEdit.noChangeReason') }}
                    </div>
                  </div>
                  <div class="button-row">
                    <button
                      class="btn ghost btn-small"
                      type="button"
                      @click="selectedRevisionId = revision.id"
                    >
                      {{ t('postEdit.viewRevision') }}
                    </button>
                    <button
                      class="btn ghost btn-small"
                      type="button"
                      :disabled="activeAction === `revert:${revision.revision}`"
                      @click="revertRevision(revision)"
                    >
                      {{ activeAction === `revert:${revision.revision}` ? t('postEdit.reverting') : t('postEdit.revertToRevision') }}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div
              v-if="selectedRevision"
              class="stack"
            >
              <div class="section-title">
                {{ t('postEdit.revisionContent', { n: selectedRevision.revision }) }}
              </div>
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
import { useI18n } from 'vue-i18n'

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
const { t } = useI18n()
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
const previewHtml = computed(() => DOMPurify.sanitize(markdown.render(form.content_markdown || t('postEdit.emptyBody'))))
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
    message.value = describeError(error, t('postEdit.revisionsLoadFailed'))
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
    loadError.value = describeError(error, t('postEdit.loadFailed'))
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
      message.value = t('postEdit.created')
      await router.replace(`/admin/posts/${data.id}`)
      await load()
      return
    }

    const data = await unwrap(api.put(`/posts/${route.params.id}`, form))
    applyPost(data)
    messageType.value = 'success'
    message.value = t('postEdit.saved')
    formDirty.value = false
    await loadRevisions()
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, t('postEdit.saveFailed'))
  } finally {
    isSaving.value = false
  }
}

function actionLabel(action) {
  if (action === 'publish') return t('postEdit.actions.publish')
  if (action === 'approve') return t('postEdit.actions.approve')
  return t('postEdit.actions.archive')
}

async function runWorkflowAction(action) {
  if (activeAction.value) return
  if (!window.confirm(t('postEdit.confirmAction', { action: actionLabel(action) }))) return

  activeAction.value = action
  message.value = ''
  try {
    const data = await unwrap(api.post(`/posts/${route.params.id}/${action}`))
    applyPost(data)
    messageType.value = 'success'
    message.value = t('postEdit.actionDone', { action: actionLabel(action) })
    await loadRevisions()
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, t('postEdit.actionFailed', { action: actionLabel(action) }))
  } finally {
    activeAction.value = ''
  }
}

async function revertRevision(revision) {
  if (activeAction.value) return
  if (!window.confirm(t('postEdit.confirmRevert', { n: revision.revision }))) return

  activeAction.value = `revert:${revision.revision}`
  message.value = ''
  try {
    const data = await unwrap(api.post(`/posts/${route.params.id}/revert/${revision.revision}`))
    applyPost(data)
    messageType.value = 'success'
    message.value = t('postEdit.reverted', { n: revision.revision })
    await loadRevisions()
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, t('postEdit.revertFailed'))
  } finally {
    activeAction.value = ''
  }
}

onMounted(async () => {
  await load()
  await nextTick()
  watch(
    form,
    () => {
      formDirty.value = true
    },
    { deep: true },
  )
})

onBeforeRouteLeave(() => {
  if (formDirty.value) {
    return window.confirm(t('common.unsavedLeave'))
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
