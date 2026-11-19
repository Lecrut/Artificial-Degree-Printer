import type { RunEvent } from '../../types/run'
import type { EntryKind, EntryStatus, PhaseId } from '../../types/timeline'
import { list, num, str } from '../events'
import { line, push, type Builder, type Handler } from './builder'

const details = (e: RunEvent) => (e.details ?? {}) as Record<string, unknown>

function phaseNow(b: Builder): PhaseId {
  return b.openTask?.phase ?? (b.graphBuilt ? 'repairs' : 'planning')
}

function entry(kind: EntryKind, status: EntryStatus, title: (e: RunEvent) => string, phase?: PhaseId): Handler {
  return (b, e) => {
    push(b, { id: `${kind}:${b.entries.length}`, kind, phase: phase ?? phaseNow(b), ts: e.ts, status, title: title(e) })
  }
}

const graphBuilt: Handler = (b, e) => {
  b.graphBuilt = true
  push(b, {
    id: 'graph:built', kind: 'graph', phase: 'planning', ts: e.ts, status: 'ok', title: 'Hipergraf zbudowany',
    subtitle: `${num(e, 'vertices')} wierzchołków · ${num(e, 'edges')} worków`,
    details: list(e, 'problems').map(t => line('problem', t, 'warn')),
  })
}

const queueRebuilt: Handler = (b, e) => {
  push(b, {
    id: `queue:${num(e, 'generation')}`, kind: 'queue', phase: 'repairs', ts: e.ts, status: 'warn',
    title: `Nowa kolejka z audytu (${num(e, 'generation')})`,
    details: list(e, 'task_ids').map(t => line('zadanie', t)),
  })
}

const replanned: Handler = (b, e) => {
  push(b, {
    id: `replan:${num(e, 'round')}`, kind: 'replan', phase: 'replans', ts: e.ts, status: 'warn',
    title: `Przeplanowanie ${num(e, 'round')}`,
    subtitle: `nieudane: ${list(e, 'failed').join(', ')}`,
    details: [
      ...list(e, 'tasks').map(t => line('nowe zadanie', t, 'info')),
      ...list(e, 'interfaces_changed').map(t => line('interfejs', t, 'ok')),
      ...list(e, 'dropped').map(t => line('odrzucone', t, 'warn')),
      ...list(e, 'gaps').map(t => line('luka', t, 'fail')),
    ],
  })
}

const runEnd: Handler = (b, e) => {
  const status = str(e, 'status') || str(e, 'reason')
  const ok = status === 'COMPLETED'
  push(b, { id: `end:${b.entries.length}`, kind: 'end', phase: 'end', ts: e.ts, status: ok ? 'ok' : 'fail', title: status || 'Koniec' })
}

export const miscHandlers: Record<string, Handler> = {
  H_BUILT: graphBuilt,
  H_EXTENDED: entry('graph', 'info', e => `Hipergraf rozszerzony: ${JSON.stringify(e.helpers ?? e.tests ?? e.imports ?? '')}`),
  AGENT_CREATED: entry('agent', 'info', e => `Nowy agent: ${str(e, 'agent') || str(e, 'specialization') || JSON.stringify(details(e))}`),
  AGENT_MUTATED: entry('evolution', 'info', e => `Reguła dla ${String(details(e).agent ?? '')}: ${String(details(e).injected_rule ?? '').slice(0, 200)}`),
  HARNESS_BUG_REPORTED: entry('evolution', 'warn', e => `Zgłoszony błąd harnessu: ${String(details(e).reason ?? '')}`),
  QUEUE_REBUILT: queueRebuilt,
  REPLANNED: replanned,
  RUN_STOPPED: entry('end', 'fail', e => `Zatrzymanie: ${str(e, 'reason')}`, 'end'),
  RUN_END: runEnd,
}
