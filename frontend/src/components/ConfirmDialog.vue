<template>
  <Teleport to="body">
    <div
      v-if="state.open"
      class="confirm-backdrop"
      @click.self="cancel"
    >
      <div
        class="confirm-card panel"
        role="dialog"
        aria-modal="true"
      >
        <h2>{{ state.title || t('confirm.title') }}</h2>
        <p>{{ state.message }}</p>
        <div class="button-row confirm-actions">
          <button
            class="btn ghost"
            type="button"
            @click="cancel"
          >
            {{ state.cancelLabel || t('common.cancel') }}
          </button>
          <button
            class="btn"
            :class="state.danger ? 'danger' : 'primary'"
            type="button"
            @click="ok"
          >
            {{ state.confirmLabel || t('common.confirm') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

import { resolveConfirm, useConfirmState } from '../composables/useConfirm'

const { t } = useI18n()
const state = useConfirmState()

function ok() {
  resolveConfirm(true)
}
function cancel() {
  resolveConfirm(false)
}
</script>

<style scoped>
.confirm-backdrop {
  position: fixed;
  inset: 0;
  z-index: 90;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(15, 23, 42, 0.45);
}

.confirm-card {
  width: min(420px, 100%);
  padding: 22px 22px 18px;
}

.confirm-card h2 {
  margin: 0 0 10px;
  font-size: 1.1rem;
}

.confirm-card p {
  margin: 0 0 18px;
  color: var(--muted);
  line-height: 1.6;
}

.confirm-actions {
  justify-content: flex-end;
}
</style>
