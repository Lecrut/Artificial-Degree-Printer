/** Vuetify theme colors for the states of runs, tasks and vertices. */
export type StateColor = 'success' | 'error' | 'warning' | 'info' | 'primary' | 'secondary' | 'grey'

const RUN_STATUS: Record<string, StateColor> = {
  COMPLETED: 'success',
  COMPLETED_WITH_GAPS: 'warning',
  RUNNING: 'info',
}

export function runStatusColor(status: string): StateColor {
  return RUN_STATUS[status] ?? 'error'
}

const VERTEX_STATE: Record<string, StateColor> = {
  spec: 'grey',
  stub: 'secondary',
  impl: 'info',
  written: 'info',
  drafted: 'info',
  verified: 'success',
  stale: 'warning',
  failed: 'error',
}

export function vertexStateColor(state: string): StateColor {
  return VERTEX_STATE[state] ?? 'grey'
}
