<template>
  <section class="stack">
    <div class="hero sensory-hero">
      <div>
<h1>{{ t('sensory.title') }}</h1>
        <p>{{ t('sensory.subtitle') }}</p>
      </div>
      <div class="button-row">
        <button
          class="btn primary"
          type="button"
          :disabled="isRefreshing"
          @click="refreshCurrent"
        >
          {{ isRefreshing ? '采样中…' : '立即采样' }}
        </button>
        <button
          class="btn ghost"
          type="button"
          :disabled="isLoading"
          @click="load"
        >
          刷新历史
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
      title="正在读取环境状态"
      description="正在获取最新采样和历史曲线。"
    />

    <AppError
      v-else-if="loadError"
      title="环境状态加载失败"
      :message="loadError"
      action-label="重试"
      @retry="load"
    />

    <template v-else>
      <div class="card-row">
        <div class="metric">
          <div class="muted">
            CPU
          </div>
          <strong>{{ formatPercent(current?.cpu_percent) }}</strong>
          <div class="muted">
            当前采样的计算压力。
          </div>
        </div>
        <div class="metric">
          <div class="muted">
            内存
          </div>
          <strong>{{ formatPercent(current?.memory_percent) }}</strong>
          <div class="muted">
            当前采样视角下的内存占用（默认容器命名空间）。
          </div>
        </div>
        <div class="metric">
          <div class="muted">
            磁盘
          </div>
          <strong>{{ formatPercent(current?.disk_usage_percent) }}</strong>
          <div class="muted">
            数据目录所在磁盘占用。
          </div>
        </div>
        <div class="metric">
          <div class="muted">
            盲区
          </div>
          <strong>{{ current?.is_in_blind_zone ? '是' : '否' }}</strong>
          <div class="muted">
            {{ current?.sampled_at ? formatDateTimeWithRelative(current.sampled_at) : '还没有采样时间。' }}
          </div>
        </div>
      </div>

      <div class="grid two sensory-grid">
        <div class="panel panel-pad stack">
          <div class="section-title">
            {{ t('sensory.translation') }}
          </div>
          <div class="status-banner info">
            {{ current?.translated_text || '当前采样没有触发明显环境意象。' }}
          </div>
          <dl class="meta-grid">
            <div>
              <dt>采样视角</dt>
              <dd>{{ current?.scope_label || current?.source || '-' }}</dd>
            </div>
            <div>
              <dt>来源标识</dt>
              <dd>{{ current?.source || '-' }}</dd>
            </div>
            <div>
              <dt>标签</dt>
              <dd>{{ current?.tags?.length ? current.tags.join(' / ') : '-' }}</dd>
            </div>
            <div>
              <dt>采样间隔</dt>
              <dd>{{ formatSeconds(current?.sample_interval_seconds) }}</dd>
            </div>
            <div>
              <dt>API 延迟</dt>
              <dd>{{ current?.api_latency_ms == null ? '-' : `${current.api_latency_ms} ms` }}</dd>
            </div>
          </dl>
        </div>

        <SensoryChart :items="chartItems" />
      </div>

      <div class="panel panel-pad stack">
        <div class="split">
          <div>
            <div class="section-title">
              最近采样
            </div>
            <div class="muted">
              最近 {{ history.length }} 条记录，按时间倒序展示。
            </div>
          </div>
          <label class="field compact-field">
            <span>时间窗</span>
            <select
              v-model.number="hours"
              @change="loadHistory"
            >
              <option :value="6">
                6 小时
              </option>
              <option :value="24">
                24 小时
              </option>
              <option :value="72">
                72 小时
              </option>
            </select>
          </label>
        </div>

        <AppEmpty
          v-if="!history.length"
          inline
          title="还没有感知历史"
          description="等待定时采样或点击“立即采样”后，这里会出现环境记录。"
        />

        <div
          v-else
          class="list"
        >
          <div
            v-for="item in history.slice(0, 12)"
            :key="item.id"
            class="list-item stack"
          >
            <div class="split">
              <strong>{{ formatDateTimeWithRelative(item.sampled_at) }}</strong>
              <div class="button-row">
                <span class="tag">CPU {{ formatPercent(item.cpu_percent) }}</span>
                <span class="tag">MEM {{ formatPercent(item.memory_percent) }}</span>
              </div>
            </div>
            <div class="muted">
              {{ item.translated_text || t('sensory.noTranslation') }}
            </div>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { api, unwrap } from '../api'
import AppEmpty from '../components/AppEmpty.vue'
import AppError from '../components/AppError.vue'
import AppLoading from '../components/AppLoading.vue'
import SensoryChart from '../components/SensoryChart.vue'
import { describeError } from '../utils/errors'
import { formatDateTimeWithRelative } from '../utils/time'

const { t } = useI18n()

const current = ref(null)
const history = ref([])
const chartItems = ref([])
const hours = ref(24)
const isLoading = ref(true)
const isRefreshing = ref(false)
const loadError = ref('')
const message = ref('')
const messageType = ref('info')

function formatPercent(value) {
  if (value == null || value === '') return '-'
  return `${Number(value).toFixed(1)}%`
}

function formatSeconds(value) {
  if (value == null || value === '') return '-'
  return `${Number(value).toFixed(1)} s`
}

async function loadHistory() {
  const [historyRows, chartRows] = await Promise.all([
    unwrap(api.get('/sensory/history', { params: { hours: hours.value } })),
    unwrap(api.get('/sensory/chart-data', { params: { hours: hours.value } })),
  ])
  history.value = historyRows.slice().reverse()
  chartItems.value = chartRows.slice(-24)
}

async function refreshCurrent() {
  if (isRefreshing.value) return
  isRefreshing.value = true
  message.value = ''
  try {
    current.value = await unwrap(api.get('/sensory/current'))
    await loadHistory()
    messageType.value = 'success'
    message.value = '已完成一次即时采样。'
  } catch (error) {
    messageType.value = 'error'
    message.value = describeError(error, '即时采样失败。')
  } finally {
    isRefreshing.value = false
  }
}

async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    const [currentSnapshot] = await Promise.all([unwrap(api.get('/sensory/current')), loadHistory()])
    current.value = currentSnapshot
  } catch (error) {
    loadError.value = describeError(error, '加载环境状态失败，请稍后重试。')
  } finally {
    isLoading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.sensory-hero {
  align-items: end;
}

.sensory-grid {
  align-items: start;
}

.compact-field {
  min-width: 160px;
  margin: 0;
}
</style>
