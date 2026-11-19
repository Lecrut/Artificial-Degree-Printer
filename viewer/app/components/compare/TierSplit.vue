<script setup lang="ts">
import { mdiChip } from '@mdi/js'
import type { ComparedRun } from '#shared/types/compare'
import { TIER_COLORS } from '#shared/utils/compare'
import { groupedBars } from '~/utils/chartOptions'
import { labels } from '~/utils/labels'

const props = defineProps<{ runs: ComparedRun[] }>()
const ink = useChartInk()

const option = computed(() => groupedBars(
  ink.value,
  props.runs.map(r => r.label),
  Object.entries(TIER_COLORS).map(([tier, color]) => ({ name: tier, color, values: props.runs.map(r => (r.profile.tierSeconds[tier] ?? 0) / 60) })),
  v => `${v.toFixed(0)} min`,
  true,
))
</script>

<template>
  <v-card>
    <v-card-item :title="labels.compare.tiers" :subtitle="labels.compare.tiersHint" :prepend-icon="mdiChip" />
    <v-card-text><CommonChart :option="option" :height="Math.max(200, 80 + runs.length * 44)" /></v-card-text>
  </v-card>
</template>
