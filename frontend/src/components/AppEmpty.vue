<template>
  <div class="app-state app-state-empty" :class="{ panel: !inline, 'panel-pad': !inline, 'app-state-inline': inline }">
    <div class="app-state-mark" aria-hidden="true">
      <svg viewBox="0 0 64 64" class="app-state-icon">
        <path
          d="M40 14c-8 3-14 10.9-14 20.2 0 9.3 6 17.1 14 20.3-2.4.8-4.9 1.2-7.6 1.2-12.8 0-23.2-10.3-23.2-23 0-12.7 10.4-23 23.2-23 2.7 0 5.2.4 7.6 1.3Z"
          fill="currentColor"
        />
        <path d="M45 18h9M49.5 13.5v9M13 46h11M18.5 40.5v11" stroke="currentColor" stroke-linecap="round" stroke-width="2.5" />
      </svg>
    </div>
    <div class="app-state-kicker">Archive Quiet</div>
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

<style scoped>
.app-state-empty {
  position: relative;
  overflow: hidden;
}

.app-state-empty::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at top, rgba(216, 229, 240, 0.1), transparent 24%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.02), transparent 42%);
  opacity: 0.9;
}

.app-state-mark {
  display: grid;
  place-items: center;
  width: 86px;
  height: 86px;
  border-radius: 999px;
  border: 1px solid rgba(155, 176, 198, 0.18);
  background:
    radial-gradient(circle, rgba(218, 228, 238, 0.12), transparent 62%),
    rgba(10, 14, 22, 0.72);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.06),
    0 20px 48px rgba(0, 0, 0, 0.28);
}

.app-state-icon {
  width: 42px;
  height: 42px;
  color: var(--accent-soft);
}

.app-state-kicker {
  color: var(--accent-soft);
  font-size: 0.72rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
}
</style>
