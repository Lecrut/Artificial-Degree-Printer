import type { RunEvent } from '../../types/run'
import type { EntryStatus } from '../../types/timeline'
import { list, num, str } from '../events'
import { attempt, resolveTask, taskEntry, type Builder, type Handler } from './builder'

const lastLine = (text: string) => text.trim().split('\n').at(-1) ?? ''

function current(b: Builder, e: RunEvent) {
  const id = str(e, 'task_id')
  return id ? resolveTask(b, id) ?? b.openTask : b.openTask
}

function note(status: EntryStatus, kind: 'verdict' | 'rejected' | 'plan-change' | 'data' | 'note', text: (e: RunEvent) => string): Handler {
  return (b, e) => attempt(current(b, e), { ts: e.ts, kind, status, text: text(e) })
}

function finish(status: EntryStatus): Handler {
  return (b, e) => {
    const entry = taskEntry(b, str(e, 'task_id'), e.ts)
    entry.status = status
    if (status === 'waiting') attempt(entry, { ts: e.ts, kind: 'note', status, text: `odłożone: czeka na ${str(e, 'blamed')}` })
    if (b.openTask === entry) b.openTask = null
  }
}

const start: Handler = (b, e) => {
  const entry = taskEntry(b, str(e, 'task_id'), e.ts)
  if (entry.attempts.length) attempt(entry, { ts: e.ts, kind: 'note', status: 'info', text: 'start ponownie' })
  entry.status = 'running'
  entry.subtitle = [str(e, 'node'), str(e, 'agent'), str(e, 'tier')].filter(Boolean).join(' · ')
  b.openTask = entry
}

const waiting: Handler = (b, e) => {
  const entry = taskEntry(b, str(e, 'task_id'), e.ts)
  attempt(entry, { ts: e.ts, kind: 'note', status: 'waiting', text: `czeka: ${list(e, 'reasons').join('; ')}` })
}

const verdict: Handler = (b, e) => {
  const ok = str(e, 'status') === 'PASS'
  const blamed = str(e, 'failed_file') ? ` (winny: ${str(e, 'failed_file')}, ${str(e, 'failed_agent')})` : ''
  const text = ok ? 'weryfikacja przeszła' : `${str(e, 'first_issue')}${blamed}`
  attempt(taskEntry(b, str(e, 'task_id'), e.ts), { ts: e.ts, kind: 'verdict', status: ok ? 'ok' : 'fail', text })
}

const llmEnd: Handler = (b, e) => {
  const entry = current(b, e)
  if (!entry) return
  entry.llm.calls += 1
  entry.llm.seconds += num(e, 'elapsed_s')
  const agent = str(e, 'agent')
  if (agent && !entry.llm.agents.includes(agent)) entry.llm.agents.push(agent)
}

export const taskHandlers: Record<string, Handler> = {
  TASK_WAITING: waiting,
  TASK_START: start,
  VERDICT: verdict,
  TASK_DONE: finish('ok'),
  TASK_FAILED: finish('fail'),
  TASK_DEFERRED: finish('waiting'),
  LLM_CALL_END: llmEnd,
  BUILDER_ANSWER_REJECTED: note('fail', 'rejected', e => `odpowiedź odrzucona: ${lastLine(str(e, 'error')).slice(0, 300)}`),
  SPEC_WRITE_REJECTED: note('fail', 'rejected', e => `zapis odrzucony: ${[...list(e, 'violations'), ...list(e, 'refusals')][0] ?? ''}`),
  SPEC_AMENDED: note('ok', 'plan-change', e => `interfejs ${str(e, 'module')} zmieniony: ${str(e, 'reason')}`),
  SPEC_KEPT: note('info', 'plan-change', e => `interfejs ${str(e, 'module')} zostaje: ${str(e, 'reason')}`),
  SPEC_AMEND_REJECTED: note('warn', 'plan-change', e => `zmiana interfejsu ${str(e, 'module')} odrzucona`),
  REMEDIATION_SKIPPED: note('info', 'note', e => `planista naprawczy pominięty, winny: ${str(e, 'culprit')}`),
  VERTEX_BUDGET_SPENT: note('fail', 'note', e => `budżet prób wierzchołka ${str(e, 'vertex')} wyczerpany`),
  DATA_PRODUCED: note('ok', 'data', () => 'eksperyment zapisał wyniki'),
  DATA_STALE: note('warn', 'data', () => 'wyniki z nieaktualnego kodu, eksperyment od nowa'),
  DATA_FAILED: note('fail', 'data', e => `eksperyment padł: ${lastLine(str(e, 'error')).slice(0, 300)}`),
}
