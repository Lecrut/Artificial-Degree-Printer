<script setup lang="ts">
import { mdiPlay, mdiSelectAll, mdiStop } from '@mdi/js'
import type { LaunchRequest } from '#shared/types/live'
import { LAUNCH_TASKS } from '#shared/utils/launch'
import { labels } from '~/utils/labels'

defineProps<{ running: boolean }>()
const request = defineModel<LaunchRequest>({ required: true })
const emit = defineEmits<{ start: [], stop: [] }>()

const tasks = Object.entries(labels.launch.tasks).map(([value, title]) => ({ value, title }))
const providers = Object.entries(labels.launch.providers).map(([value, title]) => ({ value, title }))
const templates = [{ value: null, title: labels.launch.autoTemplate }, { value: 'thesis_plodz', title: 'thesis_plodz' }, { value: 'paper_ieee', title: 'paper_ieee' }]
const allSelected = computed(() => request.value.tasks.length === LAUNCH_TASKS.length)
</script>

<template>
  <div class="d-flex flex-column ga-3">
    <div class="d-flex align-center ga-2">
      <span class="text-overline text-primary me-auto">{{ labels.launch.task }}</span>
      <v-btn :prepend-icon="mdiSelectAll" :variant="allSelected ? 'flat' : 'tonal'" color="primary" size="small" :disabled="running" @click="request.tasks = [...LAUNCH_TASKS]">
        {{ labels.launch.allTasks }}
      </v-btn>
    </div>
    <v-chip-group v-model="request.tasks" multiple filter column color="primary" :disabled="running">
      <v-chip v-for="task in tasks" :key="task.value" :value="task.value" :text="task.title" />
    </v-chip-group>
    <div class="d-flex ga-3">
      <v-select v-model="request.provider" :items="providers" :label="labels.launch.provider" :disabled="running" hide-details />
      <v-select v-model="request.template" :items="templates" :label="labels.launch.template" :disabled="running" hide-details />
    </div>
    <v-btn v-if="!running" :prepend-icon="mdiPlay" color="primary" variant="flat" size="large" block :disabled="!request.tasks.length" @click="emit('start')">{{ labels.launch.start }}</v-btn>
    <v-btn v-else :prepend-icon="mdiStop" color="error" variant="flat" size="large" block @click="emit('stop')">{{ labels.launch.stop }}</v-btn>
  </div>
</template>
