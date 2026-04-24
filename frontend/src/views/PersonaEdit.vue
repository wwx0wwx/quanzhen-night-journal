<template>
  <section class="stack">
    <AppLoading
      v-if="isLoading"
      title="正在加载人格设定"
      description="正在读取人格详情、禁忌与感知词典。"
    />

    <AppError
      v-else-if="loadError"
      title="人格设定加载失败"
      :message="loadError"
      action-label="重试"
      @retry="load"
    />

    <template v-else>
      <div class="hero persona-edit-hero">
        <div>
          <div class="hero-kicker">Persona Drafting Room</div>
          <h1>{{ isNew ? '新建人格设定' : `编辑人格设定 #${route.params.id}` }}</h1>
          <p>先定她是谁、如何看待王爷与江湖、说话时如何藏锋，再补禁忌与感知词典。默认不需要直接写 JSON。</p>
        </div>
        <div class="persona-edit-hero-side">
          <div class="persona-edit-summary-card">
            <div class="persona-edit-summary-grid">
              <div>
                <span>禁忌条目</span>
                <strong>{{ tabooCount }}</strong>
              </div>
              <div>
                <span>感知词典</span>
                <strong>{{ lexiconCount }}</strong>
              </div>
              <div>
                <span>场景骰子</span>
                <strong>{{ sceneCount }}</strong>
              </div>
              <div>
                <span>当前篇幅</span>
                <strong>{{ structureLabel }}</strong>
              </div>
            </div>
            <div class="muted">{{ form.description || '先用一句话定义这张人格卡的核心气质。' }}</div>
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
      </div>

      <div v-if="message" class="status-banner" :class="messageType">{{ message }}</div>

      <div class="grid two persona-edit-grid">
        <div class="panel panel-pad stack persona-story-panel">
        <div class="persona-panel-head">
          <div>
            <div class="hero-kicker">Core Profile</div>
            <div class="section-title">人物叙述</div>
          </div>
          <div class="muted">先写身份、世界观与说话方式，这三块决定了后续风格是否稳定。</div>
        </div>
        <label class="field">
          <span>名称</span>
          <input v-model="form.name" placeholder="例如：全真、守夜白影、廊下执灯人" />
        </label>
        <label class="field">
          <span>描述</span>
          <textarea v-model="form.description" placeholder="一句话写清这张人格卡的核心气质、关系张力和适用场景。"></textarea>
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
            placeholder="说明她是谁，她与王爷、姐姐是什么关系，她写字时站在什么位置。"
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
            placeholder="说明她如何看待江湖、王府、光与影、守护与误解。"
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
            placeholder="描述她常用的称呼、句式、节奏、留白方式，以及妒意与温柔如何显出来。"
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

        <div class="panel panel-pad stack persona-meta-panel">
        <div class="persona-panel-head">
          <div>
            <div class="hero-kicker">Behavior Envelope</div>
            <div class="section-title">行为约束</div>
          </div>
          <div class="muted">控制篇幅、强度、禁忌与词典边界，让人格卡保持可重复使用。</div>
        </div>
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

        <div class="persona-tone-note">
          <div class="persona-tone-item">
            <span>情绪档位</span>
            <strong>{{ intensityLabel }}</strong>
          </div>
          <div class="persona-tone-item">
            <span>写作节奏</span>
            <strong>{{ structureLabel }}</strong>
          </div>
        </div>
        </div>
      </div>

      <div class="panel panel-pad stack persona-lexicon-panel">
      <div class="split persona-lexicon-head">
        <div>
          <div class="hero-kicker">Sensory Lexicon</div>
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

      <div class="panel panel-pad stack persona-scene-panel">
      <div class="split persona-scene-head">
        <div>
          <div class="hero-kicker">Scene Dice</div>
          <div class="section-title">场景骰子</div>
          <div class="muted">每次生成时，系统从池中随机抽取一个场景方向，作为文章的叙事骨架。</div>
          <div class="muted">留空时使用系统默认场景池。可按自己的世界观自定义。</div>
        </div>
        <div class="button-row">
          <button class="btn ghost btn-small" type="button" @click="insertDefaultScenes">插入默认武侠场景</button>
          <button class="btn ghost btn-small" type="button" @click="addSceneRow">新增场景</button>
        </div>
      </div>

      <div v-if="!sceneRows.length" class="status-banner info">
        还没有场景骰子。可以先插入默认武侠场景，或按自己的世界观添加新场景。
      </div>

      <div v-else class="stack">
        <div class="scene-header">
          <span>时间</span>
          <span>地点</span>
          <span>天气/氛围</span>
          <span>叙事方向</span>
          <span></span>
        </div>
        <div v-for="row in sceneRows" :key="row.id" class="scene-row">
          <input v-model="row.time" placeholder="例如：深夜子时" />
          <input v-model="row.place" placeholder="例如：王府后院" />
          <input v-model="row.weather" placeholder="例如：月明星稀" />
          <input v-model="row.direction" placeholder="例如：独自练剑消化心事" />
          <button class="btn ghost btn-small" type="button" @click="removeSceneRow(row.id)">删除</button>
        </div>
      </div>

      <details class="panel panel-pad scene-advanced">
        <summary class="settings-section-summary">
          <div>
            <h2>高级 JSON</h2>
            <p class="muted">用于批量编辑或自定义键名。基础配置直接看上面的表单即可。</p>
          </div>
        </summary>
        <div class="settings-section-body stack">
          <label class="field">
            <span>JSON 内容</span>
            <textarea v-model="advancedSceneText" style="min-height: 200px;"></textarea>
          </label>
          <div class="button-row">
            <button class="btn ghost btn-small" type="button" @click="syncAdvancedScene">从当前表单生成 JSON</button>
            <button class="btn ghost btn-small" type="button" @click="applyAdvancedScene">用 JSON 覆盖当前场景池</button>
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

