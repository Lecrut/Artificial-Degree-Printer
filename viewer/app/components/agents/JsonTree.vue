<script setup lang="ts">
import { toJsonTree } from '#shared/utils/jsonTree'

const props = defineProps<{ value: unknown }>()
const items = computed(() => toJsonTree(props.value).children ?? [toJsonTree(props.value)])
const COLORS = { string: 'success', number: 'info', boolean: 'warning', null: 'grey', object: undefined, array: undefined } as const
</script>

<template>
  <v-treeview :items="items" item-value="id" density="compact" open-on-click class="bg-transparent">
    <template #title="{ item }">
      <div class="d-flex align-start ga-2 py-1">
        <span class="text-primary text-no-wrap">{{ item.title }}</span>
        <pre v-if="item.value !== null" class="text-pre-wrap text-medium-emphasis ma-0" :class="`text-${COLORS[item.kind]}`">{{ item.value }}</pre>
      </div>
    </template>
  </v-treeview>
</template>
