<template>
  <section class="stack">
    <AppLoading
      v-if="isLoading"
      title="正在加载设置"
      description="正在获取系统配置，请稍候。"
    />

    <AppError
      v-else-if="loadError"
      title="设置页加载失败"
      :message="loadError"
      action-label="重新加载"
      @retry="load"
    />

    <template v-else>
      <div class="hero settings-hero">
        <div>
          <div class="hero-kicker">Configuration Ledger</div>
          <h1>系统设置</h1>
          <p>把站点、面板、大脑接入与发文节奏统一收束在这本配置簿里。优先确保结论清晰，其次才是字段本身。</p>
        </div>
        <div class="settings-toolbar">
          <div class="button-row">
            <button class="btn primary" :disabled="isBusy || !isDirty" @click="save">
              {{ isSaving ? '保存中...' : '保存配置' }}
            </button>
          </div>
          <div class="button-row">
            <span class="tag" :class="isDirty ? 'tag-warning' : 'tag-success'">
              {{ isDirty ? '有未保存修改' : '当前已同步' }}
            </span>
          </div>
        </div>
      </div>

      <div class="stack" v-if="saveError || saveSuccess || testError || testSuccess || isDirty">
        <div v-if="saveError" class="status-banner error">{{ saveError }}</div>
        <div v-if="testError" class="status-banner error">{{ testError }}</div>
        <div v-if="saveSuccess" class="status-banner success">{{ saveSuccess }}</div>
        <div v-if="testSuccess" class="status-banner success">{{ testSuccess }}</div>
        <div v-if="isDirty" class="status-banner warning">当前表单有未保存修改，离开页面前请确认是否需要保存。</div>
      </div>

      <AppEmpty
        v-if="!settingsSections.length"
        title="没有可展示的配置"
        description="当前前端 schema 没有定义任何可编辑字段。"
      />

      <template v-else>
        <div class="panel panel-pad config-summary-card settings-summary-card">
          <div class="settings-section-head">
            <div>
              <h2>当前发文结论</h2>
              <p class="muted">根据当前表单内容判断系统是否具备发文能力。</p>
            </div>
            <div class="button-row">
              <span class="tag" :class="configConclusion.className">{{ configConclusion.label }}</span>
            </div>
          </div>

          <div class="card-row">
            <div class="metric">
              <div class="muted">当前状态</div>
              <strong>{{ configConclusion.label }}</strong>
              <div class="muted">{{ configConclusion.description }}</div>
            </div>
            <div class="metric">
              <div class="muted">大脑接入</div>
              <strong>{{ llmReady ? '已配置' : '未配置' }}</strong>
              <div class="muted">{{ llmReady ? '可用于生成正文。' : '缺少后无法生成文章。' }}</div>
            </div>
            <div class="metric">
              <div class="muted">记忆检索</div>
              <strong>{{ embeddingReady ? '已配置' : '未配置' }}</strong>
              <div class="muted">{{ embeddingReady ? '检索与去重可正常工作。' : '未配置会导致检索、去重与记忆能力退化。' }}</div>
            </div>
            <div class="metric">
              <div class="muted">自动发文</div>
              <strong>{{ automationReady ? '已开启' : '未开启' }}</strong>
              <div class="muted">{{ automationReady ? '可按计划自动触发。' : '当前更适合手动发文。' }}</div>
            </div>
          </div>
        </div>

        <SettingsSection
          v-for="section in settingsSections"
          :key="section.id"
          :disabled="isBusy"
          :section="section"
          :values="formValues"
          @update="updateField"
        >
          <template #actions="{ section }">
            <button
              v-if="section.id === 'llm'"
              class="btn ghost btn-small"
              :disabled="isBusy"
              type="button"
              @click="testLLM"
            >
              {{ isTestingLLM ? '测试中...' : '测试大脑接入' }}
            </button>
            <button
              v-if="section.id === 'embedding'"
              class="btn ghost btn-small"
              :disabled="isBusy"
              type="button"
              @click="testEmbedding"
            >
              {{ isTestingEmbedding ? '测试中...' : '测试记忆检索' }}
            </button>
          </template>
        </SettingsSection>

      </template>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'

