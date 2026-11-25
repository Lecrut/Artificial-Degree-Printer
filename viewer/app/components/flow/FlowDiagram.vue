<script setup lang="ts">
// The canvas of the flow: Cytoscape draws into the sheet, the frame scrolls sideways on a narrow screen.
const selected = defineModel<string | null>({ required: true })
const frame = ref<HTMLElement | null>(null)
const sheet = ref<{ $el: HTMLElement } | null>(null)
const { width, height } = useFlowDiagram(frame, computed(() => sheet.value?.$el ?? null), selected)
</script>

<template>
  <div ref="frame" class="overflow-x-auto">
    <v-sheet ref="sheet" :width="width" :height="height" color="transparent" />
  </div>
</template>
