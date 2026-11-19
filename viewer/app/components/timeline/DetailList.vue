<script setup lang="ts">
import type { DetailLine } from '#shared/types/timeline'
import { entryStatusColor } from '#shared/utils/colors'

defineProps<{ details: DetailLine[] }>()
</script>

<template>
  <v-list density="compact" class="py-0 bg-transparent">
    <v-list-item v-for="(detail, i) in details" :key="i" class="px-0">
      <template #prepend>
        <v-chip :color="entryStatusColor(detail.status)" class="me-3">{{ detail.label }}</v-chip>
      </template>
      <div class="text-body-2 text-pre-wrap">{{ detail.text }}</div>
    </v-list-item>
  </v-list>
</template>
