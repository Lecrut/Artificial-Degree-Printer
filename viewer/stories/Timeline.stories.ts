import type { Meta, StoryObj } from '@storybook/vue3'
import { ref } from 'vue'
import { VCard } from 'vuetify/components'
import EntryDialog from '../app/components/timeline/EntryDialog.vue'
import PhaseStrip from '../app/components/timeline/PhaseStrip.vue'
import TaskAttempts from '../app/components/timeline/TaskAttempts.vue'
import TimelineEntryCard from '../app/components/timeline/TimelineEntryCard.vue'
import { timeline } from './fixtures'

const meta: Meta = { title: 'Timeline' }
export default meta

// One entry of each kind and status, the variety a real run has.
const samples = timeline.entries.filter((e, i, all) => all.findIndex(o => o.kind === e.kind && o.status === e.status) === i)
const busiest = timeline.entries.reduce((a, b) => (b.attempts.length > a.attempts.length ? b : a))

export const Phases: StoryObj = {
  render: () => ({
    components: { PhaseStrip, VCard },
    setup: () => ({ phases: timeline.phases, selected: ref(null) }),
    template: '<v-card class="pa-4"><PhaseStrip v-model="selected" :phases="phases" /></v-card>',
  }),
}

export const EntryCards: StoryObj = {
  render: () => ({
    components: { TimelineEntryCard },
    setup: () => ({ samples }),
    template: '<div class="d-flex flex-column ga-3"><TimelineEntryCard v-for="e in samples" :key="e.id" :entry="e" /></div>',
  }),
}

export const Attempts: StoryObj = {
  render: () => ({
    components: { TaskAttempts, VCard },
    setup: () => ({ attempts: busiest.attempts.slice(0, 8) }),
    template: '<v-card class="pa-4"><TaskAttempts :attempts="attempts" /></v-card>',
  }),
}

export const Dialog: StoryObj = {
  render: () => ({
    components: { EntryDialog },
    setup: () => ({ entries: timeline.entries, index: ref(timeline.entries.indexOf(busiest)) }),
    template: '<EntryDialog v-model="index" :entries="entries" />',
  }),
}
