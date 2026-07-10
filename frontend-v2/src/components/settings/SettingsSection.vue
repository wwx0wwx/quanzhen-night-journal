<template>
  <details
    v-if="section.collapsible"
    class="panel panel-pad settings-section"
    :open="section.openByDefault"
  >
    <summary class="settings-section-summary">
      <div>
        <div class="settings-section-kicker">
          Advanced Section
        </div>
        <h2>{{ section.title }}</h2>
        <p
          v-if="section.description"
          class="muted"
        >
          {{ section.description }}
        </p>
      </div>
      <div class="button-row settings-section-actions">
        <slot
          name="actions"
          :section="section"
        />
        <span class="tag">高级</span>
      </div>
    </summary>
    <div class="settings-section-body">
      <div class="form-grid settings-form-grid">
        <SettingField
          v-for="field in section.fields"
          :key="field.key"
          :disabled="disabled"
          :field="field"
          :model-value="values[field.key]"
          @update:model-value="emit('update', field.key, $event)"
        />
      </div>
    </div>
  </details>

  <div
    v-else
    class="panel panel-pad settings-section"
  >
    <div class="settings-section-head">
      <div>
        <div class="settings-section-kicker">
          Config Section
        </div>
        <h2>{{ section.title }}</h2>
        <p
          v-if="section.description"
          class="muted"
        >
          {{ section.description }}
        </p>
      </div>
      <div class="button-row settings-section-actions">
        <slot
          name="actions"
          :section="section"
        />
      </div>
    </div>
    <div class="form-grid settings-form-grid">
      <SettingField
        v-for="field in section.fields"
        :key="field.key"
        :disabled="disabled"
        :field="field"
        :model-value="values[field.key]"
        @update:model-value="emit('update', field.key, $event)"
      />
    </div>
  </div>
</template>

<script setup>
import SettingField from './SettingField.vue'

defineProps({
  section: {
    type: Object,
    required: true,
  },
  values: {
    type: Object,
    required: true,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update'])
</script>