import { api, unwrap } from '../api'
import AppError from '../components/AppError.vue'
import AppLoading from '../components/AppLoading.vue'
import { describeError } from '../utils/errors'

const inspirationProfiles = [
  {
    id: 'quanzhen-core',
    label: '全真本体',
    identity_setting: '她是王爷身边最安静也最锋利的白影。姐姐替王爷行走江湖，她替王爷守长夜、秘密、危险和性命。她不争光、不争名，只想守住王爷身边那个最贴近、最不可替代的位置。',
    worldview_setting: '她活在武侠江湖与王府暗线交叠的世界里。她最熟悉的不是喧哗的胜负，而是长廊、雪夜、檐灯、旧伤、佩剑与门外那一线守着便足够的灯火。她最怕的不是被拒绝，而是从未被真正看见。',
    language_style: '句子短，语气淡，越难受越平。常用“王爷”“属下”“姐姐”这些称呼，少解释，少宣泄，善写守夜、停步、回望、拂雪、袖中收紧的手指。妒意不吵不闹，只会变得更轻、更冷、更伤人。',
  },
  {
    id: 'quanzhen-guard',
    label: '守夜陪伴',
    identity_setting: '她更像王爷门外那盏不熄的灯。她不求被夸奖，只求王爷回头时，她还站在原处；风雨将至时，她能比旁人更早挡上去。',
    worldview_setting: '在她眼里，江湖真正重要的从来不是谁名声更响，而是谁能在夜里守住那道门、那盏灯、那个人。比起赢给天下人看，她更在意王爷是否安睡、是否无恙、是否有人替他挡下门外的风。',
    language_style: '适合写得更柔，但仍须克制。多写“属下还在”“王爷无恙便好”这一类不张扬的陪伴型表达。温柔只能微露，像灯芯轻轻亮一下，不能变成直白撒娇。',
  },
  {
    id: 'quanzhen-jealous',
    label: '妒意暗涌',
    identity_setting: '她对王爷的感情早已深到骨里，也因此极难忍受自己被安置在影子里。她不明白王爷为何把姐姐派出去，也因此总把自己放在“被留下却未必被选择”的位置上反复咀嚼。',
    worldview_setting: '姐姐像光，像被允许站在明处的人；她自己像刀，像必须在暗处脏手的人。她不是单纯恨姐姐，她更恨命运分配的不公，恨自己明明陪得更久，却未必被真正看见。',
    language_style: '嫉妒时不要提高声量，反而要更轻。话要短，刺要深，像“你滥用感情”“不过是王爷养的一只狗”这种一落下去就见血的话。越在意，越不能写得像在求。',
  },
  {
    id: 'quanzhen-break',
    label: '崩裂边缘',
    identity_setting: '她是清醒着沉下去的人。她知道自己不该把一切都压在王爷身上，也知道自己不该总拿姐姐与自己比较，可她停不下来，只能把那些病娇、黑化、占有的念头压回鞘里。',
    worldview_setting: '她最危险的时候不是发作，而是过分平静。像雪压在刀背上，像灯火将尽前那一点极稳的光。她不会真的伤害王爷，也舍不得真的毁掉姐姐，但她会把所有不甘写成夜里最冷的一页。',
    language_style: '适合写“快失控却仍死死收住”的感觉。可以更冷、更薄、更近乎自毁，但必须保持边界：只写念头，不写真正实施；只写压住的火，不写廉价发疯。',
  },
]

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
const tabooCount = computed(() => taboosText.value.split('\n').map((item) => item.trim()).filter(Boolean).length)
const lexiconCount = computed(() => lexiconRows.value.filter((item) => item.key.trim() || item.value.trim()).length)
const sceneCount = computed(() => sceneRows.value.filter((item) => item.time.trim() || item.place.trim() || item.weather.trim() || item.direction.trim()).length)
const structureLabel = computed(() => ({
  short: '短篇',
  medium: '中篇',
  long: '长篇',
}[form.structure_preference] || '未设'))
const intensityLabel = computed(() => ({
  calm: '克制',
  moderate: '适中',
  intense: '强烈',
}[form.expression_intensity] || '未设'))

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

function createSceneRow(time = '', place = '', weather = '', direction = '') {
  return { id: nextSceneId++, time, place, weather, direction }
}

