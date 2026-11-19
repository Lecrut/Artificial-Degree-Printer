<script setup lang="ts">
import { mdiFingerprint, mdiPackageVariantClosed } from '@mdi/js'
import type { Hypergraph } from '#shared/types/hypergraph'
import { vertexLabel } from '#shared/utils/graph'
import { roleColor } from '#shared/utils/roles'
import { vertexStateColor } from '#shared/utils/states'
import { labels } from '~/utils/labels'

const props = defineProps<{ hypergraph: Hypergraph, id: string, states: Record<string, string> }>()
const edge = computed(() => props.hypergraph.edges[props.id]!)
const spec = computed(() => edge.value.spec as {
  symbols?: Record<string, { kind: string, params?: string[] }>
  uses?: Record<string, string[]>
  packages?: string[]
  behaviour?: string[]
})
</script>

<template>
  <div class="d-flex flex-column ga-4">
    <v-table density="compact" class="bg-transparent">
      <tbody>
        <tr v-for="(role, member) in edge.members" :key="member">
          <td><v-chip :color="roleColor(role)" size="x-small" variant="flat">{{ role }} · {{ labels.graph.roleNames[role] }}</v-chip></td>
          <td class="text-body-2" :title="String(member)">{{ vertexLabel(String(member)) }}</td>
          <td><v-chip :color="vertexStateColor(states[String(member)] ?? 'spec')" size="x-small">{{ states[String(member)] ?? '—' }}</v-chip></td>
          <td><v-chip v-if="edge.observed.includes(String(member))" color="warning" size="x-small" variant="outlined">{{ labels.graph.observed }}</v-chip></td>
        </tr>
      </tbody>
    </v-table>
    <div v-if="spec.symbols">
      <div class="text-overline text-primary">{{ labels.graph.symbols }}</div>
      <div class="d-flex flex-wrap ga-1">
        <v-chip v-for="(symbol, name) in spec.symbols" :key="name" :title="symbol.params?.join(', ')" variant="outlined" color="primary">
          <span class="text-caption text-medium-emphasis me-1">{{ symbol.kind }}</span>{{ name }}
        </v-chip>
      </div>
    </div>
    <div v-if="spec.uses && Object.keys(spec.uses).length">
      <div class="text-overline text-primary">{{ labels.graph.uses }}</div>
      <div v-for="(names, module) in spec.uses" :key="module" class="d-flex flex-wrap align-center ga-1 mb-1">
        <span class="text-body-2 font-weight-medium me-1">{{ module }}:</span>
        <v-chip v-for="name in names" :key="name" size="x-small" color="secondary">{{ name }}</v-chip>
      </div>
    </div>
    <div v-if="spec.packages?.length" class="d-flex flex-wrap ga-1">
      <v-chip v-for="pkg in spec.packages" :key="pkg" :prepend-icon="mdiPackageVariantClosed" size="x-small">{{ pkg }}</v-chip>
    </div>
    <div v-if="spec.behaviour?.length">
      <div class="text-overline text-primary">{{ labels.graph.behaviour }}</div>
      <v-sheet v-for="(example, i) in spec.behaviour" :key="i" color="surface-bright" class="pa-3 mb-2">
        <pre class="text-pre-wrap text-body-2 ma-0">{{ example }}</pre>
      </v-sheet>
    </div>
    <v-chip v-if="edge.fingerprint" :prepend-icon="mdiFingerprint" class="align-self-start" :title="edge.fingerprint">{{ edge.fingerprint.slice(0, 16) }}…</v-chip>
  </div>
</template>
