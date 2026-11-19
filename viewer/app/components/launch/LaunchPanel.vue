<script setup lang="ts">
import { mdiClose, mdiConsoleLine } from '@mdi/js'
import { useDisplay } from 'vuetify'
import { formatDate } from '#shared/utils/format'
import { labels } from '~/utils/labels'

// Start, stop and the console of a benchmark, in a side panel beside the live view: logs and progress at once.
const open = defineModel<boolean>({ required: true })
const { status, error, request, start, stop } = useLauncher()
const { smAndDown } = useDisplay()
const running = computed(() => status.value?.running ?? false)
</script>

<template>
  <v-navigation-drawer v-model="open" location="end" :width="smAndDown ? 360 : 520" :temporary="smAndDown" border="s" color="surface">
    <div class="d-flex flex-column ga-4 pa-4 fill-height">
      <div class="d-flex align-center ga-3">
        <v-avatar color="primary" variant="tonal" size="40"><v-icon :icon="mdiConsoleLine" /></v-avatar>
        <div class="flex-grow-1">
          <div class="text-subtitle-1 font-weight-bold">{{ labels.launch.panel }}</div>
          <div class="text-caption text-medium-emphasis">{{ labels.launch.hint }}</div>
        </div>
        <v-btn :icon="mdiClose" variant="text" size="small" @click="open = false" />
      </div>
      <v-alert v-if="error" type="error" variant="tonal" density="compact" closable :text="error" @click:close="error = null" />
      <LaunchForm v-model="request" :running="running" @start="start" @stop="stop" />
      <div class="d-flex flex-wrap align-center ga-2">
        <span class="text-overline text-primary me-auto">{{ labels.launch.console }}</span>
        <v-chip v-if="running" color="primary" variant="flat">{{ labels.launch.running }} · PID {{ status?.pid }}</v-chip>
        <v-chip v-else-if="status?.exitCode !== null && status?.exitCode !== undefined" :color="status.exitCode === 0 ? 'success' : 'error'" variant="flat">
          {{ labels.launch.exit(status.exitCode) }}
        </v-chip>
        <v-chip v-if="status?.startedAt">{{ formatDate(status.startedAt) }}</v-chip>
      </div>
      <LaunchConsoleTail :status="status" />
    </div>
  </v-navigation-drawer>
</template>
