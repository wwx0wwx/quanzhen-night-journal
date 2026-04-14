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
      <div class="hero">
        <div>
          <h1>人格设定（写作风格）</h1>
          <p>维护不同人格设定、默认人格，以及对应的语言习惯和感知词典。</p>
        </div>
        <RouterLink class="btn primary" to="/admin/personas/new">新建人格设定</RouterLink>
      </div>

      <div v-if="actionError" class="status-banner error">{{ actionError }}</div>

      <AppEmpty
        v-if="!personas.length"
        title="还没有额外人格设定"
        description="当前只有默认人格。可以先新建一个人格设定，再按写作需求切换使用。"
      />

      <div v-else class="list">
        <div
          v-for="persona in personas"
          :key="persona.id"
          class="list-item panel stack"
        >
          <div class="split">
            <div>
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
import { onMounted, ref } from 'vue'

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
