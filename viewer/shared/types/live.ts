import type { Hypergraph } from './hypergraph'
import type { RunEvent, SourceKind } from './run'

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
  | { type: 'trace', stamp: string }

export type LaunchTask = '1' | '2' | '3' | '4'
export type LaunchProvider = 'mock' | 'ollama' | 'google'

/** The run whose saved state a new run continues from (`main.py --resume-from`): one task, no planning, nothing verified is redone. */
export interface ResumeFrom {
  source: SourceKind
  ref: string
  /** A file of the run's `logs/snapshots/`: continue from the moment after that task instead of the end state. */
  snapshot?: string
}

export interface LaunchRequest {
  /** One or more tasks of the suite, run one after another by a single `main.py`. */
  tasks: LaunchTask[]
  provider: LaunchProvider
  template: 'thesis_plodz' | 'paper_ieee' | null
  /** Needs exactly one task. */
  resume?: ResumeFrom | null
}

export interface LaunchStatus {
  running: boolean
  pid: number | null
  args: string[]
  startedAt: string | null
  exitCode: number | null
  lines: string[]
}
