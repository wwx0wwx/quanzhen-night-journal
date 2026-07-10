<template>
  <section class="stack">
    <div class="hero folder-hero">
      <div>
        <h1>{{ t('folderMonitors.title') }}</h1>
        <p>{{ t('folderMonitors.subtitle') }}</p>
      </div>
      <div class="button-row">
        <button
          class="btn ghost"
          type="button"
          :disabled="isLoading"
          @click="load"
        >
          刷新
        </button>
      </div>
    </div>

    <div
      v-if="message"
      class="status-banner"
      :class="messageType"
    >
      {{ message }}
    </div>

    <AppLoading
      v-if="isLoading"
      title="正在加载目录监控"
      description="正在读取当前监听目录。"
    />

    <AppError
      v-else-if="loadError"
      title="目录监控加载失败"
      :message="loadError"
      action-label="重试"
      @retry="load"
    />

    <template v-else>
      <div class="grid two folder-grid">
        <div class="panel panel-pad stack">
          <div class="section-title">
            新增监听目录
          </div>
          <label class="field">
            <span>目录路径</span>
            <input
              v-model="form.path"
              placeholder="/app/inbox"
            >
          </label>
          <label class="field">
            <span>文件类型</span>
            <input
              v-model="fileTypesText"
              placeholder="md, txt"
            >
          </label>
          <button
            class="btn primary"
            type="button"
            :disabled="isSaving"
            @click="createMonitor"
          >
            {{ isSaving ? '保存中…' : '开始监听' }}
          </button>
        </div>

        <div class="panel panel-pad stack">
          <div class="section-title">
            运行说明
          </div>
          <div class="status-banner info">
            默认 Docker 部署已把仓库的 ./inbox 挂载到后端容器 /app/inbox，可直接监听这个目录做投喂测试。
          </div>
          <div class="card-row">
            <div class="metric">
              <div class="muted">
                监听目录
              </div>
              <strong>{{ monitors.length }}</strong>
            </div>
            <div class="metric">
              <div class="muted">
                启用中
              </div>
              <strong>{{ activeCount }}</strong>
            </div>
          </div>
        </div>
      </div>

      <div class="panel panel-pad stack">
        <div class="split">
          <div>
            <div class="section-title">
              当前监听
            </div>
            <div class="muted">
              删除后系统会重新加载监听器。
            </div>
          </div>
          <span class="tag">{{ monitors.length }} 条</span>
        </div>

        <AppEmpty
          v-if="!monitors.length"
          inline
          title="还没有监听目录"
          description="新增目录后，系统会把新文件作为外部事件处理。"
        />

        <div
          v-else
          class="list"
        >
          <div
            v-for="item in monitors"
            :key="item.id"
            class="list-item stack"
          >
            <div class="split">
              <div
                class="stack"
                style="gap: 6px"
              >
                <strong>{{ item.path }}</strong>
                <div class="muted">
                  类型：{{ item.file_types?.join(' / ') || '-' }}
                </div>
                <div class="muted">
                  创建：{{ formatDateTimeWithRelative(item.created_at) }}
                </div>
              </div>
              <div class="button-row">
                <span
                  class="tag"
                  :class="item.is_active ? 'tag-success' : 'tag-warning'"
                >
                  {{ item.is_active ? '启用中' : '已停用' }}
                </span>
                <button
                  class="btn ghost btn-small"
                  type="button"
                  :disabled="deletingId === item.id"
                  @click="deleteMonitor(item)"
                >
                  {{ deletingId === item.id ? '删除中…' : '删除' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { api, unwrap } from '../api'
import AppEmpty from '../components/AppEmpty.vue'
import AppError from '../components/AppError.vue'
import AppLoading from '../components/AppLoading.vue'
import { describeError } from '../utils/errors'
import { formatDateTimeWithRelative } from '../utils/time'

const { t } = useI18n()

const monitors = ref([])
const isLoading = ref(true)
const isSaving = ref(false)
const deletingId = ref(null)
const loadError = ref('')
const message = ref('')
const messageType = ref('info')
const form = reactive({ path: '/app/inbox' })
const fileTypesText = ref('md, txt')
const activeCount = computed(() => monitors.value.filter((item) => item.is_active).length)

function parseFileTypes() {
  return fileTypesText.value
    .split(/[，,、\s]+/)
    .map((item) => item.trim().replace(/^\./, '').toLowerCase())
    .filter(Boolean)
}

async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    monitors.value = await unwrap(api.get('/folder-monitors'))
  } catch (error) {
    loadError.value = describeError(error, '加载目录监控失败，请稍后重试。')
  } finally {
    isLoading.value = false
  }
}

async function createMonitor() {
  if (!form.path.trim()) {
    messageType.value = 'warning'
    message.value = '请先填写目录路径。'
    return
  }
  isSaving.value = true
  message.value = ''
  try {
    await unwrap(api.post('/folder-monitors', { path: form.path.trim(), file_types: parseFileTypes() }))
    form.path = '/app/inbox'
    messageType.value = 'success'
    message.value = '监听目录已添加。'
    await load()
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, '添加监听目录失败。')
  } finally {
    isSaving.value = false
  }
}

async function deleteMonitor(item) {
  if (deletingId.value) return
  if (!window.confirm(`确认删除监听目录 ${item.path} 吗？`)) return
  deletingId.value = item.id
  message.value = ''
  try {
    await unwrap(api.delete(`/folder-monitors/${item.id}`))
    messageType.value = 'success'
    message.value = '监听目录已删除。'
    await load()
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, '删除监听目录失败。')
  } finally {
    deletingId.value = null
  }
}

onMounted(load)
</script>

<style scoped>
.folder-hero {
  align-items: end;
}

.folder-grid {
  align-items: start;
}
</style>
