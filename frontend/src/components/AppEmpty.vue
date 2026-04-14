<template>
  <div class="app-state app-state-empty" :class="{ panel: !inline, 'panel-pad': !inline, 'app-state-inline': inline }">
    <strong class="app-state-title">{{ title }}</strong>
    <div class="muted app-state-body">{{ description }}</div>
    <div class="button-row" v-if="actionLabel">
      <button class="btn ghost" type="button" :disabled="disabled" @click="$emit('action')">
        {{ actionLabel }}
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: '暂无数据',
  },
  description: {
    type: String,
    default: '当前还没有可展示的内容。',
  },
  actionLabel: {
    type: String,
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  inline: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['action'])
</script>
