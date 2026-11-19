import type { Meta, StoryObj } from '@storybook/vue3'
import { mdiHistory } from '@mdi/js'
import StatusChip from '../app/components/common/StatusChip.vue'
import PageHeader from '../app/components/common/PageHeader.vue'

const meta: Meta = { title: 'Common' }
export default meta

export const StatusChips: StoryObj = {
  render: () => ({
    components: { StatusChip },
    setup: () => ({ statuses: ['COMPLETED', 'COMPLETED_WITH_GAPS', 'CRASHED', 'HITL_PAUSED', 'NO_EVENTS', 'RUNNING'] }),
    template: '<div class="d-flex flex-wrap ga-2"><StatusChip v-for="s in statuses" :key="s" :status="s" /></div>',
  }),
}

export const Header: StoryObj = {
  render: () => ({
    components: { PageHeader },
    setup: () => ({ icon: mdiHistory }),
    template: '<PageHeader :icon="icon" title="Historia benchmarków" subtitle="wszystkie przebiegi zapisane w commitach" />',
  }),
}
