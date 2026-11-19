<script setup lang="ts">
import { mdiArrowExpand } from '@mdi/js'
import type { RunRef } from '#shared/types/run'
import { labels } from '~/utils/labels'

const props = defineProps<{ at: RunRef, step: number }>()
const emit = defineEmits<{ open: [step: number] }>()
const { data: detail, pending, error } = useCallDetail(() => props.at, () => props.step)

const PREVIEW_LINES = 14
const preview = computed(() => (detail.value?.rawAnswer ?? '').split('\n').slice(0, PREVIEW_LINES).join('\n'))
const payloadKeys = computed(() => Object.keys((detail.value?.payload ?? {}) as Record<string, unknown>))
const issues = computed(() => ((detail.value?.answer as { issues?: unknown[] } | null)?.issues ?? []).length)
</script>

<template>
  <v-sheet color="surface-bright" rounded="xl" class="pa-4 my-2">
    <v-progress-linear v-if="pending" indeterminate color="primary" />
    <v-alert v-else-if="error" type="error" variant="tonal" density="compact" :text="labels.common.loadError" />
    <v-expand-transition>
      <div v-if="detail" class="d-flex flex-column ga-3">
        <div class="d-flex flex-wrap align-center ga-2">
          <span class="text-caption text-medium-emphasis">{{ labels.agents.payload }}:</span>
          <v-chip v-for="key in payloadKeys" :key="key" color="secondary">{{ key }}</v-chip>
          <v-chip v-if="issues" color="warning">{{ labels.agents.issues(issues) }}</v-chip>
          <v-spacer />
          <v-btn :prepend-icon="mdiArrowExpand" color="primary" variant="tonal" size="small" @click="emit('open', step)">
            {{ labels.agents.full }}
          </v-btn>
        </div>
        <v-alert v-if="detail.error" type="error" variant="tonal" density="compact" :text="detail.error" />
        <pre class="text-pre-wrap text-medium-emphasis ma-0">{{ preview }}</pre>
      </div>
    </v-expand-transition>
  </v-sheet>
</template>
