<script setup lang="ts">
import { mdiFlask, mdiSourceCommit } from '@mdi/js'
import type { ChangelogDay } from '#shared/utils/changelogDays'
import { formatClock } from '#shared/utils/format'
import { labels } from '~/utils/labels'

const props = defineProps<{ day: ChangelogDay }>()
const opened = ref<number | null>(null)
// Short enough for a chip on a phone; the full title is in the tooltip and the dialog.
const headline = (title: string) => {
  const head = title.split(/\s[—(]/)[0]!
  return head.length > 40 ? `${head.slice(0, 38)}…` : head
}
const title = computed(() => labels.changelog.day(props.day.day))
</script>

<template>
  <v-card>
    <v-card-item :title="title" :subtitle="labels.changelog.counts(day.commits.length, day.entries.length)" />
    <v-card-text class="d-flex flex-column ga-4">
      <div v-if="day.commits.length" class="d-flex flex-column ga-1">
        <div v-for="commit in day.commits" :key="commit.sha" class="d-flex flex-wrap align-center ga-2">
          <v-icon :icon="commit.benchmarks ? mdiFlask : mdiSourceCommit" :color="commit.benchmarks ? 'primary' : undefined" size="18" />
          <span class="text-caption text-medium-emphasis">{{ formatClock(commit.date) }}</span>
          <span class="text-body-2 font-weight-medium text-break">{{ commit.message }}</span>
          <v-chip size="x-small">{{ commit.short }}</v-chip>
          <v-chip size="x-small" color="success">+{{ commit.insertions.toLocaleString('pl-PL') }}</v-chip>
          <v-chip size="x-small" color="error">−{{ commit.deletions.toLocaleString('pl-PL') }}</v-chip>
        </div>
      </div>
      <div v-if="day.entries.length" class="d-flex flex-wrap ga-2">
        <v-chip
          v-for="(entry, i) in day.entries"
          :key="entry.id"
          color="secondary"
          variant="tonal"
          link
          :title="entry.title"
          @click="opened = i"
        >
          {{ headline(entry.title) }}
        </v-chip>
      </div>
    </v-card-text>
    <ChangelogAuditDialog v-model="opened" :entries="day.entries" :title="title" />
  </v-card>
</template>
