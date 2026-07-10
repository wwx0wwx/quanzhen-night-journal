<template>
  <section class="panel panel-pad setup-stage">
    <div style="display:flex;justify-content:flex-end;margin-bottom:8px">
      <LanguageToggle />
    </div>
    <div class="hero setup-hero">
      <div>
        <h1>{{ t('setup.title') }}</h1>
        <p>{{ t('setup.subtitle') }}</p>
      </div>
      <div class="setup-hero-note">
        <span class="tag">仅需三步</span>
        <div class="muted">
          先让系统可登录、可命名、可生成，再继续补足细节。
        </div>
      </div>
    </div>

    <form
      class="stack"
      @submit.prevent="submit"
    >
      <section class="setup-section stack">
        <div class="setup-section-head">
          <div class="setup-section-kicker">
            01
          </div>
          <div>
            <h2>安全</h2>
            <p class="muted">
              先设置管理员密码，后续登录后台就使用这组账号。
            </p>
          </div>
        </div>
        <div class="form-grid">
          <label class="field">
            <span>{{ t('setup.password') }}</span>
            <input
              v-model="form.new_password"
              type="password"
              autocomplete="new-password"
              :placeholder="t('setup.passwordPlaceholder')"
            >
            <div class="field-help-list">
              <small class="field-help">初始化成功后会自动用 `admin` 账号登录。</small>
            </div>
          </label>
        </div>
      </section>

      <section class="setup-section stack">
        <div class="setup-section-head">
          <div class="setup-section-kicker">
            02
          </div>
          <div>
            <h2>站点</h2>
            <p class="muted">
              这些内容会影响前台展示和公开访问地址。
            </p>
          </div>
        </div>
        <div class="form-grid">
          <label class="field">
            <span>{{ t('setup.siteTitle') }}</span>
            <input
              v-model="form.site_title"
              :placeholder="t('setup.siteTitlePlaceholder')"
            >
          </label>

          <label class="field">
            <span>{{ t('setup.siteSubtitle') }}</span>
            <input
              v-model="form.site_subtitle"
              :placeholder="t('setup.siteSubtitlePlaceholder')"
            >
          </label>

          <label class="field">
            <span>{{ t('setup.domain') }}</span>
            <input
              v-model="form.site_domain"
              :placeholder="t('setup.domainPlaceholder')"
            >
            <div class="field-help-list">
              <small class="field-help">只填写域名本身，不要带 `http://` 或 `https://`。</small>
              <small class="field-help">未配置域名时仅后台管理可用，博客需要域名才能公开访问。</small>
            </div>
          </label>
        </div>
      </section>

      <section class="setup-section stack">
        <div class="setup-section-head">
          <div class="setup-section-kicker">
            03
          </div>
          <div>
            <h2>AI 模型</h2>
            <p class="muted">
              首次可先接好 LLM，用来完成正文生成。记忆检索相关配置保持原样提交，后续可在配置页再补。
            </p>
          </div>
        </div>

        <div class="panel panel-pad stack setup-provider-card">
          <div class="setup-subsection-head">
            <div class="section-title">
              LLM
            </div>
            <div class="muted">
              负责正文生成、改写和主要推理。
            </div>
          </div>
          <div class="form-grid">
            <label class="field">
              <span>LLM Base URL</span>
              <input
                v-model="form.llm_base_url"
                :placeholder="t('setup.llmBasePlaceholder')"
              >
            </label>

            <label class="field">
              <span>LLM API Key</span>
              <input
                v-model="form.llm_api_key"
                type="password"
                autocomplete="off"
                :placeholder="t('setup.llmKeyPlaceholder')"
              >
              <div class="field-help-list">
                <small class="field-help">如何获取？去你正在使用的模型服务后台创建 API Key，再复制到这里。</small>
              </div>
            </label>

            <label class="field">
              <span>LLM Model ID</span>
              <input
                v-model="form.llm_model_id"
                :placeholder="t('setup.llmModelPlaceholder')"
              >
            </label>
          </div>
        </div>
      </section>

      <div class="button-row">
        <button
          class="btn primary"
          type="submit"
          :disabled="isSubmitting"
        >
          {{ isSubmitting ? t('setup.submitting') : t('setup.submit') }}
        </button>
      </div>

      <div class="muted">
        {{ message }}
      </div>
    </form>
  </section>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import LanguageToggle from '../components/LanguageToggle.vue'
import { useRouter } from 'vue-router'

import { api, unwrap } from '../api'
import { useAuthStore } from '../stores/auth'
import { getPostLoginRoute } from '../utils/adminNavigation'
import { describeError } from '../utils/errors'

const { t } = useI18n()

const auth = useAuthStore()
const router = useRouter()
const isSubmitting = ref(false)
const message = ref(t('setup.successHint'))
const form = reactive({
  new_password: '',
  site_title: '',
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

  if (form.new_password.length < 8) {
    message.value = t('setup.passwordShort')
    return
  }
  if (form.site_domain && /^https?:\/\//.test(form.site_domain)) {
    message.value = t('setup.domainInvalid')
    return
  }

  isSubmitting.value = true
  try {
    await unwrap(api.post('/setup/complete', form))
    await auth.refresh()
    const loginData = await auth.login({ username: 'admin', password: form.new_password })
    router.push(getPostLoginRoute(Boolean(loginData.system_initialized ?? loginData.is_initialized)))
  } catch (error) {
    message.value = describeError(error, t('setup.failed'))
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.setup-stage {
  max-width: 980px;
  margin: 4vh auto 0;
}

.setup-hero {
  align-items: end;
}

.setup-hero-note {
  display: grid;
  gap: 10px;
  justify-items: end;
  text-align: right;
}

.setup-provider-card {
  background: var(--panel);
}

@media (max-width: 900px) {
  .setup-hero-note {
    justify-items: start;
    text-align: left;
  }
}
</style>
