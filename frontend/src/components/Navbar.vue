<template>
  <header class="nav-wrap">
    <div class="nav-inner panel">
      <div class="nav-brand">
        <div class="brand">{{ brandTitle }}</div>
        <div class="brand-status">
          <span class="brand-status-dot"></span>
          <span>{{ brandStatus }}</span>
        </div>
      </div>

      <nav class="nav-primary" aria-label="后台主导航">
        <RouterLink :to="overview.to" class="nav-primary-link" :class="{ active: isOverviewActive }">
          {{ overview.label }}
        </RouterLink>
        <RouterLink
          v-for="section in sections"
          :key="section.id"
          :to="section.to"
          class="nav-primary-link"
          :class="{ active: isSectionActive(section) }"
        >
          {{ section.label }}
        </RouterLink>
      </nav>

      <button class="btn ghost nav-toggle" type="button" @click="drawerOpen = !drawerOpen">
        {{ drawerOpen ? '收起导航' : '展开导航' }}
      </button>

      <ThemeToggle class="nav-theme-toggle" />
    </div>

    <div v-if="showSubmenu" class="nav-submenu panel">
      <div class="nav-submenu-title">{{ currentSection.label }}</div>
      <div class="nav-submenu-links">
        <RouterLink
          v-for="item in currentSection.items"
          :key="item.to"
          :to="item.to"
          :class="{ active: isActive(item.to) }"
        >
          {{ item.label }}
        </RouterLink>
        <button
          v-if="currentSection.id === 'advanced'"
          class="btn ghost btn-small nav-submenu-logout"
          type="button"
          @click="handleLogout"
        >
          退出登录
        </button>
      </div>
    </div>

    <Transition name="drawer">
      <div v-if="drawerOpen" class="nav-drawer panel">
        <RouterLink :to="overview.to" class="nav-drawer-top-link" :class="{ active: isOverviewActive }" @click="drawerOpen = false">
          {{ overview.label }}
        </RouterLink>

        <div v-for="section in sections" :key="section.id" class="nav-drawer-group">
          <RouterLink
            :to="section.to"
            class="nav-drawer-top-link"
            :class="{ active: isSectionActive(section) }"
            @click="drawerOpen = false"
          >
            {{ section.label }}
          </RouterLink>
          <div class="nav-drawer-links">
            <RouterLink
              v-for="item in section.items"
              :key="item.to"
              :to="item.to"
              :class="{ active: isActive(item.to) }"
              @click="drawerOpen = false"
            >
              {{ item.label }}
            </RouterLink>
            <button
              v-if="section.id === 'advanced'"
              class="btn ghost btn-small nav-drawer-logout"
              type="button"
              @click="handleLogout"
            >
              退出登录
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </header>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api, unwrap } from '../api'
import { useAuthStore } from '../stores/auth'
import ThemeToggle from './ThemeToggle.vue'

const overview = { label: '总览', to: '/admin/' }

const sections = [
  {
    id: 'content',
    label: '内容',
    to: '/admin/posts',
    items: [
      { label: '文章', to: '/admin/posts' },
      { label: '任务', to: '/admin/tasks' },
    ],
  },
  {
    id: 'config',
    label: '配置',
    to: '/admin/settings',
    items: [
      { label: '系统设置', to: '/admin/settings' },
      { label: '人格设定', to: '/admin/personas' },
      { label: '记忆碎片', to: '/admin/memories' },
    ],
  },
  {
    id: 'advanced',
    label: '高级',
    to: '/admin/ghost',
    items: [
      { label: '迁移与备份', to: '/admin/ghost' },
      { label: '系统日志', to: '/admin/audit' },
    ],
  },
  {
    id: 'about',
    label: '关于',
    to: '/admin/about',
    items: [{ label: '关于', to: '/admin/about' }],
  },
]

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const drawerOpen = ref(false)
const branding = reactive({
  siteTitle: '',
  panelTitle: '',
  panelStatusText: '{user} 正在守夜',
})

const isOverviewActive = computed(() => route.path === overview.to)
const currentSection = computed(() => sections.find((section) => isSectionActive(section)) || null)
const showSubmenu = computed(() => {
  if (!currentSection.value) return false
  return currentSection.value.items.length > 1 || currentSection.value.id === 'advanced'
})
const brandTitle = computed(() => branding.panelTitle.trim() || branding.siteTitle.trim() || 'Night Journal')
const brandStatus = computed(() => renderStatusText(branding.panelStatusText))

function isActive(path) {
  if (path === overview.to) return route.path === path
  return route.path.startsWith(path)
}

function isSectionActive(section) {
  return section.items.some((item) => isActive(item.to))
}

function renderStatusText(template) {
  const value = String(template || '').trim() || '{user} 正在守夜'
  return value.includes('{user}')
    ? value.replaceAll('{user}', auth.username || 'admin')
    : value
}

