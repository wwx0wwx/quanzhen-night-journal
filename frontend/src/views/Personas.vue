<template>
  <section class="stack">
    <AppLoading
      v-if="isLoading"
      :title="t('personas.loadingTitle')"
      :description="t('personas.loadingDesc')"
    />

    <AppError
      v-else-if="loadError"
      :title="t('personas.loadError')"
      :message="loadError"
      action-label="重新加载"
      @retry="load"
    />

    <template v-else>
      <div class="hero personas-hero">
        <div>
<h1>{{ t('personas.title') }}</h1>
          <p>
            {{ t('personas.subtitle') }}
          </p>
        </div>
        <div class="personas-hero-actions">
          <div class="muted">
            默认角色用于日常自动写作；其他角色可以在需要时选用。
          </div>
          <RouterLink
            class="btn primary"
            to="/admin/personas/new"
          >
            {{ t('personas.newPersona') }}
          </RouterLink>
        </div>
      </div>

      <div
        v-if="actionError"
        class="status-banner error"
      >
        {{ actionError }}
      </div>

      <div class="card-row">
        <div class="metric">
          <div class="muted">
            角色数量
          </div>
          <strong>{{ personas.length }}</strong>
          <div class="muted">
            已创建的全部角色。
          </div>
        </div>
        <div class="metric">
          <div class="muted">
            启用中
          </div>
          <strong>{{ activeCount }}</strong>
          <div class="muted">
            仍可编辑和使用的角色。
          </div>
        </div>
        <div class="metric">
          <div class="muted">
            默认角色
          </div>
          <strong>{{ defaultPersonaName }}</strong>
          <div class="muted">
            默认角色会优先参与写作与记忆读取。
          </div>
        </div>
      </div>

      <AppEmpty
        v-if="!personas.length"
        title="还没有其他角色"
        description="当前只有默认角色。可以再建几个不同风格的角色。"
      />

      <div
        v-else
        class="list persona-list"
      >
        <div
          v-for="persona in personas"
          :key="persona.id"
          class="list-item panel stack persona-card"
        >
          <div class="split persona-card-head">
            <div class="persona-card-title">
              <div class="persona-card-index">
                #{{ persona.id }}
              </div>
              <strong>{{ persona.name }}</strong>
              <div class="muted">
                {{ persona.description || '暂无描述' }}
              </div>
            </div>
            <div class="button-row">
              <span
                v-if="persona.is_default"
                class="tag"
              >默认</span>
              <span class="tag">{{ persona.structure_preference }}</span>
              <span
                class="tag"
                :class="persona.is_active ? 'tag-success' : 'tag-warning'"
              >
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
            <RouterLink
              class="btn ghost btn-small"
              :to="`/admin/personas/${persona.id}`"
            >
              编辑
            </RouterLink>
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
import { useI18n } from 'vue-i18n'
import { confirmAction } from '../composables/useConfirm'
import { useToastStore } from '../stores/toast'

import AppEmpty from '../components/AppEmpty.vue'
import AppError from '../components/AppError.vue'
import AppLoading from '../components/AppLoading.vue'
import { usePersonaStore } from '../stores/persona'
import { describeError } from '../utils/errors'

const { t } = useI18n()
const toast = useToastStore()

const store = usePersonaStore()
const personas = ref([])
const isLoading = ref(true)
const loadError = ref('')
const actionError = ref('')
const isDeleting = ref(null)
const activeCount = computed(() => personas.value.filter((item) => item.is_active).length)
const defaultPersonaName = computed(() => personas.value.find((item) => item.is_default)?.name || '未设')

function structureLabel(value) {
  return (
    {
      short: '短篇',
      medium: '中篇',
      long: '长篇',
    }[value] || '未设'
  )
}

function intensityLabel(value) {
  return (
    {
      calm: '克制',
      moderate: '适中',
      intense: '强烈',
    }[value] || '未设'
  )
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
    loadError.value = describeError(error, '加载角色列表失败。')
  } finally {
    isLoading.value = false
  }
}

async function removePersona(persona) {
  if (isDeleting.value || persona.is_default) return
  if (!(await confirmAction({ title: t('common.delete'), message: t('personaEdit.deleteConfirm'), confirmLabel: t('common.delete'), danger: true }))) return

  actionError.value = ''
  isDeleting.value = persona.id
  try {
    personas.value = await store.remove(persona.id)
  } catch (error) {
    actionError.value = describeError(error, '删除角色失败。')
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
  border: 1px solid var(--line);
  background: var(--panel-soft);
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
