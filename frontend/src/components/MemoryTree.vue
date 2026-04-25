<template>
  <div class="panel panel-pad memory-tree-card">
    <div class="memory-tree-head">
      <div>
        <div class="hero-kicker">Layered Ledger</div>
        <div class="section-title">记忆分层</div>
      </div>
      <div class="muted">系统会按 L0 至 L3 展开最近归档的素材，方便快速确认哪一层还缺内容。</div>
    </div>

    <div v-if="!groups.length" class="memory-tree-empty muted">当前还没有可展示的记忆条目。</div>

    <div v-else class="memory-tree-grid">
      <section v-for="group in groups" :key="group.level" class="memory-level-card">
        <div class="memory-level-head">
          <div class="button-row">
            <span class="tag">{{ levelLabel(group.level) }}</span>
            <span class="muted">{{ group.items.length }} 条</span>
          </div>
          <div class="memory-level-rule"></div>
        </div>

        <div class="list memory-level-list">
          <article v-for="item in group.items" :key="item.id" class="list-item memory-entry">
            <div class="memory-entry-head">
              <strong>{{ item.summary || item.content }}</strong>
              <span class="memory-entry-id">#{{ item.id }}</span>
            </div>
            <div class="memory-entry-meta">
              <span>{{ personaName(item.persona_id) }}</span>
              <span v-if="item.tags?.length">{{ item.tags.join(' / ') }}</span>
            </div>
          </article>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  memories: { type: Array, default: () => [] },
  personas: { type: Array, default: () => [] },
})

const levelMap = {
  L0: 'L0 核心设定',
  L1: 'L1 长期主题',
  L2: 'L2 近期线索',
  L3: 'L3 瞬时片段',
}

function levelLabel(level) {
  return levelMap[level] || level
}

function personaName(personaId) {
  return props.personas.find((item) => item.id === personaId)?.name || `#${personaId}`
}

const groups = computed(() => ['L0', 'L1', 'L2', 'L3'].map((level) => ({
  level,
  items: props.memories.filter((item) => item.level === level).slice(0, 4),
})).filter((group) => group.items.length))
</script>

<style scoped>
.memory-tree-card {
  display: grid;
  gap: 20px;
}

.memory-tree-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}

.memory-tree-head .muted {
  max-width: 32ch;
  text-align: right;
  line-height: 1.7;
}

.memory-tree-empty {
  padding: 18px;
  border-radius: 16px;
  border: 1px dashed var(--line-strong);
  background: var(--panel-soft);
}

.memory-tree-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.memory-level-card {
  display: grid;
  gap: 14px;
  padding: 18px;
  border-radius: 18px;
  border: 1px solid var(--line);
  background: var(--panel);
}

.memory-level-head {
  display: grid;
  gap: 12px;
}

.memory-level-rule {
  height: 1px;
  background: linear-gradient(90deg, var(--line-strong), transparent 78%);
}

.memory-level-list {
  gap: 10px;
}

.memory-entry {
  gap: 10px;
  min-height: 126px;
}

.memory-entry-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.memory-entry-head strong {
  line-height: 1.7;
}

.memory-entry-id {
  color: var(--muted);
  font-size: 0.78rem;
  letter-spacing: 0.12em;
}

.memory-entry-meta {
  display: grid;
  gap: 6px;
  color: var(--secondary);
  font-size: 0.9rem;
  line-height: 1.6;
}

@media (max-width: 680px) {
  .memory-tree-head,
  .memory-entry-head {
    flex-direction: column;
  }

  .memory-tree-head .muted {
    max-width: none;
    text-align: left;
  }
}
</style>
