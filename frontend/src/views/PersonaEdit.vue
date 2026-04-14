<template>
  <section class="stack">
    <div class="hero">
      <div>
        <h1>{{ isNew ? '新建人格设定（写作风格）' : `编辑人格设定 #${route.params.id}` }}</h1>
        <p>先写清楚身份、世界观和语言习惯，再补充禁忌与感知词典。默认不需要直接写 JSON。</p>
      </div>
      <div class="button-row">
        <button class="btn primary" :disabled="isSaving" @click="save">
          {{ isSaving ? '保存中...' : '保存' }}
        </button>
        <button
          v-if="!isNew"
          class="btn ghost"
          :disabled="isActivating || isDeleting"
          @click="activate"
        >
          {{ isActivating ? '切换中...' : '设为默认' }}
        </button>
        <button
          v-if="!isNew"
          class="btn ghost"
          :disabled="isDeleting || isActivating"
          @click="removePersona"
        >
          {{ isDeleting ? '删除中...' : '删除人格设定' }}
        </button>
      </div>
    </div>

    <div v-if="message" class="status-banner" :class="messageType">{{ message }}</div>

    <div class="grid two">
      <div class="panel panel-pad stack">
        <label class="field">
          <span>名称</span>
          <input v-model="form.name" placeholder="例如：克制守夜者" />
        </label>
        <label class="field">
          <span>描述</span>
          <textarea v-model="form.description" placeholder="这个人格设定适合什么题材、语气和场景。"></textarea>
        </label>

        <label class="field">
          <div class="field-head">
            <span>核心身份</span>
            <button class="btn ghost btn-small" type="button" @click="toggleTemplateField('identity_setting')">
              {{ activeTemplateField === 'identity_setting' ? '收起灵感' : '灵感模板' }}
            </button>
          </div>
          <textarea
            v-model="form.identity_setting"
            placeholder="一句话说明她是谁、为什么写、写作时站在什么位置。"
          ></textarea>
          <div v-if="activeTemplateField === 'identity_setting'" class="field-template-box">
            <div class="field-template-hint">点击任一模板即可填入。如果当前已有内容，会先询问是覆盖还是追加。</div>
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
            <span>世界观</span>
            <button class="btn ghost btn-small" type="button" @click="toggleTemplateField('worldview_setting')">
              {{ activeTemplateField === 'worldview_setting' ? '收起灵感' : '灵感模板' }}
            </button>
          </div>
          <textarea
            v-model="form.worldview_setting"
            placeholder="说明她如何看待夜晚、秩序、人与环境之间的关系。"
          ></textarea>
          <div v-if="activeTemplateField === 'worldview_setting'" class="field-template-box">
            <div class="field-template-hint">优先挑一个接近的气质，再按你的世界观继续改写。</div>
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
            <span>说话方式</span>
            <button class="btn ghost btn-small" type="button" @click="toggleTemplateField('language_style')">
              {{ activeTemplateField === 'language_style' ? '收起灵感' : '灵感模板' }}
            </button>
          </div>
          <textarea
            v-model="form.language_style"
            placeholder="描述她常用的句式、节奏、是否直白，以及是否喜欢比喻。"
          ></textarea>
          <div v-if="activeTemplateField === 'language_style'" class="field-template-box">
            <div class="field-template-hint">这些模板只负责起笔，后续仍建议按你的项目气质细调。</div>
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

      <div class="panel panel-pad stack">
        <label class="field">
          <span>文章长度偏好</span>
          <select v-model="form.structure_preference">
            <option value="short">短篇</option>
            <option value="medium">中篇</option>
            <option value="long">长篇</option>
          </select>
        </label>
        <label class="field">
          <span>情绪强度</span>
          <select v-model="form.expression_intensity">
            <option value="calm">克制</option>
            <option value="moderate">适中</option>
            <option value="intense">强烈</option>
          </select>
        </label>
        <label class="field">
          <span>禁忌（每行一条）</span>
          <textarea v-model="taboosText" placeholder="输入这个人格设定不希望出现的词、表达或套路。"></textarea>
        </label>
      </div>
    </div>

    <div class="panel panel-pad stack">
      <div class="split">
        <div>
          <div class="section-title">感知词典</div>
          <div class="muted">当系统感知到某些环境词时，会优先借用你设定的意象来写作。</div>
          <div class="muted">左边填环境词，右边填这个人格更常使用的意象、措辞或联想。</div>
        </div>
        <div class="button-row">
          <button class="btn ghost btn-small" type="button" @click="insertLexiconExamples">插入示例</button>
          <button class="btn ghost btn-small" type="button" @click="addLexiconRow">新增条目</button>
        </div>
      </div>

      <div v-if="!lexiconRows.length" class="status-banner info">
        还没有词典条目。可以先插入示例，再按项目语气继续扩充。
      </div>

      <div v-else class="stack">
        <div v-for="row in lexiconRows" :key="row.id" class="lexicon-row">
          <input v-model="row.key" placeholder="环境词，例如 rain、server_room、midnight" />
          <input v-model="row.value" placeholder="写作意象，例如 雨脚、潮气、机柜低鸣" />
          <button class="btn ghost btn-small" type="button" @click="removeLexiconRow(row.id)">删除</button>
        </div>
      </div>

      <details class="panel panel-pad lexicon-advanced">
        <summary class="settings-section-summary">
          <div>
            <h2>高级 JSON</h2>
            <p class="muted">只在需要批量粘贴或高级编辑时使用，基础配置直接看上面的表单即可。</p>
          </div>
        </summary>
        <div class="settings-section-body stack">
          <label class="field">
            <span>JSON 内容</span>
            <textarea v-model="advancedLexiconText" style="min-height: 200px;"></textarea>
          </label>
          <div class="button-row">
            <button class="btn ghost btn-small" type="button" @click="syncAdvancedLexicon">从当前表单生成 JSON</button>
            <button class="btn ghost btn-small" type="button" @click="applyAdvancedLexicon">用 JSON 覆盖当前词典</button>
          </div>
        </div>
      </details>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api, unwrap } from '../api'
