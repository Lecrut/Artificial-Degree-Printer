import type { Point, RunProfile } from '../types/compare'
import type { RunEvent, RunRef } from '../types/run'
import { num, str } from './events'
import { summarizeRun } from './summary'

/** Characters per token, the usual rough ratio; the models run locally and report no token counts. */
export const CHARS_PER_TOKEN = 4

/** Series colors of compared runs, validated for color-blind separation on the navy surface (max 4 runs). */
export const SERIES_COLORS = ['#3987e5', '#d95926', '#199e70', '#c98500'] as const
export const MAX_COMPARED = SERIES_COLORS.length

/** Model tiers get their own validated pair, so a tier never looks like one of the runs. */
export const TIER_COLORS: Record<string, string> = { SML: '#199e70', LRM: '#9085e9' }

/** A running total that steps up at each event it is given. */
function runningTotal(start: number, events: RunEvent[], amount: (e: RunEvent) => number): Point[] {
  let total = 0
  const points: Point[] = [[0, 0]]
  for (const e of events) {
    total += amount(e)
    points.push([(Date.parse(e.ts) - start) / 60_000, total])
  }
  return points
}

/** Totals and running totals of one run: calls, model time, prompt size, finished tasks, per agent and tier. */
export function runProfile(task: string, events: RunEvent[]): RunProfile {
  const summary = summarizeRun(task, events)
  const start = events.length ? Date.parse(events[0]!.ts) : 0
  const ends = events.filter(e => e.event === 'LLM_CALL_END')
  const starts = events.filter(e => e.event === 'LLM_CALL_START')
  const done = events.filter(e => e.event === 'TASK_DONE')

  const agents: RunProfile['agents'] = {}
  const tierSeconds: Record<string, number> = {}
  for (const e of ends) {
    const agent = (agents[str(e, 'agent')] ??= { calls: 0, seconds: 0 })
    agent.calls += 1
    agent.seconds += num(e, 'elapsed_s')
    tierSeconds[str(e, 'tier')] = (tierSeconds[str(e, 'tier')] ?? 0) + num(e, 'elapsed_s')
  }

  return {
    summary,
    llmSeconds: ends.reduce((sum, e) => sum + num(e, 'elapsed_s'), 0),
    tierSeconds,
    promptChars: starts.reduce((sum, e) => sum + num(e, 'prompt_chars'), 0),
    agents,
    over: {
      calls: runningTotal(start, ends, () => 1),
      llmMinutes: runningTotal(start, ends, e => num(e, 'elapsed_s') / 60),
      tasksDone: runningTotal(start, done, () => 1),
      promptTokens: runningTotal(start, starts, e => num(e, 'prompt_chars') / CHARS_PER_TOKEN),
    },
  }
}

/** The total of a running series at a minute: its last step at or before it. */
export function valueAt(points: Point[], minute: number): number | null {
  if (!points.length || minute < points[0]![0]) return null
  let value = points[0]![1]
  for (const [m, v] of points) {
    if (m > minute) break
    value = v
  }
  return value
}

/** `git:362092f:01_rl_tictactoe` — a run as one URL-safe token, and back. */
export function runKey(at: RunRef): string {
  return `${at.source}:${at.ref}:${at.task}`
}

export function parseRunKey(key: string): RunRef | null {
  const [source, ref, task] = key.split(':')
  if (!task || !ref || !['git', 'results', 'live'].includes(source ?? '')) return null
  return { source: source as RunRef['source'], ref, task }
}
