import type { Hypergraph } from '../types/hypergraph'

export interface GraphNode {
  id: string
  label: string
  group: 'vertex' | 'bag' | 'helper'
  kind: string
  state: string
}

export interface GraphLink {
  id: string
  source: string
  target: string
  label: string
  group: 'member' | 'order' | 'helper'
  observed: boolean
}

export interface GraphElements {
  nodes: GraphNode[]
  links: GraphLink[]
}

/** Short name of a vertex: `tests/test_core.py` → `test_core.py`, `thesis.md#ch3` → `rozdz. 3`. */
export function vertexLabel(id: string): string {
  const chapter = /#ch(\d+)$/.exec(id)
  return chapter ? `rozdz. ${chapter[1]}` : id.split('/').at(-1) ?? id
}

export function bagLabel(id: string): string {
  const [type, name = ''] = id.split(':')
  return `${type} ${vertexLabel(name)}`
}

/** H drawn as a bipartite graph: vertices, bags (hyperedges) as their own nodes, members linked with their role. */
export function graphElements(h: Hypergraph, states: Record<string, string>): GraphElements {
  const nodes: GraphNode[] = Object.entries(h.vertices).map(([id, v]) => ({
    id: `v:${id}`, label: vertexLabel(id), group: 'vertex', kind: v.kind, state: states[id] ?? v.state,
  }))
  const links: GraphLink[] = []
  for (const [id, edge] of Object.entries(h.edges)) {
    nodes.push({ id: `e:${id}`, label: bagLabel(id), group: 'bag', kind: edge.type, state: '' })
    for (const [member, role] of Object.entries(edge.members)) {
      links.push({ id: `m:${id}:${member}`, source: `e:${id}`, target: `v:${member}`, label: role, group: 'member', observed: edge.observed.includes(member) })
    }
  }
  for (const [from, to] of h.order) {
    links.push({ id: `o:${from}>${to}`, source: `e:${from}`, target: `e:${to}`, label: '', group: 'order', observed: false })
  }
  for (const [id, v] of Object.entries(h.vertices)) {
    for (const file of v.files) {
      nodes.push({ id: `f:${file}`, label: vertexLabel(file), group: 'helper', kind: 'helper', state: states[id] ?? v.state })
      links.push({ id: `h:${file}`, source: `v:${id}`, target: `f:${file}`, label: 'plik', group: 'helper', observed: true })
    }
  }
  return { nodes, links }
}
