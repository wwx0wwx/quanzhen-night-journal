<template>
  <pre>{{ stamp || '尚未生成数字印记' }}</pre>
</template>

<script setup>
defineProps({
  stamp: { type: String, default: '' },
})
</script>
