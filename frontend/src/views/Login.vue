<template>
  <section class="panel panel-pad" style="max-width: 480px; margin: 8vh auto 0;">
    <div class="hero">
      <div>
        <h1>登录后台</h1>
        <p>先获取管理会话，再继续配置、巡检与发布。</p>
      </div>
    </div>

    <form class="stack" @submit.prevent="submit">
      <label class="field">
        <span>用户名</span>
        <input v-model="form.username" autocomplete="username" placeholder="默认管理员账号为 admin" />
      </label>

      <label class="field">
        <span>密码</span>
        <input
          v-model="form.password"
          type="password"
          autocomplete="current-password"
          placeholder="请输入管理员密码"
        />
      </label>

      <div class="button-row">
        <button class="btn primary" type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? '登录中…' : '登录' }}
        </button>
      </div>

      <div class="muted">{{ message }}</div>
    </form>
  </section>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'
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
    router.push(data.is_initialized ? '/admin/' : '/admin/setup')
  } catch (error) {
    message.value = describeError(error, '登录失败，请检查账号密码或稍后重试。')
  } finally {
    isSubmitting.value = false
  }
}
</script>
