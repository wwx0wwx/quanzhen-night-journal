<template>
  <label class="field" :class="{ wide: field.wide, 'field-boolean': field.type === 'boolean' }">
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
          />
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
        />
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

    <template v-else-if="field.type === 'cron'">
      <input
        :disabled="isDisabled"
        :placeholder="field.placeholder || ''"
        :readonly="field.readonly"
        type="text"
        :value="stringValue"
        @input="updateText"
      />
      <small v-if="cronDescription" class="field-help cron-hint">{{ cronDescription }}</small>
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
      />
    </template>

    <div class="field-help-list" v-if="helpLines.length || showMaskHint">
      <small v-for="line in helpLines" :key="line" class="field-help">{{ line }}</small>
      <small v-if="showMaskHint" class="field-help">保留 `******` 表示沿用当前密钥，不会覆盖后端已保存值。</small>
    </div>
  </label>
</template>

<script setup>
import { computed, ref } from 'vue'

import { api, unwrap } from '../../api'
import { cronToHuman } from '../../utils/cronHuman'

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
const showMaskHint = computed(() => props.field.type === 'secret' && stringValue.value === '******' && !showSecret.value)
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
  if (props.field.type !== 'cron') return ''
  const val = stringValue.value.trim()
  if (!val) return ''
  const desc = cronToHuman(val)
  return desc !== val ? desc : ''
})

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
</style>
