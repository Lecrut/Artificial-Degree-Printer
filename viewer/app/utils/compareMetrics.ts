import type { ComparedRun, RunProfile } from '#shared/types/compare'
import { CHARS_PER_TOKEN } from '#shared/utils/compare'
import { formatDuration } from '#shared/utils/format'
import { labels } from './labels'

export interface MetricRow {
  label: string
  value: (p: RunProfile) => number | null
  format: (value: number) => string
  /** Which way is better; a difference in that direction is green. */
  better: 'lower' | 'higher'
  /** Known only from events.jsonl; runs before 2026-11-17 have just duration, calls and replans. */
  needsEvents: boolean
}

/** The value of a row for a run, or null when that run cannot know it. */
export function metricValue(row: MetricRow, run: ComparedRun): number | null {
  return row.needsEvents && !run.hasEvents ? null : row.value(run.profile)
}

const minutes = (seconds: number) => `${(seconds / 60).toFixed(1)} min`
const integer = (n: number) => Math.round(n).toLocaleString('pl-PL')
const thousands = (n: number) => (n >= 1000 ? `${(n / 1000).toFixed(1)} tys.` : integer(n))
const rows = labels.compare.rows

// The rows of the side-by-side table, in reading order: time, progress, spending, trouble.
export const METRIC_ROWS: MetricRow[] = [
  { label: rows.duration, value: p => p.summary.durationSeconds, format: v => formatDuration(v), better: 'lower', needsEvents: false },
  { label: rows.tasksDone, value: p => p.summary.tasksDone, format: integer, better: 'higher', needsEvents: true },
  { label: rows.llmCalls, value: p => p.summary.llmCalls, format: integer, better: 'lower', needsEvents: false },
  { label: rows.llmMinutes, value: p => p.llmSeconds, format: minutes, better: 'lower', needsEvents: true },
  { label: rows.smlMinutes, value: p => p.tierSeconds.SML ?? 0, format: minutes, better: 'lower', needsEvents: true },
  { label: rows.lrmMinutes, value: p => p.tierSeconds.LRM ?? 0, format: minutes, better: 'lower', needsEvents: true },
  { label: rows.secondsPerCall, value: p => (p.summary.llmCalls ? p.llmSeconds / p.summary.llmCalls : null), format: v => `${v.toFixed(1)} s`, better: 'lower', needsEvents: true },
  { label: rows.promptTokens, value: p => (p.promptChars ? p.promptChars / CHARS_PER_TOKEN : null), format: thousands, better: 'lower', needsEvents: true },
  { label: rows.failedVerdicts, value: p => p.summary.failedVerdicts, format: integer, better: 'lower', needsEvents: true },
  { label: rows.rejectedWrites, value: p => p.summary.rejectedWrites, format: integer, better: 'lower', needsEvents: true },
  { label: rows.replans, value: p => p.summary.replans, format: integer, better: 'lower', needsEvents: false },
]

/** The change against the first run, in percent, and whether it is for the better. */
export function delta(row: MetricRow, base: ComparedRun, run: ComparedRun): { text: string, good: boolean } | null {
  const [a, b] = [metricValue(row, base), metricValue(row, run)]
  if (a === null || b === null || a === b) return null
  const pct = a === 0 ? null : ((b - a) / Math.abs(a)) * 100
  const good = row.better === 'lower' ? b < a : b > a
  return { text: pct === null ? (b > a ? '+' : '−') : `${pct > 0 ? '+' : '−'}${Math.abs(pct).toFixed(0)}%`, good }
}
