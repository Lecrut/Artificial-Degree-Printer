import type { RunEvent } from '../../types/run'
import type { EntryStatus } from '../../types/timeline'
import { list, num, str } from '../events'
import { line, push, type Handler } from './builder'

type Decision = { status?: string, why?: string }
type Diagnosis = { cause?: string, why?: string }

const records = <T>(e: RunEvent, field: string): Array<[string, T]> => {
  const value = e[field]
  return value && typeof value === 'object' ? Object.entries(value as Record<string, T>) : []
}

/** What the designer decided for each module: keep stays quiet, a change, an addition and a removal are the news. */
const STATUS: Record<string, EntryStatus> = { keep: 'ok', change: 'warn', new: 'info', remove: 'fail' }
const STATUS_WORD: Record<string, string> = { keep: 'zostaje', change: 'zmieniony', new: 'nowy', remove: 'usunięty' }

const entry = (id: string, status: EntryStatus, title: string, subtitle: string, e: RunEvent, details: ReturnType<typeof line>[]): Handler => (b) => {
  push(b, { id, kind: 'replan', phase: 'replans', ts: e.ts, status, title, subtitle, details })
}

const started: Handler = (b, e) =>
  entry(`redesign:${num(e, 'round')}:${num(e, 'attempt')}:start`, 'running', `Przeprojektowanie ${num(e, 'round')}`, `nieudane: ${list(e, 'failed').join(', ')}`, e, [])(b, e)

const audited: Handler = (b, e) =>
  entry(`redesign:audit:${b.entries.length}`, 'info', 'Audyt implementacji', `${num(e, 'files')} plików, opisanych od nowa: ${num(e, 'described')}`, e, [])(b, e)

const sourceGranted: Handler = (b, e) =>
  entry(`redesign:source:${b.entries.length}`, 'info', 'Projektant czyta kod', list(e, 'files').join(', '), e, [])(b, e)

const guidelines: Handler = (b, e) => {
  const problems = list(e, 'problems')
  const decisions = records<Decision>(e, 'decisions').map(([file, d]) =>
    line(STATUS_WORD[d.status ?? ''] ?? String(d.status), `${file}${d.why ? `: ${d.why}` : ''}`, STATUS[d.status ?? ''] ?? 'info'))
  const diagnosis = records<Diagnosis>(e, 'diagnosis').map(([file, d]) => line(`przyczyna: ${d.cause ?? '?'}`, `${file}${d.why ? `: ${d.why}` : ''}`, 'info'))
  const subtitle = problems.length ? `${problems.length} problemów w odpowiedzi` : `${decisions.length} modułów z decyzją`
  entry(`redesign:guidelines:${b.entries.length}`, problems.length ? 'warn' : 'ok', `Wytyczne projektanta (odpowiedź ${num(e, 'attempt')})`, subtitle, e, [
    ...decisions, ...diagnosis, ...problems.map(t => line('problem', t, 'fail')),
  ])(b, e)
}

const applied: Handler = (b, e) => {
  const redesigned = list(e, 'redesigned')
  entry(`redesign:${num(e, 'round')}`, 'ok', `Przeprojektowanie ${num(e, 'round')} zastosowane`, `od nowa: ${redesigned.join(', ') || '—'}`, e, [
    ...redesigned.map(t => line('od nowa', t, 'warn')),
    ...list(e, 'removed').map(t => line('usunięty', t, 'fail')),
    ...list(e, 'kept').map(t => line('zachowany', t, 'ok')),
    ...list(e, 'tasks').map(t => line('nowe zadanie', t, 'info')),
  ])(b, e)
}

const fallback: Handler = (b, e) =>
  entry(`redesign:fallback:${b.entries.length}`, 'warn', 'Przeprojektowanie nie doszło do skutku', str(e, 'reason'), e, list(e, 'problems').map(t => line('problem', t, 'fail')))(b, e)

export const redesignHandlers: Record<string, Handler> = {
  REDESIGN_STARTED: started,
  IMPLEMENTATION_AUDITED: audited,
  REDESIGN_SOURCE_GRANTED: sourceGranted,
  REDESIGN_GUIDELINES: guidelines,
  REDESIGN_APPLIED: applied,
  REDESIGN_FALLBACK: fallback,
}
