<template>
  <section class="login-stage panel panel-pad">
    <div class="login-atmosphere">
      <div class="hero-kicker">
        Silent Entry
      </div>
      <h1>登录后台</h1>
      <p>穿过值守台的夜色后，才能继续配置、巡检与发文。这里不需要热闹，只需要稳定、安静和可控。</p>
      <div class="login-atmosphere-note">
        <span class="tag">清冷幽夜</span>
        <span class="muted">本页先建立夜间控制台的第一印象。</span>
      </div>
    </div>

    <form
      class="stack login-form"
      @submit.prevent="submit"
    >
      <label class="field">
        <span>用户名</span>
        <input
          v-model="form.username"
          autocomplete="username"
          placeholder="默认管理员账号为 admin"
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

      <div class="button-row">
        <button
          class="btn primary"
          type="submit"
          :disabled="isSubmitting"
        >
          {{ isSubmitting ? '登录中…' : '登录' }}
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
import { useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'
import { getPostLoginRoute } from '../utils/adminNavigation'
import { describeError } from '../utils/errors'

const auth = useAuthStore()
const router = useRouter()
const isSubmitting = ref(false)
const message = ref('默认管理员账号为 admin。生产环境不要使用弱口令。')
const form = reactive({ username: 'admin', password: '' })

async function submit() {
  if (isSubmitting.value) return

  isSubmitting.value = true
  try {
    const data = await auth.login(form)
    router.push(getPostLoginRoute(Boolean(data.system_initialized ?? data.is_initialized)))
  } catch (error) {
    message.value = describeError(error, '登录失败，请检查账号密码或稍后重试。')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.login-stage {
  max-width: 940px;
  margin: 8vh auto 0;
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
  gap: 28px;
  overflow: hidden;
}

.login-atmosphere {
  position: relative;
  display: grid;
  align-content: start;
  gap: 16px;
  min-height: 360px;
  padding: 8px 6px 8px 0;
}

.login-atmosphere::after {
  content: '';
  position: absolute;
  right: 8%;
  top: 14px;
  width: 180px;
  height: 180px;
  border-radius: 999px;
  background: radial-gradient(circle, var(--accent-glow), var(--panel-soft) 44%, transparent 68%);
  filter: blur(3px);
  opacity: 0.9;
}

.login-atmosphere h1 {
  position: relative;
  z-index: 1;
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(2rem, 4vw, 3rem);
  letter-spacing: 0.12em;
}

.login-atmosphere p {
  position: relative;
  z-index: 1;
  max-width: 42ch;
  margin: 0;
  line-height: 1.9;
  color: var(--muted);
}

.login-atmosphere-note {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 10px;
  align-content: start;
}

.login-form {
  position: relative;
  padding: 22px;
  border-radius: 16px;
  border: 1px solid var(--line);
  background: var(--panel);
}

@media (max-width: 900px) {
  .login-stage {
    margin-top: 3vh;
    grid-template-columns: 1fr;
  }

  .login-atmosphere {
    min-height: auto;
    padding-right: 0;
  }
}
</style>
