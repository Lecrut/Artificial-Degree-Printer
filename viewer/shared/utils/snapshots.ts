import type { RunEvent } from '../types/run'
import { num, str } from './events'

/** The state of a run saved after a finished task (`SNAPSHOT_SAVED`): a point a new run can continue from. */
export interface Snapshot {
  file: string
  taskId: string
  ts: string
  verified: number
  failed: number
  vertices: number
}

export function snapshots(events: RunEvent[]): Snapshot[] {
  return events.filter(e => e.event === 'SNAPSHOT_SAVED').map(e => ({
    file: str(e, 'file'),
    taskId: str(e, 'task_id'),
    ts: e.ts,
    verified: num(e, 'verified'),
    failed: num(e, 'failed'),
    vertices: num(e, 'vertices'),
  }))
}

/** The latest snapshot of each task (a task that ran again has several). */
export function snapshotByTask(events: RunEvent[]): Record<string, Snapshot> {
  return Object.fromEntries(snapshots(events).map(s => [s.taskId, s]))
}

/** The last snapshot saved at or before a moment: where a run can be resumed to get back to it. */
export function snapshotAt(events: RunEvent[], ts: string | null): Snapshot | null {
  if (!ts) return null
  return snapshots(events).filter(s => s.ts <= ts).at(-1) ?? null
}
