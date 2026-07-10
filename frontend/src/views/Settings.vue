<template>
  <section class="stack">
    <AppLoading
      v-if="isLoading"
      :title="t('settings.loadingTitle')"
      :description="t('settings.loadingDesc')"
    />

    <AppError
      v-else-if="loadError"
      :title="t('settings.loadError')"
      :message="loadError"
      :action-label="t('common.retry')"
      @retry="load"
    />

    <template v-else>
      <div class="hero settings-hero">
        <div>
          <h1>{{ t('settings.title') }}</h1>
          <p>{{ t('settings.subtitle') }}</p>
        </div>
        <div class="settings-toolbar">
          <div class="button-row">
            <button
              class="btn ghost btn-small"
              type="button"
              :class="{ active: simpleMode }"
              @click="simpleMode = true"
            >
              {{ t('settings.modeBasic') }}
            </button>
            <button
              class="btn ghost btn-small"
              type="button"
              :class="{ active: !simpleMode }"
              @click="simpleMode = false"
            >
              {{ t('settings.modeAll') }}
            </button>
          </div>
          <label
            class="field"
            style="min-width:200px"
          >
            <span>{{ t('settings.searchFields') }}</span>
            <input
              v-model.trim="fieldQuery"
              :placeholder="t('settings.searchFields')"
            >
          </label>

          <div class="button-row">
            <button
              class="btn primary"
              :disabled="isBusy || !isDirty"
              @click="save"
            >
              {{ isSaving ? t('settings.saving') : t('settings.save') }}
            </button>
          </div>
          <div class="button-row">
            <span
              class="tag"
              :class="isDirty ? 'tag-warning' : 'tag-success'"
            >
              {{ isDirty ? t('settings.dirty') : t('settings.synced') }}
            </span>
          </div>
        </div>
      </div>

      <div
        v-if="saveError || saveSuccess || testError || testSuccess || isDirty"
        class="stack"
      >
        <div
          v-if="saveError"
          class="status-banner error"
        >
          {{ saveError }}
        </div>
        <div
          v-if="testError"
          class="status-banner error"
        >
          {{ testError }}
        </div>
        <div
          v-if="saveSuccess"
          class="status-banner success"
        >
          {{ saveSuccess }}
        </div>
        <div
          v-if="testSuccess"
          class="status-banner success"
        >
          {{ testSuccess }}
        </div>
        <div
          v-if="isDirty"
          class="status-banner warning"
        >
          {{ t('settings.dirtyBanner') }}
        </div>
      </div>

      <AppEmpty
        v-if="!translatedSections.length"
        :title="t('settings.emptyTitle')"
        :description="t('settings.emptyDesc')"
      />

      <template v-else>
        <div class="panel panel-pad config-summary-card settings-summary-card">
          <div class="settings-section-head">
            <div>
              <h2>{{ t('settings.canPublish') }}</h2>
              <p class="muted">
                {{ t('settings.canPublishHint') }}
              </p>
            </div>
            <div class="button-row">
              <span
                class="tag"
                :class="configConclusion.className"
              >{{ configConclusion.label }}</span>
            </div>
          </div>

          <div class="card-row">
            <div class="metric">
              <div class="muted">
                {{ t('settings.statusCurrent') }}
              </div>
              <strong>{{ configConclusion.label }}</strong>
              <div class="muted">
                {{ configConclusion.description }}
              </div>
            </div>
            <div class="metric">
              <div class="muted">
                {{ t('settings.llmAccess') }}
              </div>
              <strong>{{ llmReady ? t('settings.configured') : t('settings.notConfigured') }}</strong>
              <div class="muted">
                {{ llmReady ? t('settings.llmReadyDesc') : t('settings.llmMissingDesc') }}
              </div>
            </div>
            <div class="metric">
              <div class="muted">
                {{ t('settings.memorySearch') }}
              </div>
              <strong>{{ embeddingReady ? t('settings.configured') : t('settings.notConfigured') }}</strong>
              <div class="muted">
                {{ embeddingReady ? t('settings.embeddingReadyDesc') : t('settings.embeddingMissingDesc') }}
              </div>
            </div>
            <div class="metric">
              <div class="muted">
                {{ t('settings.autoWriting') }}
              </div>
              <strong>{{ automationReady ? t('settings.enabled') : t('settings.disabled') }}</strong>
              <div class="muted">
                {{ automationReady ? t('settings.automationReadyDesc') : t('settings.automationMissingDesc') }}
              </div>
            </div>
          </div>
        </div>

        <div class="panel panel-pad stack">
          <div class="settings-section-head">
            <div>
              <h2>{{ t('twofa.settingsTitle') }}</h2>
              <p class="muted">
                {{ t('twofa.settingsDesc') }}
              </p>
            </div>
            <span
              class="tag"
              :class="twofaStatus.enabled ? 'tag-success' : 'tag-warning'"
            >
              {{ twofaStatus.enabled ? t('common.enabled') : t('common.disabled') }}
            </span>
          </div>

          <div
            v-if="twofaSetup"
            class="stack"
          >
            <div class="status-banner info">
              {{ t('twofa.setupInstruction') }}
            </div>
            <label class="field">
              <span>{{ t('twofa.manualSecret') }}</span>
              <input
                :value="twofaSetup.secret"
                readonly
              >
            </label>
            <label class="field">
              <span>{{ t('twofa.confirmCode') }}</span>
              <input
                v-model.trim="twofaConfirmCode"
                inputmode="numeric"
                :placeholder="t('twofa.codePlaceholder')"
              >
            </label>
            <div class="recovery-code-grid">
              <code
                v-for="code in twofaSetup.recovery_codes"
                :key="code"
              >{{ code }}</code>
            </div>
            <div class="button-row">
              <button
                class="btn primary"
                type="button"
                :disabled="isTwofaBusy"
                @click="confirmTwofa"
              >
                {{ t('twofa.confirmEnable') }}
              </button>
              <button
                class="btn ghost"
                type="button"
                :disabled="isTwofaBusy"
                @click="twofaSetup = null"
              >
                {{ t('common.cancel') }}
              </button>
            </div>
          </div>

          <div
            v-else-if="twofaStatus.enabled"
            class="stack"
          >
            <label class="field">
              <span>{{ t('twofa.currentPassword') }}</span>
              <input
                v-model="twofaDisable.password"
                type="password"
                autocomplete="current-password"
              >
            </label>
            <label class="field">
              <span>{{ t('twofa.code') }}</span>
              <input
                v-model.trim="twofaDisable.code"
                inputmode="numeric"
                :placeholder="t('twofa.codePlaceholder')"
              >
            </label>
            <button
              class="btn ghost"
              type="button"
              :disabled="isTwofaBusy"
              @click="disableTwofa"
            >
              {{ t('twofa.disable') }}
            </button>
          </div>

          <div
            v-else
            class="button-row"
          >
            <button
              class="btn primary"
              type="button"
              :disabled="isTwofaBusy"
              @click="startTwofaSetup"
            >
              {{ t('twofa.enable') }}
            </button>
          </div>
        </div>

        <SettingsSection
          v-for="section in translatedSections"
          :key="section.id"
          :disabled="isBusy"
          :section="section"
          :values="formValues"
          @update="updateField"
        >
          <template #actions="{ section: currentSection }">
            <button
              v-if="currentSection.id === 'llm'"
              class="btn ghost btn-small"
              :disabled="isBusy"
              type="button"
              @click="testLLM"
            >
              {{ isTestingLLM ? t('common.busy') : t('settings.testLlm') }}
            </button>
            <button
              v-if="currentSection.id === 'embedding'"
              class="btn ghost btn-small"
              :disabled="isBusy"
              type="button"
              @click="testEmbedding"
            >
              {{ isTestingEmbedding ? t('common.busy') : t('settings.testEmbed') }}
            </button>
          </template>
        </SettingsSection>
      </template>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { onBeforeRouteLeave } from 'vue-router'

