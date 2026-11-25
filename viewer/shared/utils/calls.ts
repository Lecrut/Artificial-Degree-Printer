import type { AgentCallDetail, AgentCallSummary } from '../types/calls'
import type { RunEvent } from '../types/run'
import { num, str } from './events'

export type TraceRow = Record<string, unknown>

export interface LoadedCall {
  row: TraceRow
  summary: AgentCallSummary
}

const text = (row: TraceRow, key: string) => (typeof row[key] === 'string' ? (row[key] as string) : '')
const agentName = (row: TraceRow) => text(row, 'agent_md').split(/[\\/]/).at(-1)?.replace(/\.md$/, '') ?? ''

function taskOf(payload: unknown): string | null {
  const record = (payload ?? {}) as Record<string, unknown>
  const task = (record.task ?? record.failed_task) as Record<string, unknown> | undefined
  return typeof task?.task_id === 'string' ? task.task_id : null
}

function summarize(step: number, row: TraceRow, end: RunEvent | undefined, running: boolean): AgentCallSummary {
  const parsed = (row.parsed_output ?? {}) as Record<string, unknown>
  const failedEnd = end ? end.ok === false : false
  return {
    step,
    ts: text(row, 'timestamp'),
    agent: agentName(row),
    tier: text(row, 'model_tier') || (end ? str(end, 'tier') : ''),
    model: text(row, 'model_name') || (end ? str(end, 'model') : ''),
    provider: text(row, 'provider'),
    elapsedMs: typeof row.elapsed_ms === 'number' ? row.elapsed_ms : end ? num(end, 'elapsed_s') * 1000 : null,
    taskId: (end && str(end, 'task_id')) || taskOf(row.user_payload),
    ok: running ? true : row.phase !== 'error' && !failedEnd,
    ...(running ? { running: true } : {}),
    verdict: (end && str(end, 'verdict')) || (typeof parsed.status === 'string' ? parsed.status : null),
    decision: end ? str(end, 'decision') || null : null,
  }
}

/** Pairs `request` rows with `answer`/`error` rows by `step`; keeps open `request` rows when `includeRunning` is set. */
function pairRows(rows: TraceRow[], ends: Map<number, RunEvent>, includeRunning: boolean): { step: number, row: TraceRow, running: boolean }[] {
  const requests = new Map<number, TraceRow>()
  const settled = new Map<number, TraceRow>()
  const legacy: TraceRow[] = []
  for (const row of rows) {
    if (typeof row.step !== 'number') {
      if ((row.phase ?? 'answer') !== 'request') legacy.push(row)
      continue
    }
    if (row.phase === 'request') requests.set(row.step, row)
    else settled.set(row.step, { ...requests.get(row.step), ...row })
  }
  if (!requests.size && !settled.size) return legacy.map((row, i) => ({ step: i + 1, row, running: false }))
  const out = [...settled.entries()].map(([step, row]) => ({ step, row, running: false }))
  if (includeRunning) {
    for (const [step, req] of requests) {
      if (!settled.has(step)) out.push({ step, row: req, running: !ends.has(step) })
    }
  }
  return out.sort((a, b) => a.step - b.step)
}

export function parseTraceCalls(rows: TraceRow[], events: RunEvent[], includeRunning = false): LoadedCall[] {
  const ends = new Map<number, RunEvent>()
  for (const e of events) if (e.event === 'LLM_CALL_END') ends.set(num(e, 'step'), e)
  return pairRows(rows, ends, includeRunning).map(({ step, row, running }) => ({
    row,
    summary: summarize(step, row, ends.get(step), running),
  }))
}

export function toCallDetail(call: LoadedCall, fallbackPrompt = ''): AgentCallDetail {
  return {
    ...call.summary,
    systemPrompt: text(call.row, 'system_prompt') || fallbackPrompt,
    payload: call.row.user_payload ?? null,
    answer: call.row.parsed_output ?? null,
    rawAnswer: text(call.row, 'raw_response'),
    error: text(call.row, 'error') || null,
  }
}
