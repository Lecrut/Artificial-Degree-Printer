<script setup lang="ts">
import type { LaunchStatus } from '#shared/types/live'
import { labels } from '~/utils/labels'

const props = defineProps<{ status: LaunchStatus | null }>()
const scroller = ref<{ $el: HTMLElement } | null>(null)

// Follow the end of the console as lines arrive.
watch(() => props.status?.lines.length, () => nextTick(() => {
  const el = scroller.value?.$el
  if (el) el.scrollTop = el.scrollHeight
}))
</script>

<template>
  <div class="d-flex flex-column ga-2 flex-grow-1">
    <div v-if="status?.args.length" class="text-caption text-medium-emphasis text-break">python {{ status.args.join(' ') }}</div>
    <v-sheet ref="scroller" color="background" class="pa-3 overflow-y-auto flex-grow-1" min-height="240">
      <pre v-if="status?.lines.length" class="text-pre-wrap text-break text-caption text-medium-emphasis ma-0">{{ status.lines.join('\n') }}</pre>
      <v-skeleton-loader v-else-if="!status" type="text@6" color="transparent" />
      <div v-else class="text-medium-emphasis">{{ labels.launch.noOutput }}</div>
    </v-sheet>
  </div>
</template>
