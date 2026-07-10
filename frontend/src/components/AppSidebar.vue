<template>
  <aside
    class="app-sidebar"
    :class="{ open: open }"
  >
    <div class="sidebar-brand">
      <div
        class="sidebar-logo"
        aria-hidden="true"
      >
        夜
      </div>
      <div class="sidebar-brand-text">
        <div class="sidebar-brand-title">
          {{ brandTitle }}
        </div>
        <div class="sidebar-brand-sub">
          {{ brandStatus }}
        </div>
      </div>
    </div>

    <nav
      class="sidebar-nav"
      aria-label="后台导航"
    >
      <RouterLink
        to="/admin/"
        class="sidebar-link"
        :class="{ active: isActive('/admin/', true) }"
        @click="emitClose"
      >
        <span class="sidebar-link-icon">⌂</span>
        <span>首页</span>
        <span
          v-if="pendingCount > 0"
          class="sidebar-badge"
        >{{ pendingCount > 99 ? '99+' : pendingCount }}</span>
      </RouterLink>

      <div class="sidebar-section-label">
        写作
      </div>
      <RouterLink
        to="/admin/posts"
        class="sidebar-link"
        :class="{ active: isActive('/admin/posts') }"
        @click="emitClose"
      >
        <span class="sidebar-link-icon">文</span>
        <span>文章</span>
      </RouterLink>
      <RouterLink
        to="/admin/tasks"
        class="sidebar-link"
        :class="{ active: isActive('/admin/tasks') }"
        @click="emitClose"
      >
        <span class="sidebar-link-icon">任</span>
        <span>发文任务</span>
      </RouterLink>

      <div class="sidebar-section-label">
        角色与记忆
      </div>
      <RouterLink
        to="/admin/personas"
        class="sidebar-link"
        :class="{ active: isActive('/admin/personas') }"
        @click="emitClose"
      >
        <span class="sidebar-link-icon">角</span>
        <span>角色设定</span>
      </RouterLink>
      <RouterLink
        to="/admin/memories"
        class="sidebar-link"
        :class="{ active: isActive('/admin/memories') }"
        @click="emitClose"
      >
        <span class="sidebar-link-icon">记</span>
        <span>长期记忆</span>
      </RouterLink>

      <div class="sidebar-section-label">
        运行与安全
      </div>
      <RouterLink
        to="/admin/settings"
        class="sidebar-link"
        :class="{ active: isActive('/admin/settings') }"
        @click="emitClose"
      >
        <span class="sidebar-link-icon">设</span>
        <span>系统设置</span>
      </RouterLink>
      <RouterLink
        to="/admin/ghost"
        class="sidebar-link"
        :class="{ active: isActive('/admin/ghost') }"
        @click="emitClose"
      >
        <span class="sidebar-link-icon">备</span>
        <span>备份与迁移</span>
      </RouterLink>
      <RouterLink
        to="/admin/audit"
        class="sidebar-link"
        :class="{ active: isActive('/admin/audit') }"
        @click="emitClose"
      >
        <span class="sidebar-link-icon">志</span>
        <span>运行日志</span>
      </RouterLink>

      <div class="sidebar-section-label">
        更多工具
      </div>
      <RouterLink
        to="/admin/sensory"
        class="sidebar-link"
        :class="{ active: isActive('/admin/sensory') }"
        @click="emitClose"
      >
        <span class="sidebar-link-icon">感</span>
        <span>环境状态</span>
      </RouterLink>
      <RouterLink
        to="/admin/folder-monitors"
        class="sidebar-link"
        :class="{ active: isActive('/admin/folder-monitors') }"
        @click="emitClose"
      >
        <span class="sidebar-link-icon">监</span>
        <span>目录监控</span>
      </RouterLink>
      <RouterLink
        to="/admin/about"
        class="sidebar-link"
        :class="{ active: isActive('/admin/about') }"
        @click="emitClose"
      >
        <span class="sidebar-link-icon">?</span>
        <span>使用说明</span>
      </RouterLink>
    </nav>

    <div class="sidebar-footer">
      <div class="sidebar-user">
        <div class="sidebar-user-avatar">
          {{ avatarLetter }}
        </div>
        <div class="sidebar-user-meta">
          <div class="sidebar-user-name">
            {{ auth.username || 'admin' }}
          </div>
          <div class="sidebar-user-role">
            管理员
          </div>
        </div>
      </div>
      <div class="sidebar-actions">
        <ThemeToggle />
        <button
          class="btn ghost btn-small"
          type="button"
          style="flex: 1"
          @click="handleLogout"
        >
          退出登录
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api, unwrap } from '../api'
import { useAuthStore } from '../stores/auth'
import ThemeToggle from './ThemeToggle.vue'

defineProps({
  open: { type: Boolean, default: false },
  pendingCount: { type: Number, default: 0 },
})

const emit = defineEmits(['close'])

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const branding = reactive({
  siteTitle: '',
  panelTitle: '',
  panelStatusText: '{user} 已登录',
})

const brandTitle = computed(() => branding.panelTitle.trim() || branding.siteTitle.trim() || '全真夜记')
const brandStatus = computed(() => renderStatusText(branding.panelStatusText))
const avatarLetter = computed(() => String(auth.username || 'A').slice(0, 1).toUpperCase())

function isActive(path, exact = false) {
  if (exact) return route.path === path
  return route.path === path || route.path.startsWith(`${path}/`) || route.path.startsWith(path)
}

function renderStatusText(template) {
  const value = String(template || '').trim() || '{user} 已登录'
  return value.includes('{user}') ? value.replaceAll('{user}', auth.username || 'admin') : value
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
    // keep defaults
  }
}

function handleConfigUpdated(event) {
  applyBranding(event.detail || {})
}

function emitClose() {
  emit('close')
}

async function handleLogout() {
  emitClose()
  await auth.logout()
  router.push('/admin/login')
}

onMounted(async () => {
  window.addEventListener('admin-config-updated', handleConfigUpdated)
  await loadBranding()
})

onBeforeUnmount(() => {
  window.removeEventListener('admin-config-updated', handleConfigUpdated)
})
</script>
