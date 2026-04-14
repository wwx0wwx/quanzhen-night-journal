<template>
  <section class="stack">
    <div class="hero">
      <div>
        <h1>记忆碎片（素材）</h1>
        <p>按人格设定维护长期设定、检索结果和手动补充的关键素材。</p>
      </div>
    </div>

    <div v-if="message" class="status-banner" :class="messageType">{{ message }}</div>

    <div class="grid two">
      <div class="panel panel-pad stack">
        <div class="section-title">快速搜索</div>
        <div class="form-grid">
          <label class="field">
            <span>人格设定（写作风格）</span>
            <select v-model.number="search.persona_id">
              <option v-for="persona in personas" :key="persona.id" :value="persona.id">{{ persona.name }}</option>
            </select>
          </label>
          <label class="field">
            <span>搜索语句</span>
            <input v-model="search.query" placeholder="例如：雨夜、机房、门口的风" />
          </label>
          <label class="field">
            <span>记忆层级</span>
            <select v-model="search.level">
              <option value="">全部层级</option>
              <option v-for="item in levelOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
            </select>
          </label>
        </div>
        <div class="button-row">
          <button class="btn primary" type="button" @click="runSearch">检索</button>
        </div>
        <AppEmpty
          v-if="!hits.length"
          inline
          title="还没有检索结果"
          description="输入一个关键词后，系统会从当前风格的记忆中找相关素材。"
        />
        <div v-else class="list">
          <div v-for="item in hits" :key="item.id" class="list-item stack">
            <div class="button-row">
              <span class="tag">{{ levelLabel(item.level) }}</span>
              <span class="tag">{{ personaName(search.persona_id) }}</span>
            </div>
            <strong>{{ item.summary || item.content }}</strong>
            <div class="muted">相似度 {{ formatScore(item.similarity) }}，综合分 {{ formatScore(item.weighted_score) }}</div>
            <div class="muted">{{ item.content }}</div>
          </div>
        </div>
      </div>

      <div class="panel panel-pad stack">
        <div class="section-title">新增长期设定</div>
        <label class="field">
          <span>人格设定（写作风格）</span>
          <select v-model.number="form.persona_id">
            <option v-for="persona in personas" :key="persona.id" :value="persona.id">{{ persona.name }}</option>
          </select>
        </label>
        <label class="field">
          <span>层级</span>
          <select v-model="form.level">
            <option v-for="item in levelOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
          </select>
        </label>
        <label class="field">
          <span>内容</span>
          <textarea v-model="form.content" placeholder="输入这条素材或长期设定的完整内容。"></textarea>
        </label>
        <label class="field">
          <span>标签（用顿号或逗号分隔）</span>
          <input v-model="tagsText" placeholder="例如：雨夜、门口、机房" />
        </label>
        <button class="btn primary" type="button" @click="createMemory">保存素材</button>
      </div>
    </div>

    <MemoryTree :memories="memories" :personas="personas" />
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

import { api, unwrap } from '../api'
import AppEmpty from '../components/AppEmpty.vue'
import MemoryTree from '../components/MemoryTree.vue'
import { describeError } from '../utils/errors'

const levelOptions = [
  { value: 'L0', label: 'L0 核心设定' },
  { value: 'L1', label: 'L1 长期主题' },
  { value: 'L2', label: 'L2 近期线索' },
  { value: 'L3', label: 'L3 瞬时片段' },
]

const memories = ref([])
const personas = ref([])
const hits = ref([])
const message = ref('')
const messageType = ref('info')
const search = reactive({ query: '', persona_id: null, top_k: 5, level: '' })
const form = reactive({
  persona_id: null,
  level: 'L0',
  content: '',
  summary: '',
  tags: ['manual'],
  source: 'hand_written',
  weight: 1,
  review_status: 'reviewed',
  decay_strategy: 'standard',
  is_core: true,
})
const tagsText = ref('')

function levelLabel(level) {
  return levelOptions.find((item) => item.value === level)?.label || level
}

function personaName(personaId) {
  return personas.value.find((item) => item.id === personaId)?.name || `#${personaId}`
}

function formatScore(value) {
  return Number(value || 0).toFixed(2)
}

function normalizeTags() {
  return tagsText.value
    .split(/[，,、]/)
    .map((item) => item.trim())
    .filter(Boolean)
}

async function load() {
  const [memoryData, personaData] = await Promise.all([
    unwrap(api.get('/memories', { params: { page_size: 100 } })),
    unwrap(api.get('/personas')),
  ])
  memories.value = memoryData.items
  personas.value = personaData

  const defaultPersonaId = personaData[0]?.id || null
  if (!search.persona_id) search.persona_id = defaultPersonaId
  if (!form.persona_id) form.persona_id = defaultPersonaId
}

async function runSearch() {
  if (!search.persona_id || !search.query.trim()) {
    messageType.value = 'warning'
    message.value = '请先选择人格设定并输入搜索语句。'
    return
  }
  message.value = ''
  try {
    hits.value = await unwrap(api.post('/memories/search', {
      query: search.query,
      persona_id: search.persona_id,
      top_k: search.top_k,
      level_filter: search.level ? [search.level] : null,
    }))
    if (!hits.value.length) {
      messageType.value = 'info'
      message.value = '没有找到相关素材，可以换个关键词或先补充几条长期设定。'
    }
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, '检索素材失败。')
  }
}

async function createMemory() {
  if (!form.persona_id || !form.content.trim()) {
    messageType.value = 'warning'
    message.value = '请先选择人格设定并填写内容。'
    return
  }
  message.value = ''
  try {
    form.summary = form.content.trim().slice(0, 120)
    form.tags = normalizeTags().length ? normalizeTags() : ['manual']
    await unwrap(api.post('/memories', form))
    form.content = ''
    tagsText.value = ''
    messageType.value = 'success'
    message.value = '素材已保存。'
    await load()
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, '保存素材失败。')
  }
}

onMounted(load)
</script>
