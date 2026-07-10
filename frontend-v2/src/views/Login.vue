<template>
  <section class="login-card panel panel-pad">
    <div class="login-head">
      <div class="login-logo">夜</div>
      <h1>登录管理后台</h1>
      <p>登录后可以写文章、查看发文任务、修改设置和备份。</p>
    </div>

    <form
      class="stack"
      @submit.prevent="submit"
    >
      <label class="field">
        <span>用户名</span>
        <input
          v-model="form.username"
          autocomplete="username"
          placeholder="默认是 admin"
        >
      </label>

      <label class="field">
        <span>密码</span>
        <input
          v-model="form.password"
          type="password"
          autocomplete="current-password"
          placeholder="请输入管理员密码"
        >
      </label>

      <button
        class="btn primary"
        type="submit"
        :disabled="isSubmitting"
        style="width: 100%"
      >
        {{ isSubmitting ? '登录中…' : '登录' }}
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
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'
import { getPostLoginRoute } from '../utils/adminNavigation'
import { describeError } from '../utils/errors'

const auth = useAuthStore()
const router = useRouter()
const isSubmitting = ref(false)
const isError = ref(false)
const message = ref('默认账号是 admin。请使用你自己设置的密码登录。')
const form = reactive({ username: 'admin', password: '' })

async function submit() {
  if (isSubmitting.value) return

  isSubmitting.value = true
  isError.value = false
  try {
    const data = await auth.login(form)
    router.push(getPostLoginRoute(Boolean(data.system_initialized ?? data.is_initialized)))
  } catch (error) {
    isError.value = true
    message.value = describeError(error, '登录失败，请检查账号密码或稍后重试。')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.login-card {
  width: min(420px, 100%);
  margin: 0 auto;
}

.login-head {
  text-align: center;
  margin-bottom: 22px;
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
