<script setup lang="ts">
import { mdiSitemapOutline } from '@mdi/js'
import type { FlowKind } from '#shared/types/flow'
import { FLOW_KIND_COLOR } from '#shared/utils/colors'
import { labels } from '~/utils/labels'

const selected = ref<string | null>(null)
const open = computed({ get: () => selected.value !== null, set: (value) => { if (!value) selected.value = null } })
// "end" shares its legend entry with "start".
const legend = (Object.keys(labels.flow.kinds) as FlowKind[]).filter(kind => kind !== 'end')
</script>

<template>
  <div class="d-flex flex-column ga-6">
    <CommonPageHeader :icon="mdiSitemapOutline" :title="labels.flow.title" :subtitle="labels.flow.subtitle" />
    <div class="d-flex flex-wrap align-center ga-2">
      <span class="text-medium-emphasis me-2">{{ labels.flow.legend }}:</span>
      <v-chip v-for="kind in legend" :key="kind" :color="FLOW_KIND_COLOR[kind]">{{ labels.flow.kinds[kind] }}</v-chip>
    </div>
    <FlowDiagram v-model="selected" />
    <v-navigation-drawer v-model="open" location="right" temporary width="620">
      <FlowDetails v-if="selected" :id="selected" @close="selected = null" />
    </v-navigation-drawer>
  </div>
</template>
