<script setup lang="ts">
import { mdiGraphOutline, mdiTableLarge } from '@mdi/js'
import { useDisplay } from 'vuetify'
import type { Hypergraph } from '#shared/types/hypergraph'
import type { RunEvent } from '#shared/types/run'
import { labels } from '~/utils/labels'

const props = withDefaults(defineProps<{ hypergraph: Hypergraph, events: RunEvent[], active?: boolean }>(), { active: true })
const { elements, position, max, current, playing, play, stop } = useHypergraphReplay(() => props.hypergraph, () => props.events)
const selected = ref<string | null>(null)
// A phone is too narrow for the graph; the matrix scrolls instead.
const view = ref<'graph' | 'matrix'>(useDisplay().smAndDown.value ? 'matrix' : 'graph')
const dialog = ref(false)
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
        <GraphLegend />
      </div>
    </v-card>
    <v-row>
      <v-col cols="12" lg="8">
        <v-fade-transition mode="out-in">
          <GraphHypergraphCanvas v-if="view === 'graph'" v-model="selected" :elements="elements" />
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
