<script setup lang="ts">
import { mdiCodeBraces, mdiNumeric } from '@mdi/js'
import { labels } from '~/utils/labels'

defineProps<{ html: string, loading: boolean, hasCompiled: boolean }>()
const compiled = defineModel<boolean>({ required: true })
</script>

<template>
  <v-card>
    <v-card-item :title="labels.thesis.title">
      <template #append>
        <v-btn-toggle v-model="compiled" mandatory color="primary" variant="outlined" density="compact" divided>
          <v-btn :value="false" :prepend-icon="mdiCodeBraces" :text="labels.thesis.pointers" />
          <v-btn :value="true" :prepend-icon="mdiNumeric" :text="labels.thesis.values" :disabled="!hasCompiled" />
        </v-btn-toggle>
      </template>
    </v-card-item>
    <v-divider />
    <v-progress-linear v-if="loading" indeterminate color="primary" />
    <v-card-text class="px-8 py-6">
      <v-fade-transition mode="out-in">
        <!-- eslint-disable-next-line vue/no-v-html -- markdown-it runs with html:false, the source cannot inject markup -->
        <div v-if="html" :key="String(compiled)" v-html="html" />
        <v-skeleton-loader v-else-if="loading" type="heading, paragraph, paragraph, paragraph" color="transparent" />
        <div v-else class="text-medium-emphasis">{{ labels.thesis.empty }}</div>
      </v-fade-transition>
    </v-card-text>
  </v-card>
</template>
