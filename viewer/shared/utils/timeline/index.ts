import type { RunEvent } from '../../types/run'
import type { EntryStatus, PhaseId, PhaseSummary, RunTimeline, TimelineEntry } from '../../types/timeline'
import { newBuilder, type Handler } from './builder'
import { miscHandlers } from './misc'
import { planCall, planHandlers } from './plan'
import { stageCall, stageHandlers } from './planStages'
import { taskHandlers } from './tasks'

export { isPlanStep } from './plan'

const PHASES: PhaseId[] = ['planning', 'building', 'repairs', 'replans', 'end']

const HANDLERS: Record<string, Handler> = { ...planHandlers, ...stageHandlers, ...taskHandlers, ...miscHandlers }

function phaseStatus(entries: TimelineEntry[]): EntryStatus {
  if (entries.some(e => e.status === 'running')) return 'running'
  if (entries.some(e => e.status === 'fail')) return 'fail'
  if (entries.some(e => e.status === 'warn' || e.status === 'waiting')) return 'warn'
  return 'ok'
}

function summarizePhases(entries: TimelineEntry[]): PhaseSummary[] {
  return PHASES.map((id) => {
    const inPhase = entries.filter(e => e.phase === id)
    return { id, entries: inPhase.length, status: inPhase.length ? phaseStatus(inPhase) : 'info' }
  })
}

/** The run as a timeline: what a person needs to follow the plan and its execution, in the order it happened. */
export function buildTimeline(events: RunEvent[]): RunTimeline {
  const b = newBuilder()
  for (const event of events) {
    if (event.event.startsWith('LLM_CALL_') && (planCall(b, event) || stageCall(b, event))) continue
    HANDLERS[event.event]?.(b, event)
  }
  return { phases: summarizePhases(b.entries), entries: b.entries }
}
