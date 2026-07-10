<template>
  <section class="stack">
    <AppLoading
      v-if="isLoading"
      :title="t('personaEdit.loadingTitle')"
      :description="t('personaEdit.loadingDesc')"
    />

    <AppError
      v-else-if="loadError"
      :title="t('personaEdit.loadError')"
      :message="loadError"
      :action-label="t('common.retry')"
      @retry="load"
    />

    <template v-else>
      <div class="hero persona-edit-hero">
        <div>
<h1>{{ isNew ? t('personaEdit.newTitle') : t('personaEdit.editTitle', { id: route.params.id }) }}</h1>
          <p>{{ t('personaEdit.subtitle') }}</p>
        </div>
        <div class="persona-edit-hero-side">
          <div class="persona-edit-summary-card">
            <div class="persona-edit-summary-grid">
              <div>
                <span>{{ t('personaEdit.summary.taboos') }}</span>
                <strong>{{ tabooCount }}</strong>
              </div>
              <div>
                <span>{{ t('personaEdit.summary.lexicon') }}</span>
                <strong>{{ lexiconCount }}</strong>
              </div>
              <div>
                <span>{{ t('personaEdit.summary.scenes') }}</span>
                <strong>{{ sceneCount }}</strong>
              </div>
              <div>
                <span>{{ t('personaEdit.summary.length') }}</span>
                <strong>{{ structureLabel }}</strong>
              </div>
            </div>
            <div class="muted">
              {{ form.description || t('personaEdit.descriptionFallback') }}
            </div>
          </div>
          <div class="button-row">
            <button
              class="btn primary"
              :disabled="isSaving"
              @click="save"
            >
              {{ isSaving ? t('common.saving') : t('common.save') }}
            </button>
            <button
              v-if="!isNew"
              class="btn ghost"
              :disabled="isActivating || isDeleting"
              @click="activate"
            >
              {{ isActivating ? t('common.busy') : t('personaEdit.actions.setDefault') }}
            </button>
            <button
              v-if="!isNew"
              class="btn ghost"
              :disabled="isDeleting || isActivating"
              @click="removePersona"
            >
              {{ isDeleting ? t('common.busy') : t('personaEdit.actions.delete') }}
            </button>
          </div>
        </div>
      </div>

      <div
        v-if="message"
        class="status-banner"
        :class="messageType"
      >
        {{ message }}
      </div>

      <div class="grid two persona-edit-grid">
        <div class="panel panel-pad stack persona-story-panel">
          <div class="persona-panel-head">
            <div>
