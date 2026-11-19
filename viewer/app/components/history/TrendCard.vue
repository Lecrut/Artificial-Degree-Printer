<script setup lang="ts">
import { mdiChartLine } from '@mdi/js'
import type { TrendMetric, TrendPoint } from '#shared/utils/historyStats'
import { labels } from '~/utils/labels'
import { runPage } from '~/utils/runUrls'
import { trendLine } from '~/utils/trendChart'

const props = defineProps<{ points: TrendPoint[], tasks: string[] }>()
const task = defineModel<string>('task', { required: true })
const metric = defineModel<TrendMetric>('metric', { required: true })

const ink = useChartInk()
const metrics = Object.entries(labels.history.metrics).map(([value, title]) => ({ value, title }))
const last = computed(() => props.points.at(-1)?.value ?? null)
const format = (v: number) => (Number.isInteger(v) ? v.toLocaleString('pl-PL') : v.toFixed(1))
const option = computed(() => trendLine(ink.value, props.points, labels.history.metrics[metric.value], format, labels.history.trendClick))

// A click on a point opens that commit's run of the task.
function open(index: number) {
  const point = props.points[index]
  if (point) void navigateTo(runPage({ source: 'git', ref: point.short, task: task.value }))
}
</script>

<template>
  <v-card>
    <v-card-item :title="labels.history.trend" :prepend-icon="mdiChartLine">
      <template #append>
        <div class="d-flex flex-wrap ga-3">
          <v-select v-model="task" :items="tasks" hide-details min-width="220" />
          <v-select v-model="metric" :items="metrics" hide-details min-width="220" />
        </div>
      </template>
    </v-card-item>
    <v-card-text>
      <div v-if="points.length > 1" class="d-flex align-end ga-6">
        <CommonChart :option="option" :height="220" class="flex-grow-1" @pick="open" />
        <div class="text-end">
          <CommonCountUp :value="last" :format="format" class="text-h3 font-weight-bold text-primary d-block" />
          <div class="text-caption text-medium-emphasis">{{ labels.history.latest }}</div>
        </div>
      </div>
      <div v-else class="text-medium-emphasis py-6">{{ labels.history.trendEmpty }}</div>
    </v-card-text>
  </v-card>
</template>
