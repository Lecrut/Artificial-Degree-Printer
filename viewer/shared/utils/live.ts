import type { QueueTask } from '../types/live'
import type { RunEvent } from '../types/run'
import { num, str } from './events'

export interface OpenCall {
  step: number
  agent: string
  model: string
  tier: string
  taskId: string
  since: string
}

/** The agent call that has started and not finished yet: what the harness is waiting for right now. */
export function openCall(events: RunEvent[]): OpenCall | null {
  const ended = new Set(events.filter(e => e.event === 'LLM_CALL_END').map(e => num(e, 'step')))
  const start = [...events].reverse().find(e => e.event === 'LLM_CALL_START' && !ended.has(num(e, 'step')))
  if (!start) return null
  return { step: num(start, 'step'), agent: str(start, 'agent'), model: str(start, 'model'), tier: str(start, 'tier'), taskId: str(start, 'task_id'), since: start.ts }
}

export function lastVerdict(events: RunEvent[]): RunEvent | null {
  return [...events].reverse().find(e => e.event === 'VERDICT') ?? null
}

export const BOARD_COLUMNS = ['TODO', 'WAITING', 'IN_PROGRESS', 'DONE', 'FAILED'] as const
export type BoardColumn = typeof BOARD_COLUMNS[number]

const TASK_END = new Set(['TASK_DONE', 'TASK_FAILED', 'TASK_WAITING'])

/** The task the harness is working on: started and not yet done, failed or put off. Its repairs run inside it. */
export function activeTask(events: RunEvent[]): string | null {
  for (let i = events.length - 1; i >= 0; i--) {
    const e = events[i]!
    if (TASK_END.has(e.event)) return null
    if (e.event === 'TASK_START') return str(e, 'task_id') || null
  }
  return null
}

/**
 * The queue as columns of a board; an unknown status counts as to do. The task being worked on is in progress
 * whatever the queue says: during its repairs the harness has already marked it FAILED.
 */
export function boardColumns(queue: QueueTask[], active: string | null = null): Record<BoardColumn, QueueTask[]> {
  const columns = Object.fromEntries(BOARD_COLUMNS.map(c => [c, [] as QueueTask[]])) as Record<BoardColumn, QueueTask[]>
  for (const task of queue) {
    const status = task.task_id === active ? 'IN_PROGRESS' : task.status
    columns[(BOARD_COLUMNS as readonly string[]).includes(status) ? status as BoardColumn : 'TODO'].push(task)
  }
  return columns
}
