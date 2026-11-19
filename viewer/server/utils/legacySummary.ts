import type { TaskSummary } from '#shared/types/run'
import type { RunSource } from './sources/types'
import { parseJson } from '#shared/utils/json'

interface LegacyTask {
  task_id?: string
  title_pl?: string
  orchestrator_status?: string
  replan_count?: number
  llm_telemetry?: { calls_count?: number }
  timings_ms?: { total_task_ms?: number }
}

/** What `benchmark_summary.json` says about a task: runs before 2026-11-17 have no events.jsonl, only this. */
export async function legacyTask(source: RunSource, task: string): Promise<LegacyTask | null> {
  const summary = parseJson<{ tasks?: LegacyTask[] }>(await source.readShared('benchmark_summary.json'))
  return summary?.tasks?.find(t => t.task_id === task) ?? null
}

/** A summary without events, filled in from the old summary file. */
export function mergeLegacy(summary: TaskSummary, legacy: LegacyTask | null): TaskSummary {
  if (!legacy || summary.status !== 'NO_EVENTS') return summary
  const ms = legacy.timings_ms?.total_task_ms
  return {
    ...summary,
    status: legacy.orchestrator_status ?? summary.status,
    title: summary.title ?? legacy.title_pl ?? null,
    llmCalls: legacy.llm_telemetry?.calls_count ?? 0,
    replans: legacy.replan_count ?? 0,
    durationSeconds: typeof ms === 'number' ? ms / 1000 : null,
  }
}
