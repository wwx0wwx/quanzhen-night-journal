<template>
  <div class="metric gauge">
    <div
      class="ring"
      :style="{ background: `conic-gradient(var(--accent) ${score * 3.6}deg, var(--gauge-track) 0)` }"
    >
      <div class="core">
        {{ score }}
      </div>
    </div>
    <div>
      <div class="muted">
        {{ label }}
      </div>
      <div>{{ hint }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, default: '人格稳定度' },
  score: { type: Number, default: 80 },
})

const hint = computed(() => (props.score >= 85 ? '稳定而清明' : props.score >= 70 ? '轻微波动' : '需要关注'))
</script>

<style scoped>
.gauge {
  display: flex;
  align-items: center;
  gap: 18px;
}

.ring {
  --gauge-track: rgba(134, 215, 255, 0.08);
  width: 96px;
  height: 96px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  box-shadow:
    inset 0 0 0 1px var(--line-strong),
    0 0 28px var(--accent-glow);
}

.core {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--panel-strong);
  border: 1px solid var(--line-strong);
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--ink);
}
</style>
