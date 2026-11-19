<script setup lang="ts">
import { mdiCompareHorizontal } from '@mdi/js'
import { labels } from '~/utils/labels'

const { keys, options, optionsLoading, runs, pending, error, refresh, sameTask } = useCompare()
const { commits } = useHistory()
// Old runs have no events: they appear in the table, not on the charts drawn from events.
const drawable = computed(() => runs.value.filter(r => r.hasEvents))
const withoutEvents = computed(() => runs.value.filter(r => !r.hasEvents).map(r => r.label).join(', '))
const tasks = computed(() => [...new Set(commits.data.value.flatMap(c => c.tasks.map(t => t.task)))].sort())
</script>

<template>
  <div class="d-flex flex-column ga-6">
    <CommonPageHeader :icon="mdiCompareHorizontal" :title="labels.compare.title" :subtitle="labels.compare.subtitle" />
    <CompareRunPicker v-model="keys" :options="options" :loading="optionsLoading" :runs="runs" :tasks="tasks" @same-task="sameTask" />
    <CommonLoadError v-if="error" @retry="refresh()" />
    <CommonPageSkeleton v-if="pending && !runs.length" :tiles="0" />
    <v-progress-linear v-else-if="pending" indeterminate color="primary" rounded />
    <v-alert v-else-if="!keys.length" type="info" variant="tonal" :text="labels.compare.empty" />
    <template v-else-if="runs.length">
      <v-alert v-if="withoutEvents" type="warning" variant="tonal" density="compact" :text="labels.compare.noEvents(withoutEvents)" />
      <CompareMetricTable :runs="runs" />
      <template v-if="drawable.length">
        <CompareOverTimeCharts :runs="drawable" />
        <v-row>
          <v-col cols="12" lg="8"><CompareAgentBars :runs="drawable" /></v-col>
          <v-col cols="12" lg="4"><CompareTierSplit :runs="drawable" /></v-col>
        </v-row>
      </template>
    </template>
  </div>
</template>
