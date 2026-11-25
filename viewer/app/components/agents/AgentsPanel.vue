<script setup lang="ts">
import { mdiMagnify } from '@mdi/js'
import type { RunRef } from '#shared/types/run'
import { labels } from '~/utils/labels'

const props = defineProps<{ at: RunRef, focusTask?: string | null, liveStamp?: string }>()
const { calls, agents, agent, search, pending, error, refresh, openStep, detail, loading, detailFailed, position, move } = useAgentCalls(() => props.at, () => props.liveStamp)
watch(() => props.focusTask, (task) => { if (task) search.value = task }, { immediate: true })

const dialog = computed({
  get: () => openStep.value !== null,
  set: (open: boolean) => { if (!open) openStep.value = null },
})
</script>

<template>
  <v-card>
    <v-card-item :title="labels.agents.title" :subtitle="labels.agents.count(calls.length)">
      <template #append>
        <div class="d-flex flex-wrap ga-3">
          <v-select v-model="agent" :items="agents" :placeholder="labels.agents.allAgents" clearable hide-details min-width="220" />
          <v-text-field v-model="search" :placeholder="labels.agents.search" :prepend-inner-icon="mdiMagnify" clearable hide-details min-width="260" />
        </div>
      </template>
    </v-card-item>
    <CommonLoadError v-if="error" class="ma-4" @retry="refresh()" />
    <AgentsCallsTable v-else :calls="calls" :loading="pending" :at="at" @open="step => (openStep = step)" />
    <AgentsCallDialog v-model="dialog" :detail="detail" :loading="loading" :failed="detailFailed" :position="position" :total="calls.length" @move="move" />
  </v-card>
</template>
