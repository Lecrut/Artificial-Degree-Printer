<script setup lang="ts">
import { mdiBookOpenPageVariantOutline, mdiFileMultipleOutline, mdiSourceCommit } from '@mdi/js'
import type { AuditEntry, CommitInfo } from '#shared/types/changelog'
import type { CommitSummary } from '#shared/types/run'
import { formatDate } from '#shared/utils/format'
import { labels } from '~/utils/labels'
import { runPage } from '~/utils/runUrls'

const props = defineProps<{ commit: CommitSummary, info?: CommitInfo, audit: AuditEntry[] }>()
const opened = ref<number | null>(null)
const link = (task: string) => runPage({ source: 'git', ref: props.commit.sha, task })
</script>

<template>
  <CommonHoverCard height="100%">
    <v-card-item :prepend-icon="mdiSourceCommit" :title="commit.message" :subtitle="`${formatDate(commit.date)} · ${commit.short}`">
      <template #append>
        <div class="d-flex flex-wrap justify-end ga-1">
          <v-chip v-if="info" :prepend-icon="mdiFileMultipleOutline" size="x-small">{{ info.files }}</v-chip>
          <v-chip v-if="info" color="success" size="x-small">+{{ info.insertions.toLocaleString('pl-PL') }}</v-chip>
          <v-chip v-if="info" color="error" size="x-small">−{{ info.deletions.toLocaleString('pl-PL') }}</v-chip>
        </div>
      </template>
    </v-card-item>
    <v-list density="compact" class="py-0 bg-transparent">
      <HistoryTaskStatusRow v-for="summary in commit.tasks" :key="summary.task" :summary="summary" :to="link(summary.task)" />
    </v-list>
    <template v-if="audit.length">
      <v-divider />
      <v-card-text class="d-flex flex-wrap align-center ga-1 py-3">
        <v-icon :icon="mdiBookOpenPageVariantOutline" size="18" color="secondary" class="me-1" />
        <span class="text-caption text-medium-emphasis me-1">{{ labels.history.auditAt }}</span>
        <v-chip
          v-for="(entry, i) in audit.slice(0, 6)"
          :key="entry.id"
          color="secondary"
          size="x-small"
          link
          :title="entry.title"
          @click="opened = i"
        >
          {{ entry.title.split(/[.:—]/)[0] }}
        </v-chip>
        <v-chip v-if="audit.length > 6" size="x-small" link @click="opened = 6">+{{ audit.length - 6 }}</v-chip>
      </v-card-text>
    </template>
    <ChangelogAuditDialog v-model="opened" :entries="audit" :title="commit.message" />
  </CommonHoverCard>
</template>
