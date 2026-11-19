<script setup lang="ts">
import { mdiBrain, mdiCheckDecagramOutline, mdiCloseOctagonOutline } from '@mdi/js'
import type { RunEvent } from '#shared/types/run'
import { tierColor } from '#shared/utils/colors'
import { str } from '#shared/utils/events'
import { lastVerdict, openCall } from '#shared/utils/live'
import { labels } from '~/utils/labels'

const props = defineProps<{ events: RunEvent[], running: boolean }>()
const call = computed(() => (props.running ? openCall(props.events) : null))
const verdict = computed(() => lastVerdict(props.events))
const seconds = useSecondsSince(() => call.value?.since)
</script>

<template>
  <v-card height="100%">
    <v-card-item :title="labels.live.now" />
    <v-card-text class="d-flex flex-column ga-4">
      <v-fade-transition mode="out-in">
        <div v-if="call" :key="call.step" class="d-flex align-center ga-4">
          <v-progress-circular indeterminate color="primary" size="52" width="4">
            <v-icon :icon="mdiBrain" color="primary" />
          </v-progress-circular>
          <div>
            <div class="text-h6">{{ call.agent }}</div>
            <div class="d-flex flex-wrap ga-2 mt-1">
              <v-chip :color="tierColor(call.tier)">{{ call.tier }} · {{ call.model }}</v-chip>
              <v-chip v-if="call.taskId">{{ call.taskId }}</v-chip>
              <v-chip color="warning" variant="outlined">{{ seconds }} s</v-chip>
            </div>
          </div>
        </div>
        <div v-else class="text-medium-emphasis">{{ running ? labels.live.harness : labels.live.idle }}</div>
      </v-fade-transition>
      <v-alert
        v-if="verdict"
        :type="str(verdict, 'status') === 'PASS' ? 'success' : 'error'"
        :icon="str(verdict, 'status') === 'PASS' ? mdiCheckDecagramOutline : mdiCloseOctagonOutline"
        variant="tonal"
        density="compact"
        :title="`${labels.live.lastVerdict}: ${str(verdict, 'task_id')}`"
        :text="str(verdict, 'first_issue') || labels.live.passed"
      />
    </v-card-text>
  </v-card>
</template>
