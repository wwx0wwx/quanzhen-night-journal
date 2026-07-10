<template>
  <div
    class="app-state"
    :class="{ panel: !inline, 'panel-pad': !inline, 'app-state-inline': inline }"
  >
    <div
      class="loading-mark"
      aria-hidden="true"
    >
      <div class="state-spinner" />
      <div class="loading-ring" />
    </div>
    <div class="app-state-kicker">
      Synchronizing
    </div>
    <strong class="app-state-title">{{ title }}</strong>
    <div class="muted app-state-body">
      {{ description }}
    </div>
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
  border: 1px solid var(--line-strong);
  background: radial-gradient(circle, var(--accent-glow), transparent 54%), var(--panel);
  box-shadow: var(--shadow-soft);
}

.loading-ring {
  position: absolute;
  width: 60px;
  height: 60px;
  border-radius: 999px;
  border: 1px dashed var(--line-strong);
}

.app-state-kicker {
  color: var(--accent-soft);
  font-size: 0.72rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
}
</style>
