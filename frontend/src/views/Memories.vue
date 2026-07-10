<template>
  <section class="stack memories-page">
    <AppLoading
      v-if="isLoading"
      title="正在加载素材"
      description="正在读取长期记忆列表。"
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
<h1>{{ t('memories.title') }}</h1>
          <p>
            {{ t('memories.subtitle') }}
          </p>
        </div>
        <div class="memories-hero-aside">
          <div class="button-row">
            <span class="tag">{{ personas.length }} 个角色</span>
            <span class="tag">总计 {{ total }} 条</span>
            <span class="tag">当前 {{ memories.length }} 条</span>
          </div>
          <div class="muted">
            搜索负责唤回旧记忆，补录负责把新的冷线索收入档案。
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

      <div class="card-row">
        <div class="metric">
          <div class="muted">
            当前角色
          </div>
          <strong>{{ currentPersonaName }}</strong>
          <div class="muted">
            会在该角色下查找相关记忆。
          </div>
        </div>
        <div class="metric">
          <div class="muted">
            最近命中
          </div>
          <strong>{{ hits.length }}</strong>
          <div class="muted">
            {{ hits.length ? '已返回相关素材，可直接比对摘要与全文。' : '当前还没有检索结果。' }}
          </div>
        </div>
        <div class="metric">
          <div class="muted">
            当前页码
          </div>
          <strong>{{ page }} / {{ totalPages }}</strong>
          <div class="muted">
            分页浏览历史素材，避免一次性加载全部长列表。
          </div>
        </div>
      </div>

      <div class="grid two memories-grid">
        <div class="panel panel-pad stack memory-search-card">
          <div class="memory-card-head">
            <div>
<div class="section-title">
                快速搜索
              </div>
              <p class="muted">
                输入关键词，查找相关记忆。
              </p>
            </div>
            <div
              class="memory-card-glyph"
              aria-hidden="true"
            >
              <span />
              <span />
            </div>
          </div>
          <div class="form-grid">
            <label class="field">
              <span>角色设定</span>
              <select v-model.number="search.persona_id">
                <option
                  v-for="persona in personas"
                  :key="persona.id"
                  :value="persona.id"
                >{{ persona.name }}</option>
              </select>
            </label>
            <label class="field">
              <span>搜索语句</span>
              <input
                v-model="search.query"
                placeholder="例如：雨夜、机房、门口的风"
              >
            </label>
            <label class="field">
              <span>记忆层级</span>
              <select v-model="search.level">
                <option value="">全部层级</option>
                <option
                  v-for="item in levelOptions"
                  :key="item.value"
                  :value="item.value"
                >{{ item.label }}</option>
              </select>
            </label>
          </div>
          <div class="button-row">
            <button
              class="btn primary"
              type="button"
              @click="runSearch"
            >
              检索
            </button>
          </div>
          <AppEmpty
            v-if="!hits.length"
            inline
            title="还没有检索结果"
            description="输入一个关键词后，系统会从当前风格的记忆中找相关素材。"
          />
          <div
            v-else
            class="list"
          >
            <div
              v-for="item in hits"
              :key="item.id"
              class="list-item stack memory-hit"
            >
              <div class="split memories-hit-head">
                <div class="button-row">
                  <span class="tag">{{ levelLabel(item.level) }}</span>
                  <span class="tag">{{ personaName(search.persona_id) }}</span>
                </div>
                <span class="memory-score">综合分 {{ formatScore(item.weighted_score) }}</span>
              </div>
              <strong>{{ item.summary || item.content }}</strong>
              <div class="muted">
                相似度 {{ formatScore(item.similarity) }}，越高说明与当前搜索语句越接近。
              </div>
              <div class="muted">
                {{ item.content }}
              </div>
            </div>
          </div>
        </div>

        <div class="panel panel-pad stack memory-create-card">
          <div class="memory-card-head">
            <div>
