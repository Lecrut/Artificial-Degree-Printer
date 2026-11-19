import type { Hypergraph } from './hypergraph'

export type SourceKind = 'git' | 'results' | 'live'

/** One line of `events.jsonl`: `ts`, `event` and the fields of that event. */
export interface RunEvent {
  ts: string
  event: string
  [field: string]: unknown
}

export interface RunRef {
  source: SourceKind
  ref: string
  task: string
}

export interface TaskSummary {
  task: string
  status: string
  title: string | null
  started: string | null
  ended: string | null
  durationSeconds: number | null
  tasksTotal: number
  tasksDone: number
  llmCalls: number
  failedVerdicts: number
  rejectedWrites: number
  planVersions: number
  replans: number
}

export interface CommitSummary {
  sha: string
  short: string
  date: string
  message: string
  tasks: TaskSummary[]
}

export interface RunFiles {
  thesis: string | null
  thesisCompiled: string | null
  results: string | null
  pdf: string | null
  figures: string[]
}

export interface RunBundle {
  ref: RunRef
  summary: TaskSummary
  events: RunEvent[]
  hypergraph: Hypergraph | null
  blueprint: Record<string, unknown> | null
  files: RunFiles
}
