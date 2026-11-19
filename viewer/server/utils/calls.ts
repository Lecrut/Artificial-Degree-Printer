import type { AgentCallDetail, AgentCallSummary } from '#shared/types/calls'
import type { RunEvent } from '#shared/types/run'
import { num, str } from '#shared/utils/events'
import { readEvents } from './runBundle'
import { runPath } from './runLayout'
import type { RunSource } from './sources/types'
import { parseJsonLines } from '#shared/utils/json'

type TraceRow = Record<string, unknown>

const text = (row: TraceRow, key: string) => (typeof row[key] === 'string' ? (row[key] as string) : '')
const agentName = (row: TraceRow) => text(row, 'agent_md').split(/[\\/]/).at(-1)?.replace(/\.md$/, '') ?? ''

function taskOf(payload: unknown): string | null {
  const record = (payload ?? {}) as Record<string, unknown>
  const task = (record.task ?? record.failed_task) as Record<string, unknown> | undefined
  return typeof task?.task_id === 'string' ? task.task_id : null
}

async function readTrace(source: RunSource, task: string): Promise<TraceRow[]> {
  return parseJsonLines<TraceRow>((await source.readText(task, runPath(source.kind, 'trace'))) ?? '')
}

/** Answer and error rows, numbered by step; traces before 2026-11-18 have no `phase` and no `step`. */
function answers(rows: TraceRow[]): { step: number, row: TraceRow }[] {
  return rows
    .filter(row => (row.phase ?? 'answer') !== 'request')
    .map((row, i) => ({ step: typeof row.step === 'number' ? row.step : i + 1, row }))
}

function summarize(step: number, row: TraceRow, end: RunEvent | undefined): AgentCallSummary {
  const parsed = (row.parsed_output ?? {}) as Record<string, unknown>
  return {
    step,
    ts: text(row, 'timestamp'),
    agent: agentName(row),
    tier: text(row, 'model_tier'),
    model: text(row, 'model_name'),
    provider: text(row, 'provider'),
    elapsedMs: typeof row.elapsed_ms === 'number' ? row.elapsed_ms : end ? num(end, 'elapsed_s') * 1000 : null,
    taskId: (end && str(end, 'task_id')) || taskOf(row.user_payload),
    ok: row.phase !== 'error',
    verdict: (end && str(end, 'verdict')) || (typeof parsed.status === 'string' ? parsed.status : null),
    decision: end ? str(end, 'decision') || null : null,
  }
}

interface LoadedCall {
  row: TraceRow
  summary: AgentCallSummary
}

// A commit's trace (up to ~12 MB) is parsed once; files on disk are read again, they may still grow.
const parsedCommits = new Map<string, Promise<LoadedCall[]>>()

async function parse(source: RunSource, task: string): Promise<LoadedCall[]> {
  const ends = new Map<number, RunEvent>()
  for (const e of await readEvents(source, task)) if (e.event === 'LLM_CALL_END') ends.set(num(e, 'step'), e)
  return answers(await readTrace(source, task)).map(({ step, row }) => ({ row, summary: summarize(step, row, ends.get(step)) }))
}

function load(source: RunSource, task: string): Promise<LoadedCall[]> {
  if (source.kind !== 'git') return parse(source, task)
  const key = `${source.ref}:${task}`
  if (!parsedCommits.has(key)) parsedCommits.set(key, parse(source, task))
  return parsedCommits.get(key)!
}

export async function listCalls(source: RunSource, task: string): Promise<AgentCallSummary[]> {
  return (await load(source, task)).map(call => call.summary)
}

export async function callDetail(source: RunSource, task: string, step: number): Promise<AgentCallDetail | null> {
  const call = (await load(source, task)).find(c => c.summary.step === step)
  if (!call) return null
  return {
    ...call.summary,
    systemPrompt: text(call.row, 'system_prompt'),
    payload: call.row.user_payload ?? null,
    answer: call.row.parsed_output ?? null,
    rawAnswer: text(call.row, 'raw_response'),
    error: text(call.row, 'error') || null,
  }
}
