<template>
  <section class="stack">
    <div class="hero">
      <div>
        <h1>Ghost 迁移</h1>
        <p>管理导出、预览和导入，明确看到文件、冲突和恢复结果。</p>
      </div>
      <button class="btn primary" type="button" :disabled="isExporting" @click="exportGhost">
        {{ isExporting ? '导出中…' : '导出 .ghost' }}
      </button>
    </div>

    <div class="stack" v-if="actionError || actionSuccess">
      <div v-if="actionError" class="status-banner error">{{ actionError }}</div>
      <div v-if="actionSuccess" class="status-banner success">{{ actionSuccess }}</div>
    </div>

    <AppLoading
      v-if="isLoading"
      title="正在加载 Ghost 记录"
      description="正在读取导出历史和当前迁移状态。"
    />

    <AppError
      v-else-if="loadError"
      title="Ghost 页面加载失败"
      :message="loadError"
      action-label="重试"
      @retry="loadExports"
    />

    <div v-else class="grid two">
      <div class="panel panel-pad stack">
        <div class="section-title">上传预览 / 导入</div>

        <label class="field">
          <span>选择 .ghost 文件</span>
          <input type="file" accept=".ghost" @change="onFileChange" />
        </label>

        <div v-if="selectedFileName" class="muted">当前文件：{{ selectedFileName }}</div>

        <div class="button-row">
          <button class="btn ghost" type="button" :disabled="!selectedFile || isPreviewing" @click="previewGhost">
            {{ isPreviewing ? '预览中…' : '预览' }}
          </button>
          <button class="btn primary" type="button" :disabled="!selectedFile || isImporting" @click="importGhost">
            {{ isImporting ? '导入中…' : '确认导入' }}
          </button>
        </div>

        <AppEmpty
          v-if="!preview"
          inline
          title="还没有预览结果"
          description="选择一个 .ghost 文件后，可以先查看 manifest 和冲突信息。"
        />

        <template v-else>
          <div class="status-banner info">预览文件：{{ preview.filename }}</div>

          <div class="card-row">
            <div class="metric">
              <div class="muted">人格</div>
              <strong>{{ preview.manifest?.counts?.personas ?? 0 }}</strong>
            </div>
            <div class="metric">
              <div class="muted">记忆</div>
              <strong>{{ preview.manifest?.counts?.memories ?? 0 }}</strong>
            </div>
            <div class="metric">
              <div class="muted">文章</div>
              <strong>{{ preview.manifest?.counts?.posts ?? 0 }}</strong>
            </div>
            <div class="metric">
              <div class="muted">向量</div>
              <strong>{{ vectorCount }}</strong>
            </div>
          </div>

          <div class="panel panel-pad ghost-preview-box">
            <div class="section-title">Manifest</div>
            <dl class="meta-grid">
              <div>
                <dt>版本</dt>
                <dd>{{ preview.manifest?.ghost_version || '-' }}</dd>
              </div>
              <div>
                <dt>创建时间</dt>
                <dd>{{ preview.manifest?.created_at || '-' }}</dd>
              </div>
            </dl>
          </div>

          <div class="panel panel-pad ghost-preview-box">
            <div class="section-title">冲突检查</div>
            <AppEmpty
              v-if="!preview.conflicts?.length"
              inline
              title="没有发现冲突"
              description="当前包中的人格名和文章 slug 没有与现有数据重复。"
            />
            <div v-else class="list">
              <div v-for="item in preview.conflicts" :key="item" class="list-item">
                <strong>{{ item }}</strong>
                <div class="muted">导入时会保留现有数据，不会强制覆盖。</div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <div class="panel panel-pad stack">
        <div class="split">
          <div>
            <div class="section-title">历史导出</div>
            <div class="muted">保留最近生成的 .ghost 包，可直接下载验证。</div>
          </div>
          <div class="muted">{{ exports.length }} 个文件</div>
        </div>

        <AppEmpty
          v-if="!exports.length"
          inline
          title="还没有导出记录"
          description="先执行一次导出，系统会在这里列出可下载的 .ghost 文件。"
        />

        <div v-else class="list">
          <div v-for="item in exports" :key="item.filename" class="list-item stack">
            <div class="split">
              <div class="stack" style="gap: 6px;">
                <strong>{{ item.filename }}</strong>
                <div class="muted">{{ formatBytes(item.size) }}</div>
                <div class="muted">{{ item.path }}</div>
              </div>
              <div class="button-row">
                <a class="btn ghost btn-small" :href="downloadHref(item.filename)">下载</a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import { api, unwrap } from '../api'