<div class="section-title">
                {{ t('personaEdit.sections.story') }}
              </div>
            </div>
            <div class="muted">
              {{ t('personaEdit.sections.storyDesc') }}
            </div>
          </div>
          <label class="field">
            <span>{{ t('personaEdit.fields.name') }}</span>
            <input
              v-model="form.name"
              :placeholder="t('personaEdit.placeholders.name')"
            >
          </label>
          <label class="field">
            <span>{{ t('personaEdit.fields.description') }}</span>
            <textarea
              v-model="form.description"
              :placeholder="t('personaEdit.placeholders.description')"
            />
          </label>

          <label class="field">
            <div class="field-head">
              <span>{{ t('personaEdit.fields.identity') }}</span>
              <button
                class="btn ghost btn-small"
                type="button"
                @click="toggleTemplateField('identity_setting')"
              >
                {{ activeTemplateField === 'identity_setting' ? t('personaEdit.actions.hideTemplates') : t('personaEdit.actions.showTemplates') }}
              </button>
            </div>
            <textarea
              v-model="form.identity_setting"
              :placeholder="t('personaEdit.placeholders.identity')"
            />
            <div
              v-if="activeTemplateField === 'identity_setting'"
              class="field-template-box"
            >
              <div class="field-template-hint">{{ t('personaEdit.templateHint') }}</div>
              <div class="button-row">
                <button
                  v-for="template in inspirationProfiles"
                  :key="`identity-${template.id}`"
                  class="btn ghost btn-small"
                  type="button"
                  @click="applyTemplate('identity_setting', template)"
                >
                  {{ template.label }}
                </button>
              </div>
            </div>
          </label>

          <label class="field">
            <div class="field-head">
              <span>{{ t('personaEdit.fields.worldview') }}</span>
              <button
                class="btn ghost btn-small"
                type="button"
                @click="toggleTemplateField('worldview_setting')"
              >
                {{ activeTemplateField === 'worldview_setting' ? t('personaEdit.actions.hideTemplates') : t('personaEdit.actions.showTemplates') }}
              </button>
            </div>
            <textarea
              v-model="form.worldview_setting"
              :placeholder="t('personaEdit.placeholders.worldview')"
            />
            <div
              v-if="activeTemplateField === 'worldview_setting'"
              class="field-template-box"
            >
              <div class="field-template-hint">{{ t('personaEdit.worldviewTemplateHint') }}</div>
              <div class="button-row">
                <button
                  v-for="template in inspirationProfiles"
                  :key="`worldview-${template.id}`"
                  class="btn ghost btn-small"
                  type="button"
                  @click="applyTemplate('worldview_setting', template)"
                >
                  {{ template.label }}
                </button>
              </div>
            </div>
          </label>

          <label class="field">
            <div class="field-head">
              <span>{{ t('personaEdit.fields.language') }}</span>
              <button
                class="btn ghost btn-small"
                type="button"
                @click="toggleTemplateField('language_style')"
              >
                {{ activeTemplateField === 'language_style' ? t('personaEdit.actions.hideTemplates') : t('personaEdit.actions.showTemplates') }}
              </button>
            </div>
            <textarea
              v-model="form.language_style"
              :placeholder="t('personaEdit.placeholders.language')"
            />
            <div
              v-if="activeTemplateField === 'language_style'"
              class="field-template-box"
            >
              <div class="field-template-hint">{{ t('personaEdit.languageTemplateHint') }}</div>
              <div class="button-row">
                <button
                  v-for="template in inspirationProfiles"
                  :key="`language-${template.id}`"
                  class="btn ghost btn-small"
                  type="button"
                  @click="applyTemplate('language_style', template)"
                >
                  {{ template.label }}
                </button>
              </div>
            </div>
          </label>
        </div>

        <div class="panel panel-pad stack persona-meta-panel">
          <div class="persona-panel-head">
            <div>
<div class="section-title">
                {{ t('personaEdit.sections.constraints') }}
              </div>
            </div>
            <div class="muted">
              {{ t('personaEdit.sections.constraintsDesc') }}
            </div>
          </div>
          <label class="field">
            <span>{{ t('personaEdit.fields.structure') }}</span>
            <select v-model="form.structure_preference">
              <option value="short">{{ t('personaEdit.structure.short') }}</option>
              <option value="medium">{{ t('personaEdit.structure.medium') }}</option>
              <option value="long">{{ t('personaEdit.structure.long') }}</option>
            </select>
          </label>
          <label class="field">
            <span>{{ t('personaEdit.fields.intensity') }}</span>
            <select v-model="form.expression_intensity">
              <option value="calm">{{ t('personaEdit.intensity.calm') }}</option>
              <option value="moderate">{{ t('personaEdit.intensity.moderate') }}</option>
              <option value="intense">{{ t('personaEdit.intensity.intense') }}</option>
            </select>
          </label>
          <label class="field">
            <span>{{ t('personaEdit.fields.taboos') }}</span>
            <textarea
              v-model="taboosText"
              :placeholder="t('personaEdit.placeholders.taboos')"
            />
          </label>

          <div class="persona-tone-note">
            <div class="persona-tone-item">
              <span>{{ t('personaEdit.summary.intensity') }}</span>
              <strong>{{ intensityLabel }}</strong>
            </div>
            <div class="persona-tone-item">
              <span>{{ t('personaEdit.summary.rhythm') }}</span>
              <strong>{{ structureLabel }}</strong>
            </div>
          </div>
        </div>
      </div>

      <div class="panel panel-pad stack persona-lexicon-panel">
        <div class="split persona-lexicon-head">
          <div>