<div class="section-title">
                新增长期设定
              </div>
              <p class="muted">
                把新确认的事实、意象或长期线索直接补录进记忆层级，避免后续写作时漂移。
              </p>
            </div>
            <div
              class="memory-card-glyph memory-card-glyph-right"
              aria-hidden="true"
            >
              <span />
              <span />
            </div>
          </div>
          <label class="field">
            <span>角色设定</span>
            <select v-model.number="form.persona_id">
              <option
                v-for="persona in personas"
                :key="persona.id"
                :value="persona.id"
              >{{ persona.name }}</option>
            </select>
          </label>
          <label class="field">
            <span>层级</span>
            <select v-model="form.level">
              <option
                v-for="item in levelOptions"
                :key="item.value"
                :value="item.value"
              >{{ item.label }}</option>
            </select>
          </label>
          <label class="field">
            <span>内容</span>
            <textarea
              v-model="form.content"
              placeholder="输入这条素材或长期设定的完整内容。"
            />
          </label>
          <label class="field">
            <span>标签（用顿号或逗号分隔）</span>
            <input
              v-model="tagsText"
              placeholder="例如：雨夜、门口、机房"
            >
          </label>
          <button
            class="btn primary"
            type="button"
            :disabled="isCreating"
            @click="createMemory"
          >
            {{ isCreating ? '保存中…' : '保存素材' }}
          </button>
        </div>
      </div>

      <MemoryTree
        :memories="memories"
        :personas="personas"
        @select="startEdit"
      />

      <div class="grid two memories-governance-grid">
        <div class="panel panel-pad stack">
          <div class="split">
            <div>
              <div class="section-title">
                当前页素材治理
              </div>
              <div class="muted">
                对已归档素材执行编辑、复核、提升或删除。
              </div>
            </div>
            <span class="tag">{{ memories.length }} 条</span>
          </div>

          <AppEmpty
            v-if="!memories.length"
            inline
            title="当前页没有素材"
            description="新增素材或切换分页后可在这里治理记忆。"
          />

          <div
            v-else
            class="list"
          >
            <div
              v-for="item in memories"
              :key="item.id"
              class="list-item stack memory-row"
              :class="{ active: editing.id === item.id }"
            >
              <div class="split">
                <div
                  class="stack"
                  style="gap: 6px"
                >
                  <div class="button-row">
                    <span class="tag">{{ levelLabel(item.level) }}</span>
                    <span class="tag">{{ reviewStatusLabel(item.review_status) }}</span>
                    <span
                      v-if="item.is_core"
                      class="tag tag-success"
                    >核心</span>
                  </div>
                  <strong>{{ item.summary || item.content }}</strong>
                  <div class="muted">
                    {{ personaName(item.persona_id) }} · {{ item.source }} · 权重 {{ Number(item.weight || 0).toFixed(2) }}
                  </div>
                </div>
                <div class="button-row memory-row-actions">
                  <button
                    class="btn ghost btn-small"
                    type="button"
                    @click="startEdit(item)"
                  >
                    编辑
                  </button>
                  <button
                    class="btn ghost btn-small"
                    type="button"
                    :disabled="actionBusy"
                    @click="markReviewed(item)"
                  >
                    复核
                  </button>
                  <button
                    class="btn ghost btn-small"
                    type="button"
                    :disabled="actionBusy"
                    @click="promoteMemory(item)"
                  >
                    提升
                  </button>
                  <button
                    class="btn ghost btn-small"
                    type="button"
                    :disabled="actionBusy"
                    @click="deleteMemory(item)"
                  >
                    删除
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="panel panel-pad stack">
          <div class="section-title">
            编辑素材
          </div>
          <AppEmpty
            v-if="!editing.id"
            inline
            title="未选择素材"
            description="从当前页或分层视图选择一条素材后，可在这里修改内容。"
          />
          <template v-else>
            <div class="button-row">
              <span class="tag">#{{ editing.id }}</span>
              <span class="tag">{{ personaName(editing.persona_id) }}</span>
            </div>
            <label class="field">
              <span>层级</span>
              <select v-model="editing.level">
                <option
                  v-for="item in levelOptions"
                  :key="item.value"
                  :value="item.value"
                >{{ item.label }}</option>
              </select>
            </label>
            <label class="field">
              <span>内容</span>
              <textarea v-model="editing.content" />
            </label>
            <label class="field">
              <span>摘要</span>
              <textarea v-model="editing.summary" />
            </label>
            <label class="field">
              <span>标签</span>
              <input v-model="editingTagsText">
            </label>
            <div class="form-grid">
              <label class="field">
                <span>权重</span>
                <input
                  v-model.number="editing.weight"
                  min="0"
                  step="0.1"
                  type="number"
                >
              </label>
              <label class="field">
                <span>复核状态</span>
                <select v-model="editing.review_status">
                  <option value="unreviewed">
                    未复核
                  </option>
                  <option value="reviewed">
                    已复核
                  </option>
                  <option value="promoted">
                    已提升
                  </option>
                </select>
              </label>
            </div>
            <label class="toggle-control memory-core-toggle">
              <input
                v-model="editing.is_core"
                type="checkbox"
              >
              <span>核心素材</span>
            </label>
            <div class="button-row">
              <button
                class="btn primary"
                type="button"
                :disabled="actionBusy"
                @click="saveMemory"
              >
                {{ activeAction === 'save' ? '保存中…' : '保存修改' }}
              </button>
              <button
                class="btn ghost"
                type="button"
                :disabled="actionBusy"
                @click="clearEditing"
              >
                取消
              </button>
            </div>
          </template>
        </div>
      </div>

      <div class="panel panel-pad split">
        <div class="muted">
          第 {{ page }} / {{ totalPages }} 页，共 {{ total }} 条
        </div>
        <div class="button-row">
          <button
            class="btn ghost btn-small"
            :disabled="page <= 1 || isLoading"
            @click="changePage(page - 1)"
          >
            上一页
          </button>
          <button
            class="btn ghost btn-small"
            :disabled="page >= totalPages || isLoading"
            @click="changePage(page + 1)"
          >
            下一页
          </button>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { api, unwrap } from '../api'
