import type { Hypergraph } from './hypergraph'
import type { RunEvent } from './run'

/** One task of `task_queue.json`. */
export interface QueueTask {
  task_id: string
  description: string
  target_node: string
  assigned_agent: string
  status: string
  /** Repairs of this task so far; the harness keeps the status FAILED while it repairs (`T7_FIX1`, `T7_FIX2`, …). */
  repair_attempts?: number
}

/** Messages of the live stream (`/api/live/stream`). */
export type LiveMessage =
  | { type: 'run', task: string | null }
  | { type: 'events', events: RunEvent[] }
  | { type: 'state', hypergraph: Hypergraph | null, queue: QueueTask[] }

export type LaunchTask = '1' | '2' | '3' | '4' | 'all'
export type LaunchProvider = 'mock' | 'ollama' | 'google'

export interface LaunchRequest {
  task: LaunchTask
  provider: LaunchProvider
  template: 'thesis_plodz' | 'paper_ieee' | null
}

export interface LaunchStatus {
  running: boolean
  pid: number | null
  args: string[]
  startedAt: string | null
  exitCode: number | null
  lines: string[]
}