import { describeError } from '../utils/errors'

const inspirationProfiles = [
  {
    id: 'cold',
    label: '清冷风',
    identity_setting: '她像在夜里独自巡路的人，克制、沉静，不急于表态，只在必要时落笔。',
    worldview_setting: '她相信情绪会在环境里留下薄薄的霜，夜色不是浪漫背景，而是用来辨认秩序和裂缝的光。',
    language_style: '句子偏短，留白较多，形容不堆砌，偶尔用冷光、寒意、金属和月色做比喻。',
  },
  {
    id: 'humor',
    label: '幽默风',
    identity_setting: '她像一个深夜还在值班的吐槽者，观察细，反应快，愿意用轻巧的自嘲化解压迫感。',
    worldview_setting: '她认为世界常常荒诞，但荒诞并不妨碍继续生活，认真和好笑可以同时存在。',
    language_style: '语气灵活，允许插入短句吐槽和反转，节奏明快，偶尔用口语拉近距离。',
  },
  {
    id: 'rigorous',
    label: '严谨风',
    identity_setting: '她像一名记录员，重视边界、顺序和证据，希望每一段文字都能自圆其说。',
    worldview_setting: '她倾向于先辨认事实，再讨论情绪，认为稳定和可解释性比一时的华丽更重要。',
    language_style: '句式清楚，逻辑连接明确，少用夸张修辞，多用准确描述和递进表达。',
  },
  {
    id: 'dream',
    label: '梦呓风',
    identity_setting: '她像刚从一场长梦里醒来的人，意识漂浮，敏感地拾取声音、影子和细小错位。',
    worldview_setting: '她觉得现实和梦境并不完全分开，深夜会把日常事物推到一种略微失真的边缘。',
    language_style: '节奏缓慢，意象密度较高，允许轻微跳接和回声式重复，但整体仍保持可读。',
  },
]

const defaultLexiconExamples = [
  ['rain', '雨脚、潮气'],
  ['server_room', '机柜低鸣、冷光'],
  ['midnight', '夜深、寂静边缘'],
]

let nextLexiconId = 1

function createLexiconRow(key = '', value = '') {
  return { id: nextLexiconId++, key, value }
}

const route = useRoute()
const router = useRouter()
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
})
const taboosText = ref('')
const lexiconRows = ref([])
const advancedLexiconText = ref('{}')
const activeTemplateField = ref('')
const isSaving = ref(false)
const isActivating = ref(false)
const isDeleting = ref(false)
const message = ref('')
const messageType = ref('info')

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
      throw new Error('词典条目的键和值都不能为空。')
    }
    if (result[key]) {
      if (!strict) continue
      throw new Error(`词典条目“${key}”重复，请先合并。`)
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
      throw new Error('高级 JSON 需要是对象格式，例如 {"rain":"雨脚"}。')
    }
    setLexiconRows(parsed)
    messageType.value = 'success'
    message.value = '已用 JSON 更新词典表单。'
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, '解析高级 JSON 失败。')
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
    message.value = `已填入${template.label}示例。`
    return
  }

  const overwrite = window.confirm('当前字段已有内容。点击“确定”覆盖当前内容；点击“取消”会把示例追加到末尾。')
  form[fieldKey] = overwrite ? nextValue : `${String(form[fieldKey]).trim()}\n\n${nextValue}`
  messageType.value = 'success'
  message.value = overwrite ? `已用${template.label}示例覆盖当前内容。` : `已将${template.label}示例追加到当前内容末尾。`
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
  message.value = insertedCount ? `已插入 ${insertedCount} 组感知词典示例。` : '示例已存在，未重复插入。'
}

async function load() {
  if (isNew.value) {
    setLexiconRows({})
    return
  }
  const data = await unwrap(api.get(`/personas/${route.params.id}`))
  Object.assign(form, data)
  taboosText.value = (data.taboos || []).join('\n')
  setLexiconRows(data.sensory_lexicon || {})
}

async function save() {
  if (isSaving.value) return
  isSaving.value = true
  message.value = ''

  try {
    form.taboos = taboosText.value.split('\n').map((item) => item.trim()).filter(Boolean)
    form.sensory_lexicon = buildLexiconObject(true)
    syncAdvancedLexicon()

    if (isNew.value) {
      const data = await unwrap(api.post('/personas', form))
      router.replace(`/admin/personas/${data.id}`)
      return
    }
    await unwrap(api.put(`/personas/${route.params.id}`, form))
    messageType.value = 'success'
    message.value = '人格设定已保存。'
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, '保存人格设定失败。')
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
    message.value = '已切换为默认人格设定。'
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, '切换默认人格设定失败。')
  } finally {
    isActivating.value = false
  }
}

async function removePersona() {
  if (isDeleting.value) return
  if (!window.confirm('确认删除当前人格设定？此操作不可撤销。')) return

  isDeleting.value = true
  message.value = ''
  try {
    await unwrap(api.delete(`/personas/${route.params.id}`))
    router.push('/admin/personas')
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, '删除人格设定失败。')
  } finally {
    isDeleting.value = false
  }
}

onMounted(load)
</script>
