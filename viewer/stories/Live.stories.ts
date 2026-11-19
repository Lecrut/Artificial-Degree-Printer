import type { Meta, StoryObj } from '@storybook/vue3'
import TaskBoard from '../app/components/live/TaskBoard.vue'
import { queue, repairingEvents } from './fixtures'

const meta: Meta = { title: 'Live' }
export default meta

export const Board: StoryObj = {
  render: () => ({
    components: { TaskBoard },
    setup: () => ({ queue, events: repairingEvents }),
    template: '<TaskBoard :queue="queue" :events="events" />',
  }),
}
