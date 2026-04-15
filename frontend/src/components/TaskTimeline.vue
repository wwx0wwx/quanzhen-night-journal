<template>
  <div class="panel panel-pad timeline-card">
    <div class="timeline-head">
      <div>
        <div class="hero-kicker">Execution Ledger</div>
        <div class="section-title">任务轨迹</div>
      </div>
      <div class="muted">从排队到发布，按顺序保留每一段状态变化。</div>
    </div>

    <div class="list timeline-list">
      <div v-for="step in steps" :key="step.name" class="timeline-step" :class="step.state">
        <div class="timeline-node">
          <span class="timeline-index">{{ step.index }}</span>
        </div>
        <div class="list-item timeline-card-body">
          <div class="timeline-heading">
            <strong>{{ step.label }}</strong>
            <span class="tag" :class="step.tagClass">{{ step.stateLabel }}</span>
          </div>
          <div class="muted">{{ step.description }}</div>
        </div>
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
      index: index + 1,
      description: meta.description,
      state,
      stateLabel: state === 'current' ? '当前阶段' : state === 'done' ? '已完成' : '尚未进入',
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
      stateLabel: '当前结果',
      tagClass: 'tag-danger',
    })
  }

  return mapped
})
</script>

<style scoped>
.timeline-card {
  display: grid;
  gap: 18px;
}

.timeline-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}

.timeline-head .muted {
  max-width: 28ch;
  line-height: 1.7;
  text-align: right;
}

.timeline-list {
  gap: 14px;
}

.timeline-step {
  position: relative;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 14px;
  align-items: start;
}

.timeline-step::before {
  content: "";
  position: absolute;
  left: 18px;
  top: 38px;
  bottom: -14px;
  width: 1px;
  background: linear-gradient(180deg, rgba(155, 176, 198, 0.34), transparent);
}

.timeline-step:last-child::before {
  display: none;
}

.timeline-node {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 999px;
  border: 1px solid rgba(155, 176, 198, 0.18);
  background: rgba(10, 14, 22, 0.82);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.timeline-index {
  font-size: 0.82rem;
  letter-spacing: 0.08em;
  color: var(--accent-soft);
}

.timeline-card-body {
  display: grid;
  gap: 10px;
}

.timeline-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.timeline-step.done .timeline-node {
  border-color: rgba(143, 255, 209, 0.28);
  background: rgba(17, 32, 28, 0.86);
}

.timeline-step.current .timeline-node {
  border-color: rgba(176, 198, 218, 0.3);
  background:
    radial-gradient(circle, rgba(216, 229, 240, 0.12), transparent 68%),
    rgba(18, 25, 35, 0.94);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    0 0 20px rgba(157, 183, 207, 0.1);
}

.timeline-step.pending .timeline-node {
  opacity: 0.74;
}

@media (max-width: 680px) {
  .timeline-head,
  .timeline-heading {
    flex-direction: column;
  }

  .timeline-head .muted {
    max-width: none;
    text-align: left;
  }
}
</style>
