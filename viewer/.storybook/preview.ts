import type { Preview } from '@storybook/vue3'
import { VApp, VContainer, VMain } from 'vuetify/components'

// Every story sits inside a dark v-app, the same shell the viewer pages use. Vuetify is tree-shaken,
// so string templates (here and in stories) import the Vuetify components they use.
const preview: Preview = {
  decorators: [() => ({ components: { VApp, VMain, VContainer }, template: '<v-app><v-main><v-container class="pa-6"><story /></v-container></v-main></v-app>' })],
  parameters: { layout: 'fullscreen', backgrounds: { disable: true } },
}

export default preview
