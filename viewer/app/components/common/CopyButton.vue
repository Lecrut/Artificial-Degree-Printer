<script setup lang="ts">
import { mdiCheck, mdiContentCopy } from '@mdi/js'
import { labels } from '~/utils/labels'

const props = defineProps<{ text: string }>()
const copied = ref(false)

async function copy() {
  try {
    await navigator.clipboard.writeText(props.text)
    copied.value = true
    setTimeout(() => { copied.value = false }, 1500)
  }
  catch {
    copied.value = false
  }
}
</script>

<template>
  <v-btn
    :icon="copied ? mdiCheck : mdiContentCopy"
    :color="copied ? 'success' : undefined"
    :title="labels.common.copy"
    size="small"
    variant="tonal"
    @click="copy"
  />
</template>
