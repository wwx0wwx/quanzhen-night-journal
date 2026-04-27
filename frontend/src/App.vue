<template>
  <div class="shell">
    <Navbar v-if="showChrome" />
    <main
      class="view-shell"
      :class="{ solo: !showChrome }"
    >
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
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import AppErrorBoundary from './components/AppErrorBoundary.vue'
import Navbar from './components/Navbar.vue'

const route = useRoute()
const showChrome = computed(() => !['/admin/login', '/admin/setup'].includes(route.path))
</script>

<style>
.page-enter-active,
.page-leave-active {
  transition:
    opacity 0.22s ease,
    transform 0.22s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
