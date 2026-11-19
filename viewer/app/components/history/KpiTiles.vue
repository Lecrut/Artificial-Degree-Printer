<script setup lang="ts">
import { mdiCheckDecagramOutline, mdiClockOutline, mdiMessageTextOutline, mdiPlaylistPlay, mdiSourceCommit } from '@mdi/js'
import type { HistoryKpis } from '#shared/utils/historyStats'
import { labels } from '~/utils/labels'

const props = defineProps<{ kpis: HistoryKpis }>()

const tiles = computed(() => [
  { icon: mdiSourceCommit, value: props.kpis.commits, label: labels.history.kpi.commits, color: 'secondary' },
  { icon: mdiPlaylistPlay, value: props.kpis.runs, label: labels.history.kpi.runs, color: 'info' },
  {
    icon: mdiCheckDecagramOutline,
    value: props.kpis.runs ? (100 * props.kpis.completed) / props.kpis.runs : null,
    format: (n: number) => `${Math.round(n)}%`,
    label: labels.history.kpi.completed(props.kpis.completed),
    color: 'success',
  },
  { icon: mdiMessageTextOutline, value: props.kpis.llmCalls, label: labels.history.kpi.llm, color: 'primary' },
  { icon: mdiClockOutline, value: props.kpis.hours, format: (n: number) => `${n.toFixed(1)} h`, label: labels.history.kpi.hours, color: 'warning' },
])
</script>

<template>
  <v-row>
    <v-col v-for="tile in tiles" :key="tile.label" cols="12" sm="6" md>
      <v-card class="pa-4 d-flex align-center ga-4" height="100%">
        <v-avatar :color="tile.color" variant="tonal" rounded="xl" size="48">
          <v-icon :icon="tile.icon" />
        </v-avatar>
        <div>
          <CommonCountUp :value="tile.value" :format="tile.format" class="text-h5 font-weight-bold d-block" />
          <div class="text-caption text-medium-emphasis">{{ tile.label }}</div>
        </div>
      </v-card>
    </v-col>
  </v-row>
</template>
