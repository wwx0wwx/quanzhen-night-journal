<template>
  <section class="stack memories-page">
    <AppLoading
      v-if="isLoading"
      title="正在加载素材"
      description="正在读取记忆列表、人格设定和当前分页。"
    />

    <AppError
      v-else-if="loadError"
      title="素材页加载失败"
      :message="loadError"
      action-label="重试"
      @retry="load"
    />

    <template v-else>
      <div class="hero memories-hero">
        <div>
          <div class="hero-kicker">Memory Ledger</div>
          <h1>记忆碎片（素材）</h1>
          <p>按人格设定维护长期设定、检索结果和手动补充的关键素材。先确认该写作人格记得什么，再决定应该继续补写哪一层。</p>
        </div>
        <div class="memories-hero-aside">
          <div class="button-row">
            <span class="tag">{{ personas.length }} 组人格</span>
            <span class="tag">总计 {{ total }} 条</span>
            <span class="tag">当前 {{ memories.length }} 条</span>
          </div>
          <div class="muted">搜索负责唤回旧记忆，补录负责把新的冷线索收入档案。</div>
        </div>
      </div>

      <div v-if="message" class="status-banner" :class="messageType">{{ message }}</div>

      <div class="card-row">
        <div class="metric">
          <div class="muted">当前检索人格</div>
          <strong>{{ currentPersonaName }}</strong>
          <div class="muted">检索时会优先使用该人格对应的长期设定与近期线索。</div>
        </div>
        <div class="metric">
          <div class="muted">最近命中</div>
          <strong>{{ hits.length }}</strong>
          <div class="muted">{{ hits.length ? '已返回相关素材，可直接比对摘要与全文。' : '当前还没有检索结果。' }}</div>
        </div>
        <div class="metric">
          <div class="muted">当前页码</div>
          <strong>{{ page }} / {{ totalPages }}</strong>
          <div class="muted">分页浏览历史素材，避免一次性加载全部长列表。</div>
        </div>
      </div>

      <div class="grid two memories-grid">
        <div class="panel panel-pad stack memory-search-card">
          <div class="memory-card-head">
            <div>
              <div class="hero-kicker">Recall Desk</div>
              <div class="section-title">快速搜索</div>
              <p class="muted">输入场景、意象或动作词，检索当前人格下最接近的记忆条目。</p>
            </div>
            <div class="memory-card-glyph" aria-hidden="true">
              <span></span>
              <span></span>
            </div>
          </div>
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
            <div v-for="item in hits" :key="item.id" class="list-item stack memory-hit">
              <div class="split memories-hit-head">
                <div class="button-row">
                  <span class="tag">{{ levelLabel(item.level) }}</span>
                  <span class="tag">{{ personaName(search.persona_id) }}</span>
                </div>
                <span class="memory-score">综合分 {{ formatScore(item.weighted_score) }}</span>
              </div>
              <strong>{{ item.summary || item.content }}</strong>
              <div class="muted">相似度 {{ formatScore(item.similarity) }}，越高说明与当前搜索语句越接近。</div>
              <div class="muted">{{ item.content }}</div>
            </div>
          </div>
        </div>

        <div class="panel panel-pad stack memory-create-card">
          <div class="memory-card-head">
            <div>
              <div class="hero-kicker">Manual Entry</div>
              <div class="section-title">新增长期设定</div>
              <p class="muted">把新确认的事实、意象或长期线索直接补录进记忆层级，避免后续写作时漂移。</p>
            </div>
            <div class="memory-card-glyph memory-card-glyph-right" aria-hidden="true">
              <span></span>
              <span></span>
            </div>
          </div>
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

      <div class="panel panel-pad split">
        <div class="muted">第 {{ page }} / {{ totalPages }} 页，共 {{ total }} 条</div>
        <div class="button-row">
          <button class="btn ghost btn-small" :disabled="page <= 1 || isLoading" @click="changePage(page - 1)">上一页</button>
          <button class="btn ghost btn-small" :disabled="page >= totalPages || isLoading" @click="changePage(page + 1)">下一页</button>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import { api, unwrap } from '../api'
import AppError from '../components/AppError.vue'
import AppEmpty from '../components/AppEmpty.vue'
import AppLoading from '../components/AppLoading.vue'
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
const isLoading = ref(true)
const loadError = ref('')
const message = ref('')
const messageType = ref('info')
const search = reactive({ query: '', persona_id: null, top_k: 5, level: '' })
const page = ref(1)
const pageSize = 20
const total = ref(0)
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
const currentPersonaName = computed(() => personaName(search.persona_id) || '未选择')
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

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
  isLoading.value = true
  loadError.value = ''
  try {
    const [memoryData, personaData] = await Promise.all([
      unwrap(api.get('/memories', { params: { page: page.value, page_size: pageSize } })),
      unwrap(api.get('/personas')),
    ])
    memories.value = memoryData.items || []
    total.value = Number(memoryData.total || 0)
    personas.value = personaData || []

    const defaultPersonaId = personaData[0]?.id || null
    if (!search.persona_id) search.persona_id = defaultPersonaId
    if (!form.persona_id) form.persona_id = defaultPersonaId
  } catch (error) {
    loadError.value = describeError(error, '加载素材失败，请稍后重试。')
  } finally {
    isLoading.value = false
  }
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
    page.value = 1
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

function changePage(nextPage) {
  if (nextPage < 1 || nextPage > totalPages.value) return
  page.value = nextPage
  load()
}

onMounted(load)
</script>

<style scoped>
.memories-page {
  gap: 22px;
}

.memories-hero {
  align-items: end;
}

.memories-hero-aside {
  display: grid;
  gap: 10px;
  justify-items: end;
  max-width: 280px;
  text-align: right;
}

.memories-grid {
  align-items: start;
}

.memory-search-card,
.memory-create-card {
  min-height: 100%;
}

.memory-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}

.memory-card-head p {
  margin: 10px 0 0;
  max-width: 46ch;
  line-height: 1.7;
}

.memory-card-glyph {
  display: grid;
  gap: 10px;
  min-width: 96px;
  padding-top: 10px;
}

.memory-card-glyph span {
  display: block;
  height: 1px;
  background: linear-gradient(90deg, rgba(216, 229, 240, 0.5), transparent);
}

.memory-card-glyph span:last-child {
  width: 70%;
}

.memory-card-glyph-right span {
  background: linear-gradient(90deg, transparent, rgba(216, 229, 240, 0.5));
  justify-self: end;
}

.memory-hit {
  gap: 12px;
}

.memories-hit-head {
  align-items: center;
}

.memory-score {
  color: var(--accent-soft);
  font-size: 0.82rem;
  letter-spacing: 0.12em;
}

@media (max-width: 900px) {
  .memories-hero-aside {
    justify-items: start;
    max-width: none;
    text-align: left;
  }
}

@media (max-width: 680px) {
  .memory-card-head,
  .memories-hit-head {
    flex-direction: column;
  }
}
</style>
