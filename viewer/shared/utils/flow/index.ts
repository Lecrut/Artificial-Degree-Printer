import type { FlowKind } from '#shared/types/flow'
import { FLOW_EDGES } from './edges'
import { FLOW_NODES } from './nodes'

export { FLOW_EDGES, FLOW_NODES }

// The grid in pixels of the canvas; the blocks are narrower than a column and lower than a row.
export const COL_W = 270
export const ROW_H = 120

/** Size of a block per kind, so the diagram is drawn from one table. */
export const BLOCK_SIZE: Record<FlowKind, { w: number, h: number }> = {
  start: { w: 200, h: 48 },
  end: { w: 220, h: 48 },
  step: { w: 230, h: 56 },
  agent: { w: 210, h: 52 },
  decision: { w: 250, h: 100 },
  jump: { w: 215, h: 34 },
}

/** The agents on the diagram: the names of their prompt files. */
export const FLOW_AGENTS = FLOW_NODES.filter(node => node.kind === 'agent').map(node => node.id)

export interface FlowTexts {
  node: (id: string) => string
  edge: (label: string) => string
}

export interface FlowElements {
  nodes: Array<{ data: { id: string, kind: FlowKind, label: string, w: number, h: number }, position: { x: number, y: number } }>
  edges: Array<{ data: { id: string, source: string, target: string, label: string } }>
}

/** Cytoscape data for the diagram: positions from the grid, texts from the caller. */
export function flowElements(texts: FlowTexts): FlowElements {
  return {
    nodes: FLOW_NODES.map(({ id, kind, col, row }) => ({
      data: { id, kind, label: texts.node(id), ...BLOCK_SIZE[kind] },
      position: { x: col * COL_W, y: row * ROW_H },
    })),
    edges: FLOW_EDGES.map(({ from, to, label }, i) => ({
      data: { id: `e${i}`, source: from, target: to, label: label ? texts.edge(label) : '' },
    })),
  }
}

/** Width and height of the whole diagram, to give its canvas the right proportions. */
export function flowBounds(): { width: number, height: number } {
  const cols = FLOW_NODES.map(node => node.col)
  const rows = FLOW_NODES.map(node => node.row)
  const widest = Math.max(...Object.values(BLOCK_SIZE).map(size => size.w))
  const tallest = Math.max(...Object.values(BLOCK_SIZE).map(size => size.h))
  return {
    width: (Math.max(...cols) - Math.min(...cols)) * COL_W + widest,
    height: (Math.max(...rows) - Math.min(...rows)) * ROW_H + tallest,
  }
}
