<script setup lang="ts">
import { mdiPause, mdiPlay, mdiSkipNext, mdiSkipPrevious } from '@mdi/js'
import type { RunEvent } from '#shared/types/run'
import { str } from '#shared/utils/events'
import { formatClock } from '#shared/utils/format'
import { vertexStateColor } from '#shared/utils/states'
import { labels } from '~/utils/labels'

defineProps<{ max: number, playing: boolean, current: RunEvent | null }>()
const position = defineModel<number>({ required: true })
const emit = defineEmits<{ play: [], stop: [] }>()
</script>

<template>
  <div class="d-flex flex-wrap align-center ga-3">
    <v-btn-group density="comfortable" variant="tonal" divided>
      <v-btn :icon="mdiSkipPrevious" :title="labels.graph.start" @click="position = 0" />
      <v-btn :icon="playing ? mdiPause : mdiPlay" color="primary" :title="labels.graph.play" @click="playing ? emit('stop') : emit('play')" />
      <v-btn :icon="mdiSkipNext" :title="labels.graph.end" @click="position = max" />
    </v-btn-group>
    <v-slider v-model="position" :max="max" :step="1" color="primary" hide-details min-width="240" class="flex-grow-1" />
    <div class="d-flex align-center ga-2 text-body-2">
      <span class="text-medium-emphasis">{{ position }}/{{ max }}</span>
      <template v-if="current">
        <span class="text-medium-emphasis">{{ formatClock(current.ts) }}</span>
        <span>{{ str(current, 'vertex') }}</span>
        <v-chip :color="vertexStateColor(str(current, 'state'))">{{ str(current, 'state') }}</v-chip>
      </template>
      <span v-else class="text-medium-emphasis">{{ position === max ? labels.graph.final : labels.graph.initial }}</span>
    </div>
  </div>
</template>
