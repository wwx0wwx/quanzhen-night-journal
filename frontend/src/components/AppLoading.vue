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
    <strong class="app-state-title">{{ displayTitle }}</strong>
    <div class="muted app-state-body">
      {{ displayDescription }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  inline: { type: Boolean, default: false },
})
const { t } = useI18n()
const displayTitle = computed(() => props.title || t('loading.defaultTitle'))
const displayDescription = computed(() => props.description || t('loading.defaultDesc'))
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
</style>
