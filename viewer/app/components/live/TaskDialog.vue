<script setup lang="ts">
import { mdiRobotOutline, mdiTarget, mdiWrenchOutline } from '@mdi/js'
import type { QueueTask } from '#shared/types/live'
import type { RunEvent } from '#shared/types/run'
import { queueStatusColor } from '#shared/utils/colors'
import { buildTimeline } from '#shared/utils/timeline'
import { labels } from '~/utils/labels'

const props = defineProps<{ tasks: QueueTask[], events: RunEvent[], active: string | null }>()
const index = defineModel<number | null>({ required: true })
const { open, current: task, move } = useListDialog(index, () => props.tasks)
// As on the board: the task being worked on is in progress, even while the queue marks it FAILED for a repair.
const status = computed(() => (task.value?.task_id === props.active ? 'IN_PROGRESS' : task.value?.status ?? ''))
// The task's own story so far, as the timeline tells it.
const entry = computed(() => buildTimeline(props.events).entries.find(e => e.kind === 'task' && e.title === task.value?.task_id) ?? null)
</script>

<template>
  <CommonBrowseDialog
    v-model="open"
    :position="index ?? 0"
    :total="tasks.length"
    :title="task?.task_id"
    :subtitle="task ? labels.live.columns[status] ?? status : ''"
    :icon="mdiWrenchOutline"
    :color="queueStatusColor(status)"
    :max-width="900"
    min-height="40vh"
    @move="move"
  >
    <div v-if="task" class="d-flex flex-column ga-4">
      <div class="d-flex flex-wrap ga-2">
        <v-chip :color="queueStatusColor(status)" variant="flat">{{ labels.live.columns[status] ?? status }}</v-chip>
        <v-chip v-if="task.repair_attempts" color="warning" variant="tonal">{{ labels.live.repairs(task.repair_attempts) }}</v-chip>
        <v-chip :prepend-icon="mdiTarget">{{ task.target_node }}</v-chip>
        <v-chip :prepend-icon="mdiRobotOutline" color="secondary">{{ task.assigned_agent }}</v-chip>
      </div>
      <v-sheet color="surface-bright" class="pa-4 text-body-1 text-pre-wrap">{{ task.description }}</v-sheet>
      <div v-if="entry?.attempts.length">
        <div class="text-overline text-primary">{{ labels.timeline.attempts }}</div>
        <TimelineTaskAttempts :attempts="entry.attempts" />
      </div>
    </div>
  </CommonBrowseDialog>
</template>
