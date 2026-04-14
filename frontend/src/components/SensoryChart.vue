<template>
  <div class="panel panel-pad">
    <div class="section-title">感知曲线</div>
    <div class="chart">
      <div v-for="item in items" :key="item.sampled_at" class="chart-col">
        <div class="bar cpu" :style="{ height: `${item.cpu_percent || 0}%` }"></div>
        <div class="bar mem" :style="{ height: `${item.memory_percent || 0}%` }"></div>
        <small>{{ item.sampled_at.slice(11, 16) }}</small>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  items: { type: Array, default: () => [] },
})
</script>

<style scoped>
.chart {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(38px, 1fr));
  gap: 10px;
  align-items: end;
  min-height: 180px;
}

.chart-col {
  display: grid;
  justify-items: center;
  gap: 6px;
}

.bar {
  width: 14px;
  border-radius: 999px;
  box-shadow: 0 0 18px rgba(134, 215, 255, 0.08);
}

.cpu {
  background: linear-gradient(180deg, var(--accent-soft), var(--accent-strong));
}

.mem {
  background: rgba(134, 215, 255, 0.28);
}
</style>
