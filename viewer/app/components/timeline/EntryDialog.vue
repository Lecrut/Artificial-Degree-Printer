<script setup lang="ts">
import { mdiMessageTextOutline, mdiRobotOutline } from '@mdi/js'
import type { TimelineEntry } from '#shared/types/timeline'
import { entryStatusColor } from '#shared/utils/colors'
import { isPlanStep } from '#shared/utils/timeline'
import { formatClock } from '#shared/utils/format'
import { KIND_ICON, STATUS_ICON } from '~/utils/icons'
import { labels } from '~/utils/labels'

const props = defineProps<{ entries: TimelineEntry[] }>()
const index = defineModel<number | null>({ required: true })
const emit = defineEmits<{ showCalls: [taskId: string] }>()
const { open, current: entry, move } = useListDialog(index, () => props.entries)

function showCalls(taskId: string) {
  emit('showCalls', taskId)
  open.value = false
}
</script>

<template>
  <CommonBrowseDialog
    v-model="open"
    :position="index ?? 0"
    :total="entries.length"
    :title="entry?.title"
    :subtitle="entry ? [formatClock(entry.ts), labels.phases[entry.phase], entry.subtitle].filter(Boolean).join(' · ') : ''"
    :icon="entry ? KIND_ICON[entry.kind] : undefined"
    :color="entry ? entryStatusColor(entry.status) : undefined"
    @move="move"
  >
    <div v-if="entry" class="d-flex flex-column ga-4">
      <div class="d-flex flex-wrap ga-2">
        <v-chip :color="entryStatusColor(entry.status)" :prepend-icon="STATUS_ICON[entry.status]" variant="flat">{{ labels.statuses[entry.status] }}</v-chip>
        <v-chip v-for="agent in entry.llm.agents" :key="agent" :prepend-icon="mdiRobotOutline" color="secondary">{{ agent }}</v-chip>
        <v-chip v-if="entry.llm.calls" :prepend-icon="mdiMessageTextOutline" color="primary" link @click="showCalls(entry.title)">
          {{ labels.timeline.llm(entry.llm.calls, entry.llm.seconds) }}
        </v-chip>
      </div>
      <v-fade-transition mode="out-in">
        <div :key="entry.id" class="d-flex flex-column ga-4">
          <TimelineDetailList v-if="entry.details.length" :details="entry.details" />
          <TimelinePlanView v-if="isPlanStep(entry)" :entry="entry" />
          <div v-if="entry.attempts.length">
            <div class="text-overline text-primary">{{ labels.timeline.attempts }}</div>
            <TimelineTaskAttempts :attempts="entry.attempts" />
          </div>
          <div v-if="!entry.details.length && !entry.attempts.length && !isPlanStep(entry)" class="text-medium-emphasis">{{ labels.timeline.noDetails }}</div>
        </div>
      </v-fade-transition>
    </div>
  </CommonBrowseDialog>
</template>
