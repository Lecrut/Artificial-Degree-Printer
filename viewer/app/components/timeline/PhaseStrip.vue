<script setup lang="ts">
import type { PhaseId, PhaseSummary } from '#shared/types/timeline'
import { entryStatusColor } from '#shared/utils/colors'
import { labels } from '~/utils/labels'

defineProps<{ phases: PhaseSummary[] }>()
const selected = defineModel<PhaseId | null>({ default: null })

function toggle(id: PhaseId) {
  selected.value = selected.value === id ? null : id
}
</script>

<template>
  <v-timeline direction="horizontal" align="start" line-inset="8" class="overflow-x-auto">
    <v-timeline-item
      v-for="phase in phases"
      :key="phase.id"
      :dot-color="phase.entries ? entryStatusColor(phase.status) : 'grey-darken-2'"
      size="small"
    >
      <v-btn
        :variant="selected === phase.id ? 'tonal' : 'text'"
        :disabled="!phase.entries"
        size="small"
        @click="toggle(phase.id)"
      >
        {{ labels.phases[phase.id] }} · {{ phase.entries }}
      </v-btn>
    </v-timeline-item>
  </v-timeline>
</template>
