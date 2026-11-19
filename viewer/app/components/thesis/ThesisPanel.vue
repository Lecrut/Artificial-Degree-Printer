<script setup lang="ts">
import type { RunFiles, RunRef } from '#shared/types/run'

const props = defineProps<{ at: RunRef, files: RunFiles }>()
const { compiled, html, results, figures, pdf, pending, error, refresh, hasCompiled } = useThesis(() => props.at, () => props.files)
</script>

<template>
  <CommonLoadError v-if="error" @retry="refresh()" />
  <v-row v-else>
    <v-col cols="12" lg="8">
      <ThesisDocument v-model="compiled" :html="html" :loading="pending" :has-compiled="hasCompiled" />
    </v-col>
    <v-col cols="12" lg="4" class="d-flex flex-column ga-4">
      <ThesisFigureGallery :figures="figures" :pdf="pdf" />
      <ThesisResultsTable :headers="results.headers" :rows="results.rows" :loading="pending" />
    </v-col>
  </v-row>
</template>
