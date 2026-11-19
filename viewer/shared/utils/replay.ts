import type { Hypergraph } from '../types/hypergraph'
import type { RunEvent } from '../types/run'
import { str } from './events'

const STARTS_AS_STUB = new Set(['code', 'entry'])

/** The state changes of a run, in order: what the replay slider steps through. */
export function stateChanges(events: RunEvent[]): RunEvent[] {
  return events.filter(e => e.event === 'VERTEX_STATE')
}

/** States of the vertices after the first `applied` changes; all of them applied = the saved hypergraph. */
export function statesAt(h: Hypergraph, changes: RunEvent[], applied: number): Record<string, string> {
  if (applied >= changes.length) return Object.fromEntries(Object.entries(h.vertices).map(([id, v]) => [id, v.state]))
  const states: Record<string, string> = Object.fromEntries(
    Object.entries(h.vertices).map(([id, v]) => [id, STARTS_AS_STUB.has(v.kind) ? 'stub' : 'spec']),
  )
  for (const change of changes.slice(0, applied)) states[str(change, 'vertex')] = str(change, 'state')
  return states
}
