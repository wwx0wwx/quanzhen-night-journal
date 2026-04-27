<template>
  <div class="metric">
    <div class="muted">
      {{ title }}
    </div>
    <div
      v-if="subtitle"
      class="cost-subtitle"
    >
      {{ subtitle }}
    </div>
    <strong>${{ cost.toFixed(4) }}</strong>
    <div class="bar">
      <div
        class="bar-fill"
        :style="{ width: `${Math.min(100, progress)}%` }"
      />
    </div>
    <div class="muted">
      预算使用 {{ progress.toFixed(1) }}%
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, default: '今日精力消耗' },
  subtitle: { type: String, default: '模型调用费用' },
  cost: { type: Number, default: 0 },
  limit: { type: Number, default: 1 },
})

const progress = computed(() => (props.limit ? (props.cost / props.limit) * 100 : 0))
</script>

<style scoped>
.cost-subtitle {
  margin-top: 6px;
  color: var(--secondary);
  font-size: 0.92rem;
  line-height: 1.5;
}

.bar {
  height: 10px;
  margin: 12px 0 8px;
  border-radius: 999px;
  background: rgba(134, 215, 255, 0.1);
  border: 1px solid rgba(169, 223, 255, 0.12);
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent-strong), var(--accent-soft));
  box-shadow: 0 0 18px rgba(134, 215, 255, 0.18);
}
</style>
