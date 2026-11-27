<script setup lang="ts">
import { mdiGraphOutline, mdiTableLarge } from '@mdi/js'
import { useDisplay } from 'vuetify'
import type { Hypergraph } from '#shared/types/hypergraph'
import type { RunEvent, RunRef } from '#shared/types/run'
import { snapshotAt } from '#shared/utils/snapshots'
import { labels } from '~/utils/labels'

const props = withDefaults(defineProps<{ hypergraph: Hypergraph, events: RunEvent[], active?: boolean, at?: RunRef | null }>(), { active: true, at: null })
const { elements, position, max, current, playing, play, stop } = useHypergraphReplay(() => props.hypergraph, () => props.events)
const selected = ref<string | null>(null)
// A phone is too narrow for the graph; the matrix scrolls instead.
const view = ref<'graph' | 'matrix'>(useDisplay().smAndDown.value ? 'matrix' : 'graph')
const files = ref(false)
const order = ref(false)
const dialog = ref(false)
// The last snapshot saved by the replayed moment: resuming from it brings the run back to what the graph shows.
const snapshot = computed(() => snapshotAt(props.events, current.value?.ts ?? null))
// ← → step the replay while this tab is shown.
useArrowKeys(() => props.active && !dialog.value, { left: () => { position.value = Math.max(0, position.value - 1) }, right: () => { position.value = Math.min(max.value, position.value + 1) } })
const states = computed(() => Object.fromEntries(elements.value.nodes.filter(n => n.group === 'vertex').map(n => [n.id.slice(2), n.state])))
</script>

<template>
  <div class="d-flex flex-column ga-4">
    <v-card class="pa-4 d-flex flex-column ga-4">
      <GraphReplayControls v-model="position" :max="max" :playing="playing" :current="current" @play="play" @stop="stop" />
      <div class="d-flex flex-wrap align-center ga-4">
        <v-btn-toggle v-model="view" mandatory color="primary" variant="outlined" density="comfortable" divided>
          <v-btn value="graph" :prepend-icon="mdiGraphOutline" :text="labels.graph.viewGraph" />
          <v-btn value="matrix" :prepend-icon="mdiTableLarge" :text="labels.graph.viewMatrix" />
        </v-btn-toggle>
        <v-switch v-if="view === 'graph'" v-model="files" :label="labels.graph.files" color="primary" density="compact" hide-details />
        <v-switch v-if="view === 'graph'" v-model="order" :label="labels.graph.order" color="primary" density="compact" hide-details />
        <GraphLegend />
        <LaunchResumeButton v-if="at" :at="at" :snapshot="snapshot" here />
      </div>
    </v-card>
    <v-row>
      <v-col cols="12" lg="8">
        <v-fade-transition mode="out-in">
          <GraphHypergraphCanvas v-if="view === 'graph'" v-model="selected" :elements="elements" :files="files" :order="order" />
          <GraphIncidenceMatrix v-else v-model="selected" :hypergraph="hypergraph" :states="states" />
        </v-fade-transition>
      </v-col>
      <v-col cols="12" lg="4">
        <GraphElementDetails :hypergraph="hypergraph" :selected="selected" :states="states" @expand="dialog = true" />
      </v-col>
    </v-row>
    <GraphElementDialog v-model="dialog" v-model:selected="selected" :hypergraph="hypergraph" :states="states" />
  </div>
</template>
