<template>
  <section class="stack">
    <div class="hero">
      <div>
        <h1>感知与事件</h1>
        <p>查看当前快照、最近历史与外部事件记录。</p>
      </div>
      <button class="btn primary" @click="refreshAll">重新采样</button>
    </div>

    <div class="grid two">
      <div class="panel panel-pad">
        <div class="section-title">当前感知</div>
        <div class="list-item">
          <strong>{{ current.translated_text }}</strong>
          <div class="muted">标签：{{ (current.tags || []).join(' / ') }}</div>
          <div class="muted">CPU {{ current.cpu_percent }} / MEM {{ current.memory_percent }}</div>
        </div>
      </div>
      <SensoryChart :items="history.slice(0, 12)" />
    </div>

    <div class="grid two">
      <div class="panel panel-pad">
        <div class="section-title">感知历史</div>
        <div class="list">
          <div v-for="item in history.slice(0, 10)" :key="item.id" class="list-item">
            <strong>{{ item.sampled_at }}</strong>
            <div class="muted">{{ (item.tags || []).join(' / ') }}</div>
          </div>
        </div>
      </div>
      <div class="panel panel-pad">
        <div class="section-title">最近事件</div>
        <div class="list">
          <div v-for="item in events.slice(0, 10)" :key="item.id" class="list-item">
            <strong>{{ item.event_type }}</strong>
            <div class="muted">{{ item.normalized_semantic }}</div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

import { api, unwrap } from '../api'
import SensoryChart from '../components/SensoryChart.vue'

const current = reactive({})
const history = ref([])
const events = ref([])

async function refreshAll() {
  Object.assign(current, await unwrap(api.get('/sensory/current')))
  history.value = await unwrap(api.get('/sensory/history'))
  events.value = (await unwrap(api.get('/events'))).items
}

onMounted(refreshAll)
</script>
