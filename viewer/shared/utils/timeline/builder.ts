import type { RunEvent } from '../../types/run'
import type { DetailLine, EntryKind, EntryStatus, PhaseId, TaskAttempt, TimelineEntry } from '../../types/timeline'

/** The state of one pass over the events. */
export interface Builder {
  entries: TimelineEntry[]
  tasks: Map<string, TimelineEntry>
  openTask: TimelineEntry | null
  lastPlan: TimelineEntry | null
  /** The planner's step and the plan check in progress, and how many plans the planner has written. */
  planner: TimelineEntry | null
  check: TimelineEntry | null
  plans: number
  pendingReview: RunEvent | null
  graphBuilt: boolean
  /** Planning in stages: the entry of each part (`outline`, `module:<file>`) and the stage calls not yet assigned. */
  stages: Map<string, TimelineEntry>
  stageLlm: TimelineEntry['llm']
}

export type Handler = (b: Builder, e: RunEvent) => void

export function newBuilder(): Builder {
  return {
    entries: [], tasks: new Map(), openTask: null, lastPlan: null, planner: null, check: null, plans: 0, pendingReview: null, graphBuilt: false,
    stages: new Map(), stageLlm: { calls: 0, seconds: 0, agents: [] },
  }
}

interface NewEntry {
  id: string
  kind: EntryKind
  phase: PhaseId
  ts: string
  status: EntryStatus
  title: string
  subtitle?: string
  details?: DetailLine[]
}

export function push(b: Builder, entry: NewEntry): TimelineEntry {
  const full: TimelineEntry = {
    subtitle: '',
    details: [],
    ...entry,
    attempts: [],
    llm: { calls: 0, seconds: 0, agents: [] },
    step: null,
  }
  b.entries.push(full)
  return full
}

export function line(label: string, text: string, status: EntryStatus = 'info'): DetailLine {
  return { label, text, status }
}

/** Phase of a task from its id: the plan's tasks, repair queues (`Q<n>_…`, Gate 3), re-planned work (`R<n>_…`). */
function phaseOfTask(taskId: string): PhaseId {
  if (/^R\d+_/.test(taskId)) return 'replans'
  if (/^(Q\d+_|GATE_)/.test(taskId)) return 'repairs'
  return 'building'
}

/** The planned task an id belongs to: `T5_FIX1` is a fast repair of `T5`, but `Q3_FIX1` is a task of its own. */
export function resolveTask(b: Builder, taskId: string): TimelineEntry | null {
  let id = taskId
  while (!b.tasks.has(id) && /_FIX\d+$/.test(id)) id = id.replace(/_FIX\d+$/, '')
  return b.tasks.get(id) ?? null
}

export function taskEntry(b: Builder, taskId: string, ts: string): TimelineEntry {
  const known = resolveTask(b, taskId)
  if (known) return known
  const entry = push(b, { id: `task:${taskId}`, kind: 'task', phase: phaseOfTask(taskId), ts, status: 'waiting', title: taskId })
  b.tasks.set(taskId, entry)
  return entry
}

export function attempt(entry: TimelineEntry | null, item: TaskAttempt): void {
  entry?.attempts.push(item)
}
