import type { RunRef, TaskSummary } from './run'

/** A point of a running total: minutes since the run started, and the total so far. */
export type Point = [minutes: number, value: number]

/** What one run spent, as totals and as running totals over its time. */
export interface RunProfile {
  summary: TaskSummary
  /** Seconds the models computed, all and per tier (SML does the work, LRM assists). */
  llmSeconds: number
  tierSeconds: Record<string, number>
  /** Characters sent to the models; ≈ tokens = chars / 4 (local models report no tokens). */
  promptChars: number
  agents: Record<string, { calls: number, seconds: number }>
  over: {
    calls: Point[]
    llmMinutes: Point[]
    tasksDone: Point[]
    promptTokens: Point[]
  }
}

/** One run on the compare page: where it is, how it is named, which series color it wears. */
export interface ComparedRun {
  at: RunRef
  label: string
  color: string
  /** False for runs before 2026-11-17: no events.jsonl, so nothing to draw over time. */
  hasEvents: boolean
  profile: RunProfile
}
