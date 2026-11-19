import type { Meta, StoryObj } from '@storybook/vue3'
import { ref } from 'vue'
import { graphElements } from '../shared/utils/graph'
import { VCard } from 'vuetify/components'
import BagDetails from '../app/components/graph/BagDetails.vue'
import GraphLegend from '../app/components/graph/GraphLegend.vue'
import HypergraphCanvas from '../app/components/graph/HypergraphCanvas.vue'
import IncidenceMatrix from '../app/components/graph/IncidenceMatrix.vue'
import VertexDetails from '../app/components/graph/VertexDetails.vue'
import { hypergraph, states } from './fixtures'

const meta: Meta = { title: 'Graph' }
export default meta

export const Canvas: StoryObj = {
  render: () => ({
    components: { HypergraphCanvas, GraphLegend },
    setup: () => ({ elements: graphElements(hypergraph, states), selected: ref(null) }),
    template: '<div class="d-flex flex-column ga-4"><GraphLegend /><HypergraphCanvas v-model="selected" :elements="elements" /></div>',
  }),
}

export const Matrix: StoryObj = {
  render: () => ({
    components: { IncidenceMatrix },
    setup: () => ({ hypergraph, states, selected: ref(null) }),
    template: '<IncidenceMatrix v-model="selected" :hypergraph="hypergraph" :states="states" />',
  }),
}

export const Vertex: StoryObj = {
  render: () => ({
    components: { VertexDetails, VCard },
    setup: () => ({ hypergraph }),
    template: '<v-card class="pa-4" max-width="520"><VertexDetails :hypergraph="hypergraph" id="qagent.py" /></v-card>',
  }),
}

export const Bag: StoryObj = {
  render: () => ({
    components: { BagDetails, VCard },
    setup: () => ({ hypergraph, states }),
    template: '<v-card class="pa-4" max-width="520"><BagDetails :hypergraph="hypergraph" :states="states" id="I:qagent.py" /></v-card>',
  }),
}
