<template>
  <section class="stack">
    <div class="hero ghost-hero">
      <div>
        <h1>备份与迁移</h1>
        <p>两件常用事：快速备份数据库，或导出完整搬家包（方便换服务器）。导入前建议先备份。</p>
      </div>
      <div class="ghost-hero-actions">
        <div class="muted">
          导入会合并数据；同名角色和重复文章地址会保留，不会直接覆盖。
        </div>
        <button
          class="btn primary"
          type="button"
          :disabled="isExporting"
          @click="exportGhost"
        >
          {{ isExporting ? '导出中…' : '导出完整搬家包' }}
        </button>
        <button
          class="btn ghost"
          type="button"
          :disabled="isBackingUp"
          @click="backupDatabase"
        >
          {{ isBackingUp ? '备份中…' : '快速快速备份数据库' }}
        </button>
      </div>
    </div>

    <div
      v-if="actionError || actionSuccess"
      class="stack"
    >
      <div
        v-if="actionError"
        class="status-banner error"
      >
        {{ actionError }}
      </div>
      <div
        v-if="actionSuccess"
        class="status-banner success"
      >
        {{ actionSuccess }}
      </div>
    </div>

    <AppLoading
      v-if="isLoading"
      title="正在加载备份记录"
      description="正在读取导出历史和当前迁移状态。"
    />

    <AppError
      v-else-if="loadError"
      title="备份页加载失败"
      :message="loadError"
      action-label="重试"
      @retry="loadExports"
    />

    <div
      v-else
      class="grid two"
    >
      <div class="panel panel-pad stack">
        <div class="section-title">
          上传预览 / 导入
        </div>

        <label class="field">
          <span>选择 .ghost 文件</span>
          <input
            type="file"
            accept=".ghost"
            @change="onFileChange"
          >
        </label>

        <div
          v-if="selectedFileName"
          class="muted"
        >
          当前文件：{{ selectedFileName }}
        </div>

        <div class="button-row">
          <button
            class="btn ghost"
            type="button"
            :disabled="!selectedFile || isPreviewing"
            @click="previewGhost"
          >
            {{ isPreviewing ? '预览中…' : '预览' }}
          </button>
          <button
            class="btn primary"
            type="button"
            :disabled="!selectedFile || isImporting"
            @click="importGhost"
          >
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
          <div class="status-banner info">
            预览文件：{{ preview.filename }}
          </div>

          <div class="card-row">
            <div class="metric">
              <div class="muted">
                人格
              </div>
              <strong>{{ preview.manifest?.counts?.personas ?? 0 }}</strong>
            </div>
            <div class="metric">
              <div class="muted">
                记忆
              </div>
              <strong>{{ preview.manifest?.counts?.memories ?? 0 }}</strong>
            </div>
            <div class="metric">
              <div class="muted">
                文章
              </div>
              <strong>{{ preview.manifest?.counts?.posts ?? 0 }}</strong>
            </div>
            <div class="metric">
              <div class="muted">
                向量
              </div>
              <strong>{{ vectorCount }}</strong>
            </div>
          </div>

          <div class="panel panel-pad ghost-preview-box">
            <div class="section-title">
              Manifest
            </div>
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
            <div class="section-title">
              冲突检查
            </div>
            <AppEmpty
              v-if="!preview.conflicts?.length"
              inline
              title="没有发现冲突"
              description="当前包中的角色名和文章地址没有与现有数据重复。"
            />
            <div
              v-else
              class="list"
            >
              <div
                v-for="item in preview.conflicts"
                :key="item"
                class="list-item"
              >
                <strong>{{ item }}</strong>
                <div class="muted">
                  导入时会保留现有数据，不会强制覆盖。
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <div class="panel panel-pad stack">
        <div class="split">
          <div>
            <div class="section-title">
              历史导出
            </div>
            <div class="muted">
              保留最近生成的 .ghost 包，可直接下载验证。
            </div>
          </div>
          <div class="muted">
            {{ exports.length }} 个文件
          </div>
        </div>

        <div class="retention-row">
          <label class="field compact-field">
            <span>保留份数</span>
            <input
              v-model.number="exportKeep"
              min="1"
              step="1"
              type="number"
            >
          </label>
          <button
            class="btn ghost btn-small"
            type="button"
            :disabled="isPruningExports || exports.length <= exportKeep"
            @click="pruneExports"
          >
            {{ isPruningExports ? '清理中…' : '清理旧导出' }}
          </button>
        </div>

        <AppEmpty
          v-if="!exports.length"
          inline
          title="还没有导出记录"
          description="先执行一次导出，系统会在这里列出可下载的 .ghost 文件。"
        />

        <div
          v-else
          class="list"
        >
          <div
            v-for="item in exports"
            :key="item.filename"
            class="list-item stack"
          >
            <div class="split">
              <div
                class="stack"
                style="gap: 6px"
              >
                <strong>{{ item.filename }}</strong>
                <div class="muted">
                  {{ formatBytes(item.size) }}
                </div>
                <div class="muted">
                  {{ item.path }}
                </div>
              </div>
              <div class="button-row">
                <a
                  class="btn ghost btn-small"
                  :href="downloadHref(item.filename)"
                >下载</a>
                <button
                  class="btn ghost btn-small"
                  type="button"
                  :disabled="deletingExportFilename === item.filename"
                  @click="deleteExport(item.filename)"
                >
                  {{ deletingExportFilename === item.filename ? '删除中…' : '删除' }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="split">
          <div>
            <div class="section-title">
              数据库快照
            </div>
            <div class="muted">
              用于快速回滚 SQLite 运行态，不替代 `.ghost` 逻辑导出。
            </div>
          </div>
          <div class="muted">
            {{ databaseBackups.length }} 个文件
          </div>
        </div>

        <div class="retention-row">
          <label class="field compact-field">
            <span>保留份数</span>
            <input
              v-model.number="databaseBackupKeep"
              min="1"
              step="1"
              type="number"
            >
          </label>
          <button
            class="btn ghost btn-small"
            type="button"
            :disabled="isPruningDatabaseBackups || databaseBackups.length <= databaseBackupKeep"
            @click="pruneDatabaseBackups"
          >
            {{ isPruningDatabaseBackups ? '清理中…' : '清理旧快照' }}
          </button>
        </div>

        <AppEmpty
          v-if="!databaseBackups.length"
          inline
          title="还没有数据库快照"
          description="执行一次“备份数据库”后，这里会出现可下载的 SQLite 快照。"
        />

        <div
          v-else
          class="list"
        >
          <div
            v-for="item in databaseBackups"
            :key="item.filename"
            class="list-item stack"
          >
            <div class="split">
              <div
                class="stack"
                style="gap: 6px"
              >
                <strong>{{ item.filename }}</strong>
                <div class="muted">
                  {{ formatBytes(item.size) }}
                </div>
                <div class="muted">
                  {{ item.path }}
                </div>
              </div>
              <div class="button-row">
                <a
                  class="btn ghost btn-small"
                  :href="downloadDatabaseBackupHref(item.filename)"
                >下载</a>
                <button
                  class="btn ghost btn-small"
                  type="button"
                  :disabled="deletingDatabaseBackupFilename === item.filename"
                  @click="deleteDatabaseBackup(item.filename)"
                >
                  {{ deletingDatabaseBackupFilename === item.filename ? '删除中…' : '删除' }}
                </button>
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

const MAX_GHOST_FILE_BYTES = 20 * 1024 * 1024
const selectedFile = ref(null)
const selectedFileName = ref('')
const preview = ref(null)
const exports = ref([])
const databaseBackups = ref([])
const isLoading = ref(true)
const loadError = ref('')
const isExporting = ref(false)
const isBackingUp = ref(false)
const isPreviewing = ref(false)
const isImporting = ref(false)
const deletingExportFilename = ref('')
const deletingDatabaseBackupFilename = ref('')
const isPruningExports = ref(false)
const isPruningDatabaseBackups = ref(false)
const actionError = ref('')
const actionSuccess = ref('')
const exportKeep = ref(10)
const databaseBackupKeep = ref(10)

const vectorCount = computed(() => {
  if (!preview.value?.manifest?.counts) return 0
  return (preview.value.manifest.counts.memory_vectors || 0) + (preview.value.manifest.counts.post_vectors || 0)
})

function downloadHref(filename) {
  return `/api/ghost/download/${encodeURIComponent(filename)}`
}

function downloadDatabaseBackupHref(filename) {
  return `/api/ghost/download-database-backup/${encodeURIComponent(filename)}`
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
    const [ghostExports, databaseSnapshotList] = await Promise.all([
      unwrap(api.get('/ghost/list')),
      unwrap(api.get('/ghost/database-backups')),
    ])
    exports.value = ghostExports
    databaseBackups.value = databaseSnapshotList
  } catch (error) {
    loadError.value = describeError(error, '加载备份记录失败，请稍后重试。')
  } finally {
    isLoading.value = false
  }
}

