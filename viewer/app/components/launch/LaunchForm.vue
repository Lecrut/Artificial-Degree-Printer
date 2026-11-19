<script setup lang="ts">
import { mdiPlay, mdiStop } from '@mdi/js'
import type { LaunchRequest } from '#shared/types/live'
import { labels } from '~/utils/labels'

defineProps<{ running: boolean }>()
const request = defineModel<LaunchRequest>({ required: true })
const emit = defineEmits<{ start: [], stop: [] }>()

const tasks = Object.entries(labels.launch.tasks).map(([value, title]) => ({ value, title }))
const providers = Object.entries(labels.launch.providers).map(([value, title]) => ({ value, title }))
const templates = [{ value: null, title: labels.launch.autoTemplate }, { value: 'thesis_plodz', title: 'thesis_plodz' }, { value: 'paper_ieee', title: 'paper_ieee' }]
</script>

<template>
  <div class="d-flex flex-column ga-3">
    <v-select v-model="request.task" :items="tasks" :label="labels.launch.task" :disabled="running" hide-details />
    <div class="d-flex ga-3">
      <v-select v-model="request.provider" :items="providers" :label="labels.launch.provider" :disabled="running" hide-details />
      <v-select v-model="request.template" :items="templates" :label="labels.launch.template" :disabled="running" hide-details />
    </div>
    <v-btn v-if="!running" :prepend-icon="mdiPlay" color="primary" variant="flat" size="large" block @click="emit('start')">{{ labels.launch.start }}</v-btn>
    <v-btn v-else :prepend-icon="mdiStop" color="error" variant="flat" size="large" block @click="emit('stop')">{{ labels.launch.stop }}</v-btn>
  </div>
</template>