import { api, unwrap } from '../api'
import AppEmpty from '../components/AppEmpty.vue'
import AppError from '../components/AppError.vue'
import AppLoading from '../components/AppLoading.vue'
import SettingsSection from '../components/settings/SettingsSection.vue'
import { settingFields, settingsSections } from '../config/settingsSchema'
import { translateField } from '../utils/i18nField'
import { useToastStore } from '../stores/toast'
import { describeError } from '../utils/errors'

const { t } = useI18n()

const toast = useToastStore()
const simpleMode = ref(true)
const fieldQuery = ref('')

const BASIC_SECTION_IDS = new Set(['site', 'panel', 'llm', 'embedding', 'schedule', 'backup', 'quality'])

const translatedSections = computed(() => {
  const q = fieldQuery.value.trim().toLowerCase()
  return settingsSections
    .filter((section) => (simpleMode.value ? BASIC_SECTION_IDS.has(section.id) : true))
    .map((section) => {
      const base = `settingsSchema.sections.${section.id}`
      const titleKey = `${base}.title`
      const descKey = `${base}.description`
      const fields = section.fields
        .map((field) => translateField(field))
        .filter((field) => {
          if (!q) return true
          const hay = `${field.label || ''} ${field.key} ${field.help || ''}`.toLowerCase()
          return hay.includes(q)
        })
      return {
        ...section,
        title: t(titleKey) !== titleKey ? t(titleKey) : section.title,
        description: t(descKey) !== descKey ? t(descKey) : section.description,
        fields,
      }
    })
    .filter((section) => section.fields.length > 0)
})



