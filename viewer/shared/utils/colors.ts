import type { EntryStatus } from '../types/timeline'
import type { StateColor } from './states'

const ENTRY: Record<EntryStatus, StateColor> = {
  ok: 'success',
  fail: 'error',
  warn: 'warning',
  info: 'info',
  running: 'primary',
  waiting: 'grey',
}

export function entryStatusColor(status: EntryStatus): StateColor {
  return ENTRY[status]
}

/** PASS / FAIL of a critic; anything else (none, PARTIAL) stays neutral. */
export function verdictColor(verdict: string | null | undefined): StateColor | undefined {
  return verdict === 'PASS' ? 'success' : verdict === 'FAIL' ? 'error' : undefined
}

/** The large reasoning model stands out from the small model that does most of the work. */
export function tierColor(tier: string): StateColor {
  return tier === 'LRM' ? 'secondary' : 'primary'
}

const QUEUE: Record<string, StateColor> = { TODO: 'grey', WAITING: 'warning', IN_PROGRESS: 'primary', DONE: 'success', FAILED: 'error' }

/** Color of a task_queue.json status (a board column). */
export function queueStatusColor(status: string): StateColor {
  return QUEUE[status] ?? 'grey'
}
