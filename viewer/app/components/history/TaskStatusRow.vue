<script setup lang="ts">
import { mdiCheckAll, mdiClockOutline, mdiMessageTextOutline } from '@mdi/js'
import type { TaskSummary } from '#shared/types/run'
import { formatDuration } from '#shared/utils/format'
import { labels } from '~/utils/labels'

defineProps<{ summary: TaskSummary, to: string }>()
</script>

<template>
  <v-list-item :to="to" :title="summary.task" :subtitle="summary.title ?? ''" class="py-2">
    <div class="d-flex flex-wrap align-center ga-1 mt-2">
      <CommonStatusChip :status="summary.status" />
      <v-chip :title="labels.stats.tasks" :prepend-icon="mdiCheckAll">{{ summary.tasksDone }}/{{ summary.tasksTotal }}</v-chip>
      <v-chip :title="labels.stats.llmCalls" :prepend-icon="mdiMessageTextOutline">{{ summary.llmCalls }}</v-chip>
      <v-chip :title="labels.stats.duration" :prepend-icon="mdiClockOutline">{{ formatDuration(summary.durationSeconds) }}</v-chip>
    </div>
  </v-list-item>
</template>
