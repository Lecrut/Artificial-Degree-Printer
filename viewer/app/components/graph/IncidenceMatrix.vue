<script setup lang="ts">
import type { Hypergraph } from '#shared/types/hypergraph'
import { vertexLabel } from '#shared/utils/graph'
import { incidenceMatrix } from '#shared/utils/incidence'
import { BAG_COLOR, roleColor } from '#shared/utils/roles'
import { vertexStateColor } from '#shared/utils/states'

const props = defineProps<{ hypergraph: Hypergraph, states: Record<string, string> }>()
const selected = defineModel<string | null>({ default: null })
const matrix = computed(() => incidenceMatrix(props.hypergraph))
</script>

<template>
  <v-card>
    <v-table fixed-header height="640" density="compact" hover class="bg-transparent">
      <thead>
        <tr>
          <th class="bg-surface" />
          <th v-for="col in matrix.columns" :key="col.id" class="bg-surface text-center px-1">
            <v-chip
              :color="BAG_COLOR[col.type]"
              :variant="selected === `e:${col.id}` ? 'flat' : 'tonal'"
              :title="`${col.id} · ${col.size}`"
              link
              @click="selected = `e:${col.id}`"
            >
              {{ col.label }}
            </v-chip>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in matrix.rows" :key="row.id" :class="{ 'bg-surface-bright': selected === `v:${row.id}` }">
          <td class="text-no-wrap">
            <div class="d-flex align-center ga-2 cursor-pointer" @click="selected = `v:${row.id}`">
              <v-badge dot inline :color="vertexStateColor(states[row.id] ?? 'spec')" />
              <span class="text-body-2" :title="row.id">{{ vertexLabel(row.id) }}</span>
              <span class="text-caption text-medium-emphasis">{{ row.kind }} · {{ row.bags }}</span>
            </div>
          </td>
          <td v-for="col in matrix.columns" :key="col.id" class="text-center px-1">
            <v-chip
              v-if="matrix.cells[row.id]?.[col.id]"
              :color="roleColor(matrix.cells[row.id]![col.id]!.role)"
              :variant="matrix.cells[row.id]![col.id]!.observed ? 'outlined' : 'flat'"
              size="x-small"
            >
              {{ matrix.cells[row.id]![col.id]!.role }}
            </v-chip>
          </td>
        </tr>
      </tbody>
    </v-table>
  </v-card>
</template>
