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
          {{ drawerOpen ? t('common.closeMenu') : t('common.menu') }}
        </button>
        <strong>{{ mobileTitle }}</strong>
        <div class="mobile-topbar-actions">
          <LanguageToggle />
          <ThemeToggle />
        </div>
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
                :key="$route.path + ':' + locale"
              />
            </Transition>
          </router-view>
        </AppErrorBoundary>
      </div>
    </main>
    <AppToast />
    <ConfirmDialog />
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

import AppErrorBoundary from './components/AppErrorBoundary.vue'
import AppSidebar from './components/AppSidebar.vue'
import LanguageToggle from './components/LanguageToggle.vue'
import ThemeToggle from './components/ThemeToggle.vue'
import AppToast from './components/AppToast.vue'
import ConfirmDialog from './components/ConfirmDialog.vue'
import { api, unwrap } from './api'

const route = useRoute()
const { t, locale } = useI18n()
const drawerOpen = ref(false)
const pendingCount = ref(0)

const showChrome = computed(() => !['/admin/login', '/admin/setup'].includes(route.path))

const mobileTitle = computed(() => {
  const map = [
    ['/admin/', 'nav.home'],
    ['/admin/posts', 'nav.posts'],
    ['/admin/tasks', 'nav.tasks'],
    ['/admin/personas', 'nav.personas'],
    ['/admin/memories', 'nav.memories'],
    ['/admin/settings', 'nav.settings'],
    ['/admin/ghost', 'nav.backup'],
    ['/admin/audit', 'nav.audit'],
    ['/admin/sensory', 'nav.sensory'],
    ['/admin/folder-monitors', 'nav.folderMonitors'],
    ['/admin/about', 'nav.about'],
  ]
  for (const [path, key] of map) {
    if (route.path === path || (path !== '/admin/' && route.path.startsWith(path))) return t(key)
  }
  return t('common.admin')
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

.mobile-topbar-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
</style>