import AppEmpty from '../components/AppEmpty.vue'
import AppError from '../components/AppError.vue'
import AppLoading from '../components/AppLoading.vue'
import { describeError } from '../utils/errors'

const selectedFile = ref(null)
const selectedFileName = ref('')
const preview = ref(null)
const exports = ref([])
const isLoading = ref(true)
const loadError = ref('')
const isExporting = ref(false)
const isPreviewing = ref(false)
const isImporting = ref(false)
const actionError = ref('')
const actionSuccess = ref('')

const vectorCount = computed(() => {
  if (!preview.value?.manifest?.counts) return 0
  return (preview.value.manifest.counts.memory_vectors || 0) + (preview.value.manifest.counts.post_vectors || 0)
})

function downloadHref(filename) {
  return `/api/ghost/download/${encodeURIComponent(filename)}`
}

function formatBytes(value) {
  if (!value) return '0 B'
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / (1024 * 1024)).toFixed(1)} MB`
}

async function loadExports() {
  isLoading.value = true
  loadError.value = ''

  try {
    exports.value = await unwrap(api.get('/ghost/list'))
  } catch (error) {
    loadError.value = describeError(error, '加载 Ghost 记录失败，请稍后重试。')
  } finally {
    isLoading.value = false
  }
}

function onFileChange(event) {
  selectedFile.value = event.target.files?.[0] || null
  selectedFileName.value = selectedFile.value?.name || ''
  preview.value = null
  actionError.value = ''
  actionSuccess.value = ''
}

async function exportGhost() {
  if (isExporting.value) return

  actionError.value = ''
  actionSuccess.value = ''
  isExporting.value = true
  try {
    const result = await unwrap(api.post('/ghost/export', { include_api_keys: false }))
    actionSuccess.value = `导出完成：${result.filename}`
    await loadExports()
  } catch (error) {
    actionError.value = describeError(error, '导出 Ghost 失败，请稍后重试。')
  } finally {
    isExporting.value = false
  }
}

async function previewGhost() {
  if (!selectedFile.value || isPreviewing.value) return

  actionError.value = ''
  actionSuccess.value = ''
  isPreviewing.value = true
  try {
    const form = new FormData()
    form.append('file', selectedFile.value)
    preview.value = await unwrap(api.post('/ghost/preview', form))
    actionSuccess.value = '预览完成，可以确认是否导入。'
  } catch (error) {
    actionError.value = describeError(error, '预览 Ghost 文件失败，请检查文件是否完整。')
  } finally {
    isPreviewing.value = false
  }
}

async function importGhost() {
  if (!selectedFile.value || isImporting.value) return
  if (!window.confirm('确认导入这个 .ghost 包吗？现有同名人格和重复 slug 会被保留。')) return

  actionError.value = ''
  actionSuccess.value = ''
  isImporting.value = true
  try {
    const form = new FormData()
    form.append('file', selectedFile.value)
    form.append('confirm', 'true')
    preview.value = await unwrap(api.post('/ghost/import', form))
    actionSuccess.value = 'Ghost 导入完成。'
    await loadExports()
  } catch (error) {
    actionError.value = describeError(error, '导入 Ghost 失败，请稍后重试。')
  } finally {
    isImporting.value = false
  }
}

onMounted(loadExports)
</script>
