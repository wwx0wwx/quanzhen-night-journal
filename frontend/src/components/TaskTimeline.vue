<template>
  <div class="panel panel-pad timeline-card">
    <div class="timeline-head">
      <div>
        <div class="section-title">
          {{ t('timeline.title') }}
        </div>
      </div>
      <div class="muted">
        {{ t('timeline.hint') }}
      </div>
    </div>

    <div class="list timeline-list">
      <div
        v-for="step in steps"
        :key="step.name"
        class="timeline-step"
        :class="step.state"
      >
        <div class="timeline-node">
          <span class="timeline-index">{{ step.index }}</span>
        </div>
        <div class="list-item timeline-card-body">
          <div class="timeline-heading">
            <strong>{{ step.label }}</strong>
            <span
              class="tag"
              :class="step.tagClass"
            >{{ step.stateLabel }}</span>
          </div>
          <div class="muted">
            {{ step.description }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { TASK_TIMELINE_ORDER, getTaskStatusMeta } from '../utils/statusMeta'

const props = defineProps({
  status: { type: String, default: 'queued' },
})

const { t } = useI18n()

const steps = computed(() => {
  const activeIndex = TASK_TIMELINE_ORDER.indexOf(props.status)
  const mapped = TASK_TIMELINE_ORDER.map((name, index) => {
    const meta = getTaskStatusMeta(name)
    let state = 'pending'
    if (activeIndex >= index) state = index === activeIndex ? 'current' : 'done'
    if (['failed', 'circuit_open', 'aborted', 'draft_saved'].includes(props.status)) {
      state = activeIndex >= index ? 'done' : 'pending'
    }
    return {
      name,
      label: meta.label,
      index: index + 1,
      description: meta.description,
      state,
      stateLabel:
        state === 'current' ? t('timeline.current') : state === 'done' ? t('timeline.done') : t('timeline.pending'),
      tagClass: state === 'current' ? '' : state === 'done' ? 'tag-success' : 'tag-warning',
    }
  })

  if (['failed', 'circuit_open', 'aborted', 'draft_saved'].includes(props.status)) {
    const meta = getTaskStatusMeta(props.status)
    mapped.push({
      name: props.status,
      label: meta.label,
      index: mapped.length + 1,
      description: meta.description,
      state: 'current',
      stateLabel: t('timeline.current'),
      tagClass: 'tag-danger',
    })
  }

  return mapped
})
</script>

<style scoped>
.timeline-head {
  display: grid;
  gap: 6px;
  margin-bottom: 14px;
}

.timeline-list {
  gap: 10px;
}

.timeline-step {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  gap: 10px;
  align-items: start;
}

.timeline-node {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 999px;
  border: 1px solid var(--line-strong);
  background: var(--panel-soft);
  margin-top: 12px;
}

.timeline-index {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--muted);
}

.timeline-step.current .timeline-node {
  border-color: var(--accent);
  background: var(--accent-glow);
  color: var(--accent-strong);
}

.timeline-step.done .timeline-node {
  border-color: rgba(21, 128, 61, 0.35);
  color: var(--success);
}

.timeline-heading {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
</style>