import { api, unwrap } from '../api'
import AppEmpty from '../components/AppEmpty.vue'
import AppError from '../components/AppError.vue'
import AppLoading from '../components/AppLoading.vue'
import SettingsSection from '../components/settings/SettingsSection.vue'
import { settingFields, settingsSections } from '../config/settingsSchema'
import { describeError } from '../utils/errors'

const formValues = reactive({})
const fieldMeta = reactive({})

const isLoading = ref(true)
const loadError = ref('')
const isSaving = ref(false)
const saveError = ref('')
const saveSuccess = ref('')
const isTestingLLM = ref(false)
const isTestingEmbedding = ref(false)
const testError = ref('')
const testSuccess = ref('')
const initialSnapshot = ref('{}')
const hasLoaded = ref(false)

const isDirty = computed(() => hasLoaded.value && createSnapshot() !== initialSnapshot.value)
const isBusy = computed(() => isSaving.value || isTestingLLM.value || isTestingEmbedding.value)
const llmReady = computed(() => hasValue('llm.base_url') && hasValue('llm.model_id') && hasSecretValue('llm.api_key'))
const embeddingReady = computed(() => hasValue('embedding.base_url') && hasValue('embedding.model_id') && hasSecretValue('embedding.api_key'))
const automationReady = computed(() => (
  Number(formValues['schedule.days_per_cycle'] || 0) > 0 &&
  Number(formValues['schedule.posts_per_cycle'] || 0) > 0 &&
  isClockValue(formValues['schedule.publish_time'])
))
const configConclusion = computed(() => {
  if (!hasValue('site.title') || !llmReady.value) {
    return {
      label: '完全不可用',
      description: '缺少站点标题或大脑接入配置，系统无法正常生成文章。',
      className: 'tag-danger',
    }
  }
  if (!automationReady.value) {
    return {
      label: '仅可手动发文',
      description: '当前没有自动发文计划，但仍可手动触发生成和发布。',
      className: 'tag-warning',
    }
  }
  if (!embeddingReady.value) {
    return {
      label: '发文能力受限',
      description: '自动发文仍可运行，但检索、去重和记忆相关能力会退化。',
      className: 'tag-warning',
    }
  }
  return {
    label: '可正常自动发文',
    description: '博客信息、大脑接入、记忆检索和发文节奏已达到自动发文要求。',
    className: 'tag-success',
  }
})

function hasValue(key) {
  return String(formValues[key] ?? '').trim() !== ''
}

function hasSecretValue(key) {
  const value = String(formValues[key] ?? '').trim()
  return value !== ''
}

function isClockValue(value) {
  return /^\d{2}:\d{2}$/.test(String(value || '').trim())
}

function inferCategory(key) {
  const prefix = key.split('.')[0]
  const categoryMap = {
    site: 'site',
    panel: 'panel',
    llm: 'llm',
    embedding: 'embedding',
    schedule: 'schedule',
    budget: 'budget',
    qa: 'qa',
    webhook: 'webhook',
    notify: 'notify',
    anti_perfection: 'anti_perfection',
    sensory: 'sensory',
    hugo: 'hugo',
  }
  return categoryMap[prefix] || 'general'
}

function normalizeValue(field, rawValue) {
  if ((rawValue === undefined || rawValue === null) && Object.prototype.hasOwnProperty.call(field, 'defaultValue')) {
    return field.defaultValue
  }
  if (field.type === 'boolean') {
    const value = String(rawValue ?? '').trim().toLowerCase()
    return ['1', 'true', 'yes', 'on'].includes(value)
  }
  return rawValue ?? ''
}

function serializeValue(field, value) {
  if (field.type === 'boolean') {
    return value ? '1' : '0'
  }
  if (value === null || value === undefined) {
    return ''
  }
  return String(value)
}

function createSnapshot() {
  const snapshot = {}
  for (const field of settingFields) {
    snapshot[field.key] = serializeValue(field, formValues[field.key])
  }
  return JSON.stringify(snapshot)
}

