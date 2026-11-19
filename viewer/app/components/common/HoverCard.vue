<script setup lang="ts">
// A card that answers the mouse with a colored border; a shadow is invisible on the navy theme.
// The card itself is the root element, so the card can sit inside transition groups (the live board).
withDefaults(defineProps<{ accent?: string }>(), { accent: 'primary' })
const hovering = ref(false)
</script>

<template>
  <v-card :border="hovering ? `sm ${accent} opacity-75` : true" @mouseenter="hovering = true" @mouseleave="hovering = false">
    <slot />
  </v-card>
</template>
