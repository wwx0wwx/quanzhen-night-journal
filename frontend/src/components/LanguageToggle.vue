<template>
  <div
    class="lang-toggle"
    role="group"
    :aria-label="t('common.language')"
  >
    <button
      v-for="item in SUPPORTED_LOCALES"
      :key="item.code"
      type="button"
      class="lang-btn"
      :class="{ active: locale === item.code }"
      :title="item.label"
      @click="switchLocale(item.code)"
    >
      {{ item.short }}
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { SUPPORTED_LOCALES, setLocale } from '../i18n'

const { t, locale } = useI18n()

const current = computed(() => locale.value)

function switchLocale(code) {
  if (code === current.value) return
  setLocale(code)
}
</script>

<style scoped>
.lang-toggle {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px;
  border-radius: 10px;
  border: 1px solid var(--line-strong);
  background: var(--panel);
}

.lang-btn {
  min-width: 32px;
  height: 30px;
  padding: 0 8px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--muted);
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
  transition:
    background 0.15s ease,
    color 0.15s ease;
}

.lang-btn:hover {
  color: var(--ink);
  background: var(--panel-soft);
}

.lang-btn.active {
  color: var(--accent-strong);
  background: var(--accent-glow);
}
</style>
