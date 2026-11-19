<script setup lang="ts">
import { mdiArrowDownBold, mdiArrowUpBold, mdiTableLarge } from '@mdi/js'
import type { ComparedRun } from '#shared/types/compare'
import { delta, METRIC_ROWS, metricValue } from '~/utils/compareMetrics'
import { labels } from '~/utils/labels'
import { runPage } from '~/utils/runUrls'

const props = defineProps<{ runs: ComparedRun[] }>()

// One row per measure, one cell per run: its value and, after the first run, the change against it.
const table = computed(() => METRIC_ROWS.map(row => ({
  label: row.label,
  cells: props.runs.map((run, i) => {
    const value = metricValue(row, run)
    return { text: value === null ? '—' : row.format(value), change: i > 0 ? delta(row, props.runs[0]!, run) : null }
  }),
})))
</script>

<template>
  <v-card>
    <v-card-item :title="labels.compare.metrics" :subtitle="labels.compare.metricsHint" :prepend-icon="mdiTableLarge" />
    <v-table hover density="comfortable" class="bg-transparent">
      <thead>
        <tr>
          <th>{{ labels.compare.metric }}</th>
          <th v-for="run in runs" :key="run.label" class="text-end">
            <v-chip :to="runPage(run.at)" :color="run.color" variant="flat" size="small">{{ run.label }}</v-chip>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in table" :key="row.label">
          <td class="text-medium-emphasis">{{ row.label }}</td>
          <td v-for="(cell, i) in row.cells" :key="i" class="text-end text-no-wrap">
            <span class="font-weight-medium">{{ cell.text }}</span>
            <v-chip
              v-if="cell.change"
              :color="cell.change.good ? 'success' : 'error'"
              :prepend-icon="cell.change.text.startsWith('+') ? mdiArrowUpBold : mdiArrowDownBold"
              size="x-small"
              class="ms-2"
            >
              {{ cell.change.text }}
            </v-chip>
          </td>
        </tr>
      </tbody>
    </v-table>
    <v-card-text class="text-caption text-medium-emphasis">{{ labels.compare.costNote }}</v-card-text>
  </v-card>
</template>
