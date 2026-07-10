<template>
  <section class="login-card panel panel-pad">
    <div class="login-lang">
      <LanguageToggle />
    </div>
    <div class="login-head">
      <div class="login-logo">
        {{ locale === 'en' ? 'Q' : '夜' }}
      </div>
      <h1>{{ t('login.title') }}</h1>
      <p>{{ t('login.subtitle') }}</p>
    </div>

    <form
      class="stack"
      @submit.prevent="submit"
    >
      <label class="field">
        <span>{{ t('login.username') }}</span>
        <input
          v-model="form.username"
          autocomplete="username"
          :placeholder="t('login.usernamePlaceholder')"
        >
      </label>

      <label class="field">
        <span>{{ t('login.password') }}</span>
        <input
          v-model="form.password"
          type="password"
          autocomplete="current-password"
          :placeholder="t('login.passwordPlaceholder')"
        >
      </label>

      <button
        class="btn primary"
        type="submit"
        :disabled="isSubmitting"
        style="width: 100%"
      >
        {{ isSubmitting ? t('login.submitting') : t('login.submit') }}
      </button>

      <div
        class="muted"
        :class="{ 'login-error': isError }"
      >
        {{ message }}
      </div>
    </form>
  </section>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import LanguageToggle from '../components/LanguageToggle.vue'
import { useAuthStore } from '../stores/auth'
import { getPostLoginRoute } from '../utils/adminNavigation'
import { describeError } from '../utils/errors'

const auth = useAuthStore()
const router = useRouter()
const { t, locale } = useI18n()
const isSubmitting = ref(false)
const isError = ref(false)
const message = ref(t('login.hint'))
const form = reactive({ username: 'admin', password: '' })

watch(locale, () => {
  if (!isError.value) message.value = t('login.hint')
})

async function submit() {
  if (isSubmitting.value) return

  isSubmitting.value = true
  isError.value = false
  try {
    const data = await auth.login(form)
    router.push(getPostLoginRoute(Boolean(data.system_initialized ?? data.is_initialized)))
  } catch (error) {
    isError.value = true
    message.value = describeError(error, t('login.hint'))
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.login-card {
  width: min(420px, 100%);
  margin: 0 auto;
  position: relative;
}

.login-lang {
  position: absolute;
  top: 16px;
  right: 16px;
}

.login-head {
  text-align: center;
  margin-bottom: 22px;
  padding-top: 8px;
}

.login-logo {
  width: 48px;
  height: 48px;
  margin: 0 auto 14px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #0f766e, #14b8a6);
  color: #fff;
  font-weight: 700;
  font-size: 1.1rem;
}

.login-head h1 {
  margin: 0;
  font-size: 1.4rem;
  letter-spacing: -0.02em;
}

.login-head p {
  margin: 8px 0 0;
  color: var(--muted);
  line-height: 1.6;
}

.login-error {
  color: var(--danger);
}
</style>