function onFileChange(event) {
  const file = event.target.files?.[0] || null
  if (file && file.size > MAX_GHOST_FILE_BYTES) {
    selectedFile.value = null
    selectedFileName.value = ''
    preview.value = null
    actionSuccess.value = ''
    actionError.value = `文件过大，最大允许 ${(MAX_GHOST_FILE_BYTES / (1024 * 1024)).toFixed(0)} MB。`
    event.target.value = ''
    return
  }
  selectedFile.value = file
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
    actionError.value = describeError(error, '导出完整备份失败，请稍后重试。')
  } finally {
    isExporting.value = false
  }
}

async function backupDatabase() {
  if (isBackingUp.value) return

  actionError.value = ''
  actionSuccess.value = ''
  isBackingUp.value = true
  try {
    const result = await unwrap(api.post('/ghost/backup-database'))
    actionSuccess.value = `数据库备份完成：${result.filename}`
    await loadExports()
  } catch (error) {
    actionError.value = describeError(error, '数据库备份失败，请稍后重试。')
  } finally {
    isBackingUp.value = false
  }
}

async function deleteExport(filename) {
  if (deletingExportFilename.value) return
  if (!window.confirm(`确认删除导出包 ${filename} 吗？删除后将不能再下载。`)) return

  actionError.value = ''
  actionSuccess.value = ''
  deletingExportFilename.value = filename
  try {
    await unwrap(api.delete(`/ghost/${encodeURIComponent(filename)}`))
    if (preview.value?.filename === filename) {
      preview.value = null
    }
    actionSuccess.value = `已删除导出包：${filename}`
    await loadExports()
  } catch (error) {
    actionError.value = describeError(error, '删除备份包失败，请稍后重试。')
  } finally {
    deletingExportFilename.value = ''
  }
}

