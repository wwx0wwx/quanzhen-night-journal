<template>
  <div class="app-state app-state-error" :class="{ panel: !inline, 'panel-pad': !inline, 'app-state-inline': inline }">
    <strong class="app-state-title">{{ title }}</strong>
    <div class="muted app-state-body">{{ message }}</div>
    <div class="button-row" v-if="actionLabel">
      <button class="btn ghost" type="button" :disabled="disabled" @click="$emit('retry')">
        {{ actionLabel }}
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: '加载失败',
  },
  message: {
    type: String,
    default: '请求没有成功完成，请稍后重试。',
  },
  actionLabel: {
    type: String,
    default: '重试',
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

defineEmits(['retry'])
</script>
