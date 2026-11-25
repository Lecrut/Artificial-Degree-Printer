import type { AgentCallDetail, AgentCallSummary } from '#shared/types/calls'
import { parseTraceCalls, toCallDetail } from '#shared/utils/calls'
import type { LoadedCall, TraceRow } from '#shared/utils/calls'
import { parseJsonLines } from '#shared/utils/json'
import { readAgentPrompt } from './agentPrompts'
import { readEvents } from './runBundle'
import { runPath } from './runLayout'
import type { RunSource } from './sources/types'

async function readTrace(source: RunSource, task: string): Promise<TraceRow[]> {
  return parseJsonLines<TraceRow>((await source.readText(task, runPath(source.kind, 'trace'))) ?? '')
}

// A commit's trace (up to ~12 MB) is parsed once; files on disk are read again, they may still grow.
const parsedCommits = new Map<string, Promise<LoadedCall[]>>()

async function parse(source: RunSource, task: string): Promise<LoadedCall[]> {
  const [events, rows] = await Promise.all([readEvents(source, task), readTrace(source, task)])
  const activeLive = source.kind === 'live' && !events.some(e => e.event === 'RUN_END' || e.event === 'RUN_STOPPED')
  return parseTraceCalls(rows, events, activeLive)
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
  const needPrompt = typeof call.row.system_prompt !== 'string' || !call.row.system_prompt
  const fallback = needPrompt ? (await readAgentPrompt(call.summary.agent))?.markdown ?? '' : ''
  return toCallDetail(call, fallback)
}
