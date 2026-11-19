<script setup lang="ts">
import type { SourceKind, TaskSummary } from '#shared/types/run'
import { runPage } from '~/utils/runUrls'

const props = defineProps<{ title: string, subtitle: string, source: SourceKind, at: string, tasks: TaskSummary[] }>()

const link = (task: string) => runPage({ source: props.source, ref: props.at, task })
</script>

<template>
  <CommonHoverCard>
    <v-card-item :title="title" :subtitle="subtitle" />
    <v-list density="compact" class="py-0">
      <HistoryTaskStatusRow v-for="summary in tasks" :key="summary.task" :summary="summary" :to="link(summary.task)" />
    </v-list>
  </CommonHoverCard>
</template>
