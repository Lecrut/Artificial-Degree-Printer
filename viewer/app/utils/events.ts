// How events, states and roles of a run look in the viewer.
export type Ev = Record<string, any>

export const STATE_COLORS: Record<string, string> = {
  spec: 'var(--gray)',
  stub: 'var(--warn)',
  written: 'var(--info)',
  verified: 'var(--ok)',
  failed: 'var(--fail)',
  stale: 'var(--pink)',
}

export const BAG_COLORS: Record<string, string> = { I: 'var(--accent)', R: 'var(--teal)', N: 'var(--violet)' }

export const ROLE_NAMES: Record<string, string> = {
  P: 'producent',
  C: 'używa',
  T: 'test',
  O: 'wynik',
  X: 'cytujący rozdział',
}

export function eventColor(e: Ev): string {
  const name: string = e.event
  if (name === 'VERDICT') return e.status === 'PASS' ? 'var(--ok)' : 'var(--fail)'
  if (name === 'LLM_CALL_END' && e.ok === false) return 'var(--fail)'
  if (name.startsWith('LLM_')) return 'var(--gray)'
  if (name.startsWith('PLAN_')) return e.status === 'FAIL' || e.violations?.length ? 'var(--fail)' : 'var(--violet)'
  if (name.startsWith('H_') || name === 'VERTEX_STATE' || name.startsWith('SPEC_A') || name === 'SPEC_KEPT') return 'var(--teal)'
  if (name.includes('REJECTED') || name.includes('FAILED') || name === 'DATA_STALE') return 'var(--warn)'
  if (name.startsWith('AGENT_') || name.includes('MUTAT') || name.includes('SPLIT')) return 'var(--pink)'
  if (name.startsWith('TASK_')) return 'var(--info)'
  if (name.startsWith('RUN_')) return e.status === 'COMPLETED' ? 'var(--ok)' : 'var(--fail)'
  return 'var(--accent)'
}

const first = (list: unknown) => (Array.isArray(list) && list.length ? String(list[0]) : '')

export function eventSummary(e: Ev): string {
  switch (e.event) {
    case 'TASK_START': return `${e.task_id} → ${e.node} (${e.agent}, ${e.tier})`
    case 'TASK_DONE': return `${e.task_id} gotowe, naprawy: ${e.repair_attempts ?? 0}`
    case 'TASK_FAILED': return `${e.task_id} nieudane ${e.reason ?? ''}`
    case 'VERDICT': return `${e.task_id} ${e.status}${e.first_issue ? ' — ' + e.first_issue : ''}${e.failed_agent ? ` (winny: ${e.failed_agent})` : ''}`
    case 'VERTEX_STATE': return `${e.vertex} → ${e.state}${e.task_id ? ` (${e.task_id})` : ''}`
    case 'LLM_CALL_START': return `#${e.step ?? '?'} ${e.agent} → ${e.model}${e.task_id ? ` [${e.task_id}]` : ''}`
    case 'LLM_CALL_END': return e.ok === false ? `#${e.step ?? '?'} ${e.agent}: BŁĄD ${e.error}` : `#${e.step ?? '?'} ${e.agent}: ${e.decision ?? 'ok'} (${e.elapsed_s ?? 0}s)`
    case 'PLAN_CHECKED': return `próba ${e.attempt}: ${e.violations?.length ?? 0} naruszeń, ${e.gaps?.length ?? 0} luk${e.violations?.length ? ' — ' + first(e.violations) : ''}`
    case 'PLAN_REVIEWED': return `krytyk: ${e.status}, blokujące ${e.blocking?.length ?? 0}, rady ${e.advice?.length ?? 0}${e.blocking?.length ? ' — ' + first(e.blocking) : ''}`
    case 'H_BUILT': return `H: ${e.vertices} wierzchołków, ${e.edges} worków, ${e.order} relacji ≺`
    case 'H_EXTENDED': return `H rozszerzony: ${JSON.stringify(e.helpers ?? e.tests ?? e.imports ?? e)}`
    case 'SPEC_WRITE_REJECTED': return first(e.violations) || first(e.refusals)
    case 'BUILDER_ANSWER_REJECTED': return `${e.task_id} (${e.agent}): ${String(e.error ?? '').slice(0, 160)}`
    case 'RUN_END': return `${e.task}: ${e.status}`
    default: {
      const rest = Object.entries(e).filter(([k]) => k !== 'ts' && k !== 'event')
      return rest.map(([k, v]) => `${k}=${typeof v === 'object' ? JSON.stringify(v) : v}`).join(' ').slice(0, 200)
    }
  }
}

export function fmtTime(ts?: string | null): string {
  return ts ? ts.slice(11, 19) : ''
}

export function fmtDuration(a?: string | null, b?: string | null): string {
  if (!a || !b) return '—'
  const s = Math.max(0, (Date.parse(b) - Date.parse(a)) / 1000)
  if (s < 60) return `${s.toFixed(0)} s`
  if (s < 3600) return `${(s / 60).toFixed(1)} min`
  return `${(s / 3600).toFixed(1)} h`
}

export function statusColor(status: string): string {
  if (status === 'COMPLETED') return 'var(--ok)'
  if (status?.includes('FAIL') || status === 'CRASHED' || status === 'PLAN_REJECTED') return 'var(--fail)'
  return 'var(--warn)'
}
