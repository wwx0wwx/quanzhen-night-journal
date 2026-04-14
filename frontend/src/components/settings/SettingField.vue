<template>
  <label class="field" :class="{ wide: field.wide, 'field-boolean': field.type === 'boolean' }">
    <div class="field-head">
      <span>{{ field.label }}</span>
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
          :value="stringValue"
          @input="updateText"
        />
        <button class="btn ghost btn-small" type="button" :disabled="isDisabled" @click="toggleSecret">
          {{ showSecret ? '隐藏' : '显示' }}
        </button>
      </div>
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

const isDisabled = computed(() => props.disabled || props.field.readonly)
const inputType = computed(() => {
  if (props.field.type === 'number') return 'number'
  if (props.field.type === 'url') return 'url'
  return 'text'
})
const stringValue = computed(() => (props.modelValue ?? '').toString())
const showMaskHint = computed(() => props.field.type === 'secret' && stringValue.value === '******')
const helpLines = computed(() => {
  if (!props.field.help) return []
  return Array.isArray(props.field.help) ? props.field.help : [props.field.help]
})

function updateText(event) {
  emit('update:modelValue', event.target.value)
}

function updateBoolean(event) {
  emit('update:modelValue', event.target.checked)
}

function toggleSecret() {
  showSecret.value = !showSecret.value
}
</script>
