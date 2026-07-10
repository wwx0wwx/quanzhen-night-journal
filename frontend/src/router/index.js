import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '../stores/auth'
import { getPostLoginRoute } from '../utils/adminNavigation'

const routes = [
  {
    path: '/admin/login',
    component: () => import('../views/Login.vue'),
    meta: { guest: true },
  },
  {
    path: '/admin/setup',
    component: () => import('../views/Setup.vue'),
    meta: { guest: true },
  },
  { path: '/admin/', component: () => import('../views/Dashboard.vue') },
  { path: '/admin/posts', component: () => import('../views/Posts.vue') },
  { path: '/admin/posts/new', component: () => import('../views/PostEdit.vue') },
  { path: '/admin/posts/:id', component: () => import('../views/PostEdit.vue') },
  { path: '/admin/personas', component: () => import('../views/Personas.vue') },
  { path: '/admin/personas/new', component: () => import('../views/PersonaEdit.vue') },
  { path: '/admin/personas/:id', component: () => import('../views/PersonaEdit.vue') },
  { path: '/admin/memories', component: () => import('../views/Memories.vue') },
  { path: '/admin/observatory', redirect: '/admin/audit' },
  { path: '/admin/sensory', component: () => import('../views/Sensory.vue') },
  { path: '/admin/tasks', component: () => import('../views/Tasks.vue') },
  { path: '/admin/tasks/:id', component: () => import('../views/TaskDetail.vue') },
  { path: '/admin/folder-monitors', component: () => import('../views/FolderMonitors.vue') },
  { path: '/admin/settings', component: () => import('../views/Settings.vue') },
  { path: '/admin/ghost', component: () => import('../views/Ghost.vue') },
  { path: '/admin/audit', component: () => import('../views/Audit.vue') },
  { path: '/admin/about', component: () => import('../views/About.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/admin/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.loaded) {
    try {
      await auth.refresh()
    } catch {
      auth.loaded = true
      auth.isLoggedIn = false
    }
  }

  if (to.path === '/admin/setup' && auth.isInitialized && auth.isLoggedIn) {
    return '/admin/'
  }

  if (to.meta.guest) {
    if (to.path === '/admin/login' && auth.isLoggedIn) {
      return getPostLoginRoute(auth.isInitialized)
    }
    return true
  }

  if (!auth.isInitialized) {
    return '/admin/setup'
  }

  if (!auth.isLoggedIn) {
    return '/admin/login'
  }

  return true
})

export default router
