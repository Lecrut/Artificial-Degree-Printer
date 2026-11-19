<script setup lang="ts">
import { mdiAccountEditOutline, mdiAlertOutline, mdiFileOutline, mdiRepeat } from '@mdi/js'
import type { Hypergraph } from '#shared/types/hypergraph'
import { bagLabel } from '#shared/utils/graph'
import { BAG_COLOR, roleColor } from '#shared/utils/roles'
import { labels } from '~/utils/labels'

const props = defineProps<{ hypergraph: Hypergraph, id: string }>()
const vertex = computed(() => props.hypergraph.vertices[props.id]!)
const bags = computed(() => Object.entries(props.hypergraph.edges).filter(([, e]) => props.id in e.members)
  .map(([edgeId, e]) => ({ id: edgeId, type: e.type, role: e.members[props.id]!, observed: e.observed.includes(props.id) })))
</script>

<template>
  <div class="d-flex flex-column ga-4">
    <div v-if="vertex.description" class="text-body-1">{{ vertex.description }}</div>
    <div class="d-flex flex-wrap ga-2">
      <v-chip :prepend-icon="mdiRepeat">{{ labels.graph.attempts }}: {{ vertex.attempts }}</v-chip>
      <v-chip v-if="vertex.failures" :prepend-icon="mdiAlertOutline" color="error">{{ labels.graph.failures }}: {{ vertex.failures }}</v-chip>
      <v-chip v-if="vertex.last_writer" :prepend-icon="mdiAccountEditOutline" color="secondary">{{ vertex.last_writer.agent }} · {{ vertex.last_writer.task_id }}</v-chip>
      <v-chip v-for="file in vertex.files" :key="file" :prepend-icon="mdiFileOutline" color="warning">{{ file }}</v-chip>
    </div>
    <div>
      <div class="text-overline text-primary">{{ labels.graph.memberOf }}</div>
      <div class="d-flex flex-wrap ga-2">
        <v-chip v-for="bag in bags" :key="bag.id" :color="BAG_COLOR[bag.type]" :variant="bag.observed ? 'outlined' : 'tonal'">
          <v-avatar start :color="roleColor(bag.role)" size="18"><span class="text-caption font-weight-bold">{{ bag.role }}</span></v-avatar>
          {{ bagLabel(bag.id) }}
        </v-chip>
      </div>
    </div>
    <div v-if="vertex.history.length">
      <div class="text-overline text-primary">{{ labels.graph.history }}</div>
      <v-timeline side="end" align="start" density="compact" truncate-line="both" line-color="surface-variant">
        <v-timeline-item v-for="(entry, i) in vertex.history" :key="i" dot-color="error" size="x-small">
          <v-sheet color="surface-bright" class="pa-3">
            <v-chip size="x-small" class="mb-2">{{ entry.task_id }}</v-chip>
            <v-sheet color="transparent" max-height="240" rounded="0" class="overflow-y-auto"><pre v-for="(issue, j) in entry.issues" :key="j" class="text-pre-wrap text-break text-caption text-medium-emphasis ma-0">{{ issue }}</pre></v-sheet>
          </v-sheet>
        </v-timeline-item>
      </v-timeline>
    </div>
  </div>
</template>
