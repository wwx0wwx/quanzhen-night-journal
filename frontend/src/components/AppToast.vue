<template>
  <div
    class="toast-stack"
    aria-live="polite"
    aria-relevant="additions"
  >
    <TransitionGroup name="toast">
      <div
        v-for="item in toast.items"
        :key="item.id"
        class="toast-item"
        :class="item.kind"
        role="status"
      >
        <span class="toast-msg">{{ item.message }}</span>
        <button
          type="button"
          class="toast-close"
          :aria-label="t('common.close')"
          @click="toast.dismiss(item.id)"
        >
          ×
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

import { useToastStore } from '../stores/toast'

const toast = useToastStore()
const { t } = useI18n()
</script>

<style scoped>
.toast-stack {
  position: fixed;
  right: 18px;
  bottom: 18px;
  z-index: 80;
  display: grid;
  gap: 10px;
  width: min(360px, calc(100vw - 28px));
  pointer-events: none;
}

.toast-item {
  pointer-events: auto;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid var(--line);
  background: var(--panel);
  box-shadow: var(--shadow);
  color: var(--ink);
  font-size: 0.9rem;
  line-height: 1.45;
}

.toast-item.success {
  border-color: rgba(21, 128, 61, 0.28);
  background: #f0fdf4;
  color: #166534;
}

.toast-item.error {
  border-color: rgba(185, 28, 28, 0.28);
  background: #fef2f2;
  color: #991b1b;
}

.toast-item.warning {
  border-color: rgba(180, 83, 9, 0.28);
  background: #fffbeb;
  color: #92400e;
}

.toast-item.info {
  border-color: rgba(3, 105, 161, 0.22);
  background: #f0f9ff;
  color: #075985;
}

:root[data-theme='dark'] .toast-item.success {
  background: rgba(21, 128, 61, 0.16);
  color: var(--success);
}
:root[data-theme='dark'] .toast-item.error {
  background: rgba(185, 28, 28, 0.16);
  color: var(--danger);
}
:root[data-theme='dark'] .toast-item.warning {
  background: rgba(180, 83, 9, 0.16);
  color: var(--warning);
}
:root[data-theme='dark'] .toast-item.info {
  background: rgba(3, 105, 161, 0.16);
  color: var(--info);
}

.toast-msg {
  flex: 1;
  min-width: 0;
  overflow-wrap: anywhere;
}

.toast-close {
  border: 0;
  background: transparent;
  color: inherit;
  opacity: 0.7;
  cursor: pointer;
  font-size: 1.1rem;
  line-height: 1;
  padding: 0 2px;
}

.toast-enter-active,
.toast-leave-active {
  transition:
    opacity 0.18s ease,
    transform 0.18s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
