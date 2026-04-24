<template>
  <section class="stack">
    <div class="hero about-hero">
      <div>
        <div class="hero-kicker">About This Project</div>
        <h1>关于本项目</h1>
        <p>一个围绕"人格、记忆、感知、事件、生成、发布"组织起来的 AI 人格博客引擎。</p>
      </div>
    </div>

    <div class="panel panel-pad about-section">
      <h2>项目简介</h2>
      <p>
        本系统是一个自动化写作与发布平台。它不只是博客引擎——系统内建了一套完整的"数字人格"运行时：
        从人格定义、记忆管理、环境感知、场景构建到文章生成与发布，构成一条完整的内容生产链。
      </p>
      <p>
        每篇文章的生成过程会经过多重质量校验，包括长度检查、重复检测、禁用词过滤和模板化措辞识别。
        通过 QA 的文章才会进入发布流程，最终由 Hugo 静态站点呈现给读者。
      </p>
    </div>

    <div class="panel panel-pad about-section">
      <h2>快速上手</h2>
      <div class="about-steps">
        <div class="about-step">
          <div class="about-step-num">1</div>
          <div>
            <strong>初始化系统</strong>
            <p>首次打开 <code>/admin/setup</code>，设置管理员密码、站点标题和模型配置。</p>
          </div>
        </div>
        <div class="about-step">
          <div class="about-step-num">2</div>
          <div>
            <strong>登录后台</strong>
            <p>使用刚才设置的密码登录 <code>/admin/login</code>。</p>
          </div>
        </div>
        <div class="about-step">
          <div class="about-step-num">3</div>
          <div>
            <strong>完善配置</strong>
            <p>在「系统设置」中确认大脑接入（LLM）、记忆检索（Embedding）和发文节奏已正确填写。</p>
          </div>
        </div>
        <div class="about-step">
          <div class="about-step-num">4</div>
          <div>
            <strong>调整人格</strong>
            <p>在「人格设定」中编辑默认人格的系统提示词、词典和场景，或创建全新人格。</p>
          </div>
        </div>
        <div class="about-step">
          <div class="about-step-num">5</div>
          <div>
            <strong>开始发文</strong>
            <p>在「总览」页点击「立即发文」手动触发，或等待系统按设定的节奏自动生成。</p>
          </div>
        </div>
      </div>
    </div>

    <div class="panel panel-pad about-section">
      <h2>功能模块</h2>
      <div class="about-modules">
        <div class="about-module">
          <h3>人格系统</h3>
          <p>定义数字生命的身份、口吻、词典和场景池。支持多人格切换，每个人格拥有独立的表达风格。</p>
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
          <p>支持 Ghost 格式导出数字生命数据、数据库快照和 Hugo 内容备份，方便迁移和灾难恢复。</p>
        </div>
      </div>
    </div>

    <div class="panel panel-pad about-section">
      <h2>常见问题</h2>
      <details v-for="faq in faqs" :key="faq.q" class="about-faq">
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
        <a href="https://github.com" target="_blank" rel="noopener">项目主页</a>
      </div>
    </div>
  </section>
</template>

<script setup>
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
    a: '在「高级 → 迁移与备份」页面可以创建数据库快照和 Ghost 格式导出。数据库快照是原始 SQLite 文件备份，适合快速回滚；Ghost 导出包含完整的数字生命数据，适合跨实例迁移。',
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
  background: rgba(157, 183, 207, 0.08);
  border: 1px solid rgba(155, 176, 198, 0.18);
  color: var(--ink);
  font-weight: 700;
  font-size: 0.9rem;
}

.about-step p {
  margin: 4px 0 0;
  color: var(--secondary);
}

.about-step code {
  background: rgba(157, 183, 207, 0.1);
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
  background: rgba(157, 183, 207, 0.03);
  border: 1px solid rgba(155, 176, 198, 0.1);
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
  border-bottom: 1px solid rgba(155, 176, 198, 0.1);
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
