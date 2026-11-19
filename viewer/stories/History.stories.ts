import type { Meta, StoryObj } from '@storybook/vue3'
import KpiTiles from '../app/components/history/KpiTiles.vue'
import TaskStatusRow from '../app/components/history/TaskStatusRow.vue'
import { VCard, VList } from 'vuetify/components'
import RunHeader from '../app/components/run/RunHeader.vue'
import { summary } from './fixtures'

const meta: Meta = { title: 'History' }
export default meta

export const Kpis: StoryObj = {
  render: () => ({
    components: { KpiTiles },
    setup: () => ({ kpis: { commits: 20, runs: 65, completed: 20, llmCalls: 3448, hours: 19.2 } }),
    template: '<KpiTiles :kpis="kpis" />',
  }),
}

export const TaskRows: StoryObj = {
  render: () => ({
    components: { TaskStatusRow, VCard, VList },
    setup: () => ({ rows: [summary, { ...summary, task: '02_ml_anomaly_detection', status: 'CRASHED', tasksDone: 0, tasksTotal: 0, llmCalls: 1, durationSeconds: 120 }] }),
    template: '<v-card><v-list><TaskStatusRow v-for="r in rows" :key="r.task" :summary="r" to="/" /></v-list></v-card>',
  }),
}

export const RunHeaderCard: StoryObj = {
  render: () => ({
    components: { RunHeader },
    setup: () => ({ summary, at: { source: 'git', ref: '362092f', task: summary.task } }),
    template: '<RunHeader :summary="summary" :at="at" />',
  }),
}
