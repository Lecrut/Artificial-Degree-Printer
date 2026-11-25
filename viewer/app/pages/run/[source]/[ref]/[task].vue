<script setup lang="ts">
import { mdiChartTimelineVariant, mdiFileDocumentOutline, mdiGraphOutline, mdiRobotOutline } from '@mdi/js'
import type { RunRef, SourceKind } from '#shared/types/run'
import { labels } from '~/utils/labels'

const route = useRoute()
const at = computed<RunRef>(() => ({
  source: String(route.params.source) as SourceKind,
  ref: String(route.params.ref),
  task: String(route.params.task),
}))
const { data: bundle, pending, error, refresh } = useRunBundle(at)
const tab = ref('timeline')
const focusTask = ref<string | null>(null)

function showCalls(taskId: string) {
  focusTask.value = taskId
  tab.value = 'agents'
}
</script>

<template>
  <div class="d-flex flex-column ga-4">
    <CommonPageSkeleton v-if="pending" :tiles="7" />
    <CommonLoadError v-else-if="error || !bundle" :message="labels.run.notFound" @retry="refresh()" />
    <template v-else>
      <RunHeader :summary="bundle.summary" :at="at" />
      <v-tabs v-model="tab" color="primary">
        <v-tab value="timeline" :prepend-icon="mdiChartTimelineVariant" :text="labels.tabs.timeline" />
        <v-tab value="graph" :prepend-icon="mdiGraphOutline" :text="labels.tabs.graph" />
        <v-tab value="agents" :prepend-icon="mdiRobotOutline" :text="labels.tabs.agents" />
        <v-tab value="thesis" :prepend-icon="mdiFileDocumentOutline" :text="labels.tabs.thesis" />
      </v-tabs>
      <v-tabs-window v-model="tab">
        <v-tabs-window-item value="timeline">
          <TimelineRunTimeline :events="bundle.events" :at="at" @show-calls="showCalls" />
        </v-tabs-window-item>
        <v-tabs-window-item value="graph">
          <GraphHypergraphPanel v-if="bundle.hypergraph" :hypergraph="bundle.hypergraph" :events="bundle.events" :active="tab === 'graph'" :at="at" />
          <v-alert v-else type="info" variant="tonal" :text="labels.run.noGraph" />
        </v-tabs-window-item>
        <v-tabs-window-item value="agents">
          <AgentsPanel :at="at" :focus-task="focusTask" />
        </v-tabs-window-item>
        <v-tabs-window-item value="thesis">
          <ThesisPanel :at="at" :files="bundle.files" />
        </v-tabs-window-item>
      </v-tabs-window>
    </template>
  </div>
</template>
