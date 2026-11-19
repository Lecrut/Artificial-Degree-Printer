<script setup lang="ts">
import { mdiHexagonMultipleOutline, mdiMagnify } from '@mdi/js'
import { useDisplay } from 'vuetify'
import { labels } from '~/utils/labels'

// Desktop: a rail at the side; phone: a bar under the thumb. Ctrl K searches everything from anywhere.
const { mdAndUp } = useDisplay()
const palette = useState('palette-open', () => false)
</script>

<template>
  <v-app>
    <v-app-bar border="b" height="64">
      <template #prepend>
        <v-avatar color="primary" variant="tonal" rounded="xl" class="ms-2">
          <v-icon :icon="mdiHexagonMultipleOutline" />
        </v-avatar>
      </template>
      <v-app-bar-title>
        <NuxtLink to="/" class="d-flex align-baseline ga-2 text-decoration-none text-high-emphasis">
          <span class="font-weight-bold">{{ labels.app }}</span>
          <span class="text-caption text-medium-emphasis d-none d-lg-inline">{{ labels.tagline }}</span>
        </NuxtLink>
      </v-app-bar-title>
      <template #append>
        <v-btn
          v-if="mdAndUp"
          :prepend-icon="mdiMagnify"
          variant="tonal"
          color="primary"
          class="me-4 px-4 text-none"
          min-width="320"
          @click="palette = true"
        >
          <span class="text-medium-emphasis me-auto">{{ labels.nav.search }}</span>
          <template #append><v-chip size="x-small" variant="outlined">{{ labels.nav.shortcut }}</v-chip></template>
        </v-btn>
        <v-btn v-else :icon="mdiMagnify" :title="labels.nav.search" @click="palette = true" />
      </template>
    </v-app-bar>
    <NavAppRail v-if="mdAndUp" />
    <NavBottomNav v-else />
    <NavCommandPalette />
    <v-main>
      <v-container class="py-8 px-4 px-md-6" max-width="1680">
        <NuxtPage />
      </v-container>
    </v-main>
  </v-app>
</template>
