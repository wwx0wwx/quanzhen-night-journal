<template>
  <div
    class="shell"
    :class="showChrome ? 'with-sidebar' : 'solo-shell'"
  >
    <template v-if="showChrome">
      <header class="mobile-topbar">
        <button
          class="btn ghost btn-small"
          type="button"
          @click="drawerOpen = !drawerOpen"
        >
          {{ drawerOpen ? '关闭菜单' : '菜单' }}
        </button>
        <strong>{{ mobileTitle }}</strong>
        <ThemeToggle />
      </header>

      <div
        v-if="drawerOpen"
        class="mobile-backdrop"
        @click="drawerOpen = false"
      />

      <AppSidebar
        :open="drawerOpen"
        :pending-count="pendingCount"
        @close="drawerOpen = false"
      />
    </template>

    <main
      class="view-shell"
      :class="{ solo: !showChrome }"
    >
<div :class="showChrome ? 'view-content' : ''">
        <AppErrorBoundary>
          <router-view v-slot="{ Component }">
            <Transition
              name="page"
              mode="out-in"
            >
              <component
                :is="Component"
                :key="$route.path"
              />
            </Transition>
          </router-view>
        </AppErrorBoundary>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import AppErrorBoundary from './components/AppErrorBoundary.vue'
import AppSidebar from './components/AppSidebar.vue'
import ThemeToggle from './components/ThemeToggle.vue'
import { api, unwrap } from './api'

const route = useRoute()
const drawerOpen = ref(false)
const pendingCount = ref(0)

const showChrome = computed(() => !['/admin/login', '/admin/setup'].includes(route.path))

const mobileTitle = computed(() => {
  const map = {
    '/admin/': '首页',
    '/admin/posts': '文章',
    '/admin/tasks': '发文任务',
    '/admin/personas': '角色设定',
    '/admin/memories': '长期记忆',
    '/admin/settings': '系统设置',
    '/admin/ghost': '备份与迁移',
    '/admin/audit': '运行日志',
    '/admin/sensory': '环境状态',
    '/admin/folder-monitors': '目录监控',
    '/admin/about': '使用说明',
  }
  for (const [path, title] of Object.entries(map)) {
    if (route.path === path || (path !== '/admin/' && route.path.startsWith(path))) return title
  }
  return '管理后台'
})

watch(
  () => route.path,
  () => {
    drawerOpen.value = false
  },
)

async function refreshPending() {
  if (!showChrome.value) return
  try {
    const data = await unwrap(api.get('/dashboard'))
    const failed = Number(data?.risk_overview?.failed || 0) - Number(data?.risk_overview?.failed_acknowledged || 0)
    const circuit =
      Number(data?.risk_overview?.circuit_open || 0) - Number(data?.risk_overview?.circuit_open_acknowledged || 0)
    const waiting = Number(data?.risk_overview?.waiting_human_signoff || 0)
    pendingCount.value = Math.max(0, failed) + Math.max(0, circuit) + Math.max(0, waiting)
  } catch {
    // ignore badge errors
  }
}

onMounted(refreshPending)
watch(() => route.path, refreshPending)
</script>

<style>
.page-enter-active,
.page-leave-active {
  transition:
    opacity 0.16s ease,
    transform 0.16s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(4px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-3px);
}
</style>
