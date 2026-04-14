<template>
  <div class="panel panel-pad">
    <div class="section-title">任务轨迹</div>
    <div class="list timeline-list">
      <div v-for="step in steps" :key="step.name" class="list-item timeline-step" :class="step.state">
        <strong>{{ step.label }}</strong>
        <div class="muted">{{ step.description }}</div>
        <div class="muted">{{ step.stateLabel }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

import { TASK_TIMELINE_ORDER, getTaskStatusMeta } from '../utils/statusMeta'

const props = defineProps({
  status: { type: String, default: 'queued' },
})

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
      description: meta.description,
      state,
      stateLabel: state === 'current' ? '当前阶段' : state === 'done' ? '已完成' : '尚未进入',
    }
  })

  if (['failed', 'circuit_open', 'aborted', 'draft_saved'].includes(props.status)) {
    const meta = getTaskStatusMeta(props.status)
    mapped.push({
      name: props.status,
      label: meta.label,
      description: meta.description,
      state: 'current',
      stateLabel: '当前结果',
    })
  }

  return mapped
})
</script>