const formValues = reactive({})
const fieldMeta = reactive({})

const isLoading = ref(true)
const loadError = ref('')
const isSaving = ref(false)
const saveError = ref('')
const saveSuccess = ref('')
const isTestingLLM = ref(false)
const isTestingEmbedding = ref(false)
const isTwofaBusy = ref(false)
const testError = ref('')
const testSuccess = ref('')
const twofaStatus = reactive({ enabled: false, confirmed: false })
const twofaSetup = ref(null)
const twofaConfirmCode = ref('')
const twofaDisable = reactive({ password: '', code: '' })
const initialSnapshot = ref('{}')
const hasLoaded = ref(false)

const isDirty = computed(() => hasLoaded.value && createSnapshot() !== initialSnapshot.value)
const isBusy = computed(() => isSaving.value || isTestingLLM.value || isTestingEmbedding.value || isTwofaBusy.value)
const llmReady = computed(() => hasValue('llm.base_url') && hasValue('llm.model_id') && hasSecretValue('llm.api_key'))
const embeddingReady = computed(
  () => hasValue('embedding.base_url') && hasValue('embedding.model_id') && hasSecretValue('embedding.api_key'),
)
const automationReady = computed(
  () =>
    Number(formValues['schedule.days_per_cycle'] || 0) > 0 &&
    Number(formValues['schedule.posts_per_cycle'] || 0) > 0 &&
    isClockValue(formValues['schedule.publish_time']),
)
const configConclusion = computed(() => {
  if (!hasValue('site.title') || !llmReady.value) {
    return {
      label: t('settings.unavailable'),
      description: t('settings.unavailableDesc'),
      className: 'tag-danger',
    }
  }
  if (!automationReady.value) {
    return {
      label: t('settings.manualOnly'),
      description: t('settings.manualOnlyDesc'),
      className: 'tag-warning',
    }
  }
  if (!embeddingReady.value) {
    return {
      label: t('settings.limited'),
      description: t('settings.limitedDesc'),
      className: 'tag-warning',
    }
  }
  return {
    label: t('settings.ready'),
    description: t('settings.readyDesc'),
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
    backup: 'backup',
  }
  return categoryMap[prefix] || 'general'
}

function normalizeValue(field, rawValue) {
  if ((rawValue === undefined || rawValue === null) && Object.prototype.hasOwnProperty.call(field, 'defaultValue')) {
    return field.defaultValue
  }
  if (field.type === 'boolean') {
    const value = String(rawValue ?? '')
      .trim()
      .toLowerCase()
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
  toast.success(t('toast.saved'))
    saveSuccess.value = ''
  testError.value = ''
  testSuccess.value = ''
}

function broadcastPanelConfig() {
  if (typeof window === 'undefined') return
  window.dispatchEvent(
    new CustomEvent('admin-config-updated', {
      detail: {
        'site.title': serializeValue({ type: 'text' }, formValues['site.title']),
        'panel.title': serializeValue({ type: 'text' }, formValues['panel.title']),
        'panel.status_text': serializeValue({ type: 'text' }, formValues['panel.status_text']),
      },
    }),
  )
}

function updateField(key, value) {
  formValues[key] = value
  saveError.value = ''
  toast.success(t('toast.saved'))
    saveSuccess.value = ''
}

async function load() {
  isLoading.value = true
  loadError.value = ''

  try {
    const configData = await unwrap(api.get('/config'))
    const securityData = await unwrap(api.get('/auth/2fa/status'))

    for (const field of settingFields) {
      formValues[field.key] = normalizeValue(field, configData[field.key]?.value)
      fieldMeta[field.key] = {
        category: configData[field.key]?.category || inferCategory(field.key),
        encrypted: configData[field.key]?.encrypted ?? field.type === 'secret',
      }
    }

    initialSnapshot.value = createSnapshot()
    Object.assign(twofaStatus, securityData)
    hasLoaded.value = true
  } catch (error) {
    loadError.value = describeError(error, '加载系统设置失败，请稍后重试。')
  } finally {
    isLoading.value = false
  }
}

async function reloadTwofaStatus() {
  Object.assign(twofaStatus, await unwrap(api.get('/auth/2fa/status')))
}

async function startTwofaSetup() {
  if (isTwofaBusy.value) return
  isTwofaBusy.value = true
  try {
    twofaSetup.value = await unwrap(api.post('/auth/2fa/setup'))
    twofaConfirmCode.value = ''
    toast.success(t('twofa.setupStarted'))
  } catch (error) {
    saveError.value = describeError(error, t('twofa.setupFailed'))
  } finally {
    isTwofaBusy.value = false
  }
}

async function confirmTwofa() {
  if (isTwofaBusy.value) return
  isTwofaBusy.value = true
  try {
    await unwrap(api.post('/auth/2fa/confirm', { code: twofaConfirmCode.value }))
    twofaSetup.value = null
    twofaConfirmCode.value = ''
    await reloadTwofaStatus()
    toast.success(t('twofa.enabledToast'))
  } catch (error) {
    saveError.value = describeError(error, t('twofa.confirmFailed'))
  } finally {
    isTwofaBusy.value = false
  }
}

async function disableTwofa() {
  if (isTwofaBusy.value) return
  isTwofaBusy.value = true
  try {
    await unwrap(api.post('/auth/2fa/disable', { password: twofaDisable.password, code: twofaDisable.code }))
    twofaDisable.password = ''
    twofaDisable.code = ''
    await reloadTwofaStatus()
    toast.success(t('twofa.disabledToast'))
  } catch (error) {
    saveError.value = describeError(error, t('twofa.disableFailed'))
  } finally {
    isTwofaBusy.value = false
  }
}

async function save() {
  if (!isDirty.value || isSaving.value) return

  saveError.value = ''
  toast.success(t('toast.saved'))
    saveSuccess.value = ''

  isSaving.value = true
  try {
    const items = buildItems()
    if (!items.length) {
      initialSnapshot.value = createSnapshot()
      toast.success(t('toast.saved'))
    saveSuccess.value = '没有需要保存的修改。'
      return
    }
    const result = await unwrap(api.put('/config', { items }))
    initialSnapshot.value = createSnapshot()
    broadcastPanelConfig()
    toast.success(t('toast.saved'))
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
  background: var(--panel);
}

.recovery-code-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 8px;
}

.recovery-code-grid code {
  padding: 8px 10px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel-soft);
}
</style>
