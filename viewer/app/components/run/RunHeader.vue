<script setup lang="ts">
import {
  mdiAlertOctagonOutline, mdiCancel, mdiCheckAll, mdiClockOutline, mdiCompareHorizontal, mdiFileTreeOutline, mdiMessageTextOutline, mdiRefresh,
} from '@mdi/js'
import type { RunRef, TaskSummary } from '#shared/types/run'
import { runKey } from '#shared/utils/compare'
import { formatDate, formatDuration } from '#shared/utils/format'
import { runStatusColor } from '#shared/utils/states'
import { labels } from '~/utils/labels'

const props = defineProps<{ summary: TaskSummary, at: RunRef }>()

const stats = computed(() => [
  { icon: mdiClockOutline, label: labels.stats.duration, value: props.summary.durationSeconds, format: formatDuration, color: 'warning' },
  { icon: mdiCheckAll, label: labels.stats.tasks, value: props.summary.tasksDone, format: (n: number) => `${Math.round(n)}/${props.summary.tasksTotal}`, color: 'success' },
  { icon: mdiMessageTextOutline, label: labels.stats.llmCalls, value: props.summary.llmCalls, color: 'primary' },
  { icon: mdiFileTreeOutline, label: labels.stats.planVersions, value: props.summary.planVersions, color: 'secondary' },
  { icon: mdiAlertOctagonOutline, label: labels.stats.failedVerdicts, value: props.summary.failedVerdicts, color: 'error' },
  { icon: mdiCancel, label: labels.stats.rejectedWrites, value: props.summary.rejectedWrites, color: 'error' },
  { icon: mdiRefresh, label: labels.stats.replans, value: props.summary.replans, color: 'info' },
])
const crumbs = computed(() => [
  { title: labels.tabs.history, to: '/' },
  { title: props.at.source === 'git' ? props.at.ref.slice(0, 7) : labels.sources[props.at.source], disabled: true },
  { title: props.summary.task, disabled: true },
])
</script>

<template>
  <div class="d-flex flex-column ga-3">
    <v-breadcrumbs :items="crumbs" density="compact" class="pa-0 text-medium-emphasis" />
    <v-card class="pa-2">
      <div class="d-flex flex-wrap align-center ga-4 pa-4">
        <v-avatar :color="runStatusColor(summary.status)" variant="tonal" rounded="xl" size="56">
          <span class="text-h6 font-weight-bold">{{ summary.task.slice(0, 2) }}</span>
        </v-avatar>
        <div class="flex-grow-1 text-break">
          <div class="text-h5 font-weight-bold">{{ summary.task }}</div>
          <div class="text-body-2 text-medium-emphasis">{{ summary.title ?? '' }}</div>
        </div>
        <div class="d-flex flex-column align-start align-sm-end ga-1">
          <CommonStatusChip :status="summary.status" />
          <span class="text-caption text-medium-emphasis">{{ formatDate(summary.started) }}</span>
          <v-btn :to="{ path: '/compare', query: { runs: runKey(at) } }" :prepend-icon="mdiCompareHorizontal" color="primary" variant="tonal" size="small" class="mt-1" :text="labels.nav.compareThis" />
          <LaunchResumeButton :at="at" />
        </div>
      </div>
      <v-card-text>
        <v-row density="compact">
          <v-col v-for="stat in stats" :key="stat.label" cols="6" sm="4" md>
            <v-sheet color="surface-bright" rounded="xl" class="pa-3 d-flex align-center ga-3 fill-height">
              <v-icon :icon="stat.icon" :color="stat.color" />
              <div>
                <CommonCountUp :value="stat.value" :format="stat.format" class="text-h6 font-weight-bold d-block" />
                <div class="text-caption text-medium-emphasis">{{ stat.label }}</div>
              </div>
            </v-sheet>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </div>
</template>
