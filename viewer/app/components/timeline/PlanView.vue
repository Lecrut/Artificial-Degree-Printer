<script setup lang="ts">
import { mdiCodeBraces, mdiFileDocumentOutline, mdiRobotOutline, mdiTarget } from '@mdi/js'
import type { AgentCallDetail } from '#shared/types/calls'
import type { TimelineEntry } from '#shared/types/timeline'
import { labels } from '~/utils/labels'
import { callApi } from '~/utils/runUrls'

interface PlannedTask { task_id: string, description: string, target_node: string, assigned_agent: string }
interface PlanAnswer {
  tasks?: PlannedTask[]
  interfaces?: Record<string, string>
  academic_blueprint?: { thesis_title?: string, thesis_statement?: string }
}

// The plan itself, as the planner wrote it: its answer in the agent trace (tasks, module interfaces, the thesis).
const props = defineProps<{ entry: TimelineEntry }>()
const at = useRunAt()
const writing = computed(() => props.entry.status === 'running')
const { data, pending, error, refresh } = useAsyncData(
  () => `plan-${at.value?.source}-${at.value?.ref}-${at.value?.task}-${props.entry.step}-${writing.value}`,
  async () => (at.value && props.entry.step && !writing.value ? (await $fetch<AgentCallDetail>(callApi(at.value, props.entry.step))).answer as PlanAnswer : null),
  { watch: [writing] },
)
const plan = computed(() => data.value ?? null)
</script>

<template>
  <div class="d-flex flex-column ga-4">
    <v-alert v-if="writing" type="info" variant="tonal" density="compact" :text="labels.timeline.planWriting" />
    <v-skeleton-loader v-else-if="pending" type="heading, list-item-two-line@4" color="transparent" />
    <CommonLoadError v-else-if="error" @retry="refresh()" />
    <template v-else-if="plan">
      <div v-if="plan.academic_blueprint?.thesis_title">
        <div class="text-overline text-primary">{{ labels.timeline.planThesis }}</div>
        <div class="text-subtitle-1 font-weight-bold">{{ plan.academic_blueprint.thesis_title }}</div>
        <div class="text-body-2 text-medium-emphasis">{{ plan.academic_blueprint.thesis_statement }}</div>
      </div>
      <div v-if="plan.tasks?.length">
        <div class="text-overline text-primary">{{ labels.timeline.planTasks(plan.tasks.length) }}</div>
        <v-list density="compact" class="bg-transparent py-0">
          <v-list-item v-for="task in plan.tasks" :key="task.task_id" class="px-0">
            <div class="d-flex flex-wrap align-center ga-2 mb-1">
              <v-chip color="primary" variant="flat" size="x-small">{{ task.task_id }}</v-chip>
              <v-chip size="x-small" :prepend-icon="mdiTarget">{{ task.target_node }}</v-chip>
              <v-chip size="x-small" color="secondary" :prepend-icon="mdiRobotOutline">{{ task.assigned_agent }}</v-chip>
            </div>
            <div class="text-body-2">{{ task.description }}</div>
          </v-list-item>
        </v-list>
      </div>
      <div v-if="plan.interfaces && Object.keys(plan.interfaces).length">
        <div class="text-overline text-primary">{{ labels.timeline.planInterfaces }}</div>
        <v-expansion-panels variant="accordion" multiple>
          <v-expansion-panel v-for="(code, module) in plan.interfaces" :key="module" color="surface-bright" elevation="0">
            <v-expansion-panel-title>
              <v-icon :icon="String(module).endsWith('.py') ? mdiCodeBraces : mdiFileDocumentOutline" size="18" class="me-2" />{{ module }}
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <pre class="text-pre-wrap text-break text-caption ma-0">{{ code }}</pre>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </div>
    </template>
  </div>
</template>
