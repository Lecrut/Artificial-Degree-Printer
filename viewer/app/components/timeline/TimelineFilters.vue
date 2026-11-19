<script setup lang="ts">
import { mdiMagnify } from '@mdi/js'
import type { EntryKind } from '#shared/types/timeline'
import type { TimelineFilters } from '~/composables/useTimeline'
import { labels } from '~/utils/labels'

const filters = defineModel<TimelineFilters>({ required: true })
const kinds = Object.keys(labels.kinds) as EntryKind[]
</script>

<template>
  <div class="d-flex flex-wrap align-center ga-4">
    <v-chip-group v-model="filters.kinds" multiple column selected-class="text-primary">
      <v-chip v-for="kind in kinds" :key="kind" :value="kind" filter>{{ labels.kinds[kind] }}</v-chip>
    </v-chip-group>
    <v-switch v-model="filters.onlyProblems" :label="labels.timeline.onlyProblems" color="error" density="compact" hide-details />
    <v-text-field
      v-model="filters.search"
      :placeholder="labels.timeline.search"
      :prepend-inner-icon="mdiMagnify"
      density="compact"
      variant="outlined"
      hide-details
      clearable
      max-width="360"
    />
  </div>
</template>
