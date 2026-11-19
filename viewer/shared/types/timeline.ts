export type EntryKind = 'plan' | 'graph' | 'agent' | 'task' | 'queue' | 'replan' | 'evolution' | 'end'
export type EntryStatus = 'ok' | 'fail' | 'warn' | 'info' | 'running' | 'waiting'
export type PhaseId = 'planning' | 'building' | 'repairs' | 'replans' | 'end'

/** One labelled detail of an entry (a violation, a changed module, a reason). */
export interface DetailLine {
  label: string
  text: string
  status: EntryStatus
}

/** One step inside a task: a verdict, a rejected answer, a change of the plan, the experiment, a note. */
export interface TaskAttempt {
  ts: string
  kind: 'verdict' | 'rejected' | 'plan-change' | 'data' | 'note'
  status: EntryStatus
  text: string
}

export interface LlmUsage {
  calls: number
  seconds: number
  agents: string[]
}

export interface TimelineEntry {
  id: string
  kind: EntryKind
  phase: PhaseId
  ts: string
  status: EntryStatus
  title: string
  subtitle: string
  details: DetailLine[]
  attempts: TaskAttempt[]
  llm: LlmUsage
  /** The model call whose answer is this entry's content (the plan the planner wrote), if any. */
  step: number | null
}

export interface PhaseSummary {
  id: PhaseId
  entries: number
  status: EntryStatus
}

export interface RunTimeline {
  phases: PhaseSummary[]
  entries: TimelineEntry[]
}
