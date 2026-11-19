<script setup lang="ts">
import { mdiArrowExpand, mdiCursorDefaultClickOutline } from '@mdi/js'
import type { Hypergraph } from '#shared/types/hypergraph'
import { labels } from '~/utils/labels'

const props = defineProps<{ hypergraph: Hypergraph, selected: string | null, states: Record<string, string> }>()
const emit = defineEmits<{ expand: [] }>()
const { isVertex, id, known, state, color, subtitle } = useGraphElement(() => props.hypergraph, () => props.selected, () => props.states)
</script>

<template>
  <v-card height="100%">
    <v-empty-state v-if="!selected || !known" :icon="mdiCursorDefaultClickOutline" :title="labels.graph.details" :text="labels.graph.pick" size="64" />
    <template v-else>
      <v-card-item :title="id" :subtitle="subtitle">
        <template #append>
          <v-chip v-if="isVertex" :color="color" variant="flat" class="me-2">{{ state }}</v-chip>
          <v-btn :icon="mdiArrowExpand" :title="labels.graph.full" color="primary" variant="tonal" size="small" @click="emit('expand')" />
        </template>
      </v-card-item>
      <v-divider />
      <v-card-text class="overflow-y-auto">
        <GraphElementBody :hypergraph="hypergraph" :selected="selected" :states="states" />
      </v-card-text>
    </template>
  </v-card>
</template>
