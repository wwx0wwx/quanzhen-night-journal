<template>
  <div class="app-state" :class="{ panel: !inline, 'panel-pad': !inline, 'app-state-inline': inline }">
    <div class="state-spinner" aria-hidden="true"></div>
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