<div class="section-title">
              {{ t('personaEdit.sections.lexicon') }}
            </div>
            <div class="muted">
              {{ t('personaEdit.sections.lexiconDesc1') }}
            </div>
            <div class="muted">
              {{ t('personaEdit.sections.lexiconDesc2') }}
            </div>
          </div>
          <div class="button-row">
            <button
              class="btn ghost btn-small"
              type="button"
              @click="insertLexiconExamples"
            >
              {{ t('personaEdit.actions.insertExamples') }}
            </button>
            <button
              class="btn ghost btn-small"
              type="button"
              @click="addLexiconRow"
            >
              {{ t('personaEdit.actions.addItem') }}
            </button>
          </div>
        </div>

        <div
          v-if="!lexiconRows.length"
          class="status-banner info"
        >
          {{ t('personaEdit.emptyLexicon') }}
        </div>

        <div
          v-else
          class="stack"
        >
          <div
            v-for="row in lexiconRows"
            :key="row.id"
            class="lexicon-row"
          >
            <input
              v-model="row.key"
              :placeholder="t('personaEdit.placeholders.lexiconKey')"
            >
            <input
              v-model="row.value"
              :placeholder="t('personaEdit.placeholders.lexiconValue')"
            >
            <button
              class="btn ghost btn-small"
              type="button"
              @click="removeLexiconRow(row.id)"
            >
              {{ t('common.delete') }}
            </button>
          </div>
        </div>

        <details class="panel panel-pad lexicon-advanced">
          <summary class="settings-section-summary">
            <div>
              <h2>{{ t('personaEdit.advancedJson') }}</h2>
              <p class="muted">
                {{ t('personaEdit.lexiconJsonDesc') }}
              </p>
            </div>
          </summary>
          <div class="settings-section-body stack">
            <label class="field">
              <span>{{ t('personaEdit.jsonContent') }}</span>
              <textarea
                v-model="advancedLexiconText"
                style="min-height: 200px"
              />
            </label>
            <div class="button-row">
              <button
                class="btn ghost btn-small"
                type="button"
                @click="syncAdvancedLexicon"
              >
                {{ t('personaEdit.actions.syncJson') }}
              </button>
              <button
                class="btn ghost btn-small"
                type="button"
                @click="applyAdvancedLexicon"
              >
                {{ t('personaEdit.actions.applyLexiconJson') }}
              </button>
            </div>
          </div>
        </details>
      </div>

      <div class="panel panel-pad stack persona-scene-panel">
        <div class="split persona-scene-head">
          <div>
<div class="section-title">
              {{ t('personaEdit.sections.scenes') }}
            </div>
            <div class="muted">
              {{ t('personaEdit.sections.scenesDesc1') }}
            </div>
            <div class="muted">
              {{ t('personaEdit.sections.scenesDesc2') }}
            </div>
          </div>
          <div class="button-row">
            <button
              class="btn ghost btn-small"
              type="button"
              @click="insertDefaultScenes"
            >
              {{ t('personaEdit.actions.insertDefaultScenes') }}
            </button>
            <button
              class="btn ghost btn-small"
              type="button"
              @click="addSceneRow"
            >
              {{ t('personaEdit.actions.addScene') }}
            </button>
          </div>
        </div>

        <div
          v-if="!sceneRows.length"
          class="status-banner info"
        >
          {{ t('personaEdit.emptyScenes') }}
        </div>

        <div
          v-else
          class="stack"
        >
          <div class="scene-header">
            <span>{{ t('personaEdit.scene.time') }}</span>
            <span>{{ t('personaEdit.scene.place') }}</span>
            <span>{{ t('personaEdit.scene.weather') }}</span>
            <span>{{ t('personaEdit.scene.direction') }}</span>
            <span />
          </div>
          <div
            v-for="row in sceneRows"
            :key="row.id"
            class="scene-row"
          >
            <input
              v-model="row.time"
              :placeholder="t('personaEdit.placeholders.sceneTime')"
            >
            <input
              v-model="row.place"
              :placeholder="t('personaEdit.placeholders.scenePlace')"
            >
            <input
              v-model="row.weather"
              :placeholder="t('personaEdit.placeholders.sceneWeather')"
            >
            <input
              v-model="row.direction"
              :placeholder="t('personaEdit.placeholders.sceneDirection')"
            >
            <button
              class="btn ghost btn-small"
              type="button"
              @click="removeSceneRow(row.id)"
            >
              {{ t('common.delete') }}
            </button>
          </div>
        </div>

        <details class="panel panel-pad scene-advanced">
          <summary class="settings-section-summary">
            <div>
              <h2>{{ t('personaEdit.advancedJson') }}</h2>
              <p class="muted">
                {{ t('personaEdit.sceneJsonDesc') }}
              </p>
            </div>
          </summary>
          <div class="settings-section-body stack">
            <label class="field">
              <span>{{ t('personaEdit.jsonContent') }}</span>
              <textarea
                v-model="advancedSceneText"
                style="min-height: 200px"
              />
            </label>
            <div class="button-row">
              <button
                class="btn ghost btn-small"
                type="button"
                @click="syncAdvancedScene"
              >
                {{ t('personaEdit.actions.syncJson') }}
              </button>
              <button
                class="btn ghost btn-small"
                type="button"
                @click="applyAdvancedScene"
              >
                {{ t('personaEdit.actions.applySceneJson') }}
              </button>
            </div>
          </div>
        </details>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { api, unwrap } from '../api'
