<script setup lang="ts">
import { runStatusColor } from '#shared/utils/states'
import { runStatusIcon } from '~/utils/icons'

defineProps<{ status: string }>()
</script>

<template>
  <v-chip :color="runStatusColor(status)" :prepend-icon="runStatusIcon(status)" variant="flat">
    {{ status }}
  </v-chip>
</template>
