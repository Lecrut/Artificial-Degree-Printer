<script setup lang="ts">
import { mdiBackupRestore, mdiCloseCircleOutline, mdiPlaylistPlus } from '@mdi/js'
import type { ComparedRun } from '#shared/types/compare'
import { MAX_COMPARED } from '#shared/utils/compare'
import type { RunOption } from '~/composables/useCompare'
import { labels } from '~/utils/labels'

defineProps<{ options: RunOption[], loading: boolean, runs: ComparedRun[], tasks: string[] }>()
const keys = defineModel<string[]>({ required: true })
const emit = defineEmits<{ sameTask: [task: string] }>()
const colorOf = (runs: ComparedRun[], index: number) => runs[index]?.color
</script>

<template>
  <v-card class="pa-4 d-flex flex-column ga-4">
    <v-autocomplete
      v-model="keys"
      :items="options"
      :loading="loading"
      item-value="value"
      item-title="title"
      :placeholder="labels.compare.pick"
      :prepend-inner-icon="mdiPlaylistPlus"
      :hint="labels.compare.pickHint"
      persistent-hint
      multiple
      chips
      closable-chips
      :counter="MAX_COMPARED"
      :rules="[(v: string[]) => v.length <= MAX_COMPARED]"
    >
      <template #chip="{ props: chip, index }">
        <v-chip v-bind="chip" :color="colorOf(runs, index)" variant="flat" :close-icon="mdiCloseCircleOutline" />
      </template>
      <template #item="{ props: item, item: option }">
        <v-list-item v-bind="item" :subtitle="option.subtitle" />
      </template>
    </v-autocomplete>
    <div class="d-flex flex-wrap align-center ga-2">
      <span class="text-caption text-medium-emphasis me-1">{{ labels.compare.sameTask }}</span>
      <v-chip v-for="task in tasks" :key="task" :prepend-icon="mdiBackupRestore" color="primary" link @click="emit('sameTask', task)">{{ task }}</v-chip>
      <v-spacer />
      <v-btn v-if="keys.length" variant="text" size="small" :text="labels.compare.clear" @click="keys = []" />
    </div>
  </v-card>
</template>
