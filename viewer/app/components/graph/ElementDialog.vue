<script setup lang="ts">
import { mdiHexagonOutline, mdiRhombusOutline } from '@mdi/js'
import type { Hypergraph } from '#shared/types/hypergraph'
import { incidenceMatrix } from '#shared/utils/incidence'

const props = defineProps<{ hypergraph: Hypergraph, states: Record<string, string> }>()
const selected = defineModel<string | null>('selected', { required: true })
const open = defineModel<boolean>({ required: true })
const { isVertex, id, known, color, subtitle } = useGraphElement(() => props.hypergraph, selected, () => props.states)

// All elements in the order of the incidence map: vertices first, then bags.
const order = computed(() => {
  const m = incidenceMatrix(props.hypergraph)
  return [...m.rows.map(r => `v:${r.id}`), ...m.columns.map(c => `e:${c.id}`)]
})
const position = computed(() => order.value.indexOf(selected.value ?? ''))

function move(delta: number) {
  const next = order.value[position.value + delta]
  if (next) selected.value = next
}
</script>

<template>
  <CommonBrowseDialog
    v-model="open"
    :position="position"
    :total="order.length"
    :title="id"
    :subtitle="subtitle"
    :icon="isVertex ? mdiHexagonOutline : mdiRhombusOutline"
    :color="color"
    @move="move"
  >
    <GraphElementBody v-if="known" :hypergraph="hypergraph" :selected="selected!" :states="states" />
  </CommonBrowseDialog>
</template>
