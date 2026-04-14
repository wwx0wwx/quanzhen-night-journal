<template>
  <slot v-if="!capturedError" />
  <AppError
    v-else
    title="页面渲染失败"
    :message="capturedError"
    action-label="重新尝试"
    @retry="reset"
  />
</template>

<script setup>
import { onErrorCaptured, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import AppError from './AppError.vue'

const route = useRoute()
const capturedError = ref('')

function reset() {
  capturedError.value = ''
}

onErrorCaptured((error) => {
  capturedError.value = error?.message || '页面内部发生未处理异常。'
  return false
})

watch(() => route.fullPath, reset)
</script>
