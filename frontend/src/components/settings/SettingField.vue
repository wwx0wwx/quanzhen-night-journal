<template>
  <label
    class="field"
    :class="{ wide: field.wide, 'field-boolean': field.type === 'boolean' }"
  >
    <div class="field-head">
      <span class="setting-field-label">{{ field.label }}</span>
    </div>

    <template v-if="field.type === 'boolean'">
      <div class="toggle-field">
        <label class="toggle-control">
          <input
            :checked="Boolean(modelValue)"
            :disabled="isDisabled"
            type="checkbox"
            @change="updateBoolean"
          >
          <span>{{ Boolean(modelValue) ? '已启用' : '未启用' }}</span>
        </label>
      </div>
    </template>

    <template v-else-if="field.type === 'textarea'">
      <textarea
        :disabled="isDisabled"
        :placeholder="field.placeholder || ''"
        :readonly="field.readonly"
        :value="stringValue"
        @input="updateText"
      />
    </template>

    <template v-else-if="field.type === 'secret'">
      <div class="secret-input-wrap">
        <input
          :disabled="isDisabled"
          :placeholder="field.placeholder || ''"
          :readonly="field.readonly"
          :type="showSecret ? 'text' : 'password'"
          :value="secretDisplayValue"
          @input="updateText"
        >
        <button
          class="btn ghost btn-small"
          type="button"
          :disabled="isDisabled || isRevealing"
          @click="toggleSecret"
        >
          {{ isRevealing ? '加载中...' : showSecret ? '隐藏' : '显示' }}
        </button>
      </div>
    </template>

    <template v-else-if="field.type === 'schedule'">
      <div
        v-if="scheduleMode === 'visual'"
        class="schedule-wrap"
      >
        <select
          :disabled="isDisabled"
          :value="scheduleFreq"
          @change="onScheduleFreqChange"
        >
          <option
            v-for="opt in FREQ_LABELS"
            :key="opt.value"
            :value="opt.value"
          >{{ opt.label }}</option>
        </select>
        <input
          type="time"
          :disabled="isDisabled"
          :value="scheduleTime"
          @input="onScheduleTimeChange"
        >
        <button
          class="btn ghost btn-small"
          type="button"
          @click="scheduleMode = 'text'"
        >编辑表达式</button>
      </div>
      <div
        v-else
        class="schedule-wrap"
      >
        <input
          :disabled="isDisabled"
          :placeholder="field.placeholder || ''"
          type="text"
          :value="stringValue"
          @input="updateText"
        >
        <button
          class="btn ghost btn-small"
          type="button"
          @click="tryVisualMode"
        >切换选择器</button>
      </div>
      <small
        v-if="cronDescription"
        class="field-help cron-hint"
      >{{ cronDescription }}</small>
    </template>

    <template v-else-if="field.type === 'select'">
      <select
        :disabled="isDisabled"
        :value="stringValue"
        @change="updateText"
      >
        <option
          v-for="option in field.options || []"
          :key="option.value"
          :value="option.value"
        >
          {{ option.label }}
        </option>
      </select>
    </template>

    <template v-else>
      <input
        :disabled="isDisabled"
        :max="field.max"
        :min="field.min"
        :placeholder="field.placeholder || ''"
        :readonly="field.readonly"
        :step="field.step ?? (field.type === 'number' ? 'any' : undefined)"
        :type="inputType"
        :value="stringValue"
        @input="updateText"
      >
    </template>

    <div
      v-if="helpLines.length || showMaskHint"
      class="field-help-list"
    >
      <small
        v-for="line in helpLines"
        :key="line"
        class="field-help"
      >{{ line }}</small>
      <small
        v-if="showMaskHint"
        class="field-help"
      >保留 `******` 表示沿用当前密钥，不会覆盖后端已保存值。</small>
    </div>
  </label>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

import { api, unwrap } from '../../api'
import { buildCron, cronToHuman, FREQ_LABELS, parseCron } from '../../utils/cronHuman'

const props = defineProps({
  field: {
    type: Object,
    required: true,
  },
  modelValue: {
    type: [String, Number, Boolean],
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue'])
const showSecret = ref(false)
const isRevealing = ref(false)
const revealedValue = ref(null)

const isDisabled = computed(() => props.disabled || props.field.readonly)
const inputType = computed(() => {
  if (props.field.type === 'number') return 'number'
  if (props.field.type === 'url') return 'url'
  if (props.field.type === 'time') return 'time'
  return 'text'
})
const stringValue = computed(() => (props.modelValue ?? '').toString())
const showMaskHint = computed(
  () => props.field.type === 'secret' && stringValue.value === '******' && !showSecret.value,
)
const helpLines = computed(() => {
  if (!props.field.help) return []
  return Array.isArray(props.field.help) ? props.field.help : [props.field.help]
})

const secretDisplayValue = computed(() => {
  if (showSecret.value && revealedValue.value !== null) {
    return revealedValue.value
  }
  return stringValue.value
})

const cronDescription = computed(() => {
  if (props.field.type !== 'schedule') return ''
  const val = stringValue.value.trim()
  if (!val) return ''
  const desc = cronToHuman(val)
  return desc !== val ? desc : ''
})

const scheduleFreq = ref('daily')
const scheduleTime = ref('03:00')
const scheduleMode = ref('visual')

function initSchedule() {
  const parsed = parseCron(stringValue.value)
  if (parsed) {
    scheduleFreq.value = parsed.frequency
    scheduleTime.value = parsed.time
    scheduleMode.value = 'visual'
  } else if (stringValue.value.trim()) {
    scheduleMode.value = 'text'
  }
}

if (props.field.type === 'schedule') {
  initSchedule()
  watch(stringValue, initSchedule)
}

function onScheduleFreqChange(e) {
  scheduleFreq.value = e.target.value
  emit('update:modelValue', buildCron(scheduleFreq.value, scheduleTime.value))
}

function onScheduleTimeChange(e) {
  scheduleTime.value = e.target.value
  emit('update:modelValue', buildCron(scheduleFreq.value, scheduleTime.value))
}

function tryVisualMode() {
  const parsed = parseCron(stringValue.value)
  if (parsed) {
    scheduleFreq.value = parsed.frequency
    scheduleTime.value = parsed.time
    scheduleMode.value = 'visual'
  }
}

function updateText(event) {
  if (showSecret.value && revealedValue.value !== null) {
    revealedValue.value = null
    showSecret.value = false
  }
  emit('update:modelValue', event.target.value)
}

function updateBoolean(event) {
  emit('update:modelValue', event.target.checked)
}

async function toggleSecret() {
  if (showSecret.value) {
    showSecret.value = false
    revealedValue.value = null
    return
  }

  if (stringValue.value !== '******') {
    showSecret.value = true
    return
  }

  isRevealing.value = true
  try {
    const data = await unwrap(api.post('/config/reveal', { key: props.field.key }))
    revealedValue.value = data.value
    showSecret.value = true
  } catch {
    showSecret.value = true
  } finally {
    isRevealing.value = false
  }
}
</script>

<style scoped>
.setting-field-label {
  letter-spacing: 0.08em;
}

.cron-hint {
  color: var(--accent-soft, #8ba4bc);
  margin-top: 4px;
}

.schedule-wrap {
  display: flex;
  gap: 8px;
  align-items: center;
}

.schedule-wrap select {
  flex: 1;
  min-width: 0;
}

.schedule-wrap input[type='time'] {
  width: 120px;
  flex-shrink: 0;
}

.schedule-wrap input[type='text'] {
  flex: 1;
  min-width: 0;
}
</style>
