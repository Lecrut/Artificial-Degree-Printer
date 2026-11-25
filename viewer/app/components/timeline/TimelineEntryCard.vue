<script setup lang="ts">
import { mdiArrowExpand, mdiMessageTextOutline, mdiRobotOutline } from '@mdi/js'
import type { TimelineEntry } from '#shared/types/timeline'
import { entryStatusColor } from '#shared/utils/colors'
import { isPlanStep } from '#shared/utils/timeline'
import { formatClock } from '#shared/utils/format'
import type { Snapshot } from '#shared/utils/snapshots'
import { KIND_ICON } from '~/utils/icons'
import { labels } from '~/utils/labels'

const props = defineProps<{ entry: TimelineEntry, snapshot?: Snapshot | null }>()
const at = useRunAt()
const emit = defineEmits<{ showCalls: [taskId: string], open: [] }>()
const expandable = computed(() => props.entry.details.length > 0 || props.entry.attempts.length > 0 || isPlanStep(props.entry))
const problems = computed(() => props.entry.attempts.filter(a => a.status === 'fail').length)
</script>

<template>
  <v-expansion-panels variant="accordion" :readonly="!expandable">
    <v-expansion-panel :hide-actions="!expandable" elevation="0" class="border" color="surface">
      <v-expansion-panel-title>
        <div class="d-flex flex-wrap align-center ga-2 w-100">
          <v-icon :icon="KIND_ICON[entry.kind]" :color="entryStatusColor(entry.status)" size="20" />
          <span class="text-caption text-medium-emphasis">{{ formatClock(entry.ts) }}</span>
          <span class="text-subtitle-2 font-weight-bold">{{ entry.title }}</span>
          <span class="text-caption text-medium-emphasis text-truncate">{{ entry.subtitle }}</span>
          <v-spacer />
          <v-chip v-for="agent in entry.llm.agents" :key="agent" :prepend-icon="mdiRobotOutline" color="secondary">{{ agent }}</v-chip>
          <v-chip v-if="problems" color="error" variant="outlined">{{ labels.timeline.problems(problems) }}</v-chip>
          <v-chip
            v-if="entry.llm.calls"
            :prepend-icon="mdiMessageTextOutline"
            color="primary"
            link
            @click.stop="emit('showCalls', entry.title)"
          >
            {{ labels.timeline.llm(entry.llm.calls, entry.llm.seconds) }}
          </v-chip>
          <v-chip :color="entryStatusColor(entry.status)" variant="flat">{{ labels.statuses[entry.status] }}</v-chip>
          <LaunchResumeButton v-if="at && entry.kind === 'task'" :at="at" :snapshot="snapshot" here compact />
          <v-btn :icon="mdiArrowExpand" :title="labels.timeline.details" size="x-small" variant="tonal" @click.stop="emit('open')" />
        </div>
      </v-expansion-panel-title>
      <v-expansion-panel-text v-if="expandable">
        <TimelineDetailList v-if="entry.details.length" :details="entry.details" />
        <div v-if="entry.attempts.length" class="text-overline text-primary mt-2">{{ labels.timeline.attempts }}</div>
        <TimelineTaskAttempts v-if="entry.attempts.length" :attempts="entry.attempts" />
        <TimelinePlanView v-if="isPlanStep(entry)" :entry="entry" class="mt-2" />
      </v-expansion-panel-text>
    </v-expansion-panel>
  </v-expansion-panels>
</template>
