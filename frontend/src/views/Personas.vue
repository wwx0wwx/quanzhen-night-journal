<template>
  <section class="stack">
    <AppLoading
      v-if="isLoading"
      title="正在加载人格"
      description="正在获取人格列表与默认人格状态。"
    />

    <AppError
      v-else-if="loadError"
      title="人格列表加载失败"
      :message="loadError"
      action-label="重新加载"
      @retry="load"
    />

    <template v-else>
      <div class="hero personas-hero">
        <div>
          <div class="hero-kicker">Persona Register</div>
          <h1>人格设定（写作风格）</h1>
          <p>维护不同人格设定、默认人格，以及对应的语言习惯和感知词典。每一张人格卡都应该像一份可长期复用的夜间角色档案。</p>
        </div>
        <div class="personas-hero-actions">
          <div class="muted">默认人格决定当前系统主要写作口吻，其余人格更适合作为分支风格或专题语气。</div>
          <RouterLink class="btn primary" to="/admin/personas/new">新建人格设定</RouterLink>
        </div>
      </div>

      <div v-if="actionError" class="status-banner error">{{ actionError }}</div>

      <div class="card-row">
        <div class="metric">
          <div class="muted">人格总数</div>
          <strong>{{ personas.length }}</strong>
          <div class="muted">包含当前默认人格在内的全部已建档风格。</div>
        </div>
        <div class="metric">
          <div class="muted">启用中</div>
          <strong>{{ activeCount }}</strong>
          <div class="muted">仍可被编辑、切换和用于生成任务的人格卡。</div>
        </div>
        <div class="metric">
          <div class="muted">默认人格</div>
          <strong>{{ defaultPersonaName }}</strong>
          <div class="muted">默认人格会优先参与写作与记忆读取。</div>
        </div>
      </div>

      <AppEmpty
        v-if="!personas.length"
        title="还没有额外人格设定"
        description="当前只有默认人格。可以先新建一个人格设定，再按写作需求切换使用。"
      />

      <div v-else class="list persona-list">
        <div
          v-for="persona in personas"
          :key="persona.id"
          class="list-item panel stack persona-card"
        >
          <div class="split persona-card-head">
            <div class="persona-card-title">
              <div class="persona-card-index">#{{ persona.id }}</div>
              <strong>{{ persona.name }}</strong>
              <div class="muted">{{ persona.description || '暂无描述' }}</div>
            </div>
            <div class="button-row">
              <span class="tag" v-if="persona.is_default">默认</span>
              <span class="tag">{{ persona.structure_preference }}</span>
              <span class="tag" :class="persona.is_active ? 'tag-success' : 'tag-warning'">
                {{ persona.is_active ? '启用中' : '已停用' }}
              </span>
            </div>
          </div>

          <div class="persona-details">
            <div class="persona-detail">
              <span>篇幅偏好</span>
              <strong>{{ structureLabel(persona.structure_preference) }}</strong>
            </div>
            <div class="persona-detail">
              <span>情绪强度</span>
              <strong>{{ intensityLabel(persona.expression_intensity) }}</strong>
            </div>
            <div class="persona-detail">
              <span>词典规模</span>
              <strong>{{ lexiconCount(persona) }}</strong>
            </div>
          </div>

          <div class="button-row">
            <RouterLink class="btn ghost btn-small" :to="`/admin/personas/${persona.id}`">编辑</RouterLink>
            <button
              class="btn ghost btn-small"
              :disabled="isDeleting === persona.id || persona.is_default"
              @click="removePersona(persona)"
            >
              {{ isDeleting === persona.id ? '删除中...' : '删除' }}
            </button>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import AppEmpty from '../components/AppEmpty.vue'
import AppError from '../components/AppError.vue'
import AppLoading from '../components/AppLoading.vue'
import { usePersonaStore } from '../stores/persona'
import { describeError } from '../utils/errors'

const store = usePersonaStore()
const personas = ref([])
const isLoading = ref(true)
const loadError = ref('')
const actionError = ref('')
const isDeleting = ref(null)
const activeCount = computed(() => personas.value.filter((item) => item.is_active).length)
const defaultPersonaName = computed(() => personas.value.find((item) => item.is_default)?.name || '未设')

function structureLabel(value) {
  return {
    short: '短篇',
    medium: '中篇',
    long: '长篇',
  }[value] || '未设'
}

function intensityLabel(value) {
  return {
    calm: '克制',
    moderate: '适中',
    intense: '强烈',
  }[value] || '未设'
}

function lexiconCount(persona) {
  return Object.keys(persona.sensory_lexicon || {}).length || 0
}

async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    personas.value = await store.load()
  } catch (error) {
    loadError.value = describeError(error, '加载人格列表失败。')
  } finally {
    isLoading.value = false
  }
}

async function removePersona(persona) {
  if (isDeleting.value || persona.is_default) return
  if (!window.confirm(`确认删除人格设定「${persona.name}」？此操作不可撤销。`)) return

  actionError.value = ''
  isDeleting.value = persona.id
  try {
    personas.value = await store.remove(persona.id)
  } catch (error) {
    actionError.value = describeError(error, '删除人格设定失败。')
  } finally {
    isDeleting.value = null
  }
}

onMounted(load)
</script>

<style scoped>
.personas-hero {
  align-items: end;
}

.personas-hero-actions {
  display: grid;
  gap: 12px;
  justify-items: end;
  max-width: 300px;
  text-align: right;
}

.persona-list {
  gap: 16px;
}

.persona-card {
  gap: 18px;
}

.persona-card-head {
  align-items: flex-start;
}

.persona-card-title {
  display: grid;
  gap: 8px;
}

.persona-card-index {
  color: var(--accent-soft);
  font-size: 0.74rem;
  letter-spacing: 0.24em;
  text-transform: uppercase;
}

.persona-details {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.persona-detail {
  display: grid;
  gap: 8px;
  padding: 14px 16px;
  border-radius: 14px;
  border: 1px solid rgba(155, 176, 198, 0.12);
  background: rgba(157, 183, 207, 0.03);
}

.persona-detail span {
  color: var(--muted);
  font-size: 0.76rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.persona-detail strong {
  font-family: var(--font-display);
  letter-spacing: 0.04em;
}

@media (max-width: 900px) {
  .personas-hero-actions {
    justify-items: start;
    max-width: none;
    text-align: left;
  }
}

@media (max-width: 680px) {
  .persona-details {
    grid-template-columns: 1fr;
  }
}
</style>
