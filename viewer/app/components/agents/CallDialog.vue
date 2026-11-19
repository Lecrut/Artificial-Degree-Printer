<script setup lang="ts">
import { mdiClockOutline, mdiRobotOutline } from '@mdi/js'
import type { AgentCallDetail } from '#shared/types/calls'
import { tierColor, verdictColor } from '#shared/utils/colors'
import { formatClock } from '#shared/utils/format'
import { labels } from '~/utils/labels'

const props = defineProps<{ detail: AgentCallDetail | null, loading: boolean, failed: boolean, position: number, total: number }>()
const open = defineModel<boolean>({ required: true })
const emit = defineEmits<{ move: [delta: number] }>()
const tab = ref<'answer' | 'payload' | 'raw' | 'prompt'>('answer')

// What the copy button copies: the text of the open tab.
const copied = computed(() => {
  const d = props.detail
  if (!d) return ''
  if (tab.value === 'prompt') return d.systemPrompt
  if (tab.value === 'raw') return d.rawAnswer
  return JSON.stringify(tab.value === 'payload' ? d.payload : d.answer, null, 2)
})
</script>

<template>
  <CommonBrowseDialog
    v-model="open"
    :position="position"
    :total="total"
    :icon="mdiRobotOutline"
    :color="detail?.ok === false ? 'error' : 'primary'"
    :loading="loading"
    :max-width="1200"
    min-height="70vh"
    @move="emit('move', $event)"
  >
    <template #title>
      <template v-if="detail">
        <span>{{ detail.agent }}</span>
        <v-chip :color="tierColor(detail.tier)">{{ detail.tier }} · {{ detail.model }}</v-chip>
        <v-chip v-if="detail.verdict" :color="verdictColor(detail.verdict)" variant="flat">{{ detail.verdict }}</v-chip>
      </template>
    </template>
    <template #subtitle>
      <template v-if="detail">
        <span>#{{ detail.step }}</span>
        <span><v-icon :icon="mdiClockOutline" size="14" /> {{ formatClock(detail.ts) }}</span>
        <span v-if="detail.elapsedMs !== null">{{ (detail.elapsedMs / 1000).toFixed(1) }} s</span>
        <v-chip v-if="detail.taskId" size="x-small">{{ detail.taskId }}</v-chip>
      </template>
    </template>
    <template #header>
      <div v-if="detail?.decision" class="text-body-2 mt-2">{{ detail.decision }}</div>
    </template>
    <template #toolbar>
      <div class="d-flex align-center px-4">
        <v-tabs v-model="tab" color="primary" class="flex-grow-1">
          <v-tab value="answer" :text="labels.agents.answer" />
          <v-tab value="payload" :text="labels.agents.payload" />
          <v-tab value="raw" :text="labels.agents.raw" />
          <v-tab value="prompt" :text="labels.agents.prompt" />
        </v-tabs>
        <CommonCopyButton :text="copied" />
      </div>
    </template>
    <v-alert v-if="failed" type="error" variant="tonal" class="mb-4" :text="labels.common.loadError" />
    <div v-if="!detail && !failed" class="d-flex justify-center pa-8"><v-progress-circular indeterminate color="primary" /></div>
    <template v-else-if="detail">
      <v-alert v-if="detail.error" type="error" variant="tonal" class="mb-4" :text="detail.error" />
      <v-tabs-window v-model="tab">
        <v-tabs-window-item value="answer"><AgentsJsonTree :value="detail.answer" /></v-tabs-window-item>
        <v-tabs-window-item value="payload"><AgentsJsonTree :value="detail.payload" /></v-tabs-window-item>
        <v-tabs-window-item value="raw"><pre class="text-pre-wrap text-break text-medium-emphasis">{{ detail.rawAnswer }}</pre></v-tabs-window-item>
        <v-tabs-window-item value="prompt"><pre class="text-pre-wrap text-break text-medium-emphasis">{{ detail.systemPrompt }}</pre></v-tabs-window-item>
      </v-tabs-window>
    </template>
  </CommonBrowseDialog>
</template>
