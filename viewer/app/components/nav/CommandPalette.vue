<script setup lang="ts">
import { mdiKeyboardOutline, mdiMagnify } from '@mdi/js'
import { labels } from '~/utils/labels'

const { open, query, active, results, loading, go } = useCommandPalette()
// A group heading goes above the first result of each group.
const headed = computed(() => results.value.map((item, i) => ({ item, heading: i === 0 || results.value[i - 1]!.group !== item.group ? item.group : null })))
</script>

<template>
  <v-dialog v-model="open" max-width="680" location="top" location-strategy="static" scrollable transition="slide-y-transition" class="mt-16">
    <v-card min-height="200" max-height="70vh">
      <v-text-field
        v-model="query"
        :placeholder="labels.nav.search"
        :prepend-inner-icon="mdiMagnify"
        variant="solo"
        flat
        rounded="0"
        hide-details
        autofocus
        class="flex-grow-0"
      >
        <template #append-inner><v-chip size="x-small" variant="outlined">Esc</v-chip></template>
      </v-text-field>
      <v-progress-linear :active="loading" indeterminate color="primary" height="2" />
      <v-divider />
      <v-card-text class="pa-2">
        <v-list v-if="results.length" density="comfortable" nav class="bg-transparent">
          <template v-for="({ item, heading }, i) in headed" :key="item.to">
            <v-list-subheader v-if="heading">{{ heading }}</v-list-subheader>
            <v-list-item
              :title="item.title"
              :subtitle="item.subtitle"
              :active="i === active"
              color="primary"
              rounded="xl"
              @click="go(item)"
              @mouseenter="active = i"
            >
              <template #prepend>
                <v-avatar :color="item.color" variant="tonal" size="36" class="me-1"><v-icon :icon="item.icon" size="20" /></v-avatar>
              </template>
            </v-list-item>
          </template>
        </v-list>
        <v-skeleton-loader v-else-if="loading" type="list-item-avatar-two-line@4" color="transparent" />
        <div v-else class="text-medium-emphasis text-center pa-8">{{ labels.nav.noResults }}</div>
      </v-card-text>
      <v-divider />
      <v-card-actions class="text-caption text-medium-emphasis px-4">
        <v-icon :icon="mdiKeyboardOutline" size="16" class="me-2" />{{ labels.nav.hint }}
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
