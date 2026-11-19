<script setup lang="ts">
import { mdiChartTimelineVariant, mdiConsoleLine, mdiGraphOutline, mdiPlayCircleOutline, mdiPulse, mdiRobotOutline } from '@mdi/js'
import { labels } from '~/utils/labels'

const { task, events, hypergraph, queue, connected, loaded, failed, reconnect, summary, at } = useLiveRun()
const running = computed(() => summary.value?.status === 'RUNNING')
const tab = ref('timeline')
// The launch panel opens from the header, the empty state, or `?console=1` (the old /launch address).
const panel = ref(useRoute().query.console === '1')
</script>

<template>
  <div class="d-flex flex-column ga-6">
    <CommonPageHeader :icon="mdiPulse" :title="labels.live.title" :subtitle="labels.live.subtitle">
      <template #actions>
        <v-btn :prepend-icon="mdiConsoleLine" :color="panel ? 'primary' : undefined" :variant="panel ? 'flat' : 'tonal'" :text="labels.launch.open" @click="panel = !panel" />
      </template>
    </CommonPageHeader>
    <LaunchPanel v-model="panel" />
    <CommonLoadError v-if="!loaded && failed" :message="labels.common.reconnecting" @retry="reconnect()" />
    <CommonPageSkeleton v-else-if="!loaded" :tiles="7" />
    <v-empty-state
      v-else-if="!task || !summary || !at"
      :icon="mdiPlayCircleOutline"
      :title="labels.live.emptyTitle"
      :text="labels.live.emptyText"
    >
      <template #actions>
        <v-btn color="primary" variant="flat" :prepend-icon="mdiConsoleLine" :text="labels.launch.open" @click="panel = true" />
      </template>
    </v-empty-state>
    <template v-else>
      <div class="d-flex align-center ga-3">
        <v-chip :color="connected ? 'success' : 'error'" variant="flat">{{ connected ? labels.live.connected : labels.live.disconnected }}</v-chip>
        <v-progress-circular v-if="running" indeterminate color="primary" size="20" width="2" />
      </div>
      <RunHeader :summary="summary" :at="at" />
      <v-row>
        <v-col cols="12" lg="4"><LiveNowCard :events="events" :running="running" /></v-col>
        <v-col cols="12" lg="8"><LiveTaskBoard :queue="queue" :events="events" /></v-col>
      </v-row>
      <v-tabs v-model="tab" color="primary">
        <v-tab value="timeline" :prepend-icon="mdiChartTimelineVariant" :text="labels.tabs.timeline" />
        <v-tab value="graph" :prepend-icon="mdiGraphOutline" :text="labels.tabs.graph" :disabled="!hypergraph" />
        <v-tab value="agents" :prepend-icon="mdiRobotOutline" :text="labels.tabs.agents" />
      </v-tabs>
      <v-tabs-window v-model="tab">
        <v-tabs-window-item value="timeline"><TimelineRunTimeline :events="events" :at="at" @show-calls="tab = 'agents'" /></v-tabs-window-item>
        <v-tabs-window-item value="graph">
          <GraphHypergraphPanel v-if="hypergraph" :hypergraph="hypergraph" :events="events" :active="tab === 'graph'" />
        </v-tabs-window-item>
        <v-tabs-window-item value="agents"><AgentsPanel :at="at" /></v-tabs-window-item>
      </v-tabs-window>
    </template>
  </div>
</template>
