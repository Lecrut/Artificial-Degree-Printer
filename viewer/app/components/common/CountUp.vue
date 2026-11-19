<script setup lang="ts">
// A figure that counts up to its value when it appears or changes.
const props = withDefaults(defineProps<{ value: number | null, format?: (n: number) => string }>(), {
  format: (n: number) => Math.round(n).toLocaleString('pl-PL'),
})
const shown = useCountUp(() => props.value ?? 0)
</script>

<template>
  <span>{{ value === null ? '—' : format(shown) }}</span>
</template>
