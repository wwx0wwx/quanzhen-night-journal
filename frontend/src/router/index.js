import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '../stores/auth'
import Audit from '../views/Audit.vue'
import Dashboard from '../views/Dashboard.vue'
import Ghost from '../views/Ghost.vue'
import Login from '../views/Login.vue'
import Memories from '../views/Memories.vue'
import PersonaEdit from '../views/PersonaEdit.vue'
import Personas from '../views/Personas.vue'
import PostEdit from '../views/PostEdit.vue'
import Posts from '../views/Posts.vue'
import Settings from '../views/Settings.vue'
import Setup from '../views/Setup.vue'
import TaskDetail from '../views/TaskDetail.vue'
import { getPostLoginRoute } from '../utils/adminNavigation'

const routes = [
  { path: '/admin/login', component: Login, meta: { guest: true } },
  { path: '/admin/setup', component: Setup, meta: { guest: true } },
  { path: '/admin/', component: Dashboard },
  { path: '/admin/posts', component: Posts },
  { path: '/admin/posts/new', component: PostEdit },
  { path: '/admin/posts/:id', component: PostEdit },
  { path: '/admin/personas', component: Personas },
  { path: '/admin/personas/new', component: PersonaEdit },
  { path: '/admin/personas/:id', component: PersonaEdit },
  { path: '/admin/memories', component: Memories },
  { path: '/admin/observatory', redirect: '/admin/audit' },
  { path: '/admin/sensory', redirect: '/admin/audit' },
  { path: '/admin/tasks/:id', component: TaskDetail },
  { path: '/admin/settings', component: Settings },
  { path: '/admin/ghost', component: Ghost },
  { path: '/admin/audit', component: Audit },
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
