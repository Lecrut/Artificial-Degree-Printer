<script setup lang="ts">
import { mdiBookOpenPageVariantOutline, mdiMagnify } from '@mdi/js'
import { changelogDays } from '#shared/utils/changelogDays'
import { labels } from '~/utils/labels'

const { data, pending, error, refresh } = useChangelog()
const search = ref('')
const days = computed(() => changelogDays(data.value, search.value))
</script>

<template>
  <div class="d-flex flex-column ga-6">
    <CommonPageHeader :icon="mdiBookOpenPageVariantOutline" :title="labels.changelog.title" :subtitle="labels.changelog.subtitle">
      <template #actions>
        <v-text-field v-model="search" :placeholder="labels.changelog.search" :prepend-inner-icon="mdiMagnify" clearable hide-details min-width="320" />
      </template>
    </CommonPageHeader>
    <CommonPageSkeleton v-if="pending" :tiles="0" />
    <CommonLoadError v-else-if="error" @retry="refresh()" />
    <v-timeline side="end" align="start" truncate-line="both" line-color="surface-variant">
      <v-slide-y-transition group>
        <v-timeline-item v-for="day in days" :key="day.day" :dot-color="day.commits.some(c => c.benchmarks) ? 'primary' : 'secondary'" size="small" fill-dot>
          <template #opposite>
            <div class="text-h6 font-weight-bold text-no-wrap">{{ day.day.slice(5) }}</div>
          </template>
          <ChangelogDay :day="day" />
        </v-timeline-item>
      </v-slide-y-transition>
    </v-timeline>
  </div>
</template>
