<script setup lang="ts">
import type { Hypergraph } from '#shared/types/hypergraph'

// The details of the selected vertex or bag, fading from one element to the next.
defineProps<{ hypergraph: Hypergraph, selected: string, states: Record<string, string> }>()
</script>

<template>
  <v-fade-transition mode="out-in">
    <GraphVertexDetails v-if="selected.startsWith('v:')" :id="selected.slice(2)" :key="selected" :hypergraph="hypergraph" />
    <GraphBagDetails v-else :id="selected.slice(2)" :key="selected" :hypergraph="hypergraph" :states="states" />
  </v-fade-transition>
</template>
