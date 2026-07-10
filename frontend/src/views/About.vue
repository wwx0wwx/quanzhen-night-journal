<template>
  <section class="stack">
    <div class="hero about-hero">
      <div>
        <h1>{{ t('about.title') }}</h1>
        <p>{{ t('about.subtitle') }}</p>
      </div>
    </div>

    <div class="panel panel-pad about-section">
      <h2>{{ t('about.what') }}</h2>
      <p>
        {{ t('about.whatP1') }}
      </p>
      <p>
        {{ t('about.whatP2') }}
      </p>
    </div>

    <div class="panel panel-pad about-section">
      <h2>{{ t('about.quickStart') }}</h2>
      <div class="about-steps">
        <div class="about-step">
          <div class="about-step-num">
            1
          </div>
          <div>
            <strong>初始化系统</strong>
            <p>首次打开 <code>/admin/setup</code>，设置管理员密码、站点标题和模型配置。</p>
          </div>
        </div>
        <div class="about-step">
          <div class="about-step-num">
            2
          </div>
          <div>
            <strong>登录后台</strong>
            <p>使用刚才设置的密码登录 <code>/admin/login</code>。</p>
          </div>
        </div>
        <div class="about-step">
          <div class="about-step-num">
            3
          </div>
          <div>
            <strong>完善配置</strong>
            <p>在「系统设置」确认 AI 模型和发文节奏已填好；首页会告诉你能不能发文。</p>
          </div>
        </div>
        <div class="about-step">
          <div class="about-step-num">
            4
          </div>
          <div>
            <strong>调角色与记忆</strong>
            <p>在「角色设定」「长期记忆」里改写作口吻和背景素材（可选）。</p>
          </div>
        </div>
        <div class="about-step">
          <div class="about-step-num">
            5
          </div>
          <div>
            <strong>开始发文</strong>
            <p>在「文章」页点「立即写一篇」，或等系统按设定节奏自动写。</p>
          </div>
        </div>
      </div>
    </div>

    <div class="panel panel-pad about-section">
      <h2>功能模块</h2>
      <div class="about-modules">
        <div class="about-module">
          <h3>角色系统</h3>
          <p>定义写作身份、口吻和场景。支持多个角色切换。</p>
        </div>
        <div class="about-module">
          <h3>记忆引擎</h3>
          <p>以向量检索为基础的长期记忆系统。记忆有权重和衰减机制，影响生成时的上下文选择。</p>
        </div>
        <div class="about-module">
          <h3>环境感知</h3>
          <p>采集运行环境的 CPU、内存、IO 等指标，感知结果会融入生成上下文，让文章带上"此时此刻"的质感。</p>
        </div>
        <div class="about-module">
          <h3>生成与 QA</h3>
          <p>调用 LLM 生成正文，经过长度、重复度、禁用词、模板化等多重质量校验后才可发布。</p>
        </div>
        <div class="about-module">
          <h3>定时发布</h3>
          <p>基于"几天一轮、一轮几篇"的节奏模型自动调度发文，也可随时手动触发。</p>
        </div>
        <div class="about-module">
          <h3>迁移与备份</h3>
          <p>支持完整搬家包导出、数据库快照和站点内容备份，方便迁移和恢复。</p>
        </div>
      </div>
    </div>

    <div class="panel panel-pad about-section">
      <h2>常见问题</h2>
      <details
        v-for="faq in faqs"
        :key="faq.q"
        class="about-faq"
      >
        <summary>{{ faq.q }}</summary>
        <p>{{ faq.a }}</p>
      </details>
    </div>

    <div class="panel panel-pad about-section about-footer">
      <div class="about-version">
        <span class="muted">前端版本</span>
        <strong>{{ version }}</strong>
      </div>
      <div class="about-links">
        <a
          href="https://github.com/wwx0wwx/quanzhen-night-journal"
          target="_blank"
          rel="noopener"
        >项目主页</a>
      </div>
    </div>
  </section>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()

const version = __APP_VERSION__

const faqs = [
  {
    q: '文章生成失败怎么办？',
    a: '先检查「系统设置」中大脑接入（LLM）的接口地址、密钥和模型名称是否正确，可以点击「测试大脑接入」验证连通性。如果配置无误，查看「系统日志」中的失败详情，常见原因包括余额不足、模型名称拼写错误或服务端限流。',
  },
  {
    q: '如何修改发文频率？',
    a: '在「系统设置 → 发文节奏与预算」中调整"几天一轮"和"一轮发几篇"。例如设置 3 天一轮、每轮 2 篇，系统就会在每 3 天内发出 2 篇文章。修改后从当天开始重新计算轮次。',
  },
  {
    q: '记忆检索（Embedding）必须配置吗？',
    a: '不是必须的。如果不配置 Embedding，系统仍然可以正常生成和发布文章，但记忆检索、去重和相似度判断功能会退化。建议在条件允许时配置。',
  },
  {
    q: '如何绑定自己的域名？',
    a: '在「系统设置 → 博客信息」中填写域名（不带 http://），然后将域名的 DNS A 记录指向服务器的公网 IP。系统会自动检测 DNS 并签发 HTTPS 证书。如果使用 Cloudflare 代理，还需要在 .env 中设置 ALLOW_CLOUDFLARE_PROXY_DOMAIN=true。',
  },
  {
    q: '数据如何备份和恢复？',
    a: '在「备份与迁移」可以做快速数据库备份，或导出完整搬家包。搬家包适合换服务器；数据库快照适合快速回滚。',
  },
  {
    q: '什么是"反完美化"？',
    a: '反完美化是一个可选的质量策略。开启后，系统会在检测到连续生成过于"工整"的内容时，适度引入变化，避免文风过于模式化。可以在「高级配置」中控制触发条件和冷却时间。',
  },
]
</script>

<style scoped>
.about-hero {
  text-align: center;
}

.about-hero p {
  max-width: 560px;
  margin: 0 auto;
}

.about-section h2 {
  margin-bottom: 16px;
}

.about-steps {
  display: grid;
  gap: 16px;
}

.about-step {
  display: grid;
  grid-template-columns: 36px 1fr;
  gap: 14px;
  align-items: start;
}

.about-step-num {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: var(--panel-soft);
  border: 1px solid var(--line-strong);
  color: var(--ink);
  font-weight: 700;
  font-size: 0.9rem;
}

.about-step p {
  margin: 4px 0 0;
  color: var(--secondary);
}

.about-step code {
  background: var(--panel-soft);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.88em;
}

.about-modules {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.about-module {
  padding: 16px;
  border-radius: 12px;
  background: var(--panel-soft);
  border: 1px solid var(--line);
}

.about-module h3 {
  margin: 0 0 8px;
  font-size: 1rem;
}

.about-module p {
  margin: 0;
  color: var(--secondary);
  font-size: 0.92rem;
}

.about-faq {
  padding: 14px 0;
  border-bottom: 1px solid var(--line);
}

.about-faq:last-child {
  border-bottom: none;
}

.about-faq summary {
  cursor: pointer;
  font-weight: 600;
  color: var(--ink);
  list-style: none;
}

.about-faq summary::before {
  content: '▸ ';
  color: var(--accent-soft);
}

.about-faq[open] summary::before {
  content: '▾ ';
}

.about-faq p {
  margin: 10px 0 0 16px;
  color: var(--secondary);
  line-height: 1.7;
}

.about-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.about-version {
  display: flex;
  align-items: center;
  gap: 10px;
}

.about-links a {
  color: var(--accent-soft);
}
</style>
