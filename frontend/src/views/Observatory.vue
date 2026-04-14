<template>
  <section class="stack">
    <div class="hero">
      <div>
        <h1>观测中心</h1>
        <p>健康评分、预算、任务轨迹和记忆树在这里集中展示。</p>
      </div>
    </div>

    <div class="card-row">
      <StabilityGauge label="人格稳定度" :score="Number(health.persona_stability || 0)" />
      <StabilityGauge label="记忆一致性" :score="Number(health.memory_coherence || 0)" />
      <CostChart
        title="今日精力消耗"
        subtitle="模型调用费用"
        :cost="Number(health.cost?.cost || 0)"
        :limit="Number(health.cost?.limit || 1)"
      />
    </div>

    <div class="grid two">
      <MemoryTree :memories="memories" />
      <TaskTimeline :status="task.status || 'queued'" />
    </div>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

import { api, unwrap } from '../api'
import CostChart from '../components/CostChart.vue'
import MemoryTree from '../components/MemoryTree.vue'
import StabilityGauge from '../components/StabilityGauge.vue'
import TaskTimeline from '../components/TaskTimeline.vue'

const health = reactive({})
const memories = ref([])
const task = reactive({})

onMounted(async () => {
  Object.assign(health, await unwrap(api.get('/health/dashboard')))
  memories.value = (await unwrap(api.get('/memories'))).items
  const tasks = (await unwrap(api.get('/tasks'))).items
  Object.assign(task, tasks[0] || {})
})
</script>
