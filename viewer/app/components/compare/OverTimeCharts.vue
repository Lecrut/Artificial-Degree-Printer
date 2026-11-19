<script setup lang="ts">
import { mdiChartBellCurveCumulative, mdiCheckAll, mdiCounter, mdiMessageTextOutline, mdiTimerOutline } from '@mdi/js'
import type { ComparedRun, RunProfile } from '#shared/types/compare'
import { lineOverlay } from '~/utils/chartOptions'
import { labels } from '~/utils/labels'

const props = defineProps<{ runs: ComparedRun[] }>()
const ink = useChartInk()

type Measure = keyof RunProfile['over']
const integer = (v: number) => Math.round(v).toLocaleString('pl-PL')
const CHARTS: { measure: Measure, icon: string, format: (v: number) => string }[] = [
  { measure: 'tasksDone', icon: mdiCheckAll, format: integer },
  { measure: 'calls', icon: mdiMessageTextOutline, format: integer },
  { measure: 'llmMinutes', icon: mdiTimerOutline, format: v => v.toFixed(v < 10 ? 1 : 0) },
  { measure: 'promptTokens', icon: mdiCounter, format: v => (v >= 1000 ? `${Math.round(v / 1000)}k` : integer(v)) },
]

// The same four running totals for every run, overlaid on one time axis per measure.
const charts = computed(() => CHARTS.map(chart => ({
  ...chart,
  title: labels.compare.charts[chart.measure],
  // Prompt sizes are logged since 2026-11-18; an older run has no line here rather than a false zero.
  option: lineOverlay(
    ink.value,
    props.runs.filter(r => chart.measure !== 'promptTokens' || r.profile.promptChars > 0)
      .map(r => ({ name: r.label, color: r.color, points: r.profile.over[chart.measure] })),
    labels.compare.minutes,
    chart.format,
  ),
})))
</script>

<template>
  <div class="d-flex flex-column ga-3">
    <div class="d-flex align-center ga-3">
      <v-icon :icon="mdiChartBellCurveCumulative" color="primary" />
      <div>
        <div class="text-h6">{{ labels.compare.overTime }}</div>
        <div class="text-caption text-medium-emphasis">{{ labels.compare.overTimeHint }}</div>
      </div>
    </div>
    <v-row>
      <v-col v-for="chart in charts" :key="chart.measure" cols="12" lg="6">
        <v-card>
          <v-card-item :title="chart.title" :prepend-icon="chart.icon" />
          <v-card-text><CommonChart :option="chart.option" /></v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>
