<script setup lang="ts">
import type { EChartsOption } from 'echarts'
import VChart from 'vue-echarts'
import '~/utils/echarts'

// An ECharts canvas filling a sheet of the given height; resizes with the layout.
withDefaults(defineProps<{ option: EChartsOption, height?: number }>(), { height: 320 })
// A click anywhere on the plot picks the point under the crosshair (its index on a category x axis),
// so the user does not have to hit an 8 px dot.
const emit = defineEmits<{ pick: [index: number] }>()
let hovered: number | null = null

function onAxisPointer(event: unknown) {
  const x = (event as { axesInfo?: { axisDim: string, value: number }[] }).axesInfo?.find(a => a.axisDim === 'x')
  hovered = x ? Number(x.value) : null
}
function onClick() {
  if (hovered !== null) emit('pick', hovered)
}
</script>

<template>
  <v-sheet :height="height" color="transparent" rounded="0">
    <VChart :option="option" autoresize class="w-100 h-100" @update-axis-pointer="onAxisPointer" @zr:click="onClick" />
  </v-sheet>
</template>
