<script setup lang="ts">
import { mdiRobotOutline } from '@mdi/js'
import type { ComparedRun } from '#shared/types/compare'
import { groupedBars } from '~/utils/chartOptions'
import { labels } from '~/utils/labels'

const props = defineProps<{ runs: ComparedRun[] }>()
const ink = useChartInk()
const measure = ref<'calls' | 'seconds'>('calls')

// Agents ordered by what they spent across all runs, the busiest on top.
const agents = computed(() => {
  const total = new Map<string, number>()
  for (const run of props.runs) for (const [agent, s] of Object.entries(run.profile.agents)) total.set(agent, (total.get(agent) ?? 0) + s[measure.value])
  return [...total.entries()].sort((a, b) => b[1] - a[1]).map(([agent]) => agent)
})
const option = computed(() => groupedBars(
  ink.value,
  agents.value,
  props.runs.map(r => ({ name: r.label, color: r.color, values: agents.value.map(a => r.profile.agents[a]?.[measure.value] ?? 0) })),
  v => Math.round(v).toLocaleString('pl-PL'),
))
const height = computed(() => Math.max(240, 56 + agents.value.length * (14 * props.runs.length + 18)))
</script>

<template>
  <v-card height="100%">
    <v-card-item :title="labels.compare.agents" :subtitle="labels.compare.agentsHint" :prepend-icon="mdiRobotOutline">
      <template #append>
        <v-btn-toggle v-model="measure" mandatory color="primary" variant="outlined" density="compact" divided>
          <v-btn value="calls" :text="labels.compare.agentCalls" />
          <v-btn value="seconds" :text="labels.compare.agentSeconds" />
        </v-btn-toggle>
      </template>
    </v-card-item>
    <v-card-text><CommonChart :option="option" :height="height" /></v-card-text>
  </v-card>
</template>
