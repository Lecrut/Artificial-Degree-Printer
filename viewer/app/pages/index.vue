<script setup lang="ts">
import { mdiHistory } from '@mdi/js'
import { labels } from '~/utils/labels'

const { commits, current } = useHistory()
const { byCommit, info } = useChangelog()
const dashboard = useHistoryDashboard(() => commits.data.value)
const { preset, custom, tasks, statuses, filtered, kpis, trendTask, trendMetric, points, allTasks, allStatuses } = dashboard
</script>

<template>
  <div class="d-flex flex-column ga-6">
    <CommonPageHeader :icon="mdiHistory" :title="labels.history.title" :subtitle="labels.history.subtitle" />
    <CommonPageSkeleton v-if="commits.pending.value" :tiles="5" />
    <CommonLoadError v-else-if="commits.error.value" @retry="commits.refresh()" />
    <template v-else>
      <HistoryKpiTiles :kpis="kpis" />
      <HistoryFilters
        v-model:preset="preset"
        v-model:custom="custom"
        v-model:tasks="tasks"
        v-model:statuses="statuses"
        :all-tasks="allTasks"
        :all-statuses="allStatuses"
      />
      <v-row>
        <v-col cols="12" xl="8">
          <HistoryTrendCard v-model:task="trendTask" v-model:metric="trendMetric" :points="points" :tasks="allTasks" />
        </v-col>
        <v-col cols="12" xl="4">
          <HistoryRunList
            v-if="current.data.value.length"
            :title="labels.history.current"
            :subtitle="labels.history.currentHint"
            source="results"
            at="current"
            :tasks="current.data.value"
          />
        </v-col>
      </v-row>
      <div class="d-flex align-center ga-3">
        <div class="text-h6">{{ labels.history.commits }}</div>
        <v-chip color="primary">{{ filtered.length }}</v-chip>
      </div>
      <v-alert v-if="!filtered.length" type="info" variant="tonal" :text="labels.history.empty" />
      <v-row>
        <v-fade-transition group>
          <v-col v-for="commit in filtered" :key="commit.sha" cols="12" md="6" xl="4">
            <!-- Cards render as they scroll into view: twenty at once froze the page for a third of a second. -->
            <v-lazy min-height="320" :options="{ rootMargin: '400px' }" transition="fade-transition">
              <HistoryCommitCard :commit="commit" :info="info(commit.sha)" :audit="byCommit.get(commit.sha) ?? []" />
            </v-lazy>
          </v-col>
        </v-fade-transition>
      </v-row>
    </template>
  </div>
</template>
