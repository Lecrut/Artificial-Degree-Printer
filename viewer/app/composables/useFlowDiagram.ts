import type { Core } from 'cytoscape'
import type { FlowEdgeLabel } from '#shared/types/flow'
import { flowBounds, flowElements } from '#shared/utils/flow'
import { labels } from '~/utils/labels'

// Narrower than this the diagram scrolls sideways inside its frame instead of shrinking to unreadable.
const MIN_WIDTH = 1100
const PADDING = 24

const texts = {
  node: (id: string) => labels.flow.nodes[id]?.label ?? id,
  edge: (label: string) => labels.flow.edges[label as FlowEdgeLabel] ?? label,
}

/** A tap on a block selects it, a tap on the background clears the selection; the pointer shows what can be tapped. */
function listen(cy: Core, canvas: HTMLElement, selected: Ref<string | null>) {
  cy.on('tap', 'node', (event) => { selected.value = event.target.id() })
  cy.on('tap', (event) => { if (event.target === cy) selected.value = null })
  cy.on('mouseover', 'node', (event) => { event.target.addClass('hovered'); canvas.style.cursor = 'pointer' })
  cy.on('mouseout', 'node', (event) => { event.target.removeClass('hovered'); canvas.style.cursor = '' })
}

/**
 * The flow diagram in `canvas`: blocks at the positions of the grid (no automatic layout), a tap selects a block.
 * `frame` is the scrolling box around the canvas; the canvas takes its width (not less than MIN_WIDTH) and the height of the diagram's proportions.
 */
export function useFlowDiagram(frame: Ref<HTMLElement | null>, canvas: Ref<HTMLElement | null>, selected: Ref<string | null>) {
  const style = useFlowStyle()
  const bounds = flowBounds()
  const width = ref(MIN_WIDTH)
  const height = computed(() => Math.round(((width.value - 2 * PADDING) * bounds.height) / bounds.width + 2 * PADDING))
  let cy: Core | null = null

  const refit = () => {
    width.value = Math.max(frame.value?.clientWidth ?? MIN_WIDTH, MIN_WIDTH)
    void nextTick(() => { cy?.resize(); cy?.fit(undefined, PADDING) })
  }

  async function build() {
    const { default: cytoscape } = await import('cytoscape')
    const elements = flowElements(texts)
    cy = cytoscape({
      container: canvas.value,
      elements: [...elements.nodes.map(node => ({ group: 'nodes' as const, ...node })), ...elements.edges.map(edge => ({ group: 'edges' as const, ...edge }))],
      style: style.value,
      layout: { name: 'preset', fit: true, padding: PADDING },
      userZoomingEnabled: false,
      userPanningEnabled: false,
      boxSelectionEnabled: false,
      autoungrabify: true,
    })
    listen(cy, canvas.value!, selected)
  }

  watch(selected, (id) => {
    cy?.elements().unselect()
    if (id) cy?.getElementById(id).select()
  })
  watch(style, next => cy?.style(next))
  onMounted(async () => {
    width.value = Math.max(frame.value?.clientWidth ?? MIN_WIDTH, MIN_WIDTH)
    await nextTick()
    await build()
    refit()
    window.addEventListener('resize', refit)
  })
  onBeforeUnmount(() => { window.removeEventListener('resize', refit); cy?.destroy() })

  return { width, height }
}