function buildItems() {
  const initialValues = JSON.parse(initialSnapshot.value || '{}')
  return settingFields
    .filter((field) => serializeValue(field, formValues[field.key]) !== (initialValues[field.key] ?? ''))
    .map((field) => ({
      key: field.key,
      value: serializeValue(field, formValues[field.key]),
      category: fieldMeta[field.key]?.category || inferCategory(field.key),
      encrypted: Boolean(fieldMeta[field.key]?.encrypted),
    }))
}

function buildProviderPayload(prefix) {
  return {
    base_url: serializeValue({ type: 'url' }, formValues[`${prefix}.base_url`]),
    api_key: serializeValue({ type: 'secret' }, formValues[`${prefix}.api_key`]),
    model_id: serializeValue({ type: 'text' }, formValues[`${prefix}.model_id`]),
  }
}

function resetTransientMessages() {
  saveError.value = ''
  saveSuccess.value = ''
  testError.value = ''
  testSuccess.value = ''
}

function broadcastPanelConfig() {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent('admin-config-updated', {
    detail: {
      'site.title': serializeValue({ type: 'text' }, formValues['site.title']),
      'panel.title': serializeValue({ type: 'text' }, formValues['panel.title']),
      'panel.status_text': serializeValue({ type: 'text' }, formValues['panel.status_text']),
    },
  }))
}

function updateField(key, value) {
  formValues[key] = value
  saveError.value = ''
  saveSuccess.value = ''
}

async function load() {
  isLoading.value = true
  loadError.value = ''

  try {
    const configData = await unwrap(api.get('/config'))

    for (const field of settingFields) {
      formValues[field.key] = normalizeValue(field, configData[field.key]?.value)
      fieldMeta[field.key] = {
        category: configData[field.key]?.category || inferCategory(field.key),
        encrypted: configData[field.key]?.encrypted ?? field.type === 'secret',
      }
    }

    initialSnapshot.value = createSnapshot()
    hasLoaded.value = true
  } catch (error) {
    loadError.value = describeError(error, '加载系统设置失败，请稍后重试。')
  } finally {
    isLoading.value = false
  }
}

async function save() {
  if (!isDirty.value || isSaving.value) return

  saveError.value = ''
  saveSuccess.value = ''

  isSaving.value = true
  try {
    const items = buildItems()
    if (!items.length) {
      initialSnapshot.value = createSnapshot()
      saveSuccess.value = '没有需要保存的修改。'
      return
    }
    const result = await unwrap(api.put('/config', { items }))
    initialSnapshot.value = createSnapshot()
    broadcastPanelConfig()
    saveSuccess.value = result.site_runtime?.reason || '配置已保存。'
  } catch (error) {
    saveError.value = describeError(error, '保存配置失败，请检查填写内容后重试。')
  } finally {
    isSaving.value = false
  }
}

async function testLLM() {
  if (isTestingLLM.value) return

  testError.value = ''
  testSuccess.value = ''

  isTestingLLM.value = true
  try {
    const data = await unwrap(api.post('/config/test-llm', buildProviderPayload('llm')))
    testSuccess.value = `大脑接入测试通过：${data.reply}`
  } catch (error) {
    testError.value = describeError(error, '大脑接入测试失败，请检查接口地址、密钥和模型名称。')
  } finally {
    isTestingLLM.value = false
  }
}

async function testEmbedding() {
  if (isTestingEmbedding.value) return

  testError.value = ''
  testSuccess.value = ''

  isTestingEmbedding.value = true
  try {
    const data = await unwrap(api.post('/config/test-embedding', buildProviderPayload('embedding')))
    testSuccess.value = `记忆检索测试通过：维度 ${data.dimensions}`
  } catch (error) {
    testError.value = describeError(error, '记忆检索测试失败，请检查接口地址、密钥和模型名称。')
  } finally {
    isTestingEmbedding.value = false
  }
}

onMounted(async () => {
  resetTransientMessages()
  await load()
})

onBeforeRouteLeave(() => {
  if (isDirty.value) {
    return window.confirm('有未保存的修改，确定要离开吗？')
  }
})
</script>

<style scoped>
.settings-summary-card {
  background:
    linear-gradient(180deg, rgba(232, 238, 245, 0.03), transparent 100%),
    rgba(10, 14, 21, 0.76);
}
</style>
