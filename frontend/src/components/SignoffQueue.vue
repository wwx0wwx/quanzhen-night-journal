<template>
  <div class="panel panel-pad stack">
    <div class="split">
      <div>
        <div class="section-title">
          {{ t('signoff.title') }}
        </div>
        <p class="muted" style="margin: 6px 0 0">
          {{ t('signoff.subtitle') }}
        </p>
      </div>
      <span
        v-if="items.length"
        class="tag tag-warning"
      >{{ items.length }}</span>
    </div>

    <AppEmpty
      v-if="!loading && !items.length"
      inline
      :title="t('signoff.empty')"
    />

    <div
      v-else
      class="list"
    >
      <div
        v-for="task in items"
        :key="task.id"
        class="list-item stack"
      >
        <div class="split">
          <strong>{{ t('dashboard.taskN', { id: task.id }) }}</strong>
          <span class="tag tag-warning">{{ getStatusLabel('task', task.status) }}</span>
        </div>
        <div class="muted">
          {{ task.error_message || getPublishDecisionDescription(task) || getStatusDescription('task', task.status) }}
        </div>
        <div class="button-row">
          <RouterLink
            class="btn primary btn-small"
            :to="`/admin/tasks/${task.id}`"
          >
            {{ t('signoff.open') }}
          </RouterLink>
          <button
            class="btn ghost btn-small"
            type="button"
            :disabled="busyId === task.id"
            @click="$emit('approve', task)"
          >
            {{ busyId === task.id ? t('common.busy') : t('signoff.approve') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

import AppEmpty from './AppEmpty.vue'
import { getPublishDecisionDescription } from '../utils/publishDecision'
import { getStatusDescription, getStatusLabel } from '../utils/statusMeta'

defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  busyId: { type: [Number, String, null], default: null },
})

defineEmits(['approve'])

const { t } = useI18n()
</script>