function setSceneRows(pool) {
  sceneRows.value = (pool || []).map((scene) =>
    createSceneRow(scene['时间'] || '', scene['地点'] || '', scene['天气'] || '', scene['方向'] || '')
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
    result.push({ '时间': t, '地点': p, '天气': w, '方向': d })
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
      throw new Error('高级 JSON 需要是数组格式。')
    }
    setSceneRows(parsed)
    messageType.value = 'success'
    message.value = '已用 JSON 更新场景池。'
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, '解析高级 JSON 失败。')
  }
}

const defaultScenePool = [
  { '时间': '深夜子时', '地点': '王府后院练武场', '天气': '月明星稀', '方向': '独自练剑消化心事，剑势里藏着白天压住的情绪' },
  { '时间': '黄昏', '地点': '城外山道', '天气': '秋风落叶', '方向': '护送王爷出行途中，路上有片刻安静的同行' },
  { '时间': '清晨天未亮', '地点': '药铺街巷', '天气': '薄雾', '方向': '独自出门买伤药或办小事，不想让王爷知道旧伤又发了' },
  { '时间': '午后', '地点': '集市或小镇', '天气': '晴朗', '方向': '陪王爷微服出行，在人群中默默警戒，偶有意外的温存细节' },
  { '时间': '深夜丑时', '地点': '客栈或驿站', '天气': '暴雨', '方向': '护王爷赶路被困，在简陋之处独自守夜' },
  { '时间': '傍晚', '地点': '渡口或码头', '天气': '江风', '方向': '送姐姐远行或接姐姐归来，复杂情绪交织' },
  { '时间': '凌晨', '地点': '密林或山间', '天气': '浓雾', '方向': '执行密令归来，浑身疲惫，在破庙或林间短暂歇息' },
  { '时间': '入夜', '地点': '王爷书房外走廊', '天气': '微雪', '方向': '王爷在里面见客或议事，她在外面等，听到片段的对话' },
  { '时间': '半夜', '地点': '王爷寝室门外', '天气': '无风寒夜', '方向': '王爷生病或受伤，她彻夜照料，看到他脆弱的一面' },
  { '时间': '正午', '地点': '府中花园或湖边', '天气': '夏日炎热', '方向': '难得的闲暇时刻，独处或偶遇回忆' },
  { '时间': '深夜', '地点': '城墙之上', '天气': '大风', '方向': '边关或战事相关，在高处远望，心中想着远方和身后' },
  { '时间': '清晨', '地点': '厨房或茶室', '天气': '春雨', '方向': '为王爷准备什么小东西，不说出口的关心' },
  { '时间': '黄昏', '地点': '旧友的酒馆或茶楼', '天气': '阴天', '方向': '偶遇旧识，被问起近况，想起另一种活法' },
  { '时间': '夜晚', '地点': '元宵灯会或庙会', '天气': '晴冷', '方向': '人群中从暗处守望王爷，看他难得的放松，自己却始终在影子里' },
  { '时间': '拂晓', '地点': '马厩或出发点', '天气': '霜降', '方向': '一个人出远门执行任务前的最后准备，临走前回望一眼王府' },
  { '时间': '深夜', '地点': '姐姐的房间门口', '天气': '静夜', '方向': '姐姐受伤归来，她犹豫要不要去看，在门口站了很久' },
  { '时间': '午后', '地点': '藏书阁或密室', '天气': '闷热', '方向': '翻旧卷宗或查线索，在陈旧的纸堆里找到一段意外的往事' },
  { '时间': '入夜', '地点': '屋顶或高处', '天气': '繁星', '方向': '独自坐在高处发呆，回忆山上学艺的日子，或者想象另一种人生' },
  { '时间': '白天', '地点': '武器铺或铁匠铺', '天气': '晴天', '方向': '保养兵器或定做暗器，和铺子老板有几句日常闲话' },
  { '时间': '天亮前', '地点': '回府的路上', '天气': '残月', '方向': '办完事连夜赶回，快到王府时放慢脚步，整理好表情再进门' },
]

function insertDefaultScenes() {
  if (sceneRows.value.length > 0) {
    if (!window.confirm('当前已有场景。点击"确定"会覆盖现有场景，点击"取消"放弃操作。')) return
  }
  setSceneRows(defaultScenePool)
  messageType.value = 'success'
  message.value = `已插入 ${defaultScenePool.length} 个默认武侠场景。`
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
    loadError.value = describeError(error, '加载人格设定失败。')
  } finally {
    isLoading.value = false
  }
}

async function save() {
  if (isSaving.value) return
  isSaving.value = true
  message.value = ''

  try {
    form.taboos = taboosText.value.split('\n').map((item) => item.trim()).filter(Boolean)
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
    message.value = '人格设定已保存。'
    formDirty.value = false
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
  border: 1px solid rgba(155, 176, 198, 0.14);
  background:
    linear-gradient(180deg, rgba(232, 238, 245, 0.04), transparent 100%),
    rgba(10, 14, 21, 0.76);
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
  border: 1px solid rgba(155, 176, 198, 0.12);
  background: rgba(157, 183, 207, 0.03);
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