import AppError from '../components/AppError.vue'
import AppLoading from '../components/AppLoading.vue'
import { describeError } from '../utils/errors'
import { inspirationProfiles } from '../utils/personaTemplates'

const defaultLexiconExamples = [
  ['midnight', '夜深、灯火将尽、长廊尽头那一线冷光'],
  ['snow', '落雪压檐、白衣、未融的月色'],
  ['corridor', '长廊无声、门外守候、半步之外的影子'],
  ['blood', '剑上余温、袖口冷痕、洗不净的铁锈气'],
  ['rain', '雨脚敲檐、潮气贴衣、风里未说出口的话'],
]

let nextLexiconId = 1
let nextSceneId = 1

function createLexiconRow(key = '', value = '') {
  return { id: nextLexiconId++, key, value }
}

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const isNew = computed(() => !route.params.id)
const form = reactive({
  name: '',
  description: '',
  is_active: true,
  identity_setting: '',
  worldview_setting: '',
  language_style: '',
  taboos: [],
  sensory_lexicon: {},
  structure_preference: 'medium',
  expression_intensity: 'moderate',
  stability_params: { temperature_base: 0.7, temperature_range: [0.3, 1.2] },
  scene_pool: [],
})
const taboosText = ref('')
const lexiconRows = ref([])
const advancedLexiconText = ref('{}')
const sceneRows = ref([])
const advancedSceneText = ref('[]')
const activeTemplateField = ref('')
const isLoading = ref(true)
const loadError = ref('')
const isSaving = ref(false)
const formDirty = ref(false)
const isActivating = ref(false)
const isDeleting = ref(false)
const message = ref('')
const messageType = ref('info')
const tabooCount = computed(
  () =>
    taboosText.value
      .split('\n')
      .map((item) => item.trim())
      .filter(Boolean).length,
)
const lexiconCount = computed(() => lexiconRows.value.filter((item) => item.key.trim() || item.value.trim()).length)
const sceneCount = computed(
  () =>
    sceneRows.value.filter(
      (item) => item.time.trim() || item.place.trim() || item.weather.trim() || item.direction.trim(),
    ).length,
)
const structureLabel = computed(
  () =>
    ({
      short: t('personaEdit.structure.short'),
      medium: t('personaEdit.structure.medium'),
      long: t('personaEdit.structure.long'),
    })[form.structure_preference] || t('common.none'),
)
const intensityLabel = computed(
  () =>
    ({
      calm: t('personaEdit.intensity.calm'),
      moderate: t('personaEdit.intensity.moderate'),
      intense: t('personaEdit.intensity.intense'),
    })[form.expression_intensity] || t('common.none'),
)

function setLexiconRows(lexicon) {
  const rows = Object.entries(lexicon || {}).map(([key, value]) => createLexiconRow(key, value))
  lexiconRows.value = rows
  syncAdvancedLexicon()
}

