<template>
  <section class="panel panel-pad stamp-card">
    <div class="stamp-head">
      <div>
        <div class="hero-kicker">Verification Seal</div>
        <div class="section-title">数字印记</div>
        <p class="muted">用于追溯当前稿件的生成结果、签发状态与版本痕迹。</p>
      </div>
      <div class="stamp-glyph" aria-hidden="true">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>

    <pre v-if="stamp" class="stamp-code">{{ stamp }}</pre>
    <div v-else class="stamp-empty muted">当前还没有可用印记，待文章保存或任务落档后会自动生成。</div>
  </section>
</template>

<script setup>
defineProps({
  stamp: { type: String, default: '' },
})
</script>

<style scoped>
.stamp-card {
  display: grid;
  gap: 18px;
  background:
    linear-gradient(180deg, rgba(232, 238, 245, 0.04), transparent 100%),
    rgba(9, 13, 20, 0.82);
}

.stamp-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}

.stamp-head p {
  max-width: 42ch;
  margin: 10px 0 0;
  line-height: 1.7;
}

.stamp-glyph {
  display: inline-grid;
  gap: 8px;
  min-width: 108px;
  padding: 10px 0 0;
}

.stamp-glyph span {
  display: block;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(216, 229, 240, 0.52), transparent);
}

.stamp-glyph span:nth-child(2) {
  width: 76%;
  justify-self: end;
}

.stamp-glyph span:nth-child(3) {
  width: 58%;
}

.stamp-code {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.7;
}

.stamp-empty {
  padding: 18px;
  border-radius: 16px;
  border: 1px dashed rgba(155, 176, 198, 0.18);
  background: rgba(157, 183, 207, 0.03);
  line-height: 1.7;
}

@media (max-width: 680px) {
  .stamp-head {
    flex-direction: column;
  }

  .stamp-glyph {
    width: 100%;
    min-width: 0;
  }
}
</style>
