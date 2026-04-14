<template>
  <div class="shell">
    <Navbar v-if="showChrome" />
    <main class="view-shell" :class="{ solo: !showChrome }">
      <AppErrorBoundary>
        <router-view />
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