function addLexiconRow() {
  lexiconRows.value.push(createLexiconRow())
  syncAdvancedLexicon()
}

function removeLexiconRow(id) {
  lexiconRows.value = lexiconRows.value.filter((item) => item.id !== id)
  syncAdvancedLexicon()
}

function buildLexiconObject(strict = true) {
  const result = {}
  for (const row of lexiconRows.value) {
    const key = row.key.trim()
    const value = row.value.trim()
    if (!key && !value) continue
    if (!key || !value) {
      if (!strict) continue
      throw new Error(t('personaEdit.errors.lexiconIncomplete'))
    }
    if (result[key]) {
      if (!strict) continue
      throw new Error(t('personaEdit.errors.lexiconDuplicate', { key }))
    }
    result[key] = value
  }
  return result
}

function syncAdvancedLexicon() {
  advancedLexiconText.value = JSON.stringify(buildLexiconObject(false), null, 2)
}

function applyAdvancedLexicon() {
  try {
    const parsed = JSON.parse(advancedLexiconText.value || '{}')
    if (typeof parsed !== 'object' || Array.isArray(parsed) || !parsed) {
      throw new Error(t('personaEdit.errors.lexiconJsonObject'))
    }
    setLexiconRows(parsed)
    messageType.value = 'success'
    message.value = t('personaEdit.messages.lexiconJsonApplied')
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, t('personaEdit.messages.jsonParseFailed'))
  }
}

function toggleTemplateField(fieldKey) {
  activeTemplateField.value = activeTemplateField.value === fieldKey ? '' : fieldKey
}

function applyTemplate(fieldKey, template) {
  const nextValue = template[fieldKey]
  const currentValue = String(form[fieldKey] || '').trim()
  if (!currentValue) {
    form[fieldKey] = nextValue
    messageType.value = 'success'
    message.value = t('personaEdit.messages.templateInserted', { label: template.label })
    return
  }

  const overwrite = window.confirm(t('personaEdit.confirmTemplateOverwrite'))
  form[fieldKey] = overwrite ? nextValue : `${String(form[fieldKey]).trim()}\n\n${nextValue}`
  messageType.value = 'success'
  message.value = overwrite
    ? t('personaEdit.messages.templateOverwritten', { label: template.label })
    : t('personaEdit.messages.templateAppended', { label: template.label })
}

function insertLexiconExamples() {
  const currentLexicon = buildLexiconObject(false)
  let insertedCount = 0

  for (const [key, value] of defaultLexiconExamples) {
    if (currentLexicon[key]) continue
    lexiconRows.value.push(createLexiconRow(key, value))
    insertedCount += 1
  }

  syncAdvancedLexicon()
  messageType.value = 'success'
  message.value = insertedCount
    ? t('personaEdit.messages.lexiconExamplesInserted', { n: insertedCount })
    : t('personaEdit.messages.examplesAlreadyExist')
}

function createSceneRow(time = '', place = '', weather = '', direction = '') {
  return { id: nextSceneId++, time, place, weather, direction }
}

function setSceneRows(pool) {
  sceneRows.value = (pool || []).map((scene) =>
    createSceneRow(scene['时间'] || '', scene['地点'] || '', scene['天气'] || '', scene['方向'] || ''),
  )
  syncAdvancedScene()
}

function addSceneRow() {
  sceneRows.value.push(createSceneRow())
  syncAdvancedScene()
}

function removeSceneRow(id) {
  sceneRows.value = sceneRows.value.filter((item) => item.id !== id)
  syncAdvancedScene()
}

function buildScenePoolArray() {
  const result = []
  for (const row of sceneRows.value) {
    const t = row.time.trim()
    const p = row.place.trim()
    const w = row.weather.trim()
    const d = row.direction.trim()
    if (!t && !p && !w && !d) continue
    result.push({ 时间: t, 地点: p, 天气: w, 方向: d })
  }
  return result
}

function syncAdvancedScene() {
  advancedSceneText.value = JSON.stringify(buildScenePoolArray(), null, 2)
}