import AppError from '../components/AppError.vue'
import AppEmpty from '../components/AppEmpty.vue'
import AppLoading from '../components/AppLoading.vue'
import MemoryTree from '../components/MemoryTree.vue'
import { describeError } from '../utils/errors'
import {
  MEMORY_LEVEL_OPTIONS,
  createEmptyMemoryForm,
  formatScore as formatMemoryScore,
  levelLabel as formatMemoryLevel,
  normalizeTags as normalizeMemoryTags,
  parseTags as parseMemoryTags,
  reviewStatusLabel as formatReviewStatus,
} from '../utils/memoryForm'

const { t } = useI18n()

const levelOptions = MEMORY_LEVEL_OPTIONS

const memories = ref([])
const personas = ref([])
const hits = ref([])
const isLoading = ref(true)
const isCreating = ref(false)
const loadError = ref('')
const message = ref('')
const messageType = ref('info')
const activeAction = ref('')
const search = reactive({ query: '', persona_id: null, top_k: 5, level: '' })
const page = ref(1)
const pageSize = 20
const total = ref(0)
const form = reactive(createEmptyMemoryForm(1))
const tagsText = ref('')
const editing = reactive({
  id: null,
  persona_id: null,
  level: 'L0',
  content: '',
  summary: '',
  tags: [],
  weight: 1,
  review_status: 'unreviewed',
  is_core: false,
})
const editingTagsText = ref('')
const currentPersonaName = computed(() => personaName(search.persona_id) || '未选择')
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
const actionBusy = computed(() => Boolean(activeAction.value))

const levelLabel = formatMemoryLevel

function personaName(personaId) {
  return personas.value.find((item) => item.id === personaId)?.name || `#${personaId}`
}

const formatScore = formatMemoryScore

const reviewStatusLabel = formatReviewStatus

const normalizeTags = normalizeMemoryTags

const parseTags = parseMemoryTags

function startEdit(memory) {
  Object.assign(editing, {
    id: memory.id,
    persona_id: memory.persona_id,
    level: memory.level,
    content: memory.content || '',
    summary: memory.summary || '',
    tags: memory.tags || [],
    weight: Number(memory.weight ?? 1),
    review_status: memory.review_status || 'unreviewed',
    is_core: Boolean(memory.is_core),
  })
  editingTagsText.value = (memory.tags || []).join('、')
}

