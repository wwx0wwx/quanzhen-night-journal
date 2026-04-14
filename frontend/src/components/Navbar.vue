<template>
  <header class="nav-wrap">
    <div class="nav-inner panel">
      <div class="nav-brand">
        <div class="brand">全真夜记</div>
        <div class="brand-status">
          <span class="brand-status-dot"></span>
          <span>{{ auth.username || 'admin' }} 正在守夜</span>
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
  </header>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'

const overview = { label: '总览', to: '/admin/' }

const sections = [
  {
    id: 'content',
    label: '内容',
    to: '/admin/posts',
    items: [
      { label: '文章', to: '/admin/posts' },
      { label: '人格设定', to: '/admin/personas' },
      { label: '记忆碎片', to: '/admin/memories' },
    ],
  },
  {
    id: 'config',
    label: '配置',
    to: '/admin/settings',
    items: [
      { label: '设置', to: '/admin/settings' },
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
]

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const drawerOpen = ref(false)

const isOverviewActive = computed(() => route.path === overview.to)
const currentSection = computed(() => sections.find((section) => isSectionActive(section)) || null)
const showSubmenu = computed(() => {
  if (!currentSection.value) return false
  return currentSection.value.items.length > 1 || currentSection.value.id === 'advanced'
})

function isActive(path) {
  if (path === overview.to) return route.path === path
  return route.path.startsWith(path)
}

function isSectionActive(section) {
  return section.items.some((item) => isActive(item.to))
}

async function handleLogout() {
  drawerOpen.value = false
  await auth.logout()
  router.push('/admin/login')
}

watch(() => route.path, () => {
  drawerOpen.value = false
})
</script>

<style scoped>
.nav-wrap {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 20;
  padding: 14px 18px;
}

.nav-inner {
  width: min(1280px, calc(100vw - 36px));
  margin: 0 auto;
  padding: 16px 20px;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 18px;
  align-items: center;
}

.nav-brand {
  display: grid;
  gap: 8px;
}

.brand {
  font-size: 1.18rem;
  font-weight: 700;
  letter-spacing: 0.16em;
  color: var(--ink);
  text-shadow: 0 0 20px rgba(200, 242, 255, 0.14);
}

.brand-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  font-size: 0.9rem;
}

.brand-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--accent), var(--accent-soft));
  box-shadow: 0 0 16px rgba(134, 215, 255, 0.45);
}

.nav-primary {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
}

.nav-primary-link,
.nav-submenu-links a,
.nav-drawer-top-link,
.nav-drawer-links a {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 9px 14px;
  border-radius: 999px;
  color: var(--secondary);
  background: rgba(134, 215, 255, 0.04);
  border: 1px solid rgba(169, 223, 255, 0.12);
  transition: transform 0.22s ease, border-color 0.22s ease, background 0.22s ease, color 0.22s ease, box-shadow 0.22s ease;
}

.nav-primary-link:hover,
.nav-submenu-links a:hover,
.nav-drawer-top-link:hover,
.nav-drawer-links a:hover {
  transform: translateY(-1px);
  color: var(--ink);
  border-color: rgba(169, 223, 255, 0.28);
  background: rgba(134, 215, 255, 0.08);
  box-shadow: 0 10px 24px rgba(1, 7, 16, 0.24);
}

.nav-primary-link.active,
.nav-submenu-links a.active,
.nav-drawer-top-link.active,
.nav-drawer-links a.active {
  color: #041019;
  border-color: rgba(169, 223, 255, 0.24);
  background: linear-gradient(135deg, var(--accent), var(--accent-soft));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.32),
    0 14px 28px rgba(83, 191, 245, 0.24);
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
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: 0.08em;
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

@media (max-width: 1080px) {
  .nav-inner {
    grid-template-columns: 1fr auto;
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
}
</style>
