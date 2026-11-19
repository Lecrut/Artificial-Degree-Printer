<script setup lang="ts">
import { mdiBookOpenPageVariantOutline } from '@mdi/js'
import type { AuditEntry } from '#shared/types/changelog'
import { renderThesis } from '#shared/utils/markdown'

const props = defineProps<{ entries: AuditEntry[], title: string }>()
const index = defineModel<number | null>({ required: true })
const { open, current: entry, move } = useListDialog(index, () => props.entries)
const html = computed(() => (entry.value ? renderThesis(entry.value.body) : ''))
</script>

<template>
  <CommonBrowseDialog
    v-model="open"
    :position="index ?? 0"
    :total="entries.length"
    :title="entry?.title"
    :subtitle="entry ? `${title} · ${entry.date}` : ''"
    :icon="mdiBookOpenPageVariantOutline"
    color="secondary"
    :max-width="1000"
    min-height="60vh"
    @move="move"
  >
    <v-fade-transition mode="out-in">
      <!-- eslint-disable-next-line vue/no-v-html -- markdown-it runs with html:false -->
      <div v-if="entry" :key="entry.id" class="px-4 py-2" v-html="html" />
    </v-fade-transition>
  </CommonBrowseDialog>
</template>
