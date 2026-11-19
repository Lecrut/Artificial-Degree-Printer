<script setup lang="ts">
import { mdiFileOutline, mdiRobotOutline, mdiWrenchClock } from '@mdi/js'
import type { QueueTask } from '#shared/types/live'
import type { RunEvent } from '#shared/types/run'
import { queueStatusColor } from '#shared/utils/colors'
import { activeTask, BOARD_COLUMNS, boardColumns } from '#shared/utils/live'
import { labels } from '~/utils/labels'

const props = defineProps<{ queue: QueueTask[], events: RunEvent[] }>()
const active = computed(() => activeTask(props.events))
const columns = computed(() => boardColumns(props.queue, active.value))
// The board's reading order, the order ← → follow in the task dialog.
const ordered = computed(() => BOARD_COLUMNS.flatMap(column => columns.value[column]))
const opened = ref<number | null>(null)
</script>

<template>
  <v-card>
    <v-card-item :title="labels.live.board" :subtitle="labels.live.boardHint(queue.length)" />
    <v-card-text>
      <!-- Five columns side by side from md up: a wrapped row put "padło" under the others. -->
      <v-row density="compact" class="flex-md-nowrap">
        <v-col v-for="column in BOARD_COLUMNS" :key="column" cols="12" sm="6" md>
          <v-sheet color="surface-bright" class="pa-2 fill-height">
            <div class="d-flex align-center ga-2 mb-2 px-1">
              <v-badge dot inline :color="queueStatusColor(column)" />
              <span class="text-overline">{{ labels.live.columns[column] }}</span>
              <v-spacer />
              <v-chip :color="queueStatusColor(column)">{{ columns[column].length }}</v-chip>
            </div>
            <v-slide-y-transition group tag="div" class="d-flex flex-column ga-2">
              <CommonHoverCard
                v-for="task in columns[column]"
                :key="task.task_id"
                :accent="queueStatusColor(column)"
                color="surface"
                class="pa-3"
                @click="opened = ordered.indexOf(task)"
              >
                <!-- Id and repairs on top; nothing in a card may be wider than its column (see the row below). -->
                <div class="d-flex align-center ga-2">
                  <v-badge dot inline :color="queueStatusColor(column)" />
                  <span class="text-subtitle-2 font-weight-bold">{{ task.task_id }}</span>
                  <v-spacer />
                  <v-chip
                    v-if="task.repair_attempts"
                    :prepend-icon="mdiWrenchClock"
                    :color="column === 'IN_PROGRESS' ? 'warning' : undefined"
                    :variant="column === 'IN_PROGRESS' ? 'flat' : 'tonal'"
                    :title="labels.live.repairs(task.repair_attempts)"
                    size="x-small"
                  >
                    {{ column === 'IN_PROGRESS' ? labels.live.repairing(task.repair_attempts) : task.repair_attempts }}
                  </v-chip>
                </div>
                <!-- Who works on which file, as chips that shrink and cut their text rather than widen the column. -->
                <div class="d-flex flex-wrap ga-1 mt-2">
                  <v-chip size="x-small" :prepend-icon="mdiFileOutline" :title="task.target_node">
                    <span class="text-truncate">{{ task.target_node }}</span>
                  </v-chip>
                  <v-chip size="x-small" color="secondary" :prepend-icon="mdiRobotOutline" :title="task.assigned_agent">
                    <span class="text-truncate">{{ task.assigned_agent }}</span>
                  </v-chip>
                </div>
              </CommonHoverCard>
            </v-slide-y-transition>
          </v-sheet>
        </v-col>
      </v-row>
    </v-card-text>
    <LiveTaskDialog v-model="opened" :tasks="ordered" :events="events" :active="active" />
  </v-card>
</template>
