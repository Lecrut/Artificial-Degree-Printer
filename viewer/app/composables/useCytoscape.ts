import type { Core, ElementDefinition } from 'cytoscape'
import type { GraphElements } from '#shared/utils/graph'

function definitions(elements: GraphElements): ElementDefinition[] {
  return [
    ...elements.nodes.map(node => ({ group: 'nodes' as const, data: { ...node } })),
    ...elements.links.map(link => ({ group: 'edges' as const, data: { ...link } })),
  ]
}

const LAYOUT_DELAY_MS = 320

const sameShape = (cy: Core, elements: GraphElements) =>
  cy.nodes().length === elements.nodes.length && elements.nodes.every(n => cy.getElementById(n.id).nonempty())

/** Fade everything but the selected element, its bags or members, and the links between them. */
function highlight(cy: Core, id: string | null) {
  cy.elements().removeClass('faded highlighted')
  const node = id ? cy.getElementById(id) : null
  if (!node?.nonempty()) return
  const near = node.closedNeighborhood()
  cy.elements().not(near).addClass('faded')
  near.addClass('highlighted')
}

/** A Cytoscape instance in `container`: built once, then only node data and the highlight change. */
export function useCytoscape(container: Ref<HTMLElement | null>, elements: Ref<GraphElements>, selected: Ref<string | null>) {
  const style = useGraphStyle()
  const stillMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  let cy: Core | null = null

  async function build() {
    const { default: cytoscape } = await import('cytoscape')
    cy?.destroy()
    cy = cytoscape({
      container: container.value,
      elements: definitions(elements.value),
      style: style.value,
      layout: { name: 'cose', animate: false, nodeRepulsion: () => 9000, idealEdgeLength: () => 70, padding: 24 },
    })
    cy.on('tap', 'node', (event) => { selected.value = event.target.id() })
    cy.on('tap', (event) => { if (event.target === cy) selected.value = null })
    cy.on('mouseover', 'node', (event) => { event.target.addClass('hovered'); container.value!.style.cursor = 'pointer' })
    cy.on('mouseout', 'node', (event) => { event.target.removeClass('hovered'); container.value!.style.cursor = '' })
    highlight(cy, selected.value)
  }

  watch(elements, (next) => {
    if (!cy || !sameShape(cy, next)) return void build()
    const changed = next.nodes.map(node => cy!.getElementById(node.id)).filter((el, i) => el.data('state') !== next.nodes[i]!.state)
    cy.batch(() => next.nodes.forEach(node => cy!.getElementById(node.id).data('state', node.state)))
    if (!stillMotion) changed.forEach(el => el.flashClass('changed', 650))
  })
  watch(selected, id => cy && highlight(cy, id))
  watch(style, next => cy?.style(next))
  // The layout blocks for ~150 ms: it runs after the tab's slide-in, not during it.
  let delayed: ReturnType<typeof setTimeout> | undefined
  onMounted(() => { delayed = setTimeout(build, LAYOUT_DELAY_MS) })
  onBeforeUnmount(() => { clearTimeout(delayed); cy?.destroy() })

  return { fit: () => cy?.animate({ fit: { eles: cy.elements(), padding: 24 } }, { duration: 300 }) }
}
