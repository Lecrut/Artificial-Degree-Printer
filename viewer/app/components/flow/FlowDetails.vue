<script setup lang="ts">
import { mdiClose } from '@mdi/js'
import { FLOW_KIND_COLOR } from '#shared/utils/colors'
import { FLOW_NODES } from '#shared/utils/flow'
import { renderMarkdown } from '#shared/utils/markdown'
import { labels } from '~/utils/labels'

const props = defineProps<{ id: string }>()
defineEmits<{ close: [] }>()

const kind = computed(() => FLOW_NODES.find(node => node.id === props.id)?.kind ?? 'step')
const text = computed(() => labels.flow.nodes[props.id])
const agent = computed(() => (kind.value === 'agent' ? props.id : null))
const { prompt, loading, failed } = useAgentPrompt(agent)
const html = computed(() => (prompt.value ? renderMarkdown(prompt.value.markdown) : ''))
</script>

<template>
  <div class="pa-5 d-flex flex-column ga-4">
    <div class="d-flex align-start ga-3">
      <div class="flex-grow-1">
        <v-chip :color="FLOW_KIND_COLOR[kind]" class="mb-2">{{ labels.flow.kinds[kind] }}</v-chip>
        <div class="text-h6 font-weight-bold">{{ text?.label ?? id }}</div>
      </div>
      <v-btn :icon="mdiClose" :title="labels.flow.details.close" variant="text" @click="$emit('close')" />
    </div>
    <div class="text-body-1">{{ text?.note }}</div>
    <template v-if="agent">
      <v-divider />
      <div class="d-flex align-center ga-2">
        <div class="text-subtitle-1 font-weight-bold flex-grow-1">{{ labels.flow.details.prompt }}</div>
        <CommonCopyButton v-if="prompt" :text="prompt.markdown" />
      </div>
      <div class="text-caption text-medium-emphasis">{{ labels.flow.details.promptHint }}</div>
      <v-skeleton-loader v-if="loading" type="heading, paragraph, paragraph, paragraph" color="transparent" :aria-label="labels.flow.details.loading" />
      <v-alert v-else-if="failed" type="warning" variant="tonal" :text="labels.flow.details.missing" />
      <!-- eslint-disable-next-line vue/no-v-html -- markdown-it runs with html:false, a prompt file cannot inject markup -->
      <div v-else :key="id" v-html="html" />
    </template>
    <div v-else class="text-medium-emphasis">{{ labels.flow.details.noPrompt }}</div>
  </div>
</template>
