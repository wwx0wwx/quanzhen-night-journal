<template>
  <section class="panel panel-pad" style="max-width: 920px; margin: 4vh auto 0;">
    <div class="hero">
      <div>
        <h1>初始化引导</h1>
        <p>按顺序完成安全、站点和大脑接入后，系统才会解除锁定并进入可用状态。</p>
      </div>
    </div>

    <form class="stack" @submit.prevent="submit">
      <section class="setup-section stack">
        <div class="setup-section-head">
          <div class="setup-section-kicker">01</div>
          <div>
            <h2>安全</h2>
            <p class="muted">先设置管理员密码，后续登录后台就使用这组账号。</p>
          </div>
        </div>
        <div class="form-grid">
          <label class="field">
            <span>管理员密码</span>
            <input
              v-model="form.new_password"
              type="password"
              autocomplete="new-password"
              placeholder="设置一个至少 12 位、自己能妥善保管的新密码"
            />
            <div class="field-help-list">
              <small class="field-help">初始化成功后会自动用 `admin` 账号登录。</small>
            </div>
          </label>
        </div>
      </section>

      <section class="setup-section stack">
        <div class="setup-section-head">
          <div class="setup-section-kicker">02</div>
          <div>
            <h2>站点</h2>
            <p class="muted">这些内容会影响前台展示和公开访问地址。</p>
          </div>
        </div>
        <div class="form-grid">
          <label class="field">
            <span>站点标题</span>
            <input v-model="form.site_title" placeholder="例如：全真夜记" />
          </label>

          <label class="field">
            <span>副标题</span>
            <input v-model="form.site_subtitle" placeholder="例如：记录深夜、感知与缓慢校准" />
          </label>

          <label class="field">
            <span>域名</span>
            <input v-model="form.site_domain" placeholder="例如：journal.example.com" />
            <div class="field-help-list">
              <small class="field-help">只填写域名本身，不要带 `http://` 或 `https://`。</small>
            </div>
          </label>
        </div>
      </section>

      <section class="setup-section stack">
        <div class="setup-section-head">
          <div class="setup-section-kicker">03</div>
          <div>
            <h2>大脑接入</h2>
            <p class="muted">正文生成依赖 LLM，记忆检索与去重依赖 Embedding。字段名和提交结构保持不变。</p>
          </div>
        </div>

        <div class="panel panel-pad stack">
          <div class="setup-subsection-head">
            <div class="section-title">LLM</div>
            <div class="muted">负责正文生成、改写和主要推理。</div>
          </div>
          <div class="form-grid">
            <label class="field">
              <span>LLM Base URL</span>
              <input v-model="form.llm_base_url" placeholder="例如：https://api.openai.com/v1 或你的中转地址" />
            </label>

            <label class="field">
              <span>LLM API Key</span>
              <input v-model="form.llm_api_key" type="password" autocomplete="off" placeholder="输入模型服务分配给你的密钥" />
              <div class="field-help-list">
                <small class="field-help">如何获取？去你正在使用的模型服务后台创建 API Key，再复制到这里。</small>
              </div>
            </label>

            <label class="field">
              <span>LLM Model ID</span>
              <input v-model="form.llm_model_id" placeholder="例如：gpt-4.1-mini、qwen-max、deepseek-chat" />
            </label>
          </div>
        </div>

        <div class="panel panel-pad stack">
          <div class="setup-subsection-head">
            <div class="section-title">Embedding</div>
            <div class="muted">负责记忆检索、相似度判断和去重。</div>
          </div>
          <div class="form-grid">
            <label class="field">
              <span>Embedding Base URL</span>
              <input v-model="form.embedding_base_url" placeholder="例如：https://api.openai.com/v1 或你的向量服务地址" />
            </label>

            <label class="field">
              <span>Embedding API Key</span>
              <input
                v-model="form.embedding_api_key"
                type="password"
                autocomplete="off"
                placeholder="输入向量模型服务分配给你的密钥"
              />
              <div class="field-help-list">
                <small class="field-help">如何获取？通常在向量模型服务的控制台里创建，格式和 LLM Key 类似。</small>
              </div>
            </label>

            <label class="field">
              <span>Embedding Model ID</span>
              <input v-model="form.embedding_model_id" placeholder="例如：text-embedding-3-large、text-embedding-v4" />
            </label>
          </div>
        </div>
      </section>

      <div class="button-row">
        <button class="btn primary" type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? '初始化中…' : '完成初始化' }}
        </button>
      </div>

      <div class="muted">{{ message }}</div>
    </form>
  </section>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { api, unwrap } from '../api'
import { useAuthStore } from '../stores/auth'
import { getPostLoginRoute } from '../utils/adminNavigation'
import { describeError } from '../utils/errors'

const auth = useAuthStore()
const router = useRouter()
const isSubmitting = ref(false)
const message = ref('初始化完成后会自动生成默认人格。')
const form = reactive({
  new_password: '',
  site_title: '全真夜记',
  site_subtitle: '',
  site_domain: '',
  llm_base_url: '',
  llm_api_key: '',
  llm_model_id: '',
  embedding_base_url: '',
  embedding_api_key: '',
  embedding_model_id: '',
})

async function submit() {
  if (isSubmitting.value) return

  isSubmitting.value = true
  try {
    await unwrap(api.post('/setup/complete', form))
    await auth.refresh()
    const loginData = await auth.login({ username: 'admin', password: form.new_password })
    router.push(getPostLoginRoute(Boolean(loginData.system_initialized ?? loginData.is_initialized)))
  } catch (error) {
    message.value = describeError(error, '初始化失败，请检查填写内容后重试。')
  } finally {
    isSubmitting.value = false
  }
}
</script>
