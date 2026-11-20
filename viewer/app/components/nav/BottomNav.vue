<script setup lang="ts">

// On a phone the pages sit under the thumb, with an icon and a short name each.
const pages = useNavPages()
</script>

<template>
  <v-bottom-navigation grow color="primary" bg-color="surface" border="t" height="64">
    <v-btn v-for="page in pages" :key="page.to" :to="page.to" :exact="page.exact" :prepend-icon="page.icon" stacked :text="page.title" size="small" />
  </v-bottom-navigation>
</template>
