<script setup lang="ts">
import { mdiCalendarRange, mdiFilterVariant } from '@mdi/js'
import type { RangePreset } from '~/composables/useHistoryDashboard'
import { labels } from '~/utils/labels'

defineProps<{ allTasks: string[], allStatuses: string[] }>()
const preset = defineModel<RangePreset>('preset', { required: true })
const custom = defineModel<Date[]>('custom', { required: true })
const tasks = defineModel<string[]>('tasks', { required: true })
const statuses = defineModel<string[]>('statuses', { required: true })
const presets = Object.entries(labels.history.ranges) as [RangePreset, string][]
</script>

<template>
  <v-card class="pa-4">
    <div class="d-flex flex-wrap align-center ga-4">
      <v-icon :icon="mdiFilterVariant" color="primary" />
      <v-chip-group v-model="preset" mandatory selected-class="bg-primary">
        <v-chip v-for="[value, title] in presets" :key="value" :value="value" variant="outlined">{{ title }}</v-chip>
      </v-chip-group>
      <v-expand-x-transition>
        <v-date-input
          v-if="preset === 'custom'"
          v-model="custom"
          multiple="range"
          :label="labels.history.dates"
          :prepend-icon="''"
          :prepend-inner-icon="mdiCalendarRange"
          hide-details
          max-width="320"
        />
      </v-expand-x-transition>
    </div>
    <v-divider class="my-3" />
    <div class="d-flex flex-wrap align-center ga-6">
      <div class="d-flex align-center ga-2">
        <span class="text-caption text-medium-emphasis">{{ labels.history.tasksFilter }}</span>
        <v-chip-group v-model="tasks" multiple column selected-class="text-primary">
          <v-chip v-for="task in allTasks" :key="task" :value="task" filter>{{ task.slice(0, 2) }} · {{ task.slice(3) }}</v-chip>
        </v-chip-group>
      </div>
      <div class="d-flex align-center ga-2">
        <span class="text-caption text-medium-emphasis">{{ labels.history.statusFilter }}</span>
        <v-chip-group v-model="statuses" multiple column selected-class="text-primary">
          <v-chip v-for="status in allStatuses" :key="status" :value="status" filter>{{ status }}</v-chip>
        </v-chip-group>
      </div>
    </div>
  </v-card>
</template>
