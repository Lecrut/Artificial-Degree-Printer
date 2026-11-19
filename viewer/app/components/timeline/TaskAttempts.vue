<script setup lang="ts">
import { mdiChevronDown, mdiChevronUp } from '@mdi/js'
import type { TaskAttempt } from '#shared/types/timeline'
import { entryStatusColor } from '#shared/utils/colors'
import { formatClock } from '#shared/utils/format'
import { attemptIcon } from '~/utils/icons'
import { labels } from '~/utils/labels'

const props = defineProps<{ attempts: TaskAttempt[] }>()
// The first line is the message; the rest (tracebacks, doctest output) folds away until asked for.
const parts = computed(() => props.attempts.map((item) => {
  const [head = '', ...rest] = item.text.split('\n')
  return { head, rest: rest.join('\n').trim() }
}))
const open = ref(new Set<number>())
function toggle(i: number) {
  if (!open.value.delete(i)) open.value.add(i)
}
</script>

<template>
  <v-timeline side="end" align="start" truncate-line="both" density="compact" line-color="surface-variant">
    <v-timeline-item
      v-for="(item, i) in attempts"
      :key="i"
      :dot-color="entryStatusColor(item.status)"
      :icon="attemptIcon(item)"
      size="small"
      fill-dot
    >
      <v-sheet color="surface-bright" class="px-4 py-2">
        <div class="d-flex align-center ga-3">
          <span class="text-caption text-medium-emphasis text-no-wrap">{{ formatClock(item.ts) }}</span>
          <span class="text-body-2 text-break flex-grow-1">{{ parts[i]!.head }}</span>
          <v-btn
            v-if="parts[i]!.rest"
            :icon="open.has(i) ? mdiChevronUp : mdiChevronDown"
            :title="labels.timeline.moreLines"
            size="x-small"
            variant="text"
            @click="toggle(i)"
          />
        </div>
        <v-expand-transition>
          <v-sheet v-if="open.has(i)" color="background" max-height="260" class="mt-2 pa-3 text-caption text-pre-wrap text-break overflow-y-auto">{{ parts[i]!.rest }}</v-sheet>
        </v-expand-transition>
      </v-sheet>
    </v-timeline-item>
  </v-timeline>
</template>
