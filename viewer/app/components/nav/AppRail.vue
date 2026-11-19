<script setup lang="ts">
import { mdiMagnify } from '@mdi/js'
import { labels } from '~/utils/labels'
import { NAV_PAGES } from '~/utils/nav'

// Icons in a slim rail; hovering slides it open with the page names over the content.
const palette = useState('palette-open', () => false)
</script>

<template>
  <v-navigation-drawer permanent rail expand-on-hover rail-width="72" width="240" border="e" color="surface">
    <v-list nav density="comfortable" class="py-4">
      <v-list-item
        v-for="page in NAV_PAGES"
        :key="page.to"
        :to="page.to"
        :exact="page.exact"
        :prepend-icon="page.icon"
        :title="page.title"
        color="primary"
        rounded="xl"
        class="mb-1"
      />
    </v-list>
    <template #append>
      <v-list nav density="comfortable" class="py-4">
        <v-list-item :prepend-icon="mdiMagnify" :title="labels.nav.searchShort" rounded="xl" @click="palette = true">
          <template #append><v-chip size="x-small" variant="outlined">{{ labels.nav.shortcut }}</v-chip></template>
        </v-list-item>
      </v-list>
    </template>
  </v-navigation-drawer>
</template>