function clearEditing() {
  Object.assign(editing, {
    id: null,
    persona_id: null,
    level: 'L0',
    content: '',
    summary: '',
    tags: [],
    weight: 1,
    review_status: 'unreviewed',
    is_core: false,
  })
  editingTagsText.value = ''
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
    message.value = '请先选择角色并输入搜索内容。'
    return
  }
  message.value = ''
  try {
    hits.value = await unwrap(
      api.post('/memories/search', {
        query: search.query,
        persona_id: search.persona_id,
        top_k: search.top_k,
        level_filter: search.level ? [search.level] : null,
      }),
    )
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
    message.value = '请先选择角色并填写内容。'
    return
  }
  message.value = ''
  isCreating.value = true
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
  } finally {
    isCreating.value = false
  }
}

async function saveMemory() {
  if (!editing.id || activeAction.value) return
  if (!editing.content.trim()) {
    messageType.value = 'warning'
    message.value = '素材内容不能为空。'
    return
  }
  activeAction.value = 'save'
  message.value = ''
  try {
    const updated = await unwrap(
      api.put(`/memories/${editing.id}`, {
        level: editing.level,
        content: editing.content,
        summary: editing.summary,
        tags: parseTags(editingTagsText.value),
        weight: editing.weight,
        review_status: editing.review_status,
        is_core: editing.is_core,
      }),
    )
    messageType.value = 'success'
    message.value = '素材已更新。'
    startEdit(updated)
    await load()
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, '更新素材失败。')
  } finally {
    activeAction.value = ''
  }
}

async function markReviewed(memory) {
  if (activeAction.value) return
  activeAction.value = `review:${memory.id}`
  message.value = ''
  try {
    const updated = await unwrap(api.put(`/memories/${memory.id}`, { review_status: 'reviewed' }))
    messageType.value = 'success'
    message.value = '素材已标记为已复核。'
    if (editing.id === memory.id) startEdit(updated)
    await load()
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, '复核素材失败。')
  } finally {
    activeAction.value = ''
  }
}

async function promoteMemory(memory) {
  if (activeAction.value) return
  activeAction.value = `promote:${memory.id}`
  message.value = ''
  try {
    const updated = await unwrap(api.post(`/memories/${memory.id}/promote`))
    messageType.value = 'success'
    message.value = '素材已提升。'
    if (editing.id === memory.id) startEdit(updated)
    await load()
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, '提升素材失败。')
  } finally {
    activeAction.value = ''
  }
}

async function deleteMemory(memory) {
  if (activeAction.value) return
  if (!window.confirm(`确认删除素材 #${memory.id} 吗？此操作不能撤销。`)) return
  activeAction.value = `delete:${memory.id}`
  message.value = ''
  try {
    await unwrap(api.delete(`/memories/${memory.id}`))
    if (editing.id === memory.id) clearEditing()
    messageType.value = 'success'
    message.value = '素材已删除。'
    await load()
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, '删除素材失败。')
  } finally {
    activeAction.value = ''
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

.memories-governance-grid {
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
  background: linear-gradient(90deg, var(--line-strong), transparent);
}

.memory-card-glyph span:last-child {
  width: 70%;
}

.memory-card-glyph-right span {
  background: linear-gradient(90deg, transparent, var(--line-strong));
  justify-self: end;
}

.memory-hit {
  gap: 12px;
}

.memory-row.active {
  border-color: var(--accent-strong);
  background: var(--accent-glow);
}

.memory-row-actions {
  justify-content: flex-end;
}

.memory-core-toggle {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--secondary);
}

.memories-hit-head {
  align-items: center;
}

.memory-score {
  color: var(--accent-soft);
  font-size: 0.82rem;
  letter-spacing: 0.12em;
  flex-shrink: 0;
  white-space: nowrap;
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
  .memories-hit-head,
  .memory-row .split {
    flex-direction: column;
  }

  .memory-row-actions {
    justify-content: flex-start;
  }
}
</style>
