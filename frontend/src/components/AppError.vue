<template>
  <div
    class="app-state app-state-error"
    :class="{ panel: !inline, 'panel-pad': !inline, 'app-state-inline': inline }"
  >
    <div
      class="app-state-mark"
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 64 64"
        class="app-state-icon"
      >
        <path
          d="M32 12 11 49h42L32 12Z"
          fill="none"
          stroke="currentColor"
          stroke-linejoin="round"
          stroke-width="2.8"
        />
        <path
          d="M32 25v12"
          stroke="currentColor"
          stroke-linecap="round"
          stroke-width="3.2"
        />
        <circle
          cx="32"
          cy="43.2"
          r="1.9"
          fill="currentColor"
        />
      </svg>
    </div>
    <div class="app-state-kicker">
      Interruption Trace
    </div>
    <strong class="app-state-title">{{ title }}</strong>
    <div class="muted app-state-body">
      {{ message }}
    </div>
    <div
      v-if="actionLabel"
      class="button-row"
    >
      <button
        class="btn ghost"
        type="button"
        :disabled="disabled"
        @click="$emit('retry')"
      >
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

<style scoped>
.app-state-error {
  position: relative;
  overflow: hidden;
}

.app-state-error::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at top, rgba(255, 180, 194, 0.1), transparent 26%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.02), transparent 40%);
}

.app-state-mark {
  display: grid;
  place-items: center;
  width: 86px;
  height: 86px;
  border-radius: 999px;
  border: 1px solid rgba(255, 155, 176, 0.22);
  background: radial-gradient(circle, rgba(255, 175, 193, 0.1), transparent 58%), rgba(18, 11, 17, 0.76);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.05),
    0 22px 52px rgba(0, 0, 0, 0.3);
}

.app-state-icon {
  width: 40px;
  height: 40px;
  color: #ffd8e2;
}

.app-state-kicker {
  color: #ffd8e2;
  font-size: 0.72rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
}
</style>
