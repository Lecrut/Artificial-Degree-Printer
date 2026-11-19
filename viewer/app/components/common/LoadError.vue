<script setup lang="ts">
import { mdiCloudAlertOutline, mdiRefresh } from '@mdi/js'
import { labels } from '~/utils/labels'

// A failed request says so, instead of looking like "no data"; one click asks again.
defineProps<{ message?: string }>()
const emit = defineEmits<{ retry: [] }>()
</script>

<template>
  <v-alert type="error" variant="tonal" :icon="mdiCloudAlertOutline" :title="message ?? labels.common.loadError" :text="labels.common.loadErrorHint">
    <template #append>
      <v-btn :prepend-icon="mdiRefresh" color="error" variant="flat" :text="labels.common.retry" @click="emit('retry')" />
    </template>
  </v-alert>
</template>