async function pruneExports() {
  if (isPruningExports.value) return
  if (!window.confirm(`确认只保留最近 ${exportKeep.value} 个 .ghost 包，并删除更早的导出吗？`)) return

  actionError.value = ''
  actionSuccess.value = ''
  isPruningExports.value = true
  try {
    const result = await unwrap(api.post('/ghost/prune', null, { params: { keep: exportKeep.value } }))
    actionSuccess.value = `已清理 ${result.deleted} 个旧导出包。`
    await loadExports()
  } catch (error) {
    actionError.value = describeError(error, '清理旧备份失败，请稍后重试。')
  } finally {
    isPruningExports.value = false
  }
}

async function deleteDatabaseBackup(filename) {
  if (deletingDatabaseBackupFilename.value) return
  if (!window.confirm(`确认删除数据库快照 ${filename} 吗？删除后将不能再下载。`)) return

  actionError.value = ''
  actionSuccess.value = ''
  deletingDatabaseBackupFilename.value = filename
  try {
    await unwrap(api.delete(`/ghost/database-backups/${encodeURIComponent(filename)}`))
    actionSuccess.value = `已删除数据库快照：${filename}`
    await loadExports()
  } catch (error) {
    actionError.value = describeError(error, '删除数据库快照失败，请稍后重试。')
  } finally {
    deletingDatabaseBackupFilename.value = ''
  }
}

async function pruneDatabaseBackups() {
  if (isPruningDatabaseBackups.value) return
  if (!window.confirm(`确认只保留最近 ${databaseBackupKeep.value} 个数据库快照，并删除更早的快照吗？`)) return

  actionError.value = ''
  actionSuccess.value = ''
  isPruningDatabaseBackups.value = true
  try {
    const result = await unwrap(
      api.post('/ghost/database-backups/prune', null, { params: { keep: databaseBackupKeep.value } }),
    )
    actionSuccess.value = `已清理 ${result.deleted} 个旧数据库快照。`
    await loadExports()
  } catch (error) {
    actionError.value = describeError(error, '清理旧数据库快照失败，请稍后重试。')
  } finally {
    isPruningDatabaseBackups.value = false
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
    actionError.value = describeError(error, '预览备份文件失败，请检查文件是否完整。')
  } finally {
    isPreviewing.value = false
  }
}

async function importGhost() {
  if (!selectedFile.value || isImporting.value) return
  if (!window.confirm('确认导入这个完整搬家包吗？同名角色和重复文章地址会被保留、不会覆盖。')) return

  actionError.value = ''
  actionSuccess.value = ''
  isImporting.value = true
  try {
    const form = new FormData()
    form.append('file', selectedFile.value)
    form.append('confirm', 'true')
    preview.value = await unwrap(api.post('/ghost/import', form))
    actionSuccess.value = '备份导入完成。'
    await loadExports()
  } catch (error) {
    actionError.value = describeError(error, '导入备份失败，请稍后重试。')
  } finally {
    isImporting.value = false
  }
}

onMounted(loadExports)
</script>

<style scoped>
.ghost-hero {
  align-items: end;
}

.ghost-hero-actions {
  display: grid;
  gap: 12px;
  justify-items: end;
  max-width: 320px;
  text-align: right;
}

.retention-row {
  display: flex;
  align-items: end;
  gap: 12px;
  flex-wrap: wrap;
}

.compact-field {
  min-width: 160px;
  margin: 0;
}

@media (max-width: 900px) {
  .ghost-hero-actions {
    justify-items: start;
    max-width: none;
    text-align: left;
  }
}
</style>