function applyAdvancedScene() {
  try {
    const parsed = JSON.parse(advancedSceneText.value || '[]')
    if (!Array.isArray(parsed)) {
      throw new Error(t('personaEdit.errors.sceneJsonArray'))
    }
    setSceneRows(parsed)
    messageType.value = 'success'
    message.value = t('personaEdit.messages.sceneJsonApplied')
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, t('personaEdit.messages.jsonParseFailed'))
  }
}

const defaultScenePool = [
  { 时间: '深夜子时', 地点: '王府后院练武场', 天气: '月明星稀', 方向: '独自练剑消化心事，剑势里藏着白天压住的情绪' },
  { 时间: '黄昏', 地点: '城外山道', 天气: '秋风落叶', 方向: '护送王爷出行途中，路上有片刻安静的同行' },
  { 时间: '清晨天未亮', 地点: '药铺街巷', 天气: '薄雾', 方向: '独自出门买伤药或办小事，不想让王爷知道旧伤又发了' },
  { 时间: '午后', 地点: '集市或小镇', 天气: '晴朗', 方向: '陪王爷微服出行，在人群中默默警戒，偶有意外的温存细节' },
  { 时间: '深夜丑时', 地点: '客栈或驿站', 天气: '暴雨', 方向: '护王爷赶路被困，在简陋之处独自守夜' },
  { 时间: '傍晚', 地点: '渡口或码头', 天气: '江风', 方向: '送姐姐远行或接姐姐归来，复杂情绪交织' },
  { 时间: '凌晨', 地点: '密林或山间', 天气: '浓雾', 方向: '执行密令归来，浑身疲惫，在破庙或林间短暂歇息' },
  { 时间: '入夜', 地点: '王爷书房外走廊', 天气: '微雪', 方向: '王爷在里面见客或议事，她在外面等，听到片段的对话' },
  { 时间: '半夜', 地点: '王爷寝室门外', 天气: '无风寒夜', 方向: '王爷生病或受伤，她彻夜照料，看到他脆弱的一面' },
  { 时间: '正午', 地点: '府中花园或湖边', 天气: '夏日炎热', 方向: '难得的闲暇时刻，独处或偶遇回忆' },
  { 时间: '深夜', 地点: '城墙之上', 天气: '大风', 方向: '边关或战事相关，在高处远望，心中想着远方和身后' },
  { 时间: '清晨', 地点: '厨房或茶室', 天气: '春雨', 方向: '为王爷准备什么小东西，不说出口的关心' },
  { 时间: '黄昏', 地点: '旧友的酒馆或茶楼', 天气: '阴天', 方向: '偶遇旧识，被问起近况，想起另一种活法' },
  {
    时间: '夜晚',
    地点: '元宵灯会或庙会',
    天气: '晴冷',
    方向: '人群中从暗处守望王爷，看他难得的放松，自己却始终在影子里',
  },
  { 时间: '拂晓', 地点: '马厩或出发点', 天气: '霜降', 方向: '一个人出远门执行任务前的最后准备，临走前回望一眼王府' },
  { 时间: '深夜', 地点: '姐姐的房间门口', 天气: '静夜', 方向: '姐姐受伤归来，她犹豫要不要去看，在门口站了很久' },
  { 时间: '午后', 地点: '藏书阁或密室', 天气: '闷热', 方向: '翻旧卷宗或查线索，在陈旧的纸堆里找到一段意外的往事' },
  { 时间: '入夜', 地点: '屋顶或高处', 天气: '繁星', 方向: '独自坐在高处发呆，回忆山上学艺的日子，或者想象另一种人生' },
  { 时间: '白天', 地点: '武器铺或铁匠铺', 天气: '晴天', 方向: '保养兵器或定做暗器，和铺子老板有几句日常闲话' },
  { 时间: '天亮前', 地点: '回府的路上', 天气: '残月', 方向: '办完事连夜赶回，快到王府时放慢脚步，整理好表情再进门' },
]

function insertDefaultScenes() {
  if (sceneRows.value.length > 0) {
    if (!window.confirm(t('personaEdit.confirmDefaultScenesOverwrite'))) return
  }
  setSceneRows(defaultScenePool)
  messageType.value = 'success'
  message.value = t('personaEdit.messages.defaultScenesInserted', { n: defaultScenePool.length })
}

