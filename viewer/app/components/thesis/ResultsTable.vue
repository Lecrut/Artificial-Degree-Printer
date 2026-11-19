<script setup lang="ts">
import { mdiTableEye } from '@mdi/js'
import { labels } from '~/utils/labels'

const props = defineProps<{ headers: string[], rows: Record<string, string>[], loading: boolean }>()
const columns = computed(() => props.headers.map(h => ({ title: h, key: h })))
</script>

<template>
  <v-card>
    <v-card-item :title="labels.thesis.results" :prepend-icon="mdiTableEye" :subtitle="labels.thesis.rows(rows.length)" />
    <v-data-table v-if="rows.length" :headers="columns" :items="rows" density="compact" :items-per-page="10" class="bg-transparent">
      <template v-for="h in headers" :key="h" #[`item.${h}`]="{ value }">
        <span :class="Number.isFinite(Number(value)) && value !== '' ? 'text-primary font-weight-medium' : ''">{{ value }}</span>
      </template>
    </v-data-table>
    <v-skeleton-loader v-else-if="loading" type="table-tbody" color="transparent" />
    <v-card-text v-else class="text-medium-emphasis">{{ labels.thesis.noResults }}</v-card-text>
  </v-card>
</template>
