import { describe, expect, test } from 'bun:test'
import type { RunEvent } from '../types/run'
import { snapshotAt, snapshotByTask, snapshots } from './snapshots'

const saved = (ts: string, task_id: string, file: string, failed = 0): RunEvent =>
  ({ ts, event: 'SNAPSHOT_SAVED', task_id, file, verified: 2, failed, vertices: 5 })
const events: RunEvent[] = [
  { ts: '2026-11-24T10:00:00+00:00', event: 'TASK_DONE', task_id: 'T1' },
  saved('2026-11-24T10:01:00+00:00', 'T1', '001_T1.zip'),
  saved('2026-11-24T10:05:00+00:00', 'T2', '002_T2.zip', 1),
  saved('2026-11-24T10:09:00+00:00', 'T1', '003_T1.zip'),
]

describe('snapshots', () => {
  test('are read from SNAPSHOT_SAVED only', () => {
    expect(snapshots(events).map(s => s.file)).toEqual(['001_T1.zip', '002_T2.zip', '003_T1.zip'])
    expect(snapshots(events)[1]).toMatchObject({ taskId: 'T2', verified: 2, failed: 1, vertices: 5 })
  })

  test('the latest one of a task wins', () => {
    expect(snapshotByTask(events).T1?.file).toBe('003_T1.zip')
  })

  test('a moment gets the last snapshot before it, none before the first', () => {
    expect(snapshotAt(events, '2026-11-24T10:06:00+00:00')?.file).toBe('002_T2.zip')
    expect(snapshotAt(events, '2026-11-24T10:00:30+00:00')).toBeNull()
    expect(snapshotAt(events, null)).toBeNull()
  })
})
