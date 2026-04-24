<template>
  <div class="metric gauge">
    <div class="ring" :style="{ background: `conic-gradient(var(--accent) ${score * 3.6}deg, rgba(134,215,255,0.08) 0)` }">
      <div class="core">{{ score }}</div>
    </div>
    <div>
      <div class="muted">{{ label }}</div>
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
  width: 96px;
  height: 96px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  box-shadow:
    inset 0 0 0 1px rgba(169, 223, 255, 0.16),
    0 0 28px rgba(134, 215, 255, 0.08);
}

.core {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background:
    radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.16), transparent 45%),
    rgba(7, 16, 27, 0.94);
  border: 1px solid rgba(169, 223, 255, 0.16);
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--ink);
}
</style>
