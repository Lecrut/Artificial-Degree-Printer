import type { RunEvent } from '../../types/run'
import type { TimelineEntry } from '../../types/timeline'
import { list, num, str } from '../events'
import { line, push, type Builder, type Handler } from './builder'

// Planning in stages (harness §XVI, since 2026-11-21): the outline, then each module's interface, then the fused plan
// under the main critic. One entry per part; a finding reopens only its part, so a part may come back to life.
const STAGE_AGENTS = new Set(['plan_outline', 'outline_critic_guard', 'plan_module', 'module_critic_guard'])

/** The stage agents' calls (no task id): counted until the check of their part says which part they were for. */
export function stageCall(b: Builder, e: RunEvent): boolean {
  const agent = str(e, 'agent')
  if (str(e, 'task_id') || !STAGE_AGENTS.has(agent)) return false
  if (e.event !== 'LLM_CALL_START') {
    b.stageLlm.calls += 1
    b.stageLlm.seconds += num(e, 'elapsed_s')
    if (!b.stageLlm.agents.includes(agent)) b.stageLlm.agents.push(agent)
  }
  return true
}

function flushCalls(b: Builder, entry: TimelineEntry): void {
  entry.llm.calls += b.stageLlm.calls
  entry.llm.seconds += b.stageLlm.seconds
  for (const agent of b.stageLlm.agents) if (!entry.llm.agents.includes(agent)) entry.llm.agents.push(agent)
  b.stageLlm = { calls: 0, seconds: 0, agents: [] }
}

function part(b: Builder, e: RunEvent, key: string, title: string): TimelineEntry {
  const known = b.stages.get(key)
  if (known && known.status !== 'ok') return known
  const entry = push(b, { id: `plan-stage:${b.entries.length}`, kind: 'plan', phase: 'planning', ts: e.ts, status: 'running', title })
  b.stages.set(key, entry)
  return entry
}

function attemptLines(entry: TimelineEntry, e: RunEvent): void {
  const problems = list(e, 'problems')
  const critic = list(e, 'critic')
  const failed = problems.length + critic.length > 0
  entry.status = failed ? 'fail' : 'running'
  entry.details.push(
    line(`próba ${num(e, 'attempt')}`, failed ? `${problems.length} problemów, ${critic.length} blokad krytyka` : 'bez uwag', failed ? 'fail' : 'ok'),
    ...problems.map(t => line('kod', t, 'fail')),
    ...critic.map(t => line('krytyk', t, 'fail')),
  )
}

const outlineChecked: Handler = (b, e) => {
  const revision = b.stages.get('outline')?.status === 'ok'
  const entry = part(b, e, 'outline', revision ? 'Rewizja szkicu' : 'Szkic planu')
  flushCalls(b, entry)
  attemptLines(entry, e)
}

const moduleChecked: Handler = (b, e) => {
  const module = str(e, 'module')
  const entry = part(b, e, `module:${module}`, `Interfejs ${module}`)
  flushCalls(b, entry)
  attemptLines(entry, e)
}

const accepted = (key: (e: RunEvent) => string, subtitle: (e: RunEvent) => string): Handler => (b, e) => {
  const entry = b.stages.get(key(e))
  if (!entry) return
  entry.status = 'ok'
  entry.subtitle = subtitle(e)
  for (const objection of list(e, 'over_critic')) entry.details.push(line('zastrzeżenie', objection, 'warn'))
}

const reopened: Handler = (b, e) => {
  const module = str(e, 'module')
  const entry = part(b, e, `module:${module}`, `Interfejs ${module} — ponownie`)
  entry.details.push(...list(e, 'reasons').map(t => line('powód', t, 'warn')))
}

const needs: Handler = (b, e) => {
  const entry = b.stages.get(`module:${str(e, 'module')}`)
  const wanted = (e.needs ?? {}) as Record<string, unknown>
  entry?.details.push(...Object.entries(wanted).map(([dep, need]) => line('potrzebuje', `${dep}: ${String(need)}`, 'warn')))
}

const revised: Handler = (b, e) => {
  const entry = b.stages.get('outline')
  const changed = list(e, 'changed')
  entry?.details.push(line('zmienione moduły', changed.join(', ') || '—'), ...list(e, 'removed').map(t => line('usunięty', t, 'warn')))
}

const fused: Handler = (b, e) => {
  push(b, {
    id: `plan-fused:${b.entries.length}`, kind: 'plan', phase: 'planning', ts: e.ts, status: 'ok',
    title: 'Plan złożony', subtitle: `${num(e, 'tasks')} zadań · ${list(e, 'modules').length} modułów`,
  })
}

export const stageHandlers: Record<string, Handler> = {
  PLAN_OUTLINE_CHECKED: outlineChecked,
  PLAN_OUTLINE_ACCEPTED: accepted(() => 'outline', e => list(e, 'order').join(' → ')),
  PLAN_OUTLINE_REVISED: revised,
  PLAN_MODULE_CHECKED: moduleChecked,
  PLAN_MODULE_ACCEPTED: accepted(e => `module:${str(e, 'module')}`, e => `próby: ${num(e, 'attempts')}`),
  PLAN_MODULE_REOPENED: reopened,
  PLAN_MODULE_NEEDS: needs,
  PLAN_FUSED: fused,
}
