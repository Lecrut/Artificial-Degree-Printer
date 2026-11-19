<script setup lang="ts">
import { mdiFitToScreenOutline } from '@mdi/js'
import type { GraphElements } from '#shared/utils/graph'
import { labels } from '~/utils/labels'

const props = defineProps<{ elements: GraphElements }>()
const selected = defineModel<string | null>({ default: null })

const container = ref<HTMLElement | null>(null)
const { fit } = useCytoscape(container, toRef(props, 'elements'), selected)
</script>

<template>
  <v-sheet height="640" rounded="xl" color="background" border class="position-relative">
    <div ref="container" class="fill-height w-100" />
    <v-btn
      :icon="mdiFitToScreenOutline"
      :title="labels.graph.fit"
      size="small"
      variant="tonal"
      class="position-absolute top-0 right-0 ma-3"
      @click="fit"
    />
  </v-sheet>
</template>
