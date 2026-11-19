<script setup lang="ts">
// The shape of a page while its data loads: a row of tiles, then a large card, shimmering.
withDefaults(defineProps<{ tiles?: number }>(), { tiles: 4 })
</script>

<template>
  <div class="d-flex flex-column ga-6">
    <v-row v-if="tiles">
      <v-col v-for="n in tiles" :key="n" cols="12" sm="6" md>
        <v-skeleton-loader type="list-item-avatar-two-line" color="surface" class="rounded-xl" />
      </v-col>
    </v-row>
    <v-skeleton-loader type="heading, list-item-two-line, list-item-two-line, list-item-two-line, list-item-two-line" color="surface" class="rounded-xl pa-4" />
  </div>
</template>
