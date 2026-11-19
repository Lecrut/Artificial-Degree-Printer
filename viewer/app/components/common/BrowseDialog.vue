<script setup lang="ts">
import { mdiChevronLeft, mdiChevronRight, mdiClose } from '@mdi/js'
import { labels } from '~/utils/labels'

// The one dialog shape of the viewer: an item of a list, with ← → to its neighbours and Esc to close.
withDefaults(defineProps<{
  position: number
  total: number
  title?: string
  subtitle?: string
  icon?: string
  color?: string
  loading?: boolean
  maxWidth?: number
  minHeight?: string
}>(), { title: '', subtitle: '', icon: undefined, color: 'primary', loading: false, maxWidth: 980, minHeight: '50vh' })
const open = defineModel<boolean>({ required: true })
const emit = defineEmits<{ move: [delta: number] }>()

useArrowKeys(open, { left: () => emit('move', -1), right: () => emit('move', 1) })
</script>

<template>
  <v-dialog v-model="open" :max-width="maxWidth" scrollable transition="dialog-bottom-transition">
    <v-card :min-height="minHeight">
      <v-card-item class="pb-2">
        <template v-if="icon" #prepend>
          <v-avatar :color="color" variant="tonal" size="52"><v-icon :icon="icon" size="28" /></v-avatar>
        </template>
        <v-card-title class="d-flex flex-wrap align-center ga-2 font-weight-bold text-wrap">
          <slot name="title">{{ title }}</slot>
        </v-card-title>
        <v-card-subtitle class="d-flex flex-wrap align-center ga-3 text-wrap">
          <slot name="subtitle">{{ subtitle }}</slot>
        </v-card-subtitle>
        <slot name="header" />
        <template #append>
          <div class="d-flex align-center ga-1">
            <span class="text-caption text-medium-emphasis text-no-wrap me-1">{{ position + 1 }} / {{ total }}</span>
            <v-btn :icon="mdiChevronLeft" :disabled="position <= 0" :title="labels.common.prev" variant="tonal" size="small" @click="emit('move', -1)" />
            <v-btn :icon="mdiChevronRight" :disabled="position >= total - 1" :title="labels.common.next" variant="tonal" size="small" @click="emit('move', 1)" />
            <v-btn :icon="mdiClose" variant="text" size="small" @click="open = false" />
          </div>
        </template>
      </v-card-item>
      <v-progress-linear :active="loading" indeterminate color="primary" height="2" />
      <slot name="toolbar" />
      <v-divider />
      <v-card-text>
        <slot />
      </v-card-text>
      <v-divider />
      <v-card-actions class="text-caption text-medium-emphasis px-4">{{ labels.common.arrows }}</v-card-actions>
    </v-card>
  </v-dialog>
</template>
