<script setup lang="ts">
defineProps<{ title: string, subtitle?: string, icon: string }>()
</script>

<template>
  <div class="d-flex flex-wrap align-center ga-4 mb-2">
    <v-avatar color="primary" variant="tonal" rounded="xl" size="56">
      <v-icon :icon="icon" size="30" />
    </v-avatar>
    <div class="flex-grow-1">
      <div class="text-h4 font-weight-bold">{{ title }}</div>
      <div v-if="subtitle" class="text-body-1 text-medium-emphasis">{{ subtitle }}</div>
    </div>
    <slot name="actions" />
  </div>
</template>
