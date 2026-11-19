import type { RunEvent } from '../../types/run'
import type { DetailLine, PhaseId, TimelineEntry } from '../../types/timeline'
import { list, num, str } from '../events'
import { line, push, type Builder, type Handler } from './builder'

// Planning is a loop of three steps: the planner writes (or patches) the plan, the critic reads it, the harness checks it.
const PLANNER = 'task_planner'
const CRITIC = 'plan_critic_guard'

function blockers(e: RunEvent): { blocking: DetailLine[], advisory: DetailLine[] } {
  const groups = (e.blockers ?? {}) as Record<string, unknown>
  const pick = (key: string) => (Array.isArray(groups[key]) ? (groups[key] as unknown[]).map(String) : [])
  // Since 2026-11-18 the check groups its findings; earlier runs had violations / gaps / advice.
  const code = [...pick('code'), ...list(e, 'violations')]
  const critic = pick('critic')
  const advisory = [...pick('instruction'), ...list(e, 'gaps'), ...list(e, 'warnings'), ...list(e, 'advice')]
  return {
    blocking: [...code.map(t => line('kod', t, 'fail')), ...critic.map(t => line('krytyk', t, 'fail'))],
    advisory: advisory.map(t => line('uwaga', t, 'warn')),
  }
}

function review(e: RunEvent | null): DetailLine[] {
  if (!e) return []
  if (e.event === 'PLAN_REVIEW_NO_VERDICT') return [line('krytyk', 'brak czytelnego werdyktu', 'warn')]
  const status = str(e, 'status')
  return [line('krytyk', `werdykt ${status}`, status === 'PASS' ? 'ok' : 'fail')]
}

/** An entry that holds a plan the planner wrote (its answer can be shown as the plan). */
export function isPlanStep(entry: TimelineEntry): boolean {
  return entry.kind === 'plan' && entry.step !== null && entry.llm.agents.includes(PLANNER)
}

const phase = (b: Builder): PhaseId => (b.graphBuilt ? 'replans' : 'planning')

function startStep(b: Builder, e: RunEvent, title: string): TimelineEntry {
  const entry = push(b, { id: `plan:${b.entries.length}`, kind: 'plan', phase: phase(b), ts: e.ts, status: 'running', title })
  entry.llm.agents.push(str(e, 'agent'))
  entry.step = num(e, 'step') || null
  return entry
}

function endStep(entry: TimelineEntry | null, e: RunEvent): void {
  if (!entry) return
  entry.llm.calls += 1
  entry.llm.seconds += num(e, 'elapsed_s')
  if (e.ok === false) entry.status = 'fail'
}

// The planner's own summary: "Plan: 13 zadan [T1, …], cel: '…'" (to 2026-11-18) or "zadania: 12; interfejsy: 4" (since).
function describePlan(entry: TimelineEntry, decision: string): void {
  if (entry.status === 'running') entry.status = 'ok'
  const tasks = /(\d+) zada/.exec(decision)?.[1] ?? /zadania: (\d+)/.exec(decision)?.[1]
  const modules = /interfejsy: (\d+)/.exec(decision)?.[1]
  const goal = /cel: '(.+)'$/.exec(decision)?.[1]
  entry.subtitle = [tasks && `${tasks} zadań`, modules && `${modules} modułów`].filter(Boolean).join(' · ')
  if (goal) entry.details.push(line('cel', goal))
}

/** The planner's and the critic's calls (no task id): their own steps on the timeline. True when the call was theirs. */
export function planCall(b: Builder, e: RunEvent): boolean {
  const agent = str(e, 'agent')
  if (str(e, 'task_id') || (agent !== PLANNER && agent !== CRITIC)) return false
  const starting = e.event === 'LLM_CALL_START'
  if (agent === PLANNER && starting) {
    b.planner = startStep(b, e, b.plans === 0 ? 'Plan początkowy' : `Poprawka planu ${b.plans}`)
  }
  else if (agent === PLANNER) {
    endStep(b.planner, e)
    if (b.planner) describePlan(b.planner, str(e, 'decision'))
    b.plans += 1
  }
  else if (starting) b.check = startStep(b, e, `Weryfikacja planu ${b.plans}`)
  else endStep(b.check, e)
  return true
}

const checked: Handler = (b, e) => {
  const { blocking, advisory } = blockers(e)
  const fields = {
    status: blocking.length ? 'fail' : advisory.length ? 'warn' : 'ok',
    title: `Weryfikacja planu ${num(e, 'attempt') + 1}`,
    subtitle: `${list(e, 'modules').length} modułów`,
  } as const
  const details = [...review(b.pendingReview), ...blocking, ...advisory]
  // Runs without the critic's call events (before 2026-11-18, mocks) still get the check as its own entry.
  const entry = b.check ?? push(b, { id: `plan:${b.entries.length}`, kind: 'plan', phase: phase(b), ts: e.ts, ...fields })
  Object.assign(entry, fields)
  entry.details.push(...details)
  b.lastPlan = entry
  b.check = null
  b.pendingReview = null
}

const patched: Handler = (b, e) => {
  const accepted = e.accepted === true
  const changed = list(e, 'changed')
  const target = b.planner ?? b.lastPlan
  if (target && !accepted) target.status = 'warn'
  target?.details.push(
    line('łatka', `${accepted ? 'przyjęta' : 'odrzucona'}; zmieniono: ${changed.join(', ') || '—'}`, accepted ? 'ok' : 'fail'),
    ...list(e, 'fixed').map(t => line('naprawione', t, 'ok')),
    ...list(e, 'new').map(t => line('nowe', t, 'fail')),
    ...list(e, 'rejected').map(t => line('odrzucone', t, 'warn')),
  )
}

const rejected: Handler = (b, e) => {
  push(b, {
    id: `plan-rejected:${b.entries.length}`,
    kind: 'plan',
    phase: 'planning',
    ts: e.ts,
    status: 'fail',
    title: 'Plan odrzucony',
    details: list(e, 'violations').map(t => line('naruszenie', t, 'fail')),
  })
}

export const planHandlers: Record<string, Handler> = {
  PLAN_REVIEWED: (b, e) => { b.pendingReview = e },
  PLAN_REVIEW_NO_VERDICT: (b, e) => { b.pendingReview = e },
  PLAN_CHECKED: checked,
  PLAN_PATCHED: patched,
  PLAN_REJECTED: rejected,
}
