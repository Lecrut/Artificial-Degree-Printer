<script setup lang="ts">
import type { RunEvent, RunRef } from '#shared/types/run'
import { entryStatusColor } from '#shared/utils/colors'
import { KIND_ICON } from '~/utils/icons'
import { labels } from '~/utils/labels'

const props = defineProps<{ events: RunEvent[], at: RunRef | null }>()
provideRunAt(() => props.at)
const emit = defineEmits<{ showCalls: [taskId: string] }>()
const { phases, filters, phase, entries } = useTimeline(() => props.events)
const opened = ref<number | null>(null)
</script>

<template>
  <div class="d-flex flex-column ga-4">
    <v-card class="pa-4 d-flex flex-column ga-4">
      <TimelinePhaseStrip v-model="phase" :phases="phases" />
      <TimelineFilters v-model="filters" />
    </v-card>
    <v-alert v-if="!entries.length" type="info" variant="tonal" :text="labels.timeline.empty" />
    <v-timeline v-else side="end" align="start" truncate-line="both" line-color="surface-variant">
      <v-slide-y-transition group>
        <v-timeline-item
          v-for="(entry, i) in entries"
          :key="entry.id"
          :dot-color="entryStatusColor(entry.status)"
          :icon="KIND_ICON[entry.kind]"
          size="small"
          fill-dot
        >
          <TimelineEntryCard :entry="entry" @show-calls="id => emit('showCalls', id)" @open="opened = i" />
        </v-timeline-item>
      </v-slide-y-transition>
    </v-timeline>
    <TimelineEntryDialog v-model="opened" :entries="entries" @show-calls="id => emit('showCalls', id)" />
  </div>
</template>
