<template>
  <div
    class="app-state app-state-error"
    :class="{ panel: !inline, 'panel-pad': !inline, 'app-state-inline': inline }"
  >
    <div class="app-state-mark" aria-hidden="true">
      <svg viewBox="0 0 64 64" class="app-state-icon">
        <path d="M32 12 11 49h42L32 12Z" fill="none" stroke="currentColor" stroke-linejoin="round" stroke-width="2.8" />
        <path d="M32 25v12" stroke="currentColor" stroke-linecap="round" stroke-width="3.2" />
        <circle cx="32" cy="43.2" r="1.9" fill="currentColor" />
      </svg>
    </div>
    <strong class="app-state-title">{{ displayTitle }}</strong>
    <div class="muted app-state-body">{{ displayMessage }}</div>
    <div v-if="displayAction" class="button-row">
      <button class="btn ghost" type="button" :disabled="disabled" @click="$emit('retry')">
        {{ displayAction }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  title: { type: String, default: '' },
  message: { type: String, default: '' },
  actionLabel: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  inline: { type: Boolean, default: false },
})
defineEmits(['retry'])
const { t } = useI18n()
const displayTitle = computed(() => props.title || t('error.defaultTitle'))
const displayMessage = computed(() => props.message || t('errors.fallback'))
const displayAction = computed(() => props.actionLabel || t('error.defaultAction'))
</script>

<style scoped>
.app-state-error { position: relative; overflow: hidden; }
.app-state-mark {
  display: grid;
  place-items: center;
  width: 86px;
  height: 86px;
  border-radius: 999px;
  border: 1px solid rgba(185, 28, 28, 0.28);
  background: rgba(185, 28, 28, 0.06);
}
.app-state-icon { width: 40px; height: 40px; color: var(--danger); }
</style>
