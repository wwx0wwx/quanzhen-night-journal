<template>
  <div class="app-state" :class="{ panel: !inline, 'panel-pad': !inline, 'app-state-inline': inline }">
    <div class="loading-mark" aria-hidden="true">
      <div class="state-spinner"></div>
      <div class="loading-ring"></div>
    </div>
    <div class="app-state-kicker">Synchronizing</div>
    <strong class="app-state-title">{{ title }}</strong>
    <div class="muted app-state-body">{{ description }}</div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: '加载中',
  },
  description: {
    type: String,
    default: '正在获取最新数据，请稍候。',
  },
  inline: {
    type: Boolean,
    default: false,
  },
})
</script>

<style scoped>
.loading-mark {
  position: relative;
  display: grid;
  place-items: center;
  width: 88px;
  height: 88px;
  border-radius: 999px;
  border: 1px solid rgba(155, 176, 198, 0.18);
  background:
    radial-gradient(circle, rgba(216, 229, 240, 0.12), transparent 54%),
    rgba(10, 14, 22, 0.72);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.06),
    0 20px 52px rgba(0, 0, 0, 0.28);
}

.loading-ring {
  position: absolute;
  width: 60px;
  height: 60px;
  border-radius: 999px;
  border: 1px dashed rgba(155, 176, 198, 0.22);
}

.app-state-kicker {
  color: var(--accent-soft);
  font-size: 0.72rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
}
</style>
