import type { Hypergraph } from '../types/hypergraph'
import { bagLabel } from './graph'

export interface IncidenceRow {
  id: string
  kind: string
  bags: number
}

export interface IncidenceColumn {
  id: string
  type: string
  label: string
  size: number
}

export interface IncidenceCell {
  role: string
  observed: boolean
}

export interface IncidenceMatrix {
  rows: IncidenceRow[]
  columns: IncidenceColumn[]
  cells: Record<string, Record<string, IncidenceCell>>
}

const KIND_ORDER = ['entry', 'code', 'test', 'data', 'figure', 'bib', 'research', 'chapter']
const TYPE_ORDER = ['I', 'R', 'N']

/** H as a map: one row per vertex, one column per bag (hyperedge), the role where a vertex is a member. */
export function incidenceMatrix(h: Hypergraph): IncidenceMatrix {
  const cells: IncidenceMatrix['cells'] = {}
  for (const [edgeId, edge] of Object.entries(h.edges)) {
    for (const [member, role] of Object.entries(edge.members)) {
      cells[member] ??= {}
      cells[member][edgeId] = { role, observed: edge.observed.includes(member) }
    }
  }
  const rows = Object.entries(h.vertices)
    .map(([id, v]) => ({ id, kind: v.kind, bags: Object.keys(cells[id] ?? {}).length }))
    .sort((a, b) => KIND_ORDER.indexOf(a.kind) - KIND_ORDER.indexOf(b.kind) || a.id.localeCompare(b.id))
  const columns = Object.entries(h.edges)
    .map(([id, e]) => ({ id, type: e.type, label: bagLabel(id), size: Object.keys(e.members).length }))
    .sort((a, b) => TYPE_ORDER.indexOf(a.type) - TYPE_ORDER.indexOf(b.type) || a.id.localeCompare(b.id))
  return { rows, columns, cells }
}
