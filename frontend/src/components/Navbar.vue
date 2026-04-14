<template>
  <header class="nav-wrap">
    <div class="nav-inner panel">
      <div class="nav-brand">
        <div>
          <div class="brand-kicker">Quanzhen Night Journal Admin</div>
          <div class="brand">全真夜记</div>
          <div class="brand-status">
            <span class="brand-status-dot"></span>
            <span>{{ auth.username || 'admin' }} 正在守夜</span>
          </div>
        </div>
        <button class="btn ghost nav-toggle" type="button" @click="drawerOpen = !drawerOpen">
          {{ drawerOpen ? '收起导航' : '展开导航' }}
        </button>
      </div>

      <div class="nav-desktop">
        <div v-for="group in groups" :key="group.title" class="nav-group">
          <div class="nav-group-title">{{ group.title }}</div>
          <div class="nav-group-desc">{{ group.description }}</div>
          <nav class="nav-links">
            <RouterLink
              v-for="item in group.items"
              :key="item.to"
              :to="item.to"
              :class="{ active: isActive(item) }"
            >
              {{ item.label }}
            </RouterLink>
          </nav>
        </div>
      </div>

      <button class="btn ghost nav-logout" @click="handleLogout">退出</button>
    </div>

    <div v-if="drawerOpen" class="nav-drawer panel">
      <div v-for="group in groups" :key="group.title" class="nav-group">
        <div class="nav-group-title">{{ group.title }}</div>
        <div class="nav-group-desc">{{ group.description }}</div>
        <nav class="nav-drawer-links">
          <RouterLink
            v-for="item in group.items"
            :key="item.to"
            :to="item.to"
            :class="{ active: isActive(item) }"
            @click="drawerOpen = false"
          >
            {{ item.label }}
          </RouterLink>
        </nav>
      </div>

      <button class="btn ghost nav-drawer-logout" @click="handleLogout">退出登录</button>
    </div>
  </header>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'

const groups = [
  {
    title: '内容',
    description: '先看运营总览，再处理文章、人格设定和记忆碎片。',
    items: [
      { label: '总览', to: '/admin/' },
      { label: '文章', to: '/admin/posts' },
      { label: '人格设定（写作风格）', to: '/admin/personas' },
      { label: '记忆碎片（素材）', to: '/admin/memories' },
    ],
  },
  {
    title: '配置',
    description: '维护站点、模型和日常运行参数。',
    items: [
      { label: '设置', to: '/admin/settings' },
      { label: '环境输入', to: '/admin/sensory' },
    ],
  },
  {
    title: '观察',
    description: '查看系统状态、异常线索和排查信息。',
    items: [
      { label: '系统状态', to: '/admin/observatory' },
      { label: '日志', to: '/admin/audit' },
    ],
  },
  {
    title: '高级',
    description: '用于迁移、备份和特殊操作。',
    items: [
      { label: '迁移与备份', to: '/admin/ghost' },
    ],
  },
]

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const drawerOpen = ref(false)

function isActive(item) {
  if (item.to === '/admin/') return route.path === item.to
  return route.path.startsWith(item.to)
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
  padding: 16px 18px;
}

.nav-inner {
  width: min(1280px, calc(100vw - 36px));
  margin: 0 auto;
  padding: 18px 22px;
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr) auto;
  gap: 22px;
  align-items: start;
}

.nav-brand {
  display: grid;
  gap: 14px;
}

.brand-kicker {
  margin-bottom: 6px;
  font-size: 0.72rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--secondary);
}

.brand {
  font-size: 1.22rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  color: var(--ink);
  text-shadow: 0 0 20px rgba(200, 242, 255, 0.14);
}

.brand-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
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

.nav-desktop {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
}

.nav-group {
  display: grid;
  gap: 8px;
  padding: 2px 0;
}

.nav-group-title {
  font-size: 0.92rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--accent-soft);
}

.nav-group-desc {
  font-size: 0.86rem;
  color: var(--muted);
  line-height: 1.55;
}

.nav-links,
.nav-drawer-links {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.nav-links a,
.nav-drawer-links a {
  padding: 9px 13px;
  border-radius: 999px;
  color: var(--secondary);
  background: rgba(134, 215, 255, 0.04);
  border: 1px solid rgba(169, 223, 255, 0.12);
  transition: transform 0.22s ease, border-color 0.22s ease, background 0.22s ease, color 0.22s ease, box-shadow 0.22s ease;
}

.nav-links a:hover,
.nav-drawer-links a:hover {
  transform: translateY(-1px);
  color: var(--ink);
  border-color: rgba(169, 223, 255, 0.28);
  background: rgba(134, 215, 255, 0.08);
  box-shadow: 0 10px 24px rgba(1, 7, 16, 0.24);
}

.nav-links a.active,
.nav-drawer-links a.active {
  color: #041019;
  border-color: rgba(169, 223, 255, 0.24);
  background: linear-gradient(135deg, var(--accent), var(--accent-soft));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.32),
    0 14px 28px rgba(83, 191, 245, 0.24);
}

.nav-toggle,
.nav-drawer {
  display: none;
}

.nav-logout {
  align-self: center;
  min-width: 84px;
}

@media (max-width: 1080px) {
  .nav-inner {
    grid-template-columns: 1fr auto;
  }

  .nav-desktop,
  .nav-logout {
    display: none;
  }

  .nav-toggle {
    display: inline-flex;
    justify-content: center;
  }

  .nav-drawer {
    width: min(1280px, calc(100vw - 36px));
    margin: 12px auto 0;
    padding: 18px;
    display: grid;
    gap: 18px;
  }

  .nav-drawer-links {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
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
