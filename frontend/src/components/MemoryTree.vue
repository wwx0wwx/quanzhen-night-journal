<template>
  <div class="panel panel-pad">
    <div class="section-title">记忆分层</div>
    <div class="stack">
      <div v-for="group in groups" :key="group.level">
        <div class="button-row">
          <div class="tag">{{ levelLabel(group.level) }}</div>
          <div class="muted">{{ group.items.length }} 条</div>
        </div>
        <div class="list">
          <div v-for="item in group.items" :key="item.id" class="list-item">
            <strong>{{ item.summary || item.content }}</strong>
            <div class="muted">{{ personaName(item.persona_id) }}</div>
            <div class="muted">{{ item.tags?.join(' / ') }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  memories: { type: Array, default: () => [] },
  personas: { type: Array, default: () => [] },
})

const levelMap = {
  L0: 'L0 核心设定',
  L1: 'L1 长期主题',
  L2: 'L2 近期线索',
  L3: 'L3 瞬时片段',
}

function levelLabel(level) {
  return levelMap[level] || level
}

function personaName(personaId) {
  return props.personas.find((item) => item.id === personaId)?.name || `#${personaId}`
}

const groups = computed(() => ['L0', 'L1', 'L2', 'L3'].map((level) => ({
  level,
  items: props.memories.filter((item) => item.level === level).slice(0, 4),
})).filter((group) => group.items.length))
</script>
