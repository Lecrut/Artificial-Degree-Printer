<script setup lang="ts">
import { mdiFilePdfBox, mdiImageMultipleOutline, mdiImageOutline } from '@mdi/js'
import { labels } from '~/utils/labels'

const props = defineProps<{ figures: { path: string, url: string }[], pdf: string | null }>()
const zoomed = ref<number | null>(null)
const { open, current: figure, move } = useListDialog(zoomed, () => props.figures)
const name = (path: string) => path.split('/').at(-1)
</script>

<template>
  <v-card>
    <v-card-item :title="labels.thesis.figures" :prepend-icon="mdiImageMultipleOutline">
      <template #append>
        <v-btn v-if="pdf" :href="pdf" target="_blank" :prepend-icon="mdiFilePdfBox" color="primary" variant="flat">PDF</v-btn>
      </template>
    </v-card-item>
    <v-card-text>
      <v-row v-if="figures.length" density="compact">
        <v-col v-for="(item, i) in figures" :key="item.path" cols="6">
          <CommonHoverCard color="surface-bright" @click="zoomed = i">
            <v-img :src="item.url" aspect-ratio="1.4" cover />
            <v-card-subtitle class="py-2 text-truncate">{{ name(item.path) }}</v-card-subtitle>
          </CommonHoverCard>
        </v-col>
      </v-row>
      <div v-else class="text-medium-emphasis">{{ labels.thesis.noFigures }}</div>
    </v-card-text>
    <CommonBrowseDialog
      v-model="open"
      :position="zoomed ?? 0"
      :total="figures.length"
      :title="figure ? name(figure.path) : ''"
      :icon="mdiImageOutline"
      :max-width="1200"
      min-height="auto"
      @move="move"
    >
      <v-fade-transition mode="out-in">
        <v-img v-if="figure" :key="figure.url" :src="figure.url" max-height="72vh" />
      </v-fade-transition>
    </CommonBrowseDialog>
  </v-card>
</template>
