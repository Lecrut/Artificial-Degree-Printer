<script setup lang="ts">
import { mdiCheckCircleOutline, mdiChip, mdiCloseCircleOutline, mdiRobotOutline } from '@mdi/js'
import type { AgentCallSummary } from '#shared/types/calls'
import type { RunRef } from '#shared/types/run'
import { tierColor, verdictColor } from '#shared/utils/colors'
import { formatClock } from '#shared/utils/format'
import { labels } from '~/utils/labels'

defineProps<{ calls: AgentCallSummary[], loading: boolean, at: RunRef }>()
const emit = defineEmits<{ open: [step: number] }>()

const headers = [
  { title: '#', key: 'step', width: 64 },
  { title: labels.agents.time, key: 'ts', width: 96 },
  { title: labels.agents.agent, key: 'agent' },
  { title: labels.agents.model, key: 'tier', width: 110 },
  { title: labels.agents.task, key: 'taskId' },
  { title: labels.agents.seconds, key: 'elapsedMs', align: 'end' as const, width: 90 },
  { title: labels.agents.decision, key: 'decision', sortable: false },
]
</script>

<template>
  <v-data-table
    :headers="headers"
    :items="calls"
    :loading="loading"
    :items-per-page="25"
    item-value="step"
    show-expand
    expand-on-click
    class="bg-transparent"
  >
    <template #[`item.ts`]="{ value }">{{ formatClock(value) }}</template>
    <template #[`item.agent`]="{ item }">
      <v-chip :color="item.ok ? 'primary' : 'error'" :prepend-icon="mdiRobotOutline">{{ item.agent }}</v-chip>
    </template>
    <template #[`item.tier`]="{ item }">
      <v-chip :color="item.tier === 'LRM' ? tierColor(item.tier) : undefined" :title="item.model" :prepend-icon="mdiChip">{{ item.tier }}</v-chip>
    </template>
    <template #[`item.elapsedMs`]="{ value }">{{ value === null ? '—' : (value / 1000).toFixed(1) }}</template>
    <template #[`item.decision`]="{ item }">
      <v-sheet color="transparent" max-width="820" class="d-flex align-center ga-2 py-1">
        <v-chip
          v-if="item.verdict"
          :color="verdictColor(item.verdict)"
          :prepend-icon="item.verdict === 'PASS' ? mdiCheckCircleOutline : mdiCloseCircleOutline"
        >
          {{ item.verdict }}
        </v-chip>
        <span class="text-body-2 text-medium-emphasis text-truncate">{{ item.decision }}</span>
      </v-sheet>
    </template>
    <template #expanded-row="{ columns, item }">
      <tr>
        <td :colspan="columns.length">
          <AgentsCallPreview :at="at" :step="item.step" @open="step => emit('open', step)" />
        </td>
      </tr>
    </template>
  </v-data-table>
</template>