async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    if (isNew.value) {
      setLexiconRows({})
      setSceneRows([])
      return
    }
    const data = await unwrap(api.get(`/personas/${route.params.id}`))
    Object.assign(form, data)
    taboosText.value = (data.taboos || []).join('\n')
    setLexiconRows(data.sensory_lexicon || {})
    setSceneRows(data.scene_pool || [])
  } catch (error) {
    loadError.value = describeError(error, t('personaEdit.loadFailed'))
  } finally {
    isLoading.value = false
  }
}

async function save() {
  if (isSaving.value) return
  isSaving.value = true
  message.value = ''

  try {
    form.taboos = taboosText.value
      .split('\n')
      .map((item) => item.trim())
      .filter(Boolean)
    form.sensory_lexicon = buildLexiconObject(true)
    form.scene_pool = buildScenePoolArray()
    syncAdvancedLexicon()
    syncAdvancedScene()

    if (isNew.value) {
      const data = await unwrap(api.post('/personas', form))
      router.replace(`/admin/personas/${data.id}`)
      return
    }
    await unwrap(api.put(`/personas/${route.params.id}`, form))
    messageType.value = 'success'
    message.value = t('personaEdit.saved')
    formDirty.value = false
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, t('personaEdit.saveFailed'))
  } finally {
    isSaving.value = false
  }
}

async function activate() {
  if (isActivating.value) return
  isActivating.value = true
  message.value = ''
  try {
    await unwrap(api.post(`/personas/${route.params.id}/activate`))
    messageType.value = 'success'
    message.value = t('personaEdit.defaultSet')
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, t('personaEdit.defaultSetFailed'))
  } finally {
    isActivating.value = false
  }
}

async function removePersona() {
  if (isDeleting.value) return
  if (!window.confirm(t('personaEdit.deleteConfirm'))) return

  isDeleting.value = true
  message.value = ''
  try {
    await unwrap(api.delete(`/personas/${route.params.id}`))
    router.push('/admin/personas')
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, t('personaEdit.deleteFailed'))
  } finally {
    isDeleting.value = false
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
.persona-edit-hero {
  align-items: end;
}

.persona-edit-hero-side {
  display: grid;
  gap: 14px;
  justify-items: end;
  max-width: 360px;
}

.persona-edit-summary-card {
  width: 100%;
  padding: 18px;
  border-radius: 18px;
  border: 1px solid var(--line-strong);
  background: var(--panel);
}

.persona-edit-summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.persona-edit-summary-grid span,
.persona-tone-item span {
  color: var(--muted);
  font-size: 0.74rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.persona-edit-summary-grid strong,
.persona-tone-item strong {
  display: block;
  margin-top: 8px;
  font-family: var(--font-display);
  letter-spacing: 0.04em;
}

.persona-edit-grid {
  align-items: start;
}

.persona-story-panel,
.persona-meta-panel,
.persona-lexicon-panel {
  gap: 20px;
}

.persona-panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.persona-panel-head .muted {
  max-width: 42ch;
  text-align: right;
  line-height: 1.7;
}

.persona-tone-note {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.persona-tone-item {
  padding: 14px 16px;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: var(--panel-soft);
}

.persona-lexicon-head {
  align-items: end;
}

.persona-scene-panel {
  gap: 20px;
}

.persona-scene-head {
  align-items: end;
}

.scene-header {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 2fr 60px;
  gap: 8px;
  padding: 0 2px;
  color: var(--muted);
  font-size: 0.74rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.scene-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 2fr 60px;
  gap: 8px;
  align-items: center;
}

@media (max-width: 900px) {
  .persona-edit-hero-side {
    justify-items: start;
    max-width: none;
  }

  .persona-panel-head .muted {
    max-width: none;
    text-align: left;
  }
}

@media (max-width: 680px) {
  .persona-edit-summary-grid,
  .persona-tone-note {
    grid-template-columns: 1fr;
  }

  .persona-panel-head {
    flex-direction: column;
  }

  .scene-header {
    display: none;
  }

  .scene-row {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