function applyBranding(detail = {}) {
  if (Object.prototype.hasOwnProperty.call(detail, 'site.title')) {
    branding.siteTitle = String(detail['site.title'] || '')
  }
  if (Object.prototype.hasOwnProperty.call(detail, 'panel.title')) {
    branding.panelTitle = String(detail['panel.title'] || '')
  }
  if (Object.prototype.hasOwnProperty.call(detail, 'panel.status_text')) {
    branding.panelStatusText = String(detail['panel.status_text'] || '')
  }
}

async function loadBranding() {
  try {
    const data = await unwrap(api.get('/config'))
    applyBranding({
      'site.title': data['site.title']?.value,
      'panel.title': data['panel.title']?.value,
      'panel.status_text': data['panel.status_text']?.value,
    })
  } catch {
    // Keep local fallbacks when config cannot be loaded.
  }
}

function handleConfigUpdated(event) {
  applyBranding(event.detail || {})
}

async function handleLogout() {
  drawerOpen.value = false
  await auth.logout()
  router.push('/admin/login')
}

watch(() => route.path, () => {
  drawerOpen.value = false
})

onMounted(async () => {
  window.addEventListener('admin-config-updated', handleConfigUpdated)
  await loadBranding()
})

onBeforeUnmount(() => {
  window.removeEventListener('admin-config-updated', handleConfigUpdated)
})
</script>

<style scoped>
.nav-wrap {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 20;
  padding: 16px 20px;
}

.nav-inner {
  width: min(1280px, calc(100vw - 36px));
  margin: 0 auto;
  padding: 18px 22px;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto auto;
  gap: 22px;
  align-items: center;
}

.nav-brand {
  display: grid;
  gap: 10px;
}

.brand {
  font-family: var(--font-display);
  font-size: 1.24rem;
  font-weight: 600;
  letter-spacing: 0.22em;
  color: var(--ink);
  text-transform: uppercase;
  text-shadow: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 260px;
}

.brand-status {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--muted);
  font-size: 0.82rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.brand-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(200, 216, 232, 0.92), rgba(118, 141, 168, 0.92));
  box-shadow: 0 0 14px var(--accent-glow);
}

.nav-primary {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
}

.nav-primary-link,
.nav-submenu-links a,
.nav-drawer-top-link,
.nav-drawer-links a {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 9px 16px;
  border-radius: 999px;
  color: var(--secondary);
  background: var(--panel-soft);
  border: 1px solid var(--line);
  transition: transform 0.22s ease, border-color 0.22s ease, background 0.22s ease, color 0.22s ease, box-shadow 0.22s ease;
}

.nav-primary-link:hover,
.nav-submenu-links a:hover,
.nav-drawer-top-link:hover,
.nav-drawer-links a:hover {
  transform: translateY(-1px);
  color: var(--ink);
  border-color: var(--line-strong);
  background: var(--accent-glow);
  box-shadow: var(--shadow-soft);
}

.nav-primary-link.active,
.nav-submenu-links a.active,
.nav-drawer-top-link.active,
.nav-drawer-links a.active {
  color: var(--ink);
  border-color: var(--accent-strong);
  background: var(--accent-glow);
  box-shadow: var(--shadow-soft);
}

.nav-submenu {
  width: min(1280px, calc(100vw - 36px));
  margin: 10px auto 0;
  padding: 14px 18px;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 16px;
  align-items: center;
}

.nav-submenu-title {
  color: var(--accent-soft);
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

.nav-submenu-links {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.nav-submenu-logout {
  min-height: 40px;
}

.nav-toggle,
.nav-drawer {
  display: none;
}

.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.24s ease, transform 0.24s ease;
}

.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

@media (max-width: 1080px) {
  .nav-inner {
    grid-template-columns: 1fr auto auto;
    align-items: start;
  }

  .nav-primary,
  .nav-submenu {
    display: none;
  }

  .nav-toggle,
  .nav-drawer {
    display: grid;
  }

  .nav-toggle {
    justify-content: center;
  }

  .nav-drawer {
    width: min(1280px, calc(100vw - 36px));
    margin: 12px auto 0;
    padding: 18px;
    gap: 16px;
  }

  .nav-drawer-group {
    display: grid;
    gap: 10px;
  }

  .nav-drawer-links {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 10px;
  }

  .nav-drawer-logout {
    justify-self: start;
  }
}

@media (max-width: 900px) {
  .nav-wrap {
    padding: 12px;
  }

  .nav-inner,
  .nav-drawer {
    width: calc(100vw - 24px);
  }

  .brand {
    max-width: 200px;
  }
}

.nav-theme-toggle {
  align-self: center;
}
</style>
